import pickle
import sys

import zmq
import time
import constPipe
import string

id = str(sys.argv[1]) if len(sys.argv) > 1 else "1"
name = "mapper_" + id
name = name.upper()

context = zmq.Context()

pullAddress = "tcp://" + constPipe.HOST + ":" + constPipe.PORT_SPLITTER  # task src
pull_socket = context.socket(zmq.PULL)  # create a pull socket
pull_socket.connect(pullAddress)  # connect to task source


push_sockets = []
for i in range(1, constPipe.NUM_REDUCERS + 1):
    port = constPipe.PORT_REDUCER_START + i
    pushAddress = f"tcp://{constPipe.HOST}:{port}"  # reducer address
    push_socket = context.socket(zmq.PUSH)  # create a push socket
    push_socket.connect(pushAddress)  # connect to reducer
    push_sockets.append(push_socket)

time.sleep(1) # wait to allow all clients to connect
print(f"{name} started")

while True:
    work = pickle.loads(pull_socket.recv())  # receive work from a source
    print(f"{name} received workload '{work[1]}' from {work[0]}")

    if work[1] == constPipe.STOP_CODE:
        for ps in push_sockets:
            ps.send(pickle.dumps((name, constPipe.STOP_CODE)))
        print(f"{name} sent stop code to reducers and is exiting")
        break

    words = work[1].strip().split()

    for word in words:
        # determine reducer index by first letter
        alphabet = "abcdefghijklmnopqrstuvwxyz"
        ch = word[0].lower()
        num_reducers = getattr(constPipe, "NUM_REDUCERS", 2)
        if ch in alphabet:
            id = int((alphabet.index(ch) * num_reducers) / len(alphabet))
            id = min(id, int(num_reducers))
        else:
            id = 0
        
        push_sockets[id].send( pickle.dumps( (name, word.strip(string.punctuation)) ) )

