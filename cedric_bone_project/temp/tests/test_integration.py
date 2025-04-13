#!/usr/bin/env python3
"""
Integration tests for the P2P file sharing system
Tests the complete flow from sharing a file to downloading it
"""
import os
import sys
import time
import shutil
import hashlib
import unittest
import threading
import multiprocessing

# Add the src directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

import client
import tracker
import metainfo

class TestP2PIntegration(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        """Setup for all tests - create test directories and files"""
        # Create test directories
        os.makedirs("test_files", exist_ok=True)
        os.makedirs("test_downloads", exist_ok=True)
        os.makedirs("seeder_downloads", exist_ok=True)
        os.makedirs("leecher_downloads", exist_ok=True)
        
        # Create a test file
        cls.test_file_path = "test_files/integration_test.txt"
        cls.test_content = "This is a test file for P2P sharing integration tests.\n" * 10
        with open(cls.test_file_path, 'w') as f:
            f.write(cls.test_content)
        
        # Calculate SHA1 hash of test file for verification
        cls.file_hash = hashlib.sha1(cls.test_content.encode()).hexdigest()
        
        # Define constants
        cls.tracker_host = "localhost"
        cls.tracker_port = 8123  # Use non-standard port to avoid conflicts
        cls.tracker_url = f"{cls.tracker_host}:{cls.tracker_port}"
    
    @classmethod
    def tearDownClass(cls):
        """Cleanup after all tests"""
        # Remove test directories and their contents
        for dir_path in ["test_files", "test_downloads", "seeder_downloads", "leecher_downloads"]:
            if os.path.exists(dir_path):
                shutil.rmtree(dir_path)
    
    def test_full_p2p_flow(self):
        """Test the full P2P file sharing flow with tracker, seeder, and leecher"""
        # Start tracker in a separate process
        tracker_process = multiprocessing.Process(
            target=self._run_tracker,
            args=(self.tracker_host, self.tracker_port)
        )
        tracker_process.start()
        
        try:
            # Wait for tracker to start
            time.sleep(1)
            
            # Create and start seeder client
            seeder = client.Client(download_dir="seeder_downloads")
            
            # Share the test file
            torrent_path = seeder.share_file(self.test_file_path, self.tracker_url)
            self.assertTrue(os.path.exists(f"{os.path.basename(self.test_file_path)}.torrent"))
            
            # Wait for file to be registered with tracker
            time.sleep(1)
            
            # Create and start leecher client
            leecher = client.Client(download_dir="leecher_downloads")
            
            # Download the shared file
            torrent_filename = f"{os.path.basename(self.test_file_path)}.torrent"
            download_success = leecher.download_from_torrent(torrent_filename, "leecher_downloads")
            
            # This might fail if the download doesn't complete due to errors
            # It will help diagnose issues in the actual implementation
            self.assertTrue(download_success, "Download should complete successfully")
            
            # Check that the downloaded file exists and has correct content
            downloaded_path = os.path.join("leecher_downloads", os.path.basename(self.test_file_path))
            self.assertTrue(os.path.exists(downloaded_path))
            
            # Verify file content
            with open(downloaded_path, 'r') as f:
                content = f.read()
            self.assertEqual(content, self.test_content)
            
            # Clean up
            leecher.stop()
            seeder.stop()
            
        finally:
            # Ensure tracker is stopped
            tracker_process.terminate()
            tracker_process.join(timeout=2)
    
    def _run_tracker(self, host, port):
        """Helper method to run a tracker in a separate process"""
        try:
            # Create and start tracker
            test_tracker = tracker.Tracker(host=host, port=port)
            test_tracker.start()
        except KeyboardInterrupt:
            pass
        finally:
            # Ensure tracker is stopped
            if 'test_tracker' in locals():
                test_tracker.stop()

if __name__ == '__main__':
    unittest.main()
