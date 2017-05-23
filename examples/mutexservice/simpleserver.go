
package main

import (
	"fmt"
	"flag"

	nm "./netmutex"
)

const (
	msg = `
	Simple TCP server.
	Mutex management protocol based on JSON-RPC 2.0.
	`
)

var port int
var host string

func init() {
	flag.IntVar(&port, "port", 8900, "TCP port of server.")
	flag.StringVar(&host, "host", "0.0.0.0", "Host (ip) of server.")
	flag.Parse()
}

func main() {
	fmt.Println(msg)
	server := nm.NewServer(host, port)
	server.RunForever()
}
