package main

import (
	"bufio"
	"flag"
	"fmt"
	"log"
	"math/rand"
	"net"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/golang/protobuf/proto"

	protomsg "./messages"
)

const (
	transport = "tcp"
)

var port int
var host string
var connectionsCount int
var messageCount int
var messageSize int
var showMsg bool

func init() {
	flag.IntVar(&port, "port", 8888, "TCP port of server.")
	flag.StringVar(&host, "host", "localhost", "Host (ip) of server.")
	flag.IntVar(&connectionsCount, "connections", 100, "Parallel connections count.")
	flag.IntVar(&messageCount, "msgcount", 1000, "Total count of messages for each connections.")
	flag.IntVar(&messageSize, "msgsize", 512, "Message size.")
	flag.BoolVar(&showMsg, "show", false, "Show message content.")
	flag.Parse()
}

type resultConn struct {
	byteIn  int
	byteOut int
	time    float32
}

func randomProtoMsg() []byte {
	aSize := 10 + rand.Intn(50)
	bSize := 10 + rand.Intn(50)
	a := make([]float32, aSize)
	b := make([]float32, bSize)
	denominator := float32(rand.Intn(1000))
	for aSize > 0 {
		aSize--
		a[aSize] = float32(rand.Intn(1E6)) / denominator
	}
	for bSize > 0 {
		bSize--
		b[bSize] = float32(rand.Intn(1E6)) / denominator
	}
	msg := protomsg.DataMsg{A: a, B: b}
	if data, err := proto.Marshal(&msg); err != nil {
		log.Fatalln("Protobuf dump error", err)
		return []byte("error\n")
	} else {
		return data
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
		reader := bufio.NewReader(conn)
		buf := make([]byte, 1024)
		for msgIndex := 0; msgIndex < messageCount; msgIndex++ {
			msgOut = randomProtoMsg()
			conn.Write(msgOut)
			res.byteOut += len(msgOut)
			answerSize, err := reader.Read(buf)
			if err != nil {
				log.Println(err)
			} else {
				msg := buf[0:answerSize]
				if showMsg {
					fmt.Printf(
						"msg out: %s\nmsg in: %s\n",
						string(msgOut), string(msg))
				}
				res.byteIn += answerSize
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
