package output

import (
	"image-size-analyzer/internal/registry"
	"sort"
)

func SortData(data []registry.ImageData) {
	sort.Slice(data, func(i, j int) bool {
		return data[i].LastPush.Before(data[j].LastPush)
	})
}
