package main

import (
	"bufio"
	"flag"
	"fmt"
	"io"
	"log"
	"math"
	"net"
	"os"
	"os/signal"
	"strconv"
	"strings"
	"sync"
	"syscall"
	"time"
)

var port int
var host string

func init() {
	flag.IntVar(&port, "port", 8888, "TCP port of server.")
	flag.StringVar(&host, "host", "localhost", "Host (ip) of server.")
	flag.Parse()
}

type resultConn struct {
	byteIn  int
	byteOut int
	end     bool
}

type floatCell float32

type serverStorage struct {
	data map[string][]floatCell
	lock *sync.RWMutex
}

func (storage *serverStorage) write(code string, values []floatCell) {
	(*storage).lock.Lock()
	defer (*storage).lock.Unlock()
	size := 0
	if _, ok := storage.data[code]; !ok {
		storage.data[code] = make([]floatCell, 0)
	}
	newIndex := 0
	for _, val := range values {
		newIndex = 0
		size = len(storage.data[code])
		for i, el := range storage.data[code] {
			if val > el {
				newIndex = i + 1
			}
			if val < el {
				break
			}
		}
		lData := make([]floatCell, size+1)
		lData[newIndex] = val
		for oldIndex, nextEl := range storage.data[code] {
			if oldIndex < newIndex {
				lData[oldIndex] = nextEl
			} else {
				lData[oldIndex+1] = nextEl
			}
		}
		storage.data[code] = lData
	}
}

func (storage *serverStorage) read(code string, values []floatCell) floatCell {
	(*storage).lock.RLock()
	defer (*storage).lock.RUnlock()
	var result floatCell
	if origData, ok := storage.data[code]; ok {
		size := len(origData)
		var toLow, firstIndex bool
		var curValue, dtValue, newDtValue, value, newMinDt, minDt floatCell
		for _, val := range values {
			toLow = true
			value = 0
			data := origData
			mIndex := int(size / 2)
			firstIndex = true
			for toLow {
				curValue = data[mIndex]
				if firstIndex {
					dtValue = floatCell(math.Abs(float64(curValue-val)) + 1)
					firstIndex = false
				}
				newDtValue = floatCell(math.Abs(float64(curValue - val)))
				toLow = newDtValue < dtValue
				if toLow {
					value = curValue
					if curValue > val {
						data = data[:mIndex]
					} else {
						data = data[mIndex:]
					}
					mIndex = int(len(data) / 2)
					toLow = len(data) > 1
				}
			}
			newMinDt = floatCell(math.Abs(float64(value - val)))
			if result > 0 {
				if minDt > newMinDt {
					minDt = newMinDt
				}
				result = value
			} else {
				minDt = newMinDt
				result = value
			}
		}
	}
	return result
}

func (storage *serverStorage) sum(code string) floatCell {
	(*storage).lock.RLock()
	defer (*storage).lock.RUnlock()
	if val, ok := storage.data[code]; ok {
		var res floatCell
		for _, x := range val {
			res += x
		}
		return res
	} else {
		return 0
	}
}

func newServerStorage() *serverStorage {
	return &(serverStorage{
		data: make(map[string][]floatCell),
		lock: new(sync.RWMutex),
	})
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

func makeMsg(data []byte, storage *serverStorage) (*[]byte, error) {
	line := string(data)
	lineData := strings.Split(line, " ")
	dataSize := len(lineData) - 2
	if dataSize < 1 {
		return nil, fmt.Errorf("Incorrect data: %s", line)
	}
	code := ""
	newData := make([]floatCell, dataSize)
	isWriteCmd := true
	i := 0
	for index, val := range lineData {
		switch index {
		case 0:
			{
				isWriteCmd = "w" == val
			}
		case 1:
			{
				code = val
			}
		default:
			{
				if fVal, err := strconv.ParseFloat(val, 32); err != nil {
					return nil, err
				} else {
					newData[i] = floatCell(fVal)
					i++
				}
			}
		}
	}
	if len(code) < 1 {
		return nil, fmt.Errorf("No data in '%s'", line)
	}
	var answer []byte
	if isWriteCmd {
		storage.write(code, newData)
		answer = []byte(fmt.Sprintf("w.%s %.6f\n", code, storage.sum(code)))
	} else {
		answer = []byte(fmt.Sprintf("r.%s %.6f\n", code, storage.read(code, newData)))
	}
	return &answer, nil
}

// Read and write to socker for client.
func clientProcessing(connection net.Conn, state *serverState, storage *serverStorage) {
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
			if answer, err := makeMsg(lineData, storage); err != nil {
				data := string(lineData)
				if data == "exit" {
					wait = false
					fmt.Printf(
						"%s wanted to close connection.\n", who)
				} else {
					log.Fatalln("Message format error:", err)
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
	storage := newServerStorage()
	for state.isActive() {
		conn, err := listener.Accept()
		if err != nil {
			log.Fatal(err)
			return
		}
		go clientProcessing(conn, state, storage)
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
