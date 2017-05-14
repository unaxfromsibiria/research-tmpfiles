package workerspool

import (
	"fmt"
	"log"
	"sync"
	"time"
)

const (
	defaultTimeout       = 30
	returnToOutPipeLimit = 10000
	pipeLength           = 2
	minServiceDelay      = 10 // Microsecond
	debugMessages        = false
)

// this type you can create with codegeneration
type ContentType string

type msgType struct {
	id      uint64
	content ContentType
}

type WorkerHandler func(int, ContentType) ContentType

type workerPipe struct {
	in      chan msgType
	out     chan msgType
	active  bool
	timeout time.Duration
}

func newWorkerPipes(size, timeout int) []workerPipe {
	res := make([]workerPipe, size)
	for i := 0; i < size; i++ {
		res[i].open(time.Duration(timeout))
	}
	return res
}

func (pipe *workerPipe) open(timeout time.Duration) {
	pipe.in = make(chan msgType, pipeLength)
	pipe.out = make(chan msgType, pipeLength)
	pipe.active = true
	pipe.timeout = timeout
}

func (pipe *workerPipe) close() {
	pipe.active = false
	for !pipe.free() {
		time.Sleep(time.Microsecond * time.Duration(minServiceDelay))
	}
	close(pipe.in)
	close(pipe.out)
}

func (pipe *workerPipe) free() bool {
	return !(len(pipe.out) > 0 || len(pipe.out) > 0)
}

func (pipe *workerPipe) processing(m *msgType) (*msgType, error) {
	pipe.in <- *m
	waitTarger := true
	trying := 1
	var answerMsg msgType
	for waitTarger {
		select {
		case newMsg := <-pipe.out:
			{
				if newMsg.id != m.id {
					if debugMessages {
						fmt.Printf(
							"Source message id:%d != returned message id:%d\n",
							m.id, newMsg.id)
					}
					waitTarger = true
					answerMsg = newMsg
				} else {
					return &newMsg, nil
				}
			}
		case <-time.After(time.Second * pipe.timeout):
			{
				err := fmt.Errorf("Timeout in message: %d", m.id)
				return nil, err
			}
		}
		// return message
		waitTarger = trying < returnToOutPipeLimit
		if waitTarger {
			if pipe.active {
				pipe.out <- answerMsg
			}
			time.Sleep(time.Microsecond * time.Duration(minServiceDelay))
		}
		trying++
	}

	return nil, fmt.Errorf(
		"Can't wait message %d. (Trying limit is %d)", m.id, returnToOutPipeLimit)
}

type localStat struct {
	changeLock  *sync.RWMutex
	callByIndex map[int]uint64
}

func (stat *localStat) add(index int) {
	stat.changeLock.Lock()
	defer stat.changeLock.Unlock()
	if _, ok := stat.callByIndex[index]; !ok {
		stat.callByIndex[index] = 1
	} else {
		stat.callByIndex[index]++
	}
}

func newLocalStat() *localStat {
	return &(localStat{
		changeLock:  new(sync.RWMutex),
		callByIndex: make(map[int]uint64)})
}

// Worker pool.
type WorkerPool struct {
	seekLock *sync.RWMutex
	size     int
	seek     int
	sequence uint64
	pipe     []workerPipe
	exit     chan bool
	done     chan int
	stat     localStat
}

func worker(
	index int,
	output, input chan msgType,
	exitCh chan bool,
	doneCh chan int,
	handler WorkerHandler,
	stat *localStat) {
	//
	log.Printf("Worker %d started.\n", index)
	active := true
	for active {
		select {
		case msg := <-input:
			{
				if msg.id > 0 {
					stat.add(index)
					output <- msgType{
						id:      msg.id,
						content: handler(index, msg.content)}
				}
			}
		case <-exitCh:
			{
				active = false
			}
		}
	}
	doneCh <- index
}

// Create new pool with workers.
func NewWorkerPool(size int, handler WorkerHandler, delay uint) *WorkerPool {
	pool := WorkerPool{
		seekLock: new(sync.RWMutex),
		seek:     -1,
		pipe:     newWorkerPipes(size, defaultTimeout),
		exit:     make(chan bool, size),
		done:     make(chan int, size),
		stat:     *newLocalStat(),
		size:     size}
	for i := 0; i < size; i++ {
		go worker(
			i+1,
			pool.pipe[i].out,
			pool.pipe[i].in,
			pool.exit,
			pool.done,
			handler,
			&pool.stat)
	}
	if delay > 0 {
		time.Sleep(time.Millisecond * time.Duration(delay))
	}
	return &pool
}

func (pool *WorkerPool) getNextPipeIndex() int {
	// with roundrobin
	pool.seekLock.Lock()
	defer pool.seekLock.Unlock()
	if pool.seek < pool.size-1 {
		pool.seek++
	} else {
		pool.seek = 0
	}
	return pool.seek
}

func (pool *WorkerPool) getMsgid() uint64 {
	pool.seekLock.Lock()
	defer pool.seekLock.Unlock()
	pool.sequence++
	return pool.sequence
}

// Stop all in this pool.
func (pool *WorkerPool) Stop() {
	log.Println("Closing pool...")
	for i := 0; i < pool.size; i++ {
		pool.pipe[i].close()
		pool.exit <- true
	}
	doneWorkers := make(map[int]interface{})
	for len(doneWorkers) < pool.size {
		wIndex := <-pool.done
		doneWorkers[wIndex] = nil
		log.Printf("Worker %d done.\n", wIndex)
	}
	close(pool.done)
	close(pool.exit)
	log.Println("Pool closed.")
	for index, val := range pool.stat.callByIndex {
		fmt.Printf(" worker %d called %d\n", index, val)
	}
}

// Active.
func (pool *WorkerPool) Active() bool {
	return len(pool.exit) == 0 && len(pool.done) == 0
}

// Call processing in pool.
func (pool *WorkerPool) Exec(data ContentType) (*ContentType, error) {
	msg := msgType{id: pool.getMsgid(), content: data}
	seek := pool.getNextPipeIndex()
	for !pool.pipe[seek].free() {
		seek = pool.getNextPipeIndex()
	}
	if len(pool.exit) > 0 || len(pool.done) > 0 {
		return nil, fmt.Errorf("Stopping pool now.")
	}
	if answer, err := pool.pipe[seek].processing(&msg); err != nil {
		return nil, err
	} else {
		return &(answer.content), nil
	}
}
