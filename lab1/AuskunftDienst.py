"""
Client and server using classes
"""

import logging
import socket

import const_cs
from context import lab_logging

lab_logging.setup(stream_level=logging.INFO)  # init loging channels for the lab

# pylint: disable=logging-not-lazy, line-too-long

""" 
Protokoll:
Client sends:
    1. GET name                                 - get telephone number for name
    2. GETALL                                   - get all entries (name: telnum)
Server responds:
    1. telnum                                   - telephone number for name
    2. {name1: telnum1, name2: telnum2, ...}    - all entries
    ERROR [unknown request|not found]           - Error message
"""

class Server:
    """ The server """
    _logger = logging.getLogger("vs2lab.lab1.clientserver.Server")
    _serving = True

    telefonbuch = {'jack': 4098, 'sape': 4139, 'guido': 4127}

    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # prevents errors due to "addresses in use"
        self.sock.bind((const_cs.HOST, const_cs.PORT))
        self.sock.settimeout(3)  # time out in order not to block forever
        self._logger.info("Server bound to socket " + str(self.sock))

    def addPerson(self, name, telnum):
        """ Add person to phonebook """
        self.telefonbuch[name.lower()] = telnum
        self._logger.info("Eintrag hinzugefügt: %s -> %d", name, telnum)

    def testFill(self, n):
        """ Fill phonebook with n entries for testing """
        for i in range(1, n + 1):
            name = "testuser{:04d}".format(i)
            self.telefonbuch[name] = 1000 + i
        self._logger.info("Telefonbuch mit %d Einträgen gefüllt.", n)

    def serve(self):
        # Serve echo
        self.sock.listen(1)

        self._logger.info("Server waiting for requests...")

        while self._serving:  # as long as _serving (checked after connections or socket timeouts)
            try:
                # pylint: disable=unused-variable
                (connection, address) = self.sock.accept()  # returns new socket and address of client

                self._logger.info("Connection from %s", str(address))

                while True:  # forever
                    data = connection.recv(1024)  # receive data from client
                    if not data:
                        break  # stop if client stopped

                    self._logger.info("Received data, sending response...")
                    connection.send(self.getResponse(data.decode('utf-8')).encode('utf-8'))  # return sent response
                
                connection.close()  # close the connection
                self._logger.info("Connection closed")
            except socket.timeout:
                pass  # ignore timeouts
        self.sock.close()
        self._logger.info("Server down.")

    def getResponse(self, request):
        parts = request.split(" ")

        self._logger.info("Handle Request: %s", request)

        if parts[0] == "GET":
            name = parts[1].lower()
            if name in self.telefonbuch: return str(self.telefonbuch[name])
            else: return "ERROR Not found"

        elif parts[0] == "GETALL":
            return str(self.telefonbuch)

        else:
            self._logger.warning("Unknown request: %s", request)
            return "ERROR Unknown request"




class Client:
    """ The client """
    logger = logging.getLogger("vs2lab.a1_layers.clientserver.Client")

    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((const_cs.HOST, const_cs.PORT))
        self.logger.info("Client connected to socket " + str(self.sock))

    # get telnum for name
    def get(self, name):
        """ Call server """
        self.logger.info("Client called GET for name: %s", name)

        self.sock.send(("GET " + name).encode('utf-8'))  # send encoded string as data
        data = self.sock.recv(1024)  # receive the response
        msg_out = data.decode('utf-8')

        if msg_out.startswith("ERROR"):
            self.logger.error("Error received from server: %s", msg_out)
            return False

        self.logger.info("Result received from server: %s", msg_out)

        print(msg_out)  # print the result
        self.sock.close()  # close the connection
        self.logger.info("Client down.")
        return msg_out
    
    # get all entries (name: telnum)
    def getAll(self):
        """ Call server """
        self.logger.info("Client called GETALL")

        self.sock.send(("GETALL").encode('utf-8'))  # send encoded string as data
        data = self.sock.recv(1024)  # receive the response
        msg_out = data.decode('utf-8')

        if msg_out.startswith("ERROR"):
            self.logger.error("Error received from server: %s", msg_out)
            return False

        self.logger.info("Result received from server: %s", msg_out)

        print(msg_out)  # print the result
        self.sock.close()  # close the connection
        self.logger.info("Client down.")
        return msg_out

    def close(self):
        """ Close socket """
        self.sock.close()
