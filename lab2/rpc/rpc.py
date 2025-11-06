import constRPC

from context import lab_channel

import threading
import time

class DBList:
    def __init__(self, basic_list):
        self.value = list(basic_list)

    def append(self, data):
        self.value = self.value + [data]
        return self


class Client:
    def __init__(self):
        self.chan = lab_channel.Channel()
        self.client = self.chan.join('client')
        self.server = None

    def run(self):
        self.chan.bind(self.client)
        self.server = self.chan.subgroup('server')

    def stop(self):
        self.chan.leave('client')

    def append(self, data, db_list, callback):
        assert isinstance(db_list, DBList)

        msglst = (constRPC.APPEND, data, db_list)  # message payload
        
        while True:
            self.chan.send_to(self.server, msglst)  # send msg to server

            sender, ackmsg = self.chan.receive_from(self.server)  # wait for ACK
            if ackmsg == constRPC.ACK:
                print("Client: ACK vom Server erhalten. Warte auf Ergebnis im Hintergrund...")
                break
        
        def wait_for_result():
            while True:
                sender, resultmsg = self.chan.receive_from(self.server)
                if resultmsg[0] == constRPC.OK:
                    callback(resultmsg[1]) # Ergebnis per Callback liefern
                    break

        t = threading.Thread(target=wait_for_result)
        t.start()
        return None  # Ergebnis wird per Callback geliefert


class Server:
    def __init__(self):
        self.chan = lab_channel.Channel()
        self.server = self.chan.join('server')
        self.timeout = 3

    @staticmethod
    def append(data, db_list):
        assert isinstance(db_list, DBList)  # - Make sure we have a list
        return db_list.append(data)

    def run(self):
        self.chan.bind(self.server)
        while True:
            msgreq = self.chan.receive_from_any(self.timeout)  # wait for any request
            if msgreq is not None:
                client = msgreq[0]  # see who is the caller
                msgrpc = msgreq[1]  # fetch call & parameters
                if constRPC.APPEND == msgrpc[0]:  # check what is being requested

                    self.chan.send_to({client}, constRPC.ACK)  # send ACK
                    time.sleep(10) # simulate processing time

                    result = self.append(msgrpc[1], msgrpc[2])  # do local call
                    self.chan.send_to({client}, (constRPC.OK, result))  # return response

                else:
                    pass  # unsupported request, simply ignore
