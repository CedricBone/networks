import unittest
import os
import time
import threading
from src.peer import Peer

class TestPeer(unittest.TestCase):
    def setUp(self):

        self.peer1 = Peer('127.0.0.1', 0)
        self.peer2 = Peer('127.0.0.1', 0)
        

        self.peer1.start()
        self.peer2.start()
        

        self.test_file_path = 'test_file.txt'
        with open(self.test_file_path, 'w') as f:
            f.write('This is a test file content')

    def tearDown(self):

        self.peer1.stop()
        self.peer2.stop()
        

        if os.path.exists(self.test_file_path):
            os.remove(self.test_file_path)
        if os.path.exists('downloaded_test_file.txt'):
            os.remove('downloaded_test_file.txt')

    def test_peer_connection(self):
        self.peer1.connect_to_peer('127.0.0.1', self.peer2.port)
        self.assertIn(('127.0.0.1', self.peer2.port), self.peer1.peers)

    def test_file_sharing(self):
        self.peer1.share_file(self.test_file_path)
        self.assertIn('test_file.txt', self.peer1.files)
        
        # Verify file hash
        file_info = self.peer1.files['test_file.txt']
        self.assertIsNotNone(file_info['hash'])
        self.assertEqual(file_info['size'], os.path.getsize(self.test_file_path))

    def test_file_search(self):
        # Share a file on peer2
        self.peer2.share_file(self.test_file_path)
        
        # Connect peer1 to peer2
        self.peer1.connect_to_peer('127.0.0.1', self.peer2.port)
        time.sleep(0.1)  # Give some time for connection to establish
        
        # Search for the file from peer1
        results = self.peer1.search_file('test_file')
        # Check if any result contains the filename
        filenames = [result[0] for result in results] if results else []
        self.assertIn('test_file.txt', filenames)

    def test_file_download(self):
        # Share a file on peer2
        self.peer2.share_file(self.test_file_path)
        
        # Connect peer1 to peer2
        self.peer1.connect_to_peer('127.0.0.1', self.peer2.port)
        time.sleep(0.1)  # Give some time for connection to establish
        
        # Download the file from peer2 to peer1
        self.peer1.download_file('127.0.0.1', self.peer2.port, 'test_file.txt')
        
        # Verify the downloaded file exists and has correct content
        self.assertTrue(os.path.exists('downloaded_test_file.txt'))
        with open('downloaded_test_file.txt', 'r') as f:
            content = f.read()
        self.assertEqual(content, 'This is a test file content')

if __name__ == '__main__':
    unittest.main()
