package main

import (
	"flag"
	"fmt"
	"log"
	"math/rand"
	"net/http"
	"time"

	"github.com/pressly/chi"
	"github.com/pressly/chi/middleware"
	"github.com/pressly/chi/render"

	"./externalapi"
)

const (
	serviceUrl        = "/cars-parking/"
	locationPrecision = 1000000
	maxLat            = 90
	maxLng            = 180
)

var port int
var host string
var requestLog bool
var poolSize int

type location struct {
	lng string
	lat string
}

func newLocation(lat, lng float32) *location {
	return &(location{
		lng: fmt.Sprintf("%.6f", lng),
		lat: fmt.Sprintf("%.6f", lat)})
}

func (loc *location) asPair() []string {
	return []string{loc.lat, loc.lng}
}

func init() {
	flag.IntVar(&port, "port", 8888, "Port of server.")
	flag.IntVar(&poolSize, "pool", 10, "External API requests pool size.")
	flag.StringVar(&host, "host", "0.0.0.0", "Host (ip) of server.")
	flag.BoolVar(&requestLog, "log", false, "Request logs.")
	flag.Parse()
}

// General request to this service.
type CarLocationRequest struct {
	Id  string `json:"id"`
	Lng string `json:"lng"`
	Lat string `json:"lat"`
}

// Uses chi/render iface.
func (loc *CarLocationRequest) Bind(r *http.Request) error {
	return nil
}

// Answer format of general request.
type ParkingLocationResponse struct {
	Lng      string `json:"lng"`
	Lat      string `json:"lat"`
	Distance int    `json:"distance"`
}

// Uses chi/render iface.
func (resp *ParkingLocationResponse) Render(w http.ResponseWriter, r *http.Request) error {
	return nil
}

// List of locations (just render the mock).
type LocationResponse struct {
	Locations [][]string `json:"locations"`
}

// New list of locations.
func NewLocationResponse(locations []location) *LocationResponse {
	res := LocationResponse{Locations: make([][]string, len(locations))}
	for i, loc := range locations {
		res.Locations[i] = loc.asPair()
	}
	return &res
}

// Uses chi/render iface.
func (resp *LocationResponse) Render(w http.ResponseWriter, r *http.Request) error {
	return nil
}

func mainPage(w http.ResponseWriter, request *http.Request) {
	tpl := `<html>
	<body>Service url is: <b>%s</b></body>
	</html>`
	w.Write([]byte(fmt.Sprintf(tpl, serviceUrl)))
}

// Generate are random locations of parking with free places.
func getFreeParking() []location {
	n := 2 + rand.Intn(20)
	places := make([]location, n)
	//Longitude : max/min +180 to -180
	volumeLng := maxLng * locationPrecision
	volumeLngX2 := volumeLng * 2
	//Latitude : max/min +90 to -90
	volumeLat := maxLat * locationPrecision
	volumeLatX2 := volumeLat * 2

	dv := float32(locationPrecision)
	for i := 0; i < n; i++ {
		places[i] = *(newLocation(
			float32(rand.Intn(volumeLatX2)-volumeLat)/dv,
			float32(rand.Intn(volumeLngX2)-volumeLng)/dv))
	}
	return places
}

func parkingForCars(w http.ResponseWriter, request *http.Request) {
	defer request.Body.Close()
	req := CarLocationRequest{}
	if err := render.Bind(request, &req); err != nil {
		http.Error(w, fmt.Sprintf("Data format error: %s", err), 400)
	} else {
		// mock data
		locations := getFreeParking()
		res := ParkingLocationResponse{Distance: ^int(0)}
		var d int
		for _, pLoc := range locations {
			points := make([][]string, 2)
			points[0] = pLoc.asPair()
			points[1] = []string{req.Lat, req.Lng}
			// call external service and wait
			d = externalapi.MinDistanceServiceCall(points...)
			if d < res.Distance {
				res.Lat = pLoc.lat
				res.Lng = pLoc.lng
				res.Distance = d
			}
		}
		render.Render(w, request, &res)
	}
}

func getParking(w http.ResponseWriter, request *http.Request) {
	locations := getFreeParking()
	render.Render(w, request, NewLocationResponse(locations))
}

func main() {
	socketStr := fmt.Sprintf("%s:%d", host, port)
	fmt.Println("Server at", socketStr)
	router := chi.NewRouter()
	router.Use(render.SetContentType(render.ContentTypeJSON))
	if requestLog {
		router.Use(middleware.Logger)
	}
	router.Get("/", mainPage)
	router.Post(serviceUrl, parkingForCars)
	router.Get("/parking/", getParking)

	server := &http.Server{
		Addr:              socketStr,
		ReadTimeout:       5 * time.Second,
		WriteTimeout:      5 * time.Second,
		ReadHeaderTimeout: 5 * time.Second,
		IdleTimeout:       5 * time.Second,
		Handler:           router}

	if err := externalapi.RunExternalApiRequestPool(poolSize); err != nil {
		log.Fatalln(err)
	}
	log.Fatalln(server.ListenAndServe())
}
