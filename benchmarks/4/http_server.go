package main

import (
	"flag"
	"fmt"
	"log"
	"net/http"
	"time"

	"github.com/pressly/chi"
	"github.com/pressly/chi/middleware"
	"github.com/pressly/chi/render"

	datast "./datastruct"
)

var port int
var host string
var requestLog bool

func init() {
	flag.IntVar(&port, "port", 8888, "Port of server.")
	flag.StringVar(&host, "host", "0.0.0.0", "Host (ip) of server.")
	flag.BoolVar(&requestLog, "log", false, "Request logs.")
	flag.Parse()
}

// Simple answer for any enpoint with json.
type SimpleAnwser struct {
	Ok      bool   `json:"ok"`
	Message string `json:"message"`
	Error   string `json:"error"`
}

// Uses chi/render iface.
func (answer *SimpleAnwser) Render(w http.ResponseWriter, r *http.Request) error {
	answer.Ok = len(answer.Error) > 0
	return nil
}

// General message content in request.
type CalcDataRequest struct {
	datast.SimpleJSONMsg
}

// Uses chi/render iface.
func (calcData *CalcDataRequest) Bind(r *http.Request) error {
	return nil
}

// Answer format.
type CalcResultResponse struct {
	datast.SimpleCalcResult
}

// Uses chi/render iface.
func (answer *CalcResultResponse) Render(w http.ResponseWriter, r *http.Request) error {
	return nil
}

func mainPage(w http.ResponseWriter, request *http.Request) {
	resp := `<html>
	<body><b>Main page.</b></body>
	</html>`
	w.Write([]byte(resp))
}

func calcClientData(w http.ResponseWriter, request *http.Request) {
	// Client has a problem in the part of connections without this options.
	w.Header().Set("Connection", "close")
	defer request.Body.Close()
	calcData := CalcDataRequest{}
	if err := render.Bind(request, &calcData); err != nil {
		answer := SimpleAnwser{
			Error: fmt.Sprintf("Data format error: %s", err)}
		render.Render(w, request, &answer)
	} else {
		answer := CalcResultResponse{*(calcData.Calc())}
		render.Render(w, request, &answer)
	}
}

// For example only.
func getColor(w http.ResponseWriter, request *http.Request) {
	rgb := chi.URLParam(request, "rgb")
	tpl := `<html>
	<head><style>body{background-color: #%s;}</style></head>
	<body><b>Whith color from url page.</b></body>
	</html>`
	w.Write([]byte(fmt.Sprintf(tpl, rgb)))
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
	router.Get("/color/:rgb", getColor)
	router.Post("/calc/", calcClientData)
	//http.ListenAndServe(socketStr, router)
	server := &http.Server{
		Addr:              socketStr,
		ReadTimeout:       5 * time.Second,
		WriteTimeout:      5 * time.Second,
		ReadHeaderTimeout: 5 * time.Second,
		IdleTimeout:       5 * time.Second,
		Handler:           router}
	log.Fatal(server.ListenAndServe())
}
