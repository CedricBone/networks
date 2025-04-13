"""
Tests for the metainfo module.
"""
import os
import tempfile
import unittest
import json
from src.metainfo import create_metainfo, save_metainfo, load_metainfo


class TestMetainfo(unittest.TestCase):
    """Test cases for the metainfo module."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a test file
        self.test_data = b"This is test file content for metainfo testing."
        self.test_file = tempfile.NamedTemporaryFile(delete=False)
        self.test_file.write(self.test_data)
        self.test_file.close()
        
        # Set tracker URL for tests
        self.tracker_url = "localhost:8000"
    
    def tearDown(self):
        """Tear down test fixtures."""
        # Delete test files
        if os.path.exists(self.test_file.name):
            os.unlink(self.test_file.name)
        
        if os.path.exists("test.torrent"):
            os.unlink("test.torrent")
    
    def test_create_metainfo(self):
        """Test creating metainfo for a file."""
        # Create metainfo
        metainfo = create_metainfo(self.test_file.name, self.tracker_url)
        
        # Check that the metainfo contains the required keys
        self.assertIn("info", metainfo)
        self.assertIn("announce", metainfo)
        self.assertIn("info_hash", metainfo)
        
        # Check the info dictionary
        info = metainfo["info"]
        self.assertIn("name", info)
        self.assertIn("piece length", info)
        self.assertIn("pieces", info)
        self.assertIn("length", info)
        
        # Check the values
        self.assertEqual(metainfo["announce"], self.tracker_url)
        self.assertEqual(info["name"], os.path.basename(self.test_file.name))
        self.assertEqual(info["length"], len(self.test_data))
    
    def test_save_and_load_metainfo(self):
        """Test saving and loading metainfo."""
        # Create metainfo
        metainfo = create_metainfo(self.test_file.name, self.tracker_url)
        
        # Save to file
        save_metainfo(metainfo, "test.torrent")
        
        # Check that the file exists
        self.assertTrue(os.path.exists("test.torrent"))
        
        # Load from file
        loaded_metainfo = load_metainfo("test.torrent")
        
        # Check that the loaded metainfo matches the original
        self.assertEqual(loaded_metainfo["info_hash"], metainfo["info_hash"])
        self.assertEqual(loaded_metainfo["announce"], metainfo["announce"])
        self.assertEqual(loaded_metainfo["info"]["name"], metainfo["info"]["name"])
        self.assertEqual(loaded_metainfo["info"]["length"], metainfo["info"]["length"])


if __name__ == "__main__":
    unittest.main()
