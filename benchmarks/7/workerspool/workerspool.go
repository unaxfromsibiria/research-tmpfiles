package workerspool

import (
	"fmt"
	"log"
	"sync"
	"sync/atomic"
	"time"
)

const (
	defaultTimeout    = 10
	pipeLength        = 1000
	minServiceDelay   = 10 // Microsecond
	poolStateActive   = 1
	poolStateStopping = 2
	poolStateStopped  = 3
)

// this type you can create with codegeneration
type ContentType string

type msgType struct {
	id       uint64
	content  ContentType
	returnTo *chan msgType
}

type WorkerHandler func(int, ContentType) ContentType

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
	seekLock      *sync.RWMutex
	size          int
	seek          int
	sequence      uint64
	state         uint32
	exit          chan bool
	done          chan int
	input         chan msgType
	stat          localStat
	AnswerTimeout time.Duration
}

func worker(
	index int,
	input chan msgType,
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
				if msg.id > 0 && msg.returnTo != nil {
					stat.add(index)
					*(msg.returnTo) <- msgType{
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
		AnswerTimeout: time.Duration(defaultTimeout),
		//
		seekLock: new(sync.RWMutex),
		seek:     -1,
		input:    make(chan msgType, pipeLength),
		exit:     make(chan bool, size),
		done:     make(chan int, size),
		stat:     *newLocalStat(),
		state:    poolStateActive,
		size:     size}
	for i := 0; i < size; i++ {
		go worker(
			i+1,
			pool.input,
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

func (pool *WorkerPool) getMsgid() uint64 {
	pool.seekLock.Lock()
	defer pool.seekLock.Unlock()
	pool.sequence++
	return pool.sequence
}

// Stop all in this pool.
func (pool *WorkerPool) Stop() {
	log.Println("Closing pool...")
	atomic.StoreUint32(&(pool.state), poolStateStopping)
	for i := 0; i < pool.size; i++ {
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
	close(pool.input)
	atomic.StoreUint32(&(pool.state), poolStateStopped)
	log.Println("Pool closed.")
	for index, val := range pool.stat.callByIndex {
		fmt.Printf(" worker %d called %d\n", index, val)
	}
}

// Active.
func (pool *WorkerPool) Active() bool {
	return atomic.LoadUint32(&(pool.state)) == poolStateActive
}

// Call processing in pool.
func (pool *WorkerPool) Exec(data ContentType) (*ContentType, error) {
	if !pool.Active() {
		return nil, fmt.Errorf("Stopping pool now.")
	}
	answerChan := make(chan msgType, 1)
	defer close(answerChan)
	msg := msgType{
		id:       pool.getMsgid(),
		returnTo: &answerChan,
		content:  data}

	pool.input <- msg
	select {
	case newMsg := <-answerChan:
		{
			if newMsg.id != msg.id {
				err := fmt.Errorf(
					"Source message id:%d != returned message id:%d",
					msg.id, newMsg.id)
				return nil, err
			}
			return &(newMsg.content), nil
		}
	case <-time.After(time.Second * pool.AnswerTimeout):
		{
			err := fmt.Errorf("Timeout in message: %d", msg.id)
			return nil, err
		}
	}
}
