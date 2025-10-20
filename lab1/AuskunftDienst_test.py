"""
Simple client server unit test
"""

import logging
import threading
import unittest

import AuskunftDienst
from context import lab_logging

lab_logging.setup(stream_level=logging.INFO)


class TestEchoService(unittest.TestCase):
    """The test"""
    _server = AuskunftDienst.Server()  # create single server in class variable
    _server_thread = threading.Thread(target=_server.serve)  # define thread for running server

    @classmethod
    def setUpClass(cls):
        cls._server_thread.start()  # start server loop in a thread (called only once)

    def setUp(self):
        super().setUp()
        self.client = AuskunftDienst.Client()  # create new client for each test

    def test_srv_get(self):
        """Test simple call"""
        msg = self.client.get("jack")
        self.assertEqual(msg, '4098')

    def test_srv_get_not_found(self):
        """Test GET mit unbekanntem Namen"""
        msg = self.client.get("unknown")
        self.assertFalse(msg)

    def test_srv_getall(self):
        """Test GETALL liefert alle Einträge"""
        msg = self.client.getAll()
        self.assertIn('jack', msg)
        self.assertIn('4098', msg)
        self.assertIn('sape', msg)
        self.assertIn('guido', msg)

    def test_srv_add_person(self):
        """Test Server.addPerson fügt neuen Eintrag hinzu und ist abrufbar"""
        self._server.addPerson('alice', 5555)
        msg = self.client.get('alice')
        self.assertEqual(msg, '5555')

    def test_srv_unknown_request(self):
        """Test für unbekannte Requests (direkt über Server.getResponse)"""
        resp = self._server.getResponse("FOO bar")
        self.assertEqual(resp, "ERROR Unknown request")


    """     
    def test_srv_getAll_500(self): # schon ab 50 zu viel für buffer size 1024
        logging.info("Test GETALL mit 500 Einträgen")
        
        self._server.testFill(500)
        msg = self.client.getAll()
        print(msg)
        
        self.assertIn('testuser0501', msg)
        self.assertIn('1501', msg) 
    """
    


    def tearDown(self):
        self.client.close()  # terminate client after each test

    @classmethod
    def tearDownClass(cls):
        cls._server._serving = False  # break out of server loop. pylint: disable=protected-access
        cls._server_thread.join()  # wait for server thread to terminate


if __name__ == '__main__':
    unittest.main()
