#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pandas",
#   "tabulate",
# ]
# ///

"""
This script analyzes and compares two dive JSON output files to find directories
that have grown, shrunk, been added, or been removed.
"""

import argparse
import json
import pandas as pd
from collections import defaultdict
import os

def get_dir_sizes(json_file):
    """
    Reads data from a dive JSON file and calculates directory sizes.
    Returns a pandas DataFrame with directory paths and their sizes.
    """
    import pathlib

    with open(json_file, 'r') as f:
        data = json.load(f)

    all_files = []
    for layer in data.get('layer', []):
        for file_info in layer.get('fileList', []):
            if file_info.get('size', 0) > 0 and not file_info.get('isDir', False):
                all_files.append({'path': file_info['path'], 'size': file_info['size']})

    dir_sizes = defaultdict(int)

    for file_info in all_files:
        size = file_info['size']
        # Use pathlib for robust parent path resolution
        p = pathlib.Path(file_info['path'])
        
        # Add size to all parent directories
        for parent in p.parents:
            # path.parents for 'usr/lib/foo' yields 'usr/lib', 'usr', '.'
            # we want to skip the '.' entry and format as absolute paths
            if str(parent) != '.':
                dir_sizes[f"/{parent}"] += size

    # Calculate total size for the root directory
    total_size = sum(f['size'] for f in all_files)
    dir_sizes['/'] = total_size

    df = pd.DataFrame(dir_sizes.items(), columns=['Path', 'Size'])
    return df

def compare_data(json_before, json_after, limit):
    """
    Compares two dive JSON files and identifies directories that have
    grown/shrunk the most.
    """
    try:
        df_before = get_dir_sizes(json_before)
        df_after = get_dir_sizes(json_after)

        # Merge the two dataframes on the Path
        df_merged = pd.merge(df_before, df_after, on='Path', suffixes=('_before', '_after'), how='outer')
        df_merged.fillna(0, inplace=True)

        # Calculate the difference
        df_merged['Size_diff'] = df_merged['Size_after'] - df_merged['Size_before']
        
        # Convert sizes to MiB for display
        for col in ['Size_before', 'Size_after', 'Size_diff']:
            df_merged[f'{col}_MiB'] = df_merged[col] / (1024 * 1024)

        # --- Top Grown / New Directories ---
        df_grown = df_merged[df_merged['Size_diff'] > 0].sort_values(by='Size_diff', ascending=False)
        
        print(f"Top {limit} Grown or New Directories:")
        from tabulate import tabulate
        print(tabulate(
            df_grown.head(limit)[['Path', 'Size_before_MiB', 'Size_after_MiB', 'Size_diff_MiB']],
            headers=['Path', 'Before (MiB)', 'After (MiB)', 'Growth (MiB)'],
            tablefmt='grid',
            floatfmt=".2f"
        ))
        print("\n" + "="*80 + "\n")

        # --- Top Shrunk / Removed Directories ---
        df_shrunk = df_merged[df_merged['Size_diff'] < 0].sort_values(by='Size_diff', ascending=True)

        print(f"Top {limit} Shrunk or Removed Directories:")
        print(tabulate(
            df_shrunk.head(limit)[['Path', 'Size_before_MiB', 'Size_after_MiB', 'Size_diff_MiB']],
            headers=['Path', 'Before (MiB)', 'After (MiB)', 'Shrinkage (MiB)'],
            tablefmt='grid',
            floatfmt=".2f"
        ))

    except FileNotFoundError as e:
        print(f"Error: The file '{e.filename}' was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Compare two dive JSON outputs to find directories that have grown, shrunk, or are new/removed.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("json_before", help="The path to the 'before' dive JSON file.")
    parser.add_argument("json_after", help="The path to the 'after' dive JSON file.")
    parser.add_argument("--limit", type=int, default=20, help="The number of directories to show in each list (grown and shrunk).")
    
    args = parser.parse_args()
    
    compare_data(args.json_before, args.json_after, args.limit)
