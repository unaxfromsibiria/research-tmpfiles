package main

import (
	"bufio"
	"flag"
	"fmt"
	"io"
	"log"
	"os"
	"strconv"
	"strings"
	"time"
)

var msize int
var compact bool
var show bool
var path string

func init() {
	flag.StringVar(&path, "path", "", "File path")
	flag.IntVar(&msize, "size", 0, "New matrix size.")
	flag.BoolVar(&compact, "compact", false, "Compact to size.")
	flag.BoolVar(&show, "show", false, "Print to stdout.")
	flag.Parse()
}

// MxObj - simple matrix
type MxObj struct {
	content [][]float64
}

func (mx *MxObj) size() int {
	return len(mx.content)
}

func (mx *MxObj) fill(line *[]float64) {
	mx.content = append(mx.content, *line)
}

func (mx MxObj) String() string {
	if len(mx.content) < 1 {
		return "||"
	}
	lines := make([]string, len(mx.content))
	for index, line := range mx.content {
		lineStr := ""
		for _, val := range line {
			lineStr = fmt.Sprintf("%s %.6f", lineStr, val)
		}
		lines[index] = fmt.Sprintf("|%s|", lineStr)
	}
	return strings.Join(lines, "\n")
}

func (mx *MxObj) isValid() bool {
	for _, line := range mx.content {
		if len(line) != len(mx.content) {
			return false
		}
	}
	return true
}

// Compact matrix to new size.
func (mx *MxObj) Compact(newSize int) {
	mxSize := len(mx.content)
	if mxSize < 1 {
		return
	}
	step := float64(mxSize) / float64(newSize)
	var volume, x, y, ax, bx, ay, by, i, j int
	var msum float64
	newContent := make([][]float64, newSize)
	for x = 0; x < newSize; x++ {
		ax = int(float64(x-1) * step)
		if ax < 0 {
			ax = 0
		}
		bx = int(float64(x+1) * step)
		if bx > mxSize {
			bx = mxSize
		}
		line := make([]float64, newSize)
		for y = 0; y < newSize; y++ {
			ay = int(float64(y-1) * step)
			if ay < 0 {
				ay = 0
			}
			by = int(float64(y+1) * step)
			if by > mxSize {
				by = mxSize
			}
			volume = (bx - ax) * (by - ay)
			msum = 0
			for i = ax; i < bx; i++ {
				for j = ay; j < by; j++ {
					msum += mx.content[i][j]
				}
			}
			line[y] = msum / float64(volume)
		}
		newContent[x] = line
	}
	mx.content = newContent
}

// Load matrix from text file.
func (mx *MxObj) Load(file io.Reader) error {
	scanner := bufio.NewScanner(file)
	for scanner.Scan() {
		var line []float64
		for _, x := range strings.Split(scanner.Text(), " ") {
			if val, err := strconv.ParseFloat(x, 64); err == nil {
				line = append(line, val)
			}
		}
		mx.fill(&line)
	}
	if err := scanner.Err(); err != nil {
		return err
	}
	if !mx.isValid() {
		return fmt.Errorf("Matrix size incorrect.")
	}
	return nil
}

// Save results.
func (mx *MxObj) Save(file io.Writer) error {
	lastIndex := len(mx.content) - 1
	var lastCh byte
	var data []byte
	for _, line := range mx.content {
		for index, val := range line {
			if index == lastIndex {
				lastCh = '\n'
			} else {
				lastCh = ' '
			}
			data = []byte(fmt.Sprintf("%.6f", val))
			if _, err := file.Write(append(data, lastCh)); err != nil {
				return err
			}
		}
	}
	return nil
}

func main() {
	if (compact && show) || (!compact && !show) {
		fmt.Println("Choise 'show' or 'compact' action.")
		return
	}
	mx := MxObj{}
	if file, err := os.Open(path); err != nil {
		log.Fatal(err)
		return
	} else {
		defer file.Close()
		start := time.Now()
		if err := mx.Load(file); err != nil {
			log.Fatalln(err)
		}
		openTime := float32(time.Since(start)) / 1E6
		fmt.Printf("open: %.6f ms\n", openTime)
	}
	if compact {
		if msize > 0 && msize < mx.size() {
			oldPostfix := fmt.Sprintf("_%d", mx.size())
			start := time.Now()
			mx.Compact(msize)
			openTime := float32(time.Since(start)) / 1E6
			fmt.Printf("squeeze: %.6f ms\n", openTime)
			// and save
			newPostfix := fmt.Sprintf("_%d", mx.size())
			newPath := strings.Replace(path, oldPostfix, newPostfix, 1)
			if outfile, err := os.Create(newPath); err != nil {
				log.Fatal(err)
				return
			} else {
				defer outfile.Close()
				start = time.Now()
				mx.Save(outfile)
				openTime = float32(time.Since(start)) / 1E6
				fmt.Printf("save: %.6f ms\n", openTime)
				fmt.Printf("New matrix saved into: %s", newPath)
			}
		} else {
			log.Fatalln("Incorrect size.")
		}
	}
	if show {
		fmt.Println(mx)
	}
}
