import random

def generateSentence():
    subjects = [
        "the cat", "a developer", "the system", "my neighbor", "an artist",
        "the robot", "the teacher", "your friend", "the manager", "a scientist"
    ]
    verbs = [
        "eats", "writes", "debugs", "observes", "creates",
        "transforms", "explains", "builds", "throws", "solves"
    ]
    objects = [
        "the code", "a sandwich", "the problem", "a melody",
        "the report", "a puzzle", "the machine", "the idea", "the document"
    ]
    adverbs = [
        "quickly", "carefully", "happily", "reluctantly",
        "silently", "bravely", "randomly", "gracefully"
    ]
    preps = [
        "in the morning", "on the server", "with a smile",
        "under the table", "during lunch", "without warning", "for fun"
    ]

    templates = [
        "{subj} {verb} {obj}",
        "{subj} {verb} {obj} {prep}",
        "{subj} {adverb} {verb} {obj}",
        "{subj} {verb} {obj} and {verb2} {obj2}",
        "{subj} {verb} {obj} {prep} {adverb}"
    ]

    t = random.choice(templates)
    sentence = t.format(
        subj=random.choice(subjects),
        verb=random.choice(verbs),
        obj=random.choice(objects),
        verb2=random.choice(verbs),
        obj2=random.choice(objects),
        adverb=random.choice(adverbs),
        prep=random.choice(preps)
    ).strip()

    if not sentence:
        sentence = "Something happens."

    if sentence[-1] not in ".!?":
        sentence += random.choice([".", "!", "?"])

    sentence = sentence[0].upper() + sentence[1:]
    return sentence


import pickle
import random
import time
import zmq

import constPipe

name = "splitter"
name = name.upper()

context = zmq.Context()
push_socket = context.socket(zmq.PUSH)  # create a push socket

address = f"tcp://{constPipe.HOST}:{getattr(constPipe, 'PORT_' + name)}"
push_socket.bind(address)  # bind socket to address

print(f"{name} started")
time.sleep(1) # wait to allow all clients to connect

for i in range(100):  # generate 100 sentences
    sentence = generateSentence()
    push_socket.send(pickle.dumps((name, sentence)))  # send sentence to worker

print(f"{name} sending stop code to mappers and is exiting")
for _ in range(getattr(constPipe, "NUM_MAPPERS", 3)):
    push_socket.send(pickle.dumps((name, constPipe.STOP_CODE)))  # send stop code to mappers
    time.sleep(1)