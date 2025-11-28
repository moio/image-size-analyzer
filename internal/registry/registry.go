package registry

import (
	"fmt"
	"os"
	"regexp"
	"time"

	"github.com/Masterminds/semver" // Reintroducing semver
	"github.com/google/go-containerregistry/pkg/name"
	"github.com/google/go-containerregistry/pkg/v1"
	"github.com/google/go-containerregistry/pkg/v1/remote"
)

type ImageData struct {
	Version    string
	SizeMiB    float64
	LastPush   time.Time
	Major      uint64
	Minor      uint64
	Patch      uint64
	Prerelease string
}

func GetImageSizes(registry, image, osName, arch, tagRegex string) ([]ImageData, error) {
	repoStr := fmt.Sprintf("%s/%s", registry, image)
	repo, err := name.NewRepository(repoStr)
	if err != nil {
		return nil, fmt.Errorf("parsing repo %q: %w", repoStr, err)
	}

	tags, err := remote.List(repo)
	if err != nil {
		return nil, fmt.Errorf("reading tags for %q: %w", repo, err)
	}

	re, err := regexp.Compile(tagRegex)
	if err != nil {
		return nil, fmt.Errorf("compiling regex %q: %w", tagRegex, err)
	}

	var filteredTags []string
	for _, tag := range tags {
		if re.MatchString(tag) {
			filteredTags = append(filteredTags, tag)
		}
	}

	platform := v1.Platform{
		OS:           osName,
		Architecture: arch,
	}

	var data []ImageData
	for _, tag := range filteredTags {
		imgStr := fmt.Sprintf("%s/%s:%s", registry, image, tag)
		ref, err := name.ParseReference(imgStr)
		if err != nil {
			return nil, fmt.Errorf("parsing image reference %q: %w", imgStr, err)
		}

		fmt.Fprintf(os.Stderr, "Processing tag: %s\n", tag)
		img, err := remote.Image(ref, remote.WithPlatform(platform))
		if err != nil {
			// Some tags may not be accessible, so we'll just skip them.
			continue
		}

		configFile, err := img.ConfigFile()
		if err != nil {
			continue
		}

		manifest, err := img.Manifest()
		if err != nil {
			continue
		}

		var size int64
		for _, layer := range manifest.Layers {
			size += layer.Size
		}

		sizeMiB := float64(size) / (1024 * 1024)

		imageData := ImageData{Version: tag, SizeMiB: sizeMiB, LastPush: configFile.Created.Time}

		// Attempt to parse semver
		v, err := semver.NewVersion(tag)
		if err == nil {
			imageData.Major = uint64(v.Major())
			imageData.Minor = uint64(v.Minor())
			imageData.Patch = uint64(v.Patch())
			imageData.Prerelease = v.Prerelease()
		}
		data = append(data, imageData)
	}

	return data, nil
}
