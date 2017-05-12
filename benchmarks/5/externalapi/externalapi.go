package externalapi

import (
	"fmt"
	"log"
	"net/http"
	"os"
	"strings"
	"sync"
	"time"
)

const (
	requestTimeout   = 30
	wrongDistance    = -1
	envVarNameApiUrl = "APIURL"
)

var externalApiUrl string

func init() {
	externalApiUrl = os.Getenv(envVarNameApiUrl)
	if externalApiUrl == "" {
		log.Panicf("Environment variable '%s' required.\n", envVarNameApiUrl)
	}
}

type loc struct {
	lat, lng string
}

func (point loc) String() string {
	return fmt.Sprintf("(%s, %s)", point.lat, point.lng)
}

type pointSet struct {
	points []loc
}

func (set pointSet) String() string {
	parts := make([]string, len(set.points))
	for i, p := range set.points {
		parts[i] = p.String()
	}
	return fmt.Sprintf("[%s]", strings.Join(parts, ","))
}

type pipeline struct {
	toService chan pointSet
	toClient  chan int
}

type apiCallClientPool struct {
	seek        int
	size        int
	pool        []pipeline
	seekLock    *sync.RWMutex
	exitChan    chan bool
	doneWorkers chan int
}

var apiClientPool *apiCallClientPool

func callService(client *http.Client, locations ...loc) (int, error) {
	// TODO: ;)
	return 0, nil
}

func clientWorker(index int, exitChan chan bool, input chan pointSet, output chan int) {
	log.Printf("Client api worker %d started\n", index)
	active := true
	client := http.Client{
		Timeout: time.Duration(requestTimeout) * time.Second}

	for active {
		select {
		case <-exitChan:
			{
				active = false
			}
		case points := <-input:
			{
				if distance, err := callService(&client, points.points...); err != nil {
					log.Printf(
						"in worker %d service return error: %s for %s \n",
						index, err, points)
					output <- wrongDistance
				} else {
					output <- distance
				}
			}
		}
	}
}

func newapiCallClientPool(size int) *apiCallClientPool {
	pool := apiCallClientPool{
		seek:        -1,
		pool:        make([]pipeline, size),
		exitChan:    make(chan bool, size),
		doneWorkers: make(chan int, size),
		seekLock:    new(sync.RWMutex),
		size:        size}

	for i := 0; i < size; i++ {
		// channel capacity = 1
		pool.pool[i].toService = make(chan pointSet, 1)
		pool.pool[i].toClient = make(chan int, 1)
		go clientWorker(
			i+1, pool.exitChan, pool.pool[i].toService, pool.pool[i].toClient)
	}
	return &pool
}

func (pool *apiCallClientPool) nextSeekValue() int {
	// roundrobin seek
	pool.seekLock.Lock()
	defer pool.seekLock.Unlock()
	if pool.seek < pool.size-1 {
		pool.seek++
	} else {
		pool.seek = 0
	}
	return pool.seek
}

func (pool *apiCallClientPool) call(points *pointSet) int {
	index := pool.nextSeekValue()
	var res int
	log.Printf("to worker %d points -> %s\n", index, *points)
	pool.pool[index].toService <- *points

	select {
	case distance := <-pool.pool[index].toClient:
		{
			log.Printf("from worker %d d = %d points %s\n", index, distance, *points)
			res = distance
		}
	case <-time.After(time.Second * (requestTimeout + 1)):
		{
			res = wrongDistance
			log.Panicf(
				"Error with API call timeout! Points: %s\n", *points)
		}
	}
	return res
}

func (pool *apiCallClientPool) close() {
	pool.seekLock.Lock()
	defer pool.seekLock.Unlock()
	var i int
	for i = 0; i < pool.size; i++ {
		pool.exitChan <- true
	}
	log.Println("Stopping client workers...")
	wait := true
	done := make(map[int]interface{})
	for wait {
		index := <-pool.doneWorkers
		log.Printf("Client api worker %d finished\n", index)
		done[index] = nil
		wait = len(done) < pool.size
	}
	close(pool.exitChan)
	close(pool.doneWorkers)
	for i = 0; i < pool.size; i++ {
		close(pool.pool[i].toClient)
		close(pool.pool[i].toService)
	}
	log.Println("Pool closed.")
}

// Create and run pool of requests to external API.
func RunExternalApiRequestPool(poolSize int) error {
	apiClientPool = newapiCallClientPool(poolSize)
	return nil
}

// Main API method.
func MinDistanceServiceCall(points ...[]string) int {
	set := pointSet{points: make([]loc, len(points))}
	for i, p := range points {
		if len(p) != 2 {
			log.Fatalln("Two points as strings in array requires: ['lat', 'lng']!")
		}
		set.points[i].lat = p[0]
		set.points[i].lng = p[1]
	}
	return apiClientPool.call(&set)
}
