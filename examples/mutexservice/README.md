### About.

Intended made without the dependencies.

Without external connections and persistent storage.

Only simple RPC for management of mutexes.

Release the mutex after client disconnecting and timeout functions are supported.

### Howto run it.

    $ go build ./simpleserver.go
    $ go build ./simpleclient.go

Run the server as (-help available):

    $ ./simpleserver 
    $ DEBUG=true ./simpleserver

Run client example as (-help available):

    $./simpleclient -operation example

Possible to use client as command tool for connection to server:

    $ DEBUG=true ./simpleclient -resource data2 -timeout 10
    $ DEBUG=true ./simpleclient -operation release -mutex 64d99cc2-e088-8098-9bd6-f803f0b6e410

Data transfer protocol based on JSON.
Simple using with "telnet":

    > {"jsonrpc": "2.0", "method": "capture", "params": {"resource": "data2", "autorelease": true}, "id": 5}
    > {"jsonrpc":"2.0","id":5,"result":"4111befb-53d2-0db7-10bb-1f1ce3173024"}

    > {"jsonrpc": "2.0", "method": "capture", "params": {"resource": "data2", "autorelease": true}, "id": 6}
    > {"jsonrpc":"2.0","id":6,"error":{"code":0,"message":"Resource locked by '4111befb-53d2-0db7-10bb-1f1ce3173024'"}}

    > {"jsonrpc": "2.0", "method": "capture", "params": {"timeout": 20, "resource": "data1"}, "id": 4}
    > {"jsonrpc":"2.0","id":4,"result":"e14ce61e-fe4b-634a-f94f-58068c93f7ef"}

    > {"jsonrpc": "2.0", "method": "release", "params": {"mutex": "e14ce61e-fe4b-634a-f94f-58068c93f7ef"}, "id": 6}
    > {"jsonrpc":"2.0","id":6,"error":{"code":0,"message":"Resource is free, unknown mutex 'e14ce61e-fe4b-634a-f94f-58068c93f7ef'"}}
    
    > {"jsonrpc": "2.0", "method": "capture", "params": {"resource": "data1"}, "id": 10}
    > {"jsonrpc":"2.0","id":10,"result":"79ac6ceb-0fe6-0266-d944-1db8ca89a574"}

    > {"jsonrpc": "2.0", "method": "release", "params": {"mutex": "79ac6ceb-0fe6-0266-d944-1db8ca89a574"},"id": 11}
    > {"jsonrpc":"2.0","id":11,"result":"79ac6ceb-0fe6-0266-d944-1db8ca89a574"}
