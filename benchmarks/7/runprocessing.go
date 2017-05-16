package main

import (
	"flag"
	"fmt"
	"log"
	"math/rand"
	"os"
	"os/signal"
	"runtime"
	"strconv"
	"strings"
	"syscall"
	"time"

	wp "./workerspool"
)

const (
	defaultMessageCount    = 100
	defaultInputStreamSize = 32
	defaultPoolSize        = 10
	gcEnvKey               = "GOGC"
)

var messageCount, poolSize, inputStreamSize int
var gcOff bool

type clientResult struct {
	count    int
	errCount int
	execTime float32
	inData   int
}

func init() {
	flag.IntVar(&messageCount, "message", defaultMessageCount, "Message count.")
	flag.IntVar(&poolSize, "pool", defaultPoolSize, "Pool size.")
	flag.IntVar(&inputStreamSize, "input", defaultInputStreamSize, "Count of input streams.")
	flag.Parse()
	gcOff = strings.ToLower(os.Getenv(gcEnvKey)) == "off"
	if gcOff {
		fmt.Println("GC is Off")
	}
}

func handler(worker int, data wp.ContentType) wp.ContentType {
	var answer string
	if value, err := strconv.Atoi(string(data)); err != nil {
		answer = fmt.Sprintf("error: %s", err)
	} else {
		// convert the number to hex format (base 16)
		answer = fmt.Sprintf("%x", value)
	}
	return wp.ContentType(answer)
}

func inputStream(index int, workers *wp.WorkerPool, resChan chan clientResult) {
	start := time.Now()
	result := clientResult{count: messageCount}
	for i := 0; i < messageCount; i++ {
		//simple random int value
		num := rand.Intn(1e6)
		numStr := fmt.Sprintf("%d", num)
		result.inData += len(numStr)
		if answer, err := workers.Exec(wp.ContentType(numStr)); err != nil {
			log.Println(err)
			result.errCount++
		} else {
			// return numbers in hex
			// check it
			resNum := string(*answer)
			if resNum != fmt.Sprintf("%x", num) {
				log.Printf("%d:%d %s -> %s\n", index, i, numStr, resNum)
				result.errCount++
			}
		}
	}
	result.execTime = float32(time.Since(start)) / 1E9
	resChan <- result
}

func showResult(resChan chan clientResult) {
	if gcOff {
		defer runtime.GC()
	}
	waitResult := true
	countRes := 0
	totalResCount := 0
	totalResTime := float32(0)
	totalData := 0
	waitTime := float32(0)
	start := time.Now()
	for waitResult {
		res := <-resChan
		if res.count > 0 {
			countRes++
			totalData += res.inData
			totalResTime += res.execTime
			totalResCount += res.count
			waitResult = countRes < inputStreamSize
			if !waitResult {
				waitTime = float32(time.Since(start)) / 1E9
			}
		} else {
			waitResult = false
		}
	}
	log.Printf(`
	input data size: %d
	msg count: %d
	avg worker time (ms): %.6f
	avg msg exec time (ms): %.6f
	client wait (sec): %.6f
	`,
		totalData,
		totalResCount*inputStreamSize,
		totalResTime*1000./float32(totalResCount),
		totalResTime*1000./float32(totalResCount*inputStreamSize),
		waitTime)
}

func main() {
	pool := wp.NewWorkerPool(poolSize, handler, 1)
	signalChannel := make(chan os.Signal, 1)
	signal.Notify(signalChannel, os.Interrupt)
	signal.Notify(signalChannel, syscall.SIGTERM)
	resChan := make(chan clientResult, inputStreamSize)
	defer close(resChan)
	for i := 0; i < inputStreamSize; i++ {
		go inputStream(i, pool, resChan)
	}
	go showResult(resChan)
	for msg := range signalChannel {
		log.Printf("out with: %s\n", msg)
		break
	}
	pool.Stop()
}
