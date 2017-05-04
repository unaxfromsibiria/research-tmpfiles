package datastruct

import (
	"bytes"
	"encoding/json"
	"fmt"
	"log"
	"math/rand"
)

// Content of source calc data.
type SimpleJSONMsg struct {
	A []string `json:"a"`
	B []string `json:"b"`
}

// Create random data.
func RandSimpleJSONMsg() *SimpleJSONMsg {
	aSize := 10 + rand.Intn(50)
	bSize := 10 + rand.Intn(50)
	data := SimpleJSONMsg{
		A: make([]string, aSize),
		B: make([]string, bSize)}
	denominator := float32(rand.Intn(1000))
	for aSize > 0 {
		aSize--
		data.A[aSize] = fmt.Sprintf("%.6f", float32(rand.Intn(1E6))/denominator)
	}
	for bSize > 0 {
		bSize--
		data.B[bSize] = fmt.Sprintf("%.6f", float32(rand.Intn(1E6))/denominator)
	}
	return &data
}

// Create random data in bytes buffer.
func RandSimpleJSONMsgAsBuffer() *bytes.Buffer {
	data := RandSimpleJSONMsg()
	buf := new(bytes.Buffer)
	if res, err := json.Marshal(*data); err != nil {
		log.Fatalln(err)
		buf.WriteString("error")
	} else {
		buf.Write(res)
	}
	return buf
}
