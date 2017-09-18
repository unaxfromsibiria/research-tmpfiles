package main

import (
	"flag"
	"image"
	"image/jpeg"
	"log"
	"os"
	"time"
)

const (
	LayersCount       = 3
	localitySize      = 5
	defaultDifference = 64
)

var imgPath string

type LayerFilter struct {
	w, h     int
	contentR [][]uint8
	contentG [][]uint8
	contentB [][]uint8
	layerR   [][]uint8
	layerG   [][]uint8
	layerB   [][]uint8
}

func init() {
	flag.StringVar(&imgPath, "img", "", "File path")
	flag.Parse()
}

func maxDifference(dataPtr *[][]uint8, w, h, x, y int) uint8 {
	var i, j int
	ax := x - localitySize
	bx := x + localitySize
	ay := y - localitySize
	by := y + localitySize
	var maxV uint8 = 255
	var minV uint8
	data := *dataPtr
	if ax < 0 {
		ax = 0
	}
	if bx > w {
		bx = w
	}
	if ay < 0 {
		ay = 0
	}
	if by > h {
		by = h
	}

	for i = ax; i < bx; i++ {
		for j = ay; j < by; j++ {
			if minV > data[i][j] {
				minV = data[i][j]
			} else if maxV < data[i][j] {
				maxV = data[i][j]
			}
		}
	}
	return maxV - minV
}

func searchCounter(w, h int, data, layer *[][]uint8, result chan bool) {
	var i, j int
	for i = 0; i < w; i++ {
		for j = 0; j < h; j++ {
			if maxDifference(data, w, h, i, j) > defaultDifference {
				(*layer)[i][j] = 1
			}
		}
	}
	result <- true
}

func (layers *LayerFilter) apply() {
	done := make(chan bool, LayersCount)
	go searchCounter(layers.w, layers.h, &(layers.contentR), &(layers.layerR), done)
	go searchCounter(layers.w, layers.h, &(layers.contentG), &(layers.layerG), done)
	go searchCounter(layers.w, layers.h, &(layers.contentB), &(layers.layerB), done)
	doneCount := 0
	for res := range done {
		if res {
			doneCount++
		}
		if doneCount >= LayersCount {
			break
		}
	}
}

func initLayers(img image.Image, start time.Time) *LayerFilter {
	data := img.Bounds()
	w := data.Max.X
	h := data.Max.Y
	layers := LayerFilter{w: w, h: h}
	layers.contentR = make([][]uint8, w)
	layers.contentG = make([][]uint8, w)
	layers.contentB = make([][]uint8, w)
	layers.layerR = make([][]uint8, w)
	layers.layerG = make([][]uint8, w)
	layers.layerB = make([][]uint8, w)

	for i := 0; i < w; i++ {
		lineR := make([]uint8, h)
		lineG := make([]uint8, h)
		lineB := make([]uint8, h)
		for j := 0; j < h; j++ {
			r, g, b, _ := img.At(i, j).RGBA()
			lineR[j], lineG[j], lineB[j] = uint8(r), uint8(g), uint8(b)
		}
		layers.contentR[i] = lineR
		layers.contentG[i] = lineG
		layers.contentB[i] = lineB
		layers.layerR[i] = make([]uint8, h)
		layers.layerG[i] = make([]uint8, h)
		layers.layerB[i] = make([]uint8, h)
	}
	doneTime := time.Now()
	execTime := doneTime.Sub(start)
	log.Println("Init time: ", execTime)
	return &layers
}

func main() {
	log.Println("Open image from", imgPath)
	startTime := time.Now()
	if file, err := os.Open(imgPath); err != nil {
		log.Fatalln(err)
	} else if img, err := jpeg.Decode(file); err != nil {
		log.Fatalln(err)
	} else {
		defer file.Close()
		layers := initLayers(img, startTime)
		start := time.Now()
		layers.apply()
		doneTime := time.Now()
		execTime := doneTime.Sub(start)
		log.Println("Apply time: ", execTime)
	}
}
