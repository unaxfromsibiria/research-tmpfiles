package main

import (
	"flag"
	"fmt"
	"math/rand"
	"time"

	nm "./netmutex"
)

var port int
var host string
var operation string
var mutexId string
var resource string
var capruteTimeout int
var captureAutoRelease bool

func init() {
	flag.IntVar(&port, "port", 8900, "TCP port of server.")
	flag.StringVar(&host, "host", "127.0.0.1", "Host (ip) of server.")
	flag.StringVar(&operation, "operation", "capture", "Client action (capture,release,example).")
	flag.StringVar(&mutexId, "mutex", "", "Mutex Id.")
	flag.StringVar(&resource, "resource", "", "Resource name.")
	flag.IntVar(&capruteTimeout, "timeout", 0, "Auto release mutex timeout (for operation - capture).")
	flag.BoolVar(&captureAutoRelease, "autorelease", false, "Auto release mutex after disconnection.")
	flag.Parse()
}

func capture(client *nm.Client) string {
	mutex, err := client.Capture(resource, capruteTimeout, captureAutoRelease)
	if err != nil {
		return fmt.Sprintf("Capture problem: %s", err)
	}
	return fmt.Sprintf("Mutex id: %s", mutex)
}

func release(client *nm.Client) string {
	mutex, err := client.Release(mutexId)
	if err != nil {
		return fmt.Sprintf("Release problem: %s", err)
	}
	return fmt.Sprintf("Mutex id: %s", mutex)
}

func randomClientRun(index, commandCount int, results chan float32, resourcePool []string) {
	start := time.Now()
	fmt.Println("client", index, "started")
	client := nm.NewClient(host, port)
	err := client.Open()
	defer client.Close()
	if err != nil {
		fmt.Println("client connection error", err)
	} else {
		for i := 0; i < commandCount; i++ {
			timeout := 2 + rand.Intn(18)
			resrc := resourcePool[(1+rand.Intn(len(resourcePool)))-1]
			autoRel := rand.Intn(10) > 5
			res, err := client.Capture(resrc, timeout, autoRel)
			if err != nil {
				fmt.Println(index, "error>", err)
			} else {
				fmt.Println(index, "mutex>", res)
			}
		}
	}
	result := (float32(time.Since(start)) / 1E6)
	fmt.Printf("client connection %d time: %.2f ms\n", index, result)
	results <- result
}

func example(client *nm.Client) string {
	msg := `
	Create %d client connection.
	Send %d command with random parameters.
	Using %d resource names.
	`
	clientCount := 25
	commandCount := 100
	resourcePoolSize := 50
	fmt.Printf(msg, clientCount, commandCount, resourcePoolSize)
	resources := make([]string, resourcePoolSize)
	for i := 0; i < resourcePoolSize; i++ {
		randBytes, _ := nm.NewMutexId()
		resources[i] = nm.MutexToStr(*randBytes)
	}
	done := make(chan float32, clientCount)
	for i := 1; i <= clientCount; i++ {
		go randomClientRun(i, commandCount, done, resources)
	}
	var results []float32
	for len(results) < clientCount {
		execTime := <-done
		if execTime > 0 {
			results = append(results, execTime)
		}
	}
	advTime := float32(0)
	for _, clTime := range results {
		advTime += clTime
	}
	advTime /= float32(clientCount)
	return fmt.Sprintf(
		"average client time: %.2f ms average call method time: %.2f ms",
		advTime, advTime/float32(commandCount))
}

func main() {
	client := nm.NewClient(host, port)
	err := client.Open()
	defer client.Close()
	if err != nil {
		fmt.Println("client connection error", err)
	} else {
		switch operation {
		case "capture":
			fmt.Println(capture(client))
		case "release":
			fmt.Println(release(client))
		case "example":
			fmt.Println(example(client))
		}
	}
}
