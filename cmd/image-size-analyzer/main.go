package main

import (
	"flag"
	"fmt"
	"image-size-analyzer/internal/output"
	"image-size-analyzer/internal/registry"
	"os"
	"strings"
)

func main() {
	image := flag.String("image", "google-appengine/python", "OCI image to analyze (e.g., golang)")
	registryName := flag.String("registry", "gcr.io", "Registry to use")
	csv := flag.Bool("csv", true, "Generate CSV output")
	osName := flag.String("os", "linux", "Operating system for the image")
	arch := flag.String("arch", "amd64", "Architecture for the image")
	tagRegex := flag.String("tag-regex", ".*", "Regex to filter tags")
	flag.Parse()

	if *image == "" {
		fmt.Println("Error: --image flag is required")
		flag.Usage()
		os.Exit(1)
	}

	fmt.Printf("Analyzing image: %s/%s for %s/%s\n", *registryName, *image, *osName, *arch)

	data, err := registry.GetImageSizes(*registryName, *image, *osName, *arch, *tagRegex)
	if err != nil {
		fmt.Printf("Error: %v\n", err)
		os.Exit(1)
	}

	sanitizedImage := strings.ReplaceAll(*image, "/", "_")
	csvFileName := fmt.Sprintf("%s_%s_%s.csv", sanitizedImage, *osName, *arch)

	if *csv {
		file, err := os.Create(csvFileName)
		if err != nil {
			fmt.Printf("Error creating CSV file: %v\n", err)
			os.Exit(1)
		}
		defer file.Close()

		if err := output.ToCSV(data, file, *registryName, *image, *osName, *arch); err != nil {
			fmt.Printf("Error generating CSV: %v\n", err)
			os.Exit(1)
		}
		fmt.Printf("CSV output saved to %s\n", csvFileName)
	}
}
