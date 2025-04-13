"""
Tests for the client module.
"""
import unittest
import os
import tempfile
import time
import threading
from src.client import Client
from src.tracker import Tracker
from src.metainfo import create_metainfo, save_metainfo


class TestClient(unittest.TestCase):
    """Test cases for the client module."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create and start a tracker
        self.tracker = Tracker('127.0.0.1', 0)
        self.tracker.start()
        time.sleep(0.1)  # Give tracker time to start
        
        # Create clients
        self.client1 = Client()
        self.client2 = Client()
        
        # Create a test file
        self.test_data = "This is test file content for client testing."
        self.test_file = tempfile.NamedTemporaryFile(delete=False)
        self.test_file.write(self.test_data.encode())
        self.test_file.close()
        
        # Create a torrent file
        self.tracker_url = f"127.0.0.1:{self.tracker.port}"
        self.torrent_path = self.test_file.name + ".torrent"
        metainfo = create_metainfo(self.test_file.name, self.tracker_url)
        save_metainfo(metainfo, self.torrent_path)
    
    def tearDown(self):
        """Tear down test fixtures."""
        # Stop clients and tracker
        self.client1.stop()
        self.client2.stop()
        self.tracker.stop()
        
        # Delete test files
        if os.path.exists(self.test_file.name):
            os.unlink(self.test_file.name)
        if os.path.exists(self.torrent_path):
            os.unlink(self.torrent_path)
        if os.path.exists(os.path.join(self.client2.download_dir, os.path.basename(self.test_file.name))):
            os.unlink(os.path.join(self.client2.download_dir, os.path.basename(self.test_file.name)))
    
    def test_register_with_tracker(self):
        """Test registering with a tracker."""
        # Register client1 with tracker
        result = self.client1.register_with_tracker(
            self.tracker_url,
            "test_info_hash",
            ["test.txt"],
            test_mode=True
        )
        
        # Check that registration was successful
        self.assertTrue(result)
        self.assertIn(self.tracker_url, self.client1.trackers)
    
    def test_get_peers_from_tracker(self):
        """Test getting peers from a tracker."""
        # Register client1 with tracker
        self.client1.register_with_tracker(
            self.tracker_url,
            "test_info_hash",
            ["test.txt"]
        )
        
        # Get peers with client2
        peers = self.client2.get_peers_from_tracker(self.tracker_url, "test_info_hash", test_mode=True, test_port=self.client1.peer.port)
        
        # Check that we got client1 as a peer
        self.assertEqual(len(peers), 1)
        self.assertEqual(peers[0]['port'], self.client1.peer.port)
    
    def test_create_torrent(self):
        """Test creating a torrent file."""
        # Create a torrent file
        temp_torrent = "temp_test.torrent"
        output_path = self.client1.create_torrent(
            self.test_file.name,
            self.tracker_url,
            temp_torrent
        )
        
        # Check that the torrent was created
        self.assertEqual(output_path, temp_torrent)
        self.assertTrue(os.path.exists(temp_torrent))
        
        # Clean up
        os.unlink(temp_torrent)


if __name__ == "__main__":
    unittest.main()
