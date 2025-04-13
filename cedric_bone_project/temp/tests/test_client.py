#!/usr/bin/env python3
"""
Tests for the client module functionality
"""
import os
import sys
import json
import socket
import hashlib
import unittest
from unittest.mock import patch, MagicMock, mock_open

# Add the src directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

import client
import metainfo

class TestClient(unittest.TestCase):
    
    def setUp(self):
        # Create a client instance for testing
        self.test_client = client.Client(download_dir="test_downloads")
        
        # Test data
        self.test_file_data = b"This is test file data for client testing."
        self.test_file_name = "test_file.txt"
        self.test_file_path = f"test_files/{self.test_file_name}"
        self.test_tracker_url = "localhost:8000"
        
        # Create test downloads directory
        os.makedirs("test_downloads", exist_ok=True)
        
        # Calculate SHA1 hash of test data
        self.test_file_hash = hashlib.sha1(self.test_file_data).hexdigest()
        
        # Create a sample metainfo structure for testing
        self.sample_metainfo = {
            "info": {
                "name": self.test_file_name,
                "piece length": 262144,
                "pieces_binary": self.test_file_hash,
                "piece_hashes": [self.test_file_hash],
                "length": len(self.test_file_data)
            },
            "announce": self.test_tracker_url,
            "info_hash": "980852ed5c00fe740c14bf25d21b4084a458bf2b",
            "file_hash": self.test_file_hash
        }
    
    def tearDown(self):
        # Stop the client
        if hasattr(self, 'test_client'):
            self.test_client.stop()
            
        # Clean up test files
        if os.path.exists("test_downloads"):
            for file in os.listdir("test_downloads"):
                file_path = os.path.join("test_downloads", file)
                if os.path.isfile(file_path):
                    os.remove(file_path)
    
    def test_init(self):
        """Test client initialization"""
        # Verify client properties
        self.assertEqual(self.test_client.download_dir, "test_downloads")
        self.assertIsInstance(self.test_client.peer_id, str)
        self.assertEqual(len(self.test_client.peer_id), 20)  # peer_id should be 20 chars
        self.assertIsInstance(self.test_client.peer, object)
        self.assertIsInstance(self.test_client.trackers, list)
    
    def test_calculate_file_hash(self):
        """Test calculating file hash"""
        # Mock open to return our test data
        with patch('builtins.open', mock_open(read_data=self.test_file_data)):
            # Calculate hash
            result = self.test_client.calculate_file_hash("dummy_path")
            
            # Verify hash matches expected
            self.assertEqual(result, self.test_file_hash)
    
    def test_verify_file_hash(self):
        """Test verifying file hash"""
        # Mock calculate_file_hash to return our test hash
        with patch.object(self.test_client, 'calculate_file_hash', return_value=self.test_file_hash):
            # Test with matching hash (should return True)
            self.assertTrue(self.test_client.verify_file_hash("dummy_path", self.test_file_hash))
            
            # Test with mismatched hash (should return False)
            self.assertFalse(self.test_client.verify_file_hash("dummy_path", "wronghash"))
    
    def test_add_tracker(self):
        """Test adding a tracker"""
        # Add a test tracker
        result = self.test_client.add_tracker("localhost", 8000)
        
        # Verify tracker was added
        self.assertTrue(result)
        self.assertIn({"host": "localhost", "port": 8000}, self.test_client.trackers)
    
    @patch('socket.socket')
    def test_get_peers_from_tracker(self, mock_socket):
        """Test getting peers from a tracker"""
        # Setup mock socket
        mock_instance = MagicMock()
        mock_socket.return_value = mock_instance
        
        # Mock successful tracker response
        mock_response = {
            "peers": [
                {"peer_id": "peer1", "ip": "127.0.0.1", "port": 12345},
                {"peer_id": "peer2", "ip": "127.0.0.1", "port": 12346}
            ]
        }
        mock_instance.recv.return_value = json.dumps(mock_response).encode()
        
        # Get peers
        peers = self.test_client.get_peers_from_tracker(self.test_tracker_url, "test_hash")
        
        # Verify request was sent correctly
        send_data = json.loads(mock_instance.sendall.call_args[0][0].decode())
        self.assertEqual(send_data["type"], "get_peers")
        self.assertEqual(send_data["info_hash"], "test_hash")
        
        # Verify peers were returned
        self.assertEqual(len(peers), 2)
        self.assertEqual(peers[0]["peer_id"], "peer1")
        self.assertEqual(peers[1]["port"], 12346)
    
    @patch('os.path.isfile')
    @patch('builtins.open', new_callable=mock_open)
    @patch.object(client.Client, 'register_with_tracker')
    @patch.object(client.Client, 'create_torrent')
    def test_share_file(self, mock_create_torrent, mock_register, mock_file, mock_isfile):
        """Test sharing a file"""
        # Setup mocks
        mock_isfile.return_value = True
        mock_file().read.return_value = self.test_file_data
        
        # Mock successful torrent creation
        mock_create_torrent.return_value = f"{self.test_file_name}.torrent"
        
        # Mock successful tracker registration
        mock_register.return_value = True
        
        # Share the file
        with patch('os.makedirs'):
            result = self.test_client.share_file(self.test_file_path, self.test_tracker_url)
        
        # Verify file was shared successfully
        self.assertTrue(result)
        
        # Verify torrent was created and registered
        mock_create_torrent.assert_called_once()
        mock_register.assert_called_once()
    
    @patch('metainfo.load_metainfo')
    @patch.object(client.Client, 'get_peers_from_tracker')
    def test_download_from_torrent_no_peers(self, mock_get_peers, mock_load_metainfo):
        """Test downloading a torrent with no available peers"""
        # Setup mocks
        mock_load_metainfo.return_value = self.sample_metainfo
        mock_get_peers.return_value = []  # No peers available
        
        # Attempt download
        result = self.test_client.download_from_torrent("test.torrent")
        
        # Verify download failed due to no peers
        self.assertFalse(result)
        
        # Verify get_peers was called with correct hash
        mock_get_peers.assert_called_once_with(
            self.test_tracker_url, 
            self.sample_metainfo["info_hash"]
        )
    
    @patch('metainfo.load_metainfo')
    @patch.object(client.Client, 'get_peers_from_tracker')
    @patch.object(client.Client, 'verify_file_hash')
    @patch('socket.socket')
    def test_download_from_torrent_success(self, mock_socket, mock_verify, mock_get_peers, mock_load_metainfo):
        """Test successfully downloading a torrent"""
        # Setup mocks
        mock_load_metainfo.return_value = self.sample_metainfo
        
        # Mock available peers
        mock_get_peers.return_value = [
            {"peer_id": "peer1", "ip": "127.0.0.1", "port": 12345}
        ]
        
        # Mock successful piece download
        mock_socket_instance = MagicMock()
        mock_socket.return_value = mock_socket_instance
        mock_socket_instance.recv.return_value = self.test_file_data
        
        # Mock successful file verification
        mock_verify.return_value = True
        
        # Attempt download with patched open
        with patch('builtins.open', mock_open()):
            result = self.test_client.download_from_torrent("test.torrent")
        
        # Verify download was successful
        self.assertTrue(result)
        
        # Verify socket connection was made to download piece
        mock_socket_instance.connect.assert_called()
        mock_socket_instance.sendall.assert_called()
        
        # Verify file was verified
        mock_verify.assert_called_once()
    
    @patch('metainfo.create_metainfo')
    def test_create_torrent(self, mock_create_metainfo):
        """Test creating a torrent file"""
        # Setup mocks
        mock_create_metainfo.return_value = self.sample_metainfo
        
        # Create torrent
        with patch('builtins.open', mock_open()):
            result = self.test_client.create_torrent(self.test_file_path, self.test_tracker_url)
        
        # Verify torrent was created
        self.assertEqual(result, f"{self.test_file_name}.torrent")
        
        # Verify metainfo was created and saved
        mock_create_metainfo.assert_called_once_with(self.test_file_path, self.test_tracker_url)
    
    @patch('socket.socket')
    def test_register_with_tracker(self, mock_socket):
        """Test registering with tracker"""
        # Setup mock socket
        mock_instance = MagicMock()
        mock_socket.return_value = mock_instance
        
        # Mock successful tracker response
        mock_response = {"status": "ok"}
        mock_instance.recv.return_value = json.dumps(mock_response).encode()
        
        # Register with tracker
        result = self.test_client.register_with_tracker(self.test_tracker_url, self.sample_metainfo)
        
        # Verify registration was successful
        self.assertTrue(result)
        
        # Verify request was sent correctly
        send_data = json.loads(mock_instance.sendall.call_args[0][0].decode())
        self.assertEqual(send_data["type"], "announce")
        self.assertEqual(send_data["info_hash"], self.sample_metainfo["info_hash"])
        self.assertIn(self.sample_metainfo["info"]["name"], send_data["files"])

if __name__ == '__main__':
    unittest.main()
