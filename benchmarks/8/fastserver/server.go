package main

import (
	"bufio"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"log"
	"math/rand"
	"net"
	"os"
	"os/signal"
	"strconv"
	"sync"
	"syscall"
	"time"
)

var port int
var host string
var messageSize int
var asciiBase []byte

func init() {
	flag.IntVar(&port, "port", 8888, "TCP port of server.")
	flag.StringVar(&host, "host", "localhost", "Host (ip) of server.")
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

type simpleJSONMsg struct {
	A []string `json:"a"`
	B []string `json:"b"`
}

type simpleJSONAnswer struct {
	A string `json:"a"`
	B string `json:"b"`
	C string `json:"c"`
}

type resultConn struct {
	byteIn  int
	byteOut int
	end     bool
}

func (res resultConn) String() string {
	return fmt.Sprintf("Input bytes: %d\nOutput bytes: %d", res.byteIn, res.byteOut)
}

func (res *resultConn) update(src resultConn) {
	res.byteIn += src.byteIn
	res.byteOut += src.byteOut
}

type serverState struct {
	active  bool
	results *chan resultConn
	lock    *sync.RWMutex
}

func newServerState() *serverState {
	results := make(chan resultConn, 1024)
	return &(serverState{
		active: true, results: &results, lock: new(sync.RWMutex)})
}

func (state *serverState) stop() {
	(*state).lock.Lock()
	defer (*state).lock.Unlock()
	(*state).active = false
	fmt.Println("Server stopping..")
}

func (state serverState) addOutputResult(value int) {
	if value < 1 {
		return
	}
	*(state.results) <- resultConn{byteOut: value}
}

func (state serverState) addInputResult(value int) {
	if value < 1 {
		return
	}
	*(state.results) <- resultConn{byteIn: value}
}

func (state serverState) readyToExit() {
	*(state.results) <- resultConn{end: true}
}

func (state *serverState) isActive() bool {
	(*state).lock.RLock()
	defer (*state).lock.RUnlock()
	return (*state).active
}

func makeMsg(data []byte) (*[]byte, error) {
	msg := simpleJSONMsg{}
	if err := json.Unmarshal(data, &msg); err != nil {
		return nil, err
	}
	a, b := .0, .0
	for _, val := range msg.A {
		if fval, err := strconv.ParseFloat(val, 32); err != nil {
			log.Fatalln(err)
		} else {
			a += fval
		}
	}
	for _, val := range msg.B {
		if fval, err := strconv.ParseFloat(val, 32); err != nil {
			log.Fatalln(err)
		} else {
			b += fval
		}
	}
	b = b / float64(len(msg.B))
	answer := simpleJSONAnswer{
		A: fmt.Sprintf("%.6f", a),
		B: fmt.Sprintf("%.6f", b),
		C: fmt.Sprintf("%.6f", a/b)}

	if res, err := json.Marshal(answer); err != nil {
		return nil, err
	} else {
		res = append(res, 10)
		return &res, nil
	}
}

// Read and write to socker for client.
func clientProcessing(connection net.Conn, state *serverState) {
	who := fmt.Sprintf("client:%s", connection.RemoteAddr())
	buffer := bufio.NewReader(connection)
	wait := state.isActive()
	if wait {
		fmt.Println("new", who)
	}
	for wait {
		lineData, _, err := buffer.ReadLine()
		if err != nil {
			wait = false
			if err != io.EOF {
				log.Fatal(err)
			}
		} else {
			if answer, err := makeMsg(lineData); err != nil {
				data := string(lineData)
				if data == "exit" {
					wait = false
					fmt.Printf(
						"%s wanted to close connection.\n", who)
				} else {
					log.Fatalln("Unknown msg", data, err)
				}
			} else {
				msgSize := len(lineData)
				state.addInputResult(msgSize + 1)
				if writen, err := connection.Write(*answer); err != nil {
					wait = false
					log.Fatalln(err)
				} else {
					state.addOutputResult(writen)
					wait = state.isActive()
				}
			}
			if !wait {
				connection.Close()
			}
		}
	}
	fmt.Println("gone", who)
}

func socketListen(socket string, state *serverState) {
	listener, err := net.Listen("tcp", socket)
	if err != nil {
		log.Fatal(err)
		return
	}
	defer listener.Close()
	for state.isActive() {
		conn, err := listener.Accept()
		if err != nil {
			log.Fatal(err)
			return
		}
		go clientProcessing(conn, state)
	}

}

func runServer(serverHost string, serverPort int, state *serverState) {
	socketStr := fmt.Sprintf("%s:%d", host, port)
	fmt.Println("Start server on ", socketStr)
	go socketListen(socketStr, state)
	for state.isActive() {
		time.Sleep(250 * time.Millisecond)
	}
	state.readyToExit()
}

func randomASCIIStr(size int) []byte {
	result := make([]byte, size+1)
	for i := 0; i < size; i++ {
		result[i] = asciiBase[rand.Intn(len(asciiBase))]
	}
	result[size] = '\n'
	return result
}

func main() {
	state := newServerState()
	wait := true
	signalChannel := make(chan os.Signal, 1)
	signal.Notify(signalChannel, os.Interrupt)
	signal.Notify(signalChannel, syscall.SIGTERM)
	go runServer(host, port, state)
	results := (*state).results
	totalResult := resultConn{}
	for wait {
		select {
		case newSig := <-signalChannel:
			{
				if newSig != nil {
					fmt.Println("Termination..")
					state.stop()
				}
			}
		case resConn := <-*results:
			{
				wait = !resConn.end
				totalResult.update(resConn)
			}
		}
	}
	fmt.Println("Connections returned results.")
	fmt.Println(totalResult)
}
