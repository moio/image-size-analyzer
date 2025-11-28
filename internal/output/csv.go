package output

import (
	"encoding/csv"
	"fmt"
	"image-size-analyzer/internal/registry"
	"io"
	"strconv"
)

func ToCSV(data []registry.ImageData, writer io.Writer, registryName, image, osName, arch string) error {
	SortData(data)

	w := csv.NewWriter(writer)
	defer w.Flush()

	title := fmt.Sprintf("# Image Size Analysis for %s/%s (%s/%s)", registryName, image, osName, arch)
	if err := w.Write([]string{title}); err != nil {
		return fmt.Errorf("writing CSV title: %w", err)
	}

	if err := w.Write([]string{"Version", "SizeMiB", "LastPush", "Major", "Minor", "Patch", "Prerelease"}); err != nil {
		return fmt.Errorf("writing CSV header: %w", err)
	}

	for _, record := range data {
		major := ""
		if record.Major != 0 || (record.Major == 0 && (record.Minor != 0 || record.Patch != 0 || record.Prerelease != "")) { // Only print 0 if it's a valid semver like 0.1.0
			major = strconv.FormatUint(record.Major, 10)
		}
		minor := ""
		if record.Minor != 0 || (record.Minor == 0 && (record.Major != 0 || record.Patch != 0 || record.Prerelease != "")) {
			minor = fmt.Sprintf("%d.%d", record.Major, record.Minor)
		}
		patch := ""
		if record.Patch != 0 || (record.Patch == 0 && (record.Major != 0 || record.Minor != 0 || record.Prerelease != "")) {
			patch = strconv.FormatUint(record.Patch, 10)
		}

		row := []string{
			record.Version,
			strconv.FormatFloat(record.SizeMiB, 'f', 2, 64),
			record.LastPush.Format("2006-01-02 15:04:05"),
			major,
			minor,
			patch,
			record.Prerelease,
		}
		if err := w.Write(row); err != nil {
			return fmt.Errorf("writing CSV record: %w", err)
		}
	}

	return nil
}
