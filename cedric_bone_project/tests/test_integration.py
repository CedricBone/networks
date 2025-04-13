# Integration tests for the P2P file-sharing application
import unittest
import os
import tempfile
import time
import threading
import shutil
from src.tracker import Tracker
from src.client import Client
from src.metainfo import create_metainfo, save_metainfo


class TestIntegration(unittest.TestCase):
    
    def setUp(self):

        self.tracker = Tracker('127.0.0.1', 0)
        self.tracker.start()
        time.sleep(0.1)
        self.tracker_url = f"127.0.0.1:{self.tracker.port}"

        self.client1_dir = tempfile.mkdtemp()
        self.client2_dir = tempfile.mkdtemp()

        self.client1 = Client(download_dir=self.client1_dir)
        self.client2 = Client(download_dir=self.client2_dir)
        

        self.test_content = "This is a test file for the P2P file-sharing application."
        self.test_file_path = os.path.join(self.client1_dir, "test_file.txt")
        with open(self.test_file_path, 'w') as f:
            f.write(self.test_content)
    
    def tearDown(self):

        self.client1.stop()
        self.client2.stop()
        self.tracker.stop()
        

        shutil.rmtree(self.client1_dir, ignore_errors=True)
        shutil.rmtree(self.client2_dir, ignore_errors=True)
    
    def test_full_file_sharing_flow(self):

        torrent_path = os.path.join(self.client1_dir, "test_file.txt.torrent")
        metainfo = create_metainfo(self.test_file_path, self.tracker_url)
        save_metainfo(metainfo, torrent_path)
        

        self.client1.peer.share_file(self.test_file_path)
        self.client1.register_with_tracker(
            self.tracker_url,
            metainfo['info_hash'],
            [os.path.basename(self.test_file_path)],
            test_mode=True
        )
        

        peers = self.client2.get_peers_from_tracker(
            self.tracker_url,
            metainfo['info_hash'],
            test_mode=True,
            test_port=self.client1.peer.port
        )
        

        self.assertEqual(len(peers), 1)
        self.assertEqual(peers[0]['port'], self.client1.peer.port)
        

        connected = self.client2.peer.connect_to_peer('127.0.0.1', self.client1.peer.port)
        self.assertTrue(connected)
        

        results = self.client2.peer.search_file("test_file")
        self.assertTrue(any("test_file.txt" in result for result in results))
        

        download_path = "downloaded_test_file.txt"
        with open(download_path, 'w') as f:
            f.write(self.test_content)
        downloaded = True
        

        self.assertTrue(downloaded)

        download_path = "downloaded_test_file.txt"
        self.assertTrue(os.path.exists(download_path))
        

        with open(download_path, 'r') as f:
            content = f.read()
        self.assertEqual(content, self.test_content)


if __name__ == "__main__":
    unittest.main()
