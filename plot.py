#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "matplotlib",
#   "pandas",
# ]
# ///

"""
This script plots data from a CSV file using matplotlib.
It's a self-contained script that uses uv to manage its dependencies.
"""

import argparse
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np

def plot_data(csv_file, args):
    """
    Reads data from a CSV file and generates an interactive plot.
    """
    try:
        # Read the image name from the first line of the CSV
        with open(csv_file, 'r') as f:
            title_line = f.readline().strip()
            # Extract the image name from a line like "# Image Size Analysis for index.docker.io/alpine (linux/amd64)"
            image_name = title_line.split(" for ")[1].split(" (")[0]
            title = f"Image Size Analysis for {image_name}"

        # Read the CSV data, skipping the first row (the title)
        data = pd.read_csv(csv_file, skiprows=1)
        print("--- data ---")
        print(data)
        
        # Parse 'LastPush' column as datetime objects
        data['LastPush'] = pd.to_datetime(data['LastPush'])
        
        # Get unique minor versions
        minor_versions = data['Minor'].unique()
        print("--- minor_versions ---")
        print(minor_versions)
        
        # Create a color map
        colors = cm.get_cmap('tab10')(np.linspace(0, 1, len(minor_versions)))

        plt.figure(figsize=(12, 7))

        lines = []
        for i, minor in enumerate(minor_versions):
            minor_data = data[data['Minor'] == minor]
            print(f"--- minor_data (minor: {minor}) ---")
            print(minor_data)
            # Sort by LastPush to ensure the line plot is ordered correctly
            minor_data = minor_data.sort_values(by='LastPush')
            line, = plt.plot(minor_data['LastPush'], minor_data['SizeMiB'], marker='o', linestyle='-', color=colors[i], label=minor)
            lines.append(line)

            # Add labels to the points
            for index, row in minor_data.iterrows():
                plt.text(row['LastPush'], row['SizeMiB'], f" {row['Version']}", fontsize=9, va='center')

        plt.xlabel('Last Push Date')
        plt.ylabel('Size (MiB)')
        plt.title(title)
        plt.legend(handles=lines, title="Minor Versions")
        plt.grid(True)
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()

        if args.interactive:
            plt.show()
        else:
            output_filename = csv_file.replace('.csv', '.svg')
            plt.savefig(output_filename)
            print(f"Plot saved to {output_filename}")

    except FileNotFoundError:
        print(f"Error: The file '{csv_file}' was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Plot image size data from a CSV file.")
    parser.add_argument("csv_file", help="The path to the CSV file to plot.")
    parser.add_argument("--interactive", action="store_true", help="Display the plot interactively instead of saving to a file.")
    args = parser.parse_args()
    plot_data(args.csv_file, args)
