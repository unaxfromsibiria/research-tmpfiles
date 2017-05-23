package netmutex

import (
	"bufio"
	"crypto/rand"
	"crypto/sha256"
	"encoding/json"
	"fmt"
	"io"
	"log"
	baserand "math/rand"
	"net"
	"os"
	"os/signal"
	"strconv"
	"strings"
	"sync"
	"syscall"
	"time"
)

const (
	storagePartsCount     = 256
	partIndexInKeyBytes   = 2  // 16 ^ 2 = 256
	mutexIdSize           = 16 // 128 bit
	searchOldMutexDelay   = 50 // ms
	netProtocol           = "tcp"
	serverStateCheckDelay = 25 // ms
	// protocol
	protocolVersion  = "2.0"
	rpcMethodCapture = "capture"
	rpcMethodRelease = "release"
	// limits
	commandBufferSize = 2048
	resourceSizeLimit = 512
)

var debugMode bool

func init() {
	debugMode = strings.ToLower(os.Getenv("DEBUG")) == "true"
	if debugMode {
		fmt.Println("Warning: Run with debug mode.")
	}
}

// LogInfo - local logging method
func LogInfo(from, msgTpl string, data ...interface{}) {
	log.Println("INFO", from, ">", fmt.Sprintf(msgTpl, data...))
}

// LogDebug - local logging method
func LogDebug(from, msgTpl string, data ...interface{}) {
	if debugMode {
		log.Println("DEBUG", from, ">", fmt.Sprintf(msgTpl, data...))
	}
}

// LogError - local logging method
func LogError(from, msgTpl string, data ...interface{}) {
	log.Println("ERROR", from, ">", fmt.Sprintf(msgTpl, data...))
}

// LogTerminate - critical log
func LogTerminate(from, msgTpl string, data ...interface{}) {
	log.Panicln("CRITICAL ", from, " > ", fmt.Sprintf(msgTpl, data...))
}

/// mutex management implementation \\\

// NewMutexId - create new mutex id
func NewMutexId() (*[]byte, error) {
	res := make([]byte, mutexIdSize)
	n, err := io.ReadFull(rand.Reader, res)
	if n != mutexIdSize || err != nil {
		return nil, err
	}
	return &res, nil
}

// MutexToStr - mutex string format in hex (5 groups like UUID4)
func MutexToStr(data []byte) string {
	return fmt.Sprintf(
		"%x-%x-%x-%x-%x",
		data[0:4], data[4:6], data[6:8], data[8:10], data[10:])
}

// MutexToBytes - mutex string to bytes (using mutex uuid format)
func MutexToBytes(data string) *[]byte {
	res := []byte(strings.Replace(data, "-", "", -1))
	return &res
}

// Main map with mutexes and resources divided
// to parts for using different RWMutex in goroutine.
// It's performance improvement.
type storagePart struct {
	mutex    map[string]string // map mutex to resource
	resource map[string]string // map resource to mutex
	locker   *sync.RWMutex
}

// put - put into storage, return false if resource locked for other mutex
func (stor *storagePart) put(mutex, resource string) bool {
	stor.locker.Lock()
	defer stor.locker.Unlock()
	if _, exist := stor.resource[resource]; !exist {
		stor.mutex[mutex] = resource
		stor.resource[resource] = mutex
		return true
	}
	return false
}

func (stor *storagePart) delete(mutex string) bool {
	stor.locker.Lock()
	defer stor.locker.Unlock()
	if res, exist := stor.mutex[mutex]; exist {
		delete(stor.resource, res)
		delete(stor.mutex, mutex)
		return true
	}
	return false
}

func (stor *storagePart) isExist(mutex string) bool {
	stor.locker.RLock()
	defer stor.locker.RUnlock()
	_, res := stor.mutex[mutex]
	return res
}

func (stor *storagePart) resourceMutex(resource string) (mutex string, exist bool) {
	stor.locker.RLock()
	defer stor.locker.RUnlock()
	mutex, exist = stor.resource[resource]
	return
}

func newStoragePart() *storagePart {
	return &(storagePart{
		locker:   new(sync.RWMutex),
		resource: make(map[string]string),
		mutex:    make(map[string]string)})
}

type mutexAutoReleaseAccount struct {
	timeouts map[string]int64
	locker   *sync.RWMutex
}

func (account *mutexAutoReleaseAccount) append(mutex string, killAt int64) {
	account.locker.Lock()
	defer account.locker.Unlock()
	account.timeouts[mutex] = killAt
}

func (account *mutexAutoReleaseAccount) delete(mutex string) {
	account.locker.Lock()
	defer account.locker.Unlock()
	if _, exist := account.timeouts[mutex]; exist {
		delete(account.timeouts, mutex)
	}
}

func (account *mutexAutoReleaseAccount) searchOld() []string {
	account.locker.RLock()
	defer account.locker.RUnlock()
	var result []string
	now := time.Now().UnixNano()
	for mutex, killAt := range account.timeouts {
		if now >= killAt {
			result = append(result, mutex)
		}
	}
	return result
}

// MutexStorage - storage methods and mutex management
type MutexStorage struct {
	parts              []storagePart
	autoReleaseAccount *mutexAutoReleaseAccount
}

// coroutine of release ol mutex
func freeOldMutex(account *mutexAutoReleaseAccount, storage *MutexStorage) {
	delay := time.Duration(searchOldMutexDelay) * time.Millisecond
	for {
		time.Sleep(delay)
		for _, mutex := range account.searchOld() {
			if storage.Release(mutex) {
				LogInfo("mutexAutoRelease", "Released '%s'", mutex)
			} else {
				LogError("mutexAutoRelease", "Can't release '%s'", mutex)
			}
		}
	}
}

func newMutexAutoReleaseAccount(storage *MutexStorage) *mutexAutoReleaseAccount {
	account := mutexAutoReleaseAccount{
		timeouts: make(map[string]int64),
		locker:   new(sync.RWMutex)}
	// free mutex coroutine
	go freeOldMutex(&account, storage)
	return &account
}

func getPartIndex(data string) int {
	index, err := strconv.ParseInt(data[:partIndexInKeyBytes], 16, 32)
	if err != nil {
		LogError("get part index", "convert error: %s", err)
		return 0
	}
	return int(index)
}

// GetMutex - search mutex by resource
func (storage *MutexStorage) GetMutex(resource string) (string, bool) {
	sha := sha256.New()
	var resHash string
	if _, err := sha.Write([]byte(resource)); err != nil {
		// wtf
		LogError("search mutex", "Can't create hash for resource: %s", err)
	} else {
		resHash = fmt.Sprintf("%x", sha.Sum(nil))
		mid := storagePartsCount / 2
		for i := 0; i < mid; i++ {
			// search cycle to center
			if value, exist := storage.parts[i].resourceMutex(resHash); exist {
				return value, true
			}
			if value, exist := storage.parts[storagePartsCount-i-1].resourceMutex(resHash); exist {
				return value, true
			}
		}
	}
	return "", false
}

// Capture - create new mutex for resource
// autorelease after timeout (if timeout = 0 autorelease  is not enabled)
func (storage *MutexStorage) Capture(resource string, timeout int) (string, error) {
	newMutex, err := NewMutexId()
	if err != nil {
		return "", err
	}
	// resource used as sha256 hash
	sha := sha256.New()
	var resHash string
	if _, err := sha.Write([]byte(resource)); err != nil {
		return "", err
	}
	resHash = fmt.Sprintf("%x", sha.Sum(nil))
	mutexStr := MutexToStr(*newMutex)
	index := getPartIndex(mutexStr)
	if debugMode {
		LogDebug("capture", "resource: '%s' mutex: '%s' part: %d", resource, mutexStr, index)
	}
	if storage.parts[index].put(mutexStr, resHash) {
		if timeout > 0 {
			killAt := time.Now().UnixNano() + int64(time.Duration(timeout)*time.Second)
			storage.autoReleaseAccount.append(mutexStr, killAt)
		}
		return mutexStr, nil
	}
	return "", fmt.Errorf(
		"Resource '%s' still locked", resHash)
}

// Release - free a resource by mutex id
func (storage *MutexStorage) Release(mutex string) bool {
	index := getPartIndex(mutex)
	if storage.parts[index].delete(mutex) {
		storage.autoReleaseAccount.delete(mutex)
		return true
	}
	return false
}

// NewMutexStorage - create mutex storage
func NewMutexStorage() *MutexStorage {
	storage := MutexStorage{
		parts: make([]storagePart, storagePartsCount)}
	for index := 0; index < storagePartsCount; index++ {
		storage.parts[index] = *newStoragePart()
	}
	storage.autoReleaseAccount = newMutexAutoReleaseAccount(&storage)
	return &storage
}

/// networking \\\

// Transport protocol structs (JSON-RPC 2.0 using) \\

// CommandResult - answer for command
type CommandResult struct {
	Jsonrpc string `json:"jsonrpc"`
	Id      int    `json:"id"`
	Result  string `json:"result"`
}

// ErrorInfo - error details in error answer
type ErrorInfo struct {
	Code    int    `json:"code"`
	Message string `json:"message"`
}

// CommandErrorResult - error result for command
type CommandErrorResult struct {
	Jsonrpc string    `json:"jsonrpc"`
	Id      int       `json:"id"`
	Error   ErrorInfo `json:"error"`
}

// CommandParams - params for command method
type CommandParams struct {
	Timeout     int    `json:"timeout,omitempty"`     // timeout of auto release
	Resource    string `json:"resource,omitempty"`    // resource name
	Mutex       string `json:"mutex,omitempty"`       // mutex id
	AutoRelease bool   `json:"autorelease,omitempty"` // release with connection closed
}

// Command - rpc call content
type Command struct {
	Jsonrpc string `json:"jsonrpc"`
	Id      int    `json:"id"`
	Method  string `json:"method"`
	// method values (see const):
	// "capture"
	// "release"
	Params CommandParams `json:"params"`
}

func (cmd *Command) newCommandResult(mutex string) *CommandResult {
	res := CommandResult{
		Id:      cmd.Id,
		Result:  mutex,
		Jsonrpc: protocolVersion}
	return &res
}

func (cmd *Command) newCommandResultError(err interface{}) *CommandErrorResult {
	res := CommandErrorResult{
		Id:      cmd.Id,
		Error:   ErrorInfo{Message: fmt.Sprintf("%s", err)},
		Jsonrpc: protocolVersion}
	return &res
}

// Validate - check content
func (cmd *Command) Validate() error {
	if cmd.Method != rpcMethodCapture && cmd.Method != rpcMethodRelease {
		return fmt.Errorf("Format error. Unsupported method '%s' for %d", cmd.Method, cmd.Id)
	}
	if cmd.Method == rpcMethodCapture {
		if len(cmd.Params.Resource) < 1 {
			return fmt.Errorf("Empty resource for %d", cmd.Id)
		}
	} else if cmd.Method == rpcMethodRelease {
		if len(cmd.Params.Mutex) < 1 {
			return fmt.Errorf("Empty mutex id for %d", cmd.Id)
		}
	}
	return nil
}

/// server implementation \\\

type clientConnectionData struct {
	autorelease map[string]interface{}
}

func newClientConnectionData() *clientConnectionData {
	return &(clientConnectionData{
		autorelease: make(map[string]interface{})})
}

func (clientData *clientConnectionData) addAutoReleaseMutex(mutex string) {
	clientData.autorelease[mutex] = nil
}

func (clientData *clientConnectionData) removeAutoReleaseMutex(mutex string) {
	if _, exist := clientData.autorelease[mutex]; exist {
		delete(clientData.autorelease, mutex)
	}
}

func (clientData *clientConnectionData) cleanUp(storage *MutexStorage) {
	for mutex := range clientData.autorelease {
		if storage.Release(mutex) {
			if debugMode {
				LogDebug("autorelease", "client mutex %s after disconnecting", mutex)
			}
		}
	}
}

type serverState struct {
	active     bool
	exitResult chan bool
	locker     *sync.RWMutex
}

func newServerState() *serverState {
	return &(serverState{
		exitResult: make(chan bool, 1),
		locker:     new(sync.RWMutex)})
}

func (state *serverState) changeActive(value bool) {
	state.locker.Lock()
	defer state.locker.Unlock()
	state.active = value
}

func (state *serverState) isActive() bool {
	state.locker.RLock()
	defer state.locker.RUnlock()
	return state.active
}

// Server - net server for mutex accounting
type Server struct {
	storage *MutexStorage
	socket  string
	state   *serverState
}

// NewServer - create new server
func NewServer(host string, port int) *Server {
	server := Server{
		state:   newServerState(),
		socket:  fmt.Sprintf("%s:%d", host, port),
		storage: NewMutexStorage()}
	return &server
}

// Stop - stop server
func (server *Server) Stop() {
	server.state.changeActive(false)
}

func commandExec(
	client string,
	cmd *Command,
	clientData *clientConnectionData,
	storage *MutexStorage) (string, error) {
	//
	if cmd.Method == rpcMethodCapture {
		// check
		if hasMutex, exists := storage.GetMutex(cmd.Params.Resource); exists {
			return "", fmt.Errorf("Resource locked by '%s'", hasMutex)
		}
		mutex, err := storage.Capture(cmd.Params.Resource, cmd.Params.Timeout)
		if err == nil {
			LogInfo(
				"mutex", "client %s capture resource %s mutex %s",
				client, cmd.Params.Resource, cmd.Params.Mutex)
			if cmd.Params.AutoRelease {
				// save data in connection context
				clientData.addAutoReleaseMutex(mutex)
			}
		}
		return mutex, err
	} else if cmd.Method == rpcMethodRelease {
		if storage.Release(cmd.Params.Mutex) {
			LogInfo("mutex", "client %s release mutex %s", client, cmd.Params.Mutex)
			clientData.removeAutoReleaseMutex(cmd.Params.Mutex)
			return cmd.Params.Mutex, nil
		}
		return "", fmt.Errorf("Resource is free, unknown mutex '%s'", cmd.Params.Mutex)
	}
	return "", fmt.Errorf("Processing error for metod '%s'", cmd.Method)
}

// connection processing \\
func clientHandler(connection net.Conn, state *serverState, storage *MutexStorage) {
	client := fmt.Sprintf("client:%s", connection.RemoteAddr())
	connectionData := newClientConnectionData()
	buffer := bufio.NewReader(connection)
	wait := state.isActive()
	if !wait {
		return
	}
	LogInfo("server connection", "new %s", client)
	var buf = make([]byte, commandBufferSize)
	var mutex string
	for wait {
		readCount, err := buffer.Read(buf)
		if err != nil {
			wait = false
			if err != io.EOF {
				LogError("server connection", "%s: %s", client, err)
			}
		} else {
			msgData := buf[:readCount]
			// get command
			cmd := Command{}
			var answer []byte
			var commandErr error
			if err := json.Unmarshal(msgData, &cmd); err != nil {
				commandErr = err
			} else {
				commandErr = cmd.Validate()
				if commandErr == nil {
					// execute command
					mutex, commandErr = commandExec(client, &cmd, connectionData, storage)
				}
			}
			// prepare error
			if commandErr != nil {
				errRes := cmd.newCommandResultError(commandErr)
				if data, err := json.Marshal(errRes); err != nil {
					LogError("server connection", "prepare answer to %s: %s", client, err)
					answer = []byte(fmt.Sprintln(err))
					wait = false
				} else {
					answer = append(data, 10)
				}
			} else {
				// prepare result
				cmdRes := cmd.newCommandResult(mutex)
				if data, err := json.Marshal(cmdRes); err != nil {
					LogError("server connection", "prepare result to %s: %s", client, err)
					answer = []byte(fmt.Sprintln(err))
					wait = false
				} else {
					answer = append(data, 10)
				}
			}
			// send answer
			if _, err := connection.Write(answer); err != nil {
				wait = false
				LogError("server connection", "send answer to %s: %s", client, err)
			} else if wait {
				wait = state.isActive()
			}

			if !wait {
				connection.Close()
			}
		}
	}
	// auto release mutex for this connection
	connectionData.cleanUp(storage)
	LogInfo("server connection", "close %s", client)
}

func socketListen(socket string, state *serverState, storage *MutexStorage) {
	listener, err := net.Listen(netProtocol, socket)
	if err != nil {
		LogTerminate("server", "net listen error: %s", err)
		return
	}
	defer listener.Close()
	for state.isActive() {
		conn, err := listener.Accept()
		if err != nil {
			LogError("server", "connection error: %s", err)
			return
		}
		go clientHandler(conn, state, storage)
	}

}

func runServer(server *Server) {
	go socketListen(server.socket, server.state, server.storage)
	delay := time.Duration(serverStateCheckDelay) * time.Millisecond
	for server.state.isActive() {
		time.Sleep(delay)
	}
	server.state.exitResult <- true
}

// RunForever - run server as service
func (server *Server) RunForever() {
	wait := true
	signalChannel := make(chan os.Signal, 1)
	signal.Notify(signalChannel, os.Interrupt)
	signal.Notify(signalChannel, syscall.SIGTERM)
	server.state.changeActive(true)
	go runServer(server)
	LogInfo("server", "Server in %s started", server.socket)
	for wait {
		select {
		case newSig := <-signalChannel:
			{
				if newSig != nil {
					LogInfo("server", "Stopping with %s...", newSig)
					server.Stop()
				}
			}
		case <-server.state.exitResult:
			{
				wait = false
			}
		}
	}
	close(server.state.exitResult)
	LogInfo("server", "Server in %s closed", server.socket)
}

/// client implementation \\\

// Client - connection client of manage mutexes
type Client struct {
	id         string
	active     bool
	socket     string
	connection net.Conn
}

// Open - init connection
func (client *Client) Open() error {
	client.connection = nil
	client.active = false
	if conn, err := net.Dial(netProtocol, client.socket); err != nil {
		LogDebug("client", "Can't open connection: %s", err)
		return err
	} else {
		client.connection = conn
		client.active = true
	}
	return nil
}

// Close - close connection
func (client *Client) Close() error {
	if client.active {
		return client.connection.Close()
	}
	return nil
}

// NewClient - create new client
func NewClient(host string, port int) *Client {
	randBytes, _ := NewMutexId()
	client := Client{
		socket: fmt.Sprintf("%s:%d", host, port),
		id:     MutexToStr(*randBytes)}
	return &client
}

// readAnswer - helper method
func (client *Client) readAnswer() (string, error) {
	reader := bufio.NewReader(client.connection)
	buf := make([]byte, commandBufferSize)
	if answerSize, err := reader.Read(buf); err != nil {
		return "", err
	} else {
		data := buf[:answerSize]
		if debugMode {
			LogDebug("client", "answer: %s", string(data))
		}
		answer := CommandResult{}
		if err := json.Unmarshal(data, &answer); err != nil {
			return "", err
		} else {
			if len(answer.Result) < 1 {
				// then error here
				errorAnswer := CommandErrorResult{}
				if err := json.Unmarshal(data, &errorAnswer); err != nil {
					return "", err
				}
				return "", fmt.Errorf(errorAnswer.Error.Message)
			}
			return answer.Result, nil
		}
	}
}

// Capture - capture resource (return mutex id or error)
// set timeOut > 0 if you need to release a mutex after any time (seconds)
// set autoRelease if you need to release all mutexes after closing a connection
func (client *Client) Capture(resource string, timeOut int, autoRelease bool) (string, error) {
	if len(resource) > resourceSizeLimit || len(resource) < 1 {
		return "", fmt.Errorf("Incorrect resource size ([1, %d] needed)", resourceSizeLimit)
	}
	if !client.active {
		return "", fmt.Errorf("Connection to %s sould be opened", client.socket)
	}
	cmd := Command{
		Jsonrpc: protocolVersion,
		Id:      1 + baserand.Intn(int(^uint16(0))-1),
		Method:  rpcMethodCapture,
		Params: CommandParams{
			Resource:    resource,
			Timeout:     timeOut,
			AutoRelease: autoRelease,
		},
	}
	var operError error
	if data, err := json.Marshal(&cmd); err != nil {
		operError = err
	} else {
		if debugMode {
			LogDebug("client", "send: %s", string(data))
		}
		_, err := client.connection.Write(data)
		if err != nil {
			operError = err
		}
	}
	if operError != nil {
		return "", operError
	}
	return client.readAnswer()
}

// Release - release resource with your mutex id
func (client *Client) Release(mutex string) (string, error) {
	if len(mutex) < 1 {
		return "", fmt.Errorf("Mutex Id format incorrect")
	}
	if !client.active {
		return "", fmt.Errorf("Connection to %s sould be opened", client.socket)
	}
	cmd := Command{
		Jsonrpc: protocolVersion,
		Id:      1 + baserand.Intn(int(^uint16(0))-1),
		Method:  rpcMethodRelease,
		Params: CommandParams{
			Mutex: mutex,
		},
	}
	var operError error
	if data, err := json.Marshal(&cmd); err != nil {
		operError = err
	} else {
		_, err := client.connection.Write(data)
		if debugMode {
			LogDebug("client", "send: %s", string(data))
		}
		if err != nil {
			operError = err
		}
	}
	if operError != nil {
		return "", operError
	}
	return client.readAnswer()
}
