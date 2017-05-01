package main

import (
	"bufio"
	"flag"
	"fmt"
	"math/rand"
	"net"
	"os"
	"os/signal"
	"syscall"
	"time"
)

const (
	transport = "tcp"
)

var port int
var host string
var connectionsCount int
var messageCount int
var messageSize int
var asciiBase []byte

func init() {
	flag.IntVar(&port, "port", 8888, "TCP port of server.")
	flag.StringVar(&host, "host", "localhost", "Host (ip) of server.")
	flag.IntVar(&connectionsCount, "connections", 100, "Parallel connections count.")
	flag.IntVar(&messageCount, "msgcount", 1000, "Total count of messages for each connections.")
	flag.IntVar(&messageSize, "msgsize", 512, "Message size.")
	for b := 48; b <= 57; b++ {
		asciiBase = append(asciiBase, byte(b))
	}
	for b := 65; b <= 90; b++ {
		asciiBase = append(asciiBase, byte(b))
	}
	for b := 97; b <= 122; b++ {
		asciiBase = append(asciiBase, byte(b))
	}
	flag.Parse()
}

type resultConn struct {
	byteIn  int
	byteOut int
	time    float32
}

func randomASCIIStr(size int) []byte {
	result := make([]byte, size+1)
	for i := 0; i < size; i++ {
		result[i] = asciiBase[rand.Intn(len(asciiBase))]
	}
	result[size] = '\n'
	return result
}

// General method of processing connection.
func connect(num int, serverHost string, serverPort int, result *chan resultConn) {
	fmt.Println("Start connection ", num)
	start := time.Now()
	res := resultConn{}
	msg := randomASCIIStr(messageSize)
	conn, err := net.Dial(transport, fmt.Sprintf("%s:%d", serverHost, serverPort))
	if err != nil {
		// handle error
		fmt.Println(err)
	} else {
		for msgIndex := 0; msgIndex < messageCount; msgIndex++ {
			conn.Write(msg)
			res.byteOut += messageSize + 1
			msg, err := bufio.NewReader(conn).ReadString('\n')
			if err != nil {
				fmt.Println(err)
			} else {
				res.byteIn += len(msg)
			}
		}
	}
	res.time = float32(time.Since(start)) / 1E9
	fmt.Println("End connection", num, "time", res.time)
	(*result) <- res
}

func main() {
	fmt.Printf("Start client connections to %s:%d\n", host, port)
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
		go connect(i, host, port, &results)
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
