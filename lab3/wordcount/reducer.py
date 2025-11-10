import pickle
import sys

import zmq
import time
import constPipe


id = str(sys.argv[1]) if len(sys.argv) > 1 else "1"
name = "reducer_" + id
name = name.upper()

context = zmq.Context()


pull_socket = context.socket(zmq.PULL)
port = constPipe.PORT_REDUCER_START + int(id)
pullAddress = f"tcp://{constPipe.HOST}:{port}"  # task src
pull_socket.bind(pullAddress)  # connect to task source
print(f"{name} connecting to {pullAddress}")

time.sleep(1) # wait to allow all clients to connect
print(f"{name} started")

words = {}

stopLeft = constPipe.NUM_MAPPERS
while True:
    work = pickle.loads(pull_socket.recv())  # receive work from a source
    print(f"{name} received workload {work[1]} from {work[0]}")

    if work[1] == constPipe.STOP_CODE:
        stopLeft -= 1
        print(f"{name} received stop code from {work[0]}")
        if stopLeft <= 0:
            print(f"{name} received all stop codes and is exiting")
            break

    word = work[1]
    words[word] = words.get(word, 0) + 1

    print(f"{name} current counts for {word}: {words[word]}")


print(f"{name} final word counts: {words}")