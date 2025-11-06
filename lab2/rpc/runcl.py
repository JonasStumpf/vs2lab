import rpc
import logging
import time
from context import lab_logging

lab_logging.setup(stream_level=logging.INFO)


def callback(result):
    print(f"Callback received: {result.value}")



cl = rpc.Client()
cl.run()

base_list = rpc.DBList({'foo'})

# Starte asynchronen Append
cl.append('bar', base_list, callback)

# Zeige Aktivität im Hauptthread
for i in range(15):
    print(f"Client ist aktiv... {i}")
    time.sleep(1)

cl.stop()
