package main

import (
	"bufio"
	"flag"
	"fmt"
	"io"
	"log"
	"net"
	"os"
	"os/signal"
	"sync"
	"syscall"
	"time"

	"github.com/golang/protobuf/proto"

	protomsg "./messages"
)

var port int
var host string
var messageSize int
var showDetails bool

func init() {
	flag.IntVar(&port, "port", 8888, "TCP port of server.")
	flag.StringVar(&host, "host", "localhost", "Host (ip) of server.")
	flag.IntVar(&messageSize, "msgsize", 512, "Message size.")
	flag.BoolVar(&showDetails, "show", false, "Show content of messages.")
	flag.Parse()
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
	msg := protomsg.DataMsg{}
	if err := proto.Unmarshal(data, &msg); err != nil {
		return nil, err
	}
	var a, b float32 = .0, .0
	for _, val := range msg.A {
		a += val
	}
	for _, val := range msg.B {
		b += val
	}
	b = b / float32(len(msg.B))
	c := a / b
	answer := protomsg.DataAnswer{A: &a, B: &b, C: &c}

	if res, err := proto.Marshal(&answer); err != nil {
		return nil, err
	} else {
		if showDetails {
			fmt.Printf(
				"DataAnswer(a:%.6f,b:%.6f,c:%.6f)\n", a, b, c)
		}
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
	var buf = make([]byte, 2048)
	for wait {
		readCount, err := buffer.Read(buf)
		if err != nil {
			wait = false
			if err != io.EOF {
				log.Fatal(err)
			}
		} else {
			msgData := buf[0:readCount]
			if answer, err := makeMsg(msgData); err != nil {
				data := string(msgData)
				log.Fatalln("Unknown msg", data, err)
			} else {
				state.addInputResult(readCount)
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
