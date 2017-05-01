package main

import (
	"bufio"
	"encoding/json"
	"flag"
	"fmt"
	"log"
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
var jsonDataMode bool
var showMsg bool

func init() {
	flag.IntVar(&port, "port", 8888, "TCP port of server.")
	flag.BoolVar(&jsonDataMode, "json", false, "Json message mode.")
	flag.StringVar(&host, "host", "localhost", "Host (ip) of server.")
	flag.IntVar(&connectionsCount, "connections", 100, "Parallel connections count.")
	flag.IntVar(&messageCount, "msgcount", 1000, "Total count of messages for each connections.")
	flag.IntVar(&messageSize, "msgsize", 512, "Message size.")
	flag.BoolVar(&showMsg, "show", false, "Show message content.")
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
	if jsonDataMode {
		fmt.Println("Message as JSON mode on.")
	}
}

type resultConn struct {
	byteIn  int
	byteOut int
	time    float32
}

type simpleJSONMsg struct {
	A []string `json:"a"`
	B []string `json:"b"`
}

func randomASCIIStr(size int) []byte {
	result := make([]byte, size+1)
	for i := 0; i < size; i++ {
		result[i] = asciiBase[rand.Intn(len(asciiBase))]
	}
	result[size] = '\n'
	return result
}

func jsonWithSimpleRandomVec() []byte {
	aSize := 10 + rand.Intn(50)
	bSize := 10 + rand.Intn(50)
	data := simpleJSONMsg{
		A: make([]string, aSize),
		B: make([]string, bSize)}
	denominator := float32(rand.Intn(1000))
	for aSize > 0 {
		aSize--
		data.A[aSize] = fmt.Sprintf("%.6f", float32(rand.Intn(1E6))/denominator)
	}
	for bSize > 0 {
		bSize--
		data.B[bSize] = fmt.Sprintf("%.6f", float32(rand.Intn(1E6))/denominator)
	}
	if res, err := json.Marshal(data); err != nil {
		log.Fatalln(err)
		return []byte("error\n")
	} else {
		return append(res, 10)
	}
}

// General method of processing connection.
func connect(num int, serverHost string, serverPort int, result *chan resultConn) {
	fmt.Println("Start connection ", num)
	start := time.Now()
	res := resultConn{}
	var msgOut []byte
	conn, err := net.Dial(transport, fmt.Sprintf("%s:%d", serverHost, serverPort))
	if err != nil {
		// handle error
		fmt.Println(err)
	} else {
		for msgIndex := 0; msgIndex < messageCount; msgIndex++ {
			if jsonDataMode {
				msgOut = jsonWithSimpleRandomVec()
			} else {
				msgOut = randomASCIIStr(messageSize)
			}
			conn.Write(msgOut)
			res.byteOut += len(msgOut)
			msg, err := bufio.NewReader(conn).ReadString('\n')
			if showMsg {
				fmt.Printf(
					"msg out: %s\nmsg in: %s\n",
					string(msgOut), string(msg))
			}
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
