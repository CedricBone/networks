#!/usr/bin/env python3
"""
Tests for the metainfo module functionality
"""
import os
import sys
import json
import hashlib
import unittest
from unittest.mock import patch, mock_open

# Add the src directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

import metainfo

class TestMetainfo(unittest.TestCase):
    
    def setUp(self):
        # Create a temp test file content for mocking
        self.test_data = b"This is test data for the metainfo module tests."
        
        # Expected values for our fixed test data
        self.expected_file_size = len(self.test_data)
        self.expected_file_name = "test_file.txt"
        
        # Calculate expected SHA1 hash of our test data
        self.expected_data_hash = hashlib.sha1(self.test_data).hexdigest()
        
    @patch('builtins.open', new_callable=mock_open)
    @patch('os.path.getsize')
    @patch('os.path.exists')
    @patch('os.path.basename')
    def test_create_metainfo(self, mock_basename, mock_exists, mock_getsize, mock_file):
        """Test creating metainfo data for a torrent file"""
        
        # Setup mocks
        mock_basename.return_value = self.expected_file_name
        mock_exists.return_value = True
        mock_getsize.return_value = self.expected_file_size
        mock_file().read.return_value = self.test_data
        
        # Test tracker URL
        tracker_url = "localhost:8000"
        
        # Create metainfo dictionary
        result = metainfo.create_metainfo("some/path/test_file.txt", tracker_url)
        
        # Verify the structure of the metainfo dictionary
        self.assertIsInstance(result, dict)
        self.assertIn("info", result)
        self.assertIn("announce", result)
        self.assertIn("info_hash", result)
        self.assertIn("file_hash", result)
        
        # Verify the info section
        info = result["info"]
        self.assertEqual(info["name"], self.expected_file_name)
        self.assertEqual(info["length"], self.expected_file_size)
        self.assertIn("piece_hashes", info)
        
        # Verify the fields match our expectations
        self.assertEqual(result["announce"], tracker_url)
        
        # Verify that at least one piece hash exists and it's correct
        piece_hashes = info["piece_hashes"]
        self.assertGreaterEqual(len(piece_hashes), 1)
        self.assertEqual(piece_hashes[0], self.expected_data_hash)
        
    def test_load_metainfo(self):
        """Test loading metainfo data from a torrent file"""
        # Create a sample metainfo structure
        sample_metainfo = {
            "info": {
                "name": "test_file.txt",
                "piece length": 262144,
                "pieces_binary": "45f2847ce4099b5730e57e150c8bc79232eb71e9",
                "piece_hashes": ["45f2847ce4099b5730e57e150c8bc79232eb71e9"],
                "length": 36
            },
            "announce": "localhost:8000",
            "info_hash": "980852ed5c00fe740c14bf25d21b4084a458bf2b",
            "file_hash": "cf98e5b0eb1212b9a3168aea38e3cb31c98aff3bef9afdc3e42d57c2ce0f8114"
        }
        
        # Mock the open function to return our sample metainfo
        with patch('builtins.open', mock_open(read_data=json.dumps(sample_metainfo))):
            # Test loading the mocked file
            result = metainfo.load_metainfo("test.torrent")
            
            # Verify it loaded correctly and matches our sample
            self.assertEqual(result, sample_metainfo)
            self.assertEqual(result["info"]["name"], "test_file.txt")
            self.assertEqual(result["announce"], "localhost:8000")

if __name__ == '__main__':
    unittest.main()
