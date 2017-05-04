package main

import (
	"flag"
	"fmt"
	"io/ioutil"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	datast "./datastruct"
)

const (
	mimeType = "application/json; charset=utf-8"
)

var serverURL string
var connectionsCount int
var messageCount int
var showMsg bool

func init() {
	flag.StringVar(&serverURL, "url", "http://localhost:80", "HTTP/HTTPS url of web-server.")
	flag.IntVar(&connectionsCount, "connections", 100, "Parallel connections count.")
	flag.IntVar(&messageCount, "msgcount", 1000, "Total count of messages for each connections.")
	flag.BoolVar(&showMsg, "show", false, "Show message content.")
	flag.Parse()
}

type resultConn struct {
	byteIn  int
	byteOut int
	time    float32
}

// General method of processing connection.
func connect(num int, url string, result *chan resultConn) {
	fmt.Println("Start connection ", num)
	start := time.Now()
	res := resultConn{}
	for i := 0; i < messageCount; i++ {
		msg := datast.RandSimpleJSONMsgAsBuffer()
		res.byteOut += msg.Len()
		if showMsg {
			fmt.Printf("out: %s\n", msg)
		}
		if response, err := http.Post(url, mimeType, msg); err != nil {
			log.Fatalln(err)
		} else {
			defer response.Body.Close()
			if content, err := ioutil.ReadAll(response.Body); err != nil {
				log.Fatalln(err)
			} else {
				if showMsg {
					fmt.Printf("in: %s\n", string(content))
				}
				res.byteIn += len(content)
			}
		}
	}
	res.time = float32(time.Since(start)) / 1E9
	fmt.Println("End connection", num, "time", res.time)
	(*result) <- res
}

func main() {
	fmt.Printf("Start http-client connections to %s\n", serverURL)
	results := make(chan resultConn, connectionsCount)
	defer close(results)

	signalChannel := make(chan os.Signal, 1)
	signal.Notify(signalChannel, os.Interrupt)
	signal.Notify(signalChannel, syscall.SIGTERM)
	returned := 0
	totalInVolume := 0
	totalOutVolume := 0
	var totalExecTime, avgExecTime float32
	wait := true
	for i := 1; i <= connectionsCount; i++ {
		go connect(i, serverURL, &results)
	}
	for wait {
		select {
		case newSig := <-signalChannel:
			{
				if newSig != nil {
					wait = false
					fmt.Println("Termination..")
				}
			}
		case resConn := <-results:
			{
				totalInVolume += resConn.byteIn
				totalOutVolume += resConn.byteOut
				totalExecTime += resConn.time
				returned++
				avgExecTime = totalExecTime / float32(returned)
				if returned >= connectionsCount {
					wait = false
					fmt.Println("Connections returned results.")
				}
			}
		}
	}
	if avgExecTime == 0 {
		avgExecTime = 1
	}
	fmt.Println("volume in:", totalInVolume)
	fmt.Println("volume out:", totalOutVolume)
	fmt.Println("sum exec time:", totalExecTime)
	fmt.Println("avg exec time:", avgExecTime)
	fmt.Println("bitrate in (kbps):", (float32(totalInVolume*8)/avgExecTime)/1024.0)
	fmt.Println("bitrate out (kbps):", (float32(totalOutVolume*8)/avgExecTime)/1024.0)
}
