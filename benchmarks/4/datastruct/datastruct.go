package datastruct

import (
	"bytes"
	"encoding/json"
	"fmt"
	"log"
	"math/rand"
	"strconv"
)

// Calc results.
type SimpleCalcResult struct {
	A string `json:"a"`
	B string `json:"b"`
	C string `json:"c"`
}

// Content of source calc data.
type SimpleJSONMsg struct {
	A []string `json:"a"`
	B []string `json:"b"`
}

// Create result.
func (msg *SimpleJSONMsg) Calc() *SimpleCalcResult {
	a, b := .0, .0
	for _, val := range msg.A {
		if fval, err := strconv.ParseFloat(val, 32); err != nil {
			log.Fatalln(err)
		} else {
			a += fval
		}
	}
	for _, val := range msg.B {
		if fval, err := strconv.ParseFloat(val, 32); err != nil {
			log.Fatalln(err)
		} else {
			b += fval
		}
	}
	b = b / float64(len(msg.B))
	return &(SimpleCalcResult{
		A: fmt.Sprintf("%.6f", a),
		B: fmt.Sprintf("%.6f", b),
		C: fmt.Sprintf("%.6f", a/b)})
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
