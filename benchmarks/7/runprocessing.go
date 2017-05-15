package main

import (
	"flag"
	"fmt"
	"log"
	"math/rand"
	"os"
	"os/signal"
	"syscall"

	"strconv"

	wp "./workerspool"
)

const (
	defaultMessageCount    = 100
	defaultInputStreamSize = 32
	defaultPoolSize        = 10
)

var messageCount, poolSize, inputStreamSize int

func init() {
	flag.IntVar(&messageCount, "message", defaultMessageCount, "Message count.")
	flag.IntVar(&poolSize, "pool", defaultPoolSize, "Pool size.")
	flag.IntVar(&inputStreamSize, "input", defaultInputStreamSize, "Count of input streams.")
	flag.Parse()
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

func inputStream(index int, workers *wp.WorkerPool) {
	for i := 0; i < messageCount; i++ {
		//simple random int value
		num := rand.Intn(1e6)
		numStr := fmt.Sprintf("%d", num)
		if result, err := workers.Exec(wp.ContentType(numStr)); err != nil {
			log.Println(err)
		} else {
			// return numbers in hex
			// check it
			resNum := string(*result)
			if resNum != fmt.Sprintf("%x", num) {
				log.Println("%d:%d %s -> %s\n", index, i, numStr, resNum)
			}
		}
	}
}

func main() {
	pool := wp.NewWorkerPool(poolSize, handler, 1)
	signalChannel := make(chan os.Signal, 1)
	signal.Notify(signalChannel, os.Interrupt)
	signal.Notify(signalChannel, syscall.SIGTERM)
	for i := 0; i < inputStreamSize; i++ {
		go inputStream(i, pool)
	}
	for msg := range signalChannel {
		log.Printf("out with: %s\n", msg)
		break
	}
	pool.Stop()
}
