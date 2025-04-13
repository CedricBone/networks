#!/usr/bin/env python3
"""
Core P2P node functionality for file sharing
"""
import os
import socket
import threading
import json
import time
import hashlib
from pathlib import Path
from utils import find_free_port

# Constants
CHUNK_SIZE = 1024 * 1024  # 1MB chunks for file transfer

class P2PNode:
    """Simple P2P file sharing node"""
    
    def __init__(self, shared_dir):
        """Initialize the P2P node"""
        # Setup directories
        self.shared_dir = Path(shared_dir)
        self.shared_dir.mkdir(exist_ok=True)
        
        # Initialize with a single port for the server
        self.port = find_free_port()
        
        # Set up peer tracking (manually added)
        self.peers = []  # List of (ip, port) tuples
        self.files = {}  # {filename: {size, hash, chunks}}
        self.lock = threading.Lock()
        self.running = False
        
        print(f"Node initialized on port: {self.port}")
    
    def start(self):
        """Start the P2P node"""
        self.running = True
        
        # Index files
        self._index_files()
        
        # Start server to handle incoming requests
        self.server_thread = threading.Thread(target=self._run_server)
        self.server_thread.daemon = True
        self.server_thread.start()
        
        # Start maintenance thread
        self.maintenance_thread = threading.Thread(target=self._maintenance)
        self.maintenance_thread.daemon = True
        self.maintenance_thread.start()
        
        print(f"P2P node started, sharing files from: {self.shared_dir}")
    
    def stop(self):
        """Stop the P2P node"""
        self.running = False
        time.sleep(0.5)  # Give threads time to clean up
        print("P2P node stopped")
    
    def _index_files(self):
        """Index all files in the shared directory"""
        with self.lock:
            self.files = {}
            for file_path in self.shared_dir.glob('*'):
                if file_path.is_file() and not file_path.name.startswith('.'):
                    try:
                        file_info = self._get_file_info(file_path)
                        self.files[file_path.name] = file_info
                    except Exception as e:
                        print(f"Error indexing file {file_path.name}: {e}")
            
            print(f"Indexed {len(self.files)} files")
    
    def _get_file_info(self, file_path):
        """Get metadata about a file"""
        size = file_path.stat().st_size
        num_chunks = (size + CHUNK_SIZE - 1) // CHUNK_SIZE  # Ceiling division
        
        # Calculate file hash
        file_hash = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                file_hash.update(chunk)
        
        return {
            'size': size,
            'hash': file_hash.hexdigest(),
            'num_chunks': num_chunks
        }
    
    def _run_server(self):
        """Run server to handle incoming requests"""
        # Create server socket
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            server.bind(('0.0.0.0', self.port))
            server.listen(5)
            server.settimeout(1.0)
            print(f"Server listening on port {self.port}")
        except Exception as e:
            print(f"Error starting server: {e}")
            return
        
        # Accept incoming connections
        while self.running:
            try:
                client, addr = server.accept()
                if not self.running:
                    break
                
                # Handle client in a new thread
                threading.Thread(target=self._handle_client, 
                                args=(client, addr),
                                daemon=True).start()
                
            except socket.timeout:
                pass
            except Exception as e:
                if self.running:
                    print(f"Error accepting connection: {e}")
        
        # Clean up
        server.close()
    
    def _handle_client(self, client, addr):
        """Handle client request"""
        try:
            # Set socket timeout
            client.settimeout(5.0)
            
            # Read request
            data = client.recv(4096)
            if not data:
                return
            
            # Parse request
            request = json.loads(data.decode('utf-8'))
            req_type = request.get('type')
            
            if req_type == 'list':
                # Handle file list request
                self._handle_list_request(client)
            elif req_type == 'info':
                # Handle file info request
                self._handle_info_request(client, request)
            elif req_type == 'chunk':
                # Handle chunk request
                self._handle_chunk_request(client, request)
            
        except Exception as e:
            print(f"Error handling client {addr}: {e}")
        finally:
            client.close()
    
    def _handle_list_request(self, client):
        """Handle file list request"""
        response = {
            'type': 'list_response',
            'files': list(self.files.keys())
        }
        client.sendall(json.dumps(response).encode('utf-8'))
    
    def _handle_info_request(self, client, request):
        """Handle file info request"""
        filename = request.get('filename')
        file_info = self.files.get(filename)
        
        response = {
            'type': 'info_response',
            'filename': filename,
            'info': file_info
        }
        client.sendall(json.dumps(response).encode('utf-8'))
    
    def _handle_chunk_request(self, client, request):
        """Handle file chunk request"""
        filename = request.get('filename')
        chunk_index = request.get('chunk_index')
        
        # Check if file exists
        if filename not in self.files:
            response = {
                'type': 'error',
                'error': 'File not found'
            }
            client.sendall(json.dumps(response).encode('utf-8'))
            return
        
        file_path = self.shared_dir / filename
        file_size = file_path.stat().st_size
        
        # Calculate chunk offset and size
        chunk_offset = chunk_index * CHUNK_SIZE
        chunk_size = min(CHUNK_SIZE, file_size - chunk_offset)
        
        if chunk_offset >= file_size:
            response = {
                'type': 'error',
                'error': 'Chunk index out of range'
            }
            client.sendall(json.dumps(response).encode('utf-8'))
            return
        
        # Send chunk header
        header = {
            'type': 'chunk_response',
            'filename': filename,
            'chunk_index': chunk_index,
            'chunk_size': chunk_size
        }
        
        header_bytes = json.dumps(header).encode('utf-8')
        header_size = len(header_bytes).to_bytes(4, byteorder='big')
        
        try:
            # Send header size + header
            client.sendall(header_size)
            client.sendall(header_bytes)
            
            # Send chunk data
            with open(file_path, 'rb') as f:
                f.seek(chunk_offset)
                client.sendall(f.read(chunk_size))
                
        except Exception as e:
            print(f"Error sending chunk: {e}")
    
    def _maintenance(self):
        """Periodic maintenance"""
        while self.running:
            try:
                # Refresh file index
                self._index_files()
            except Exception as e:
                print(f"Error in maintenance: {e}")
                
            # Sleep for a while
            time.sleep(15)
    
    def add_peer(self, ip, port):
        """Manually add a peer"""
        peer = (ip, int(port))
        if peer not in self.peers:
            self.peers.append(peer)
            print(f"Added peer: {ip}:{port}")
            return True
        return False
    
    def remove_peer(self, ip, port):
        """Remove a peer"""
        peer = (ip, int(port))
        if peer in self.peers:
            self.peers.remove(peer)
            print(f"Removed peer: {ip}:{port}")
            return True
        return False
    
    def get_peers(self):
        """Get list of peers"""
        return self.peers.copy()
    
    def get_files(self):
        """Get list of local files"""
        with self.lock:
            return list(self.files.keys())
    
    def request_file_list(self, peer):
        """Request file list from peer"""
        try:
            # Connect to peer
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(5.0)
            s.connect(peer)
            
            # Send request
            request = {
                'type': 'list'
            }
            s.sendall(json.dumps(request).encode('utf-8'))
            
            # Read response
            data = s.recv(4096)
            s.close()
            
            response = json.loads(data.decode('utf-8'))
            return response.get('files', [])
            
        except Exception as e:
            print(f"Error requesting file list from {peer}: {e}")
            return []
    
    def request_file_info(self, peer, filename):
        """Request file info from peer"""
        try:
            # Connect to peer
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(5.0)
            s.connect(peer)
            
            # Send request
            request = {
                'type': 'info',
                'filename': filename
            }
            s.sendall(json.dumps(request).encode('utf-8'))
            
            # Read response
            data = s.recv(4096)
            s.close()
            
            response = json.loads(data.decode('utf-8'))
            return response.get('info')
            
        except Exception as e:
            print(f"Error requesting file info from {peer}: {e}")
            return None
    
    def download_chunk(self, peer, filename, chunk_index):
        """Download a file chunk"""
        try:
            # Connect to peer
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(10.0)
            s.connect(peer)
            
            # Send request
            request = {
                'type': 'chunk',
                'filename': filename,
                'chunk_index': chunk_index
            }
            s.sendall(json.dumps(request).encode('utf-8'))
            
            # Read header size (4 bytes)
            header_size_bytes = s.recv(4)
            if not header_size_bytes:
                return None
            
            header_size = int.from_bytes(header_size_bytes, byteorder='big')
            
            # Read header
            header_bytes = s.recv(header_size)
            if not header_bytes:
                return None
            
            header = json.loads(header_bytes.decode('utf-8'))
            
            if header.get('type') == 'error':
                print(f"Error from peer: {header.get('error')}")
                return None
            
            # Read chunk data
            chunk_size = header.get('chunk_size')
            data = bytearray()
            bytes_received = 0
            
            while bytes_received < chunk_size:
                bytes_to_read = min(4096, chunk_size - bytes_received)
                chunk = s.recv(bytes_to_read)
                if not chunk:
                    break
                data.extend(chunk)
                bytes_received += len(chunk)
            
            s.close()
            return data
            
        except Exception as e:
            print(f"Error downloading chunk {chunk_index}: {e}")
            return None
    
    def download_file(self, peer, filename, progress_callback=None):
        """Download a complete file"""
        try:
            # Get file info
            file_info = self.request_file_info(peer, filename)
            if not file_info:
                print(f"Could not get file info for {filename}")
                return False
            
            # Prepare output file
            output_path = self.shared_dir / filename
            
            # Create temp file for downloading
            temp_path = self.shared_dir / f".temp_{filename}"
            if temp_path.exists():
                temp_path.unlink()
            
            # Download all chunks
            num_chunks = file_info['num_chunks']
            file_hash = hashlib.sha256()
            
            for i in range(num_chunks):
                # Download chunk
                chunk_data = self.download_chunk(peer, filename, i)
                if not chunk_data:
                    print(f"Failed to download chunk {i}")
                    if temp_path.exists():
                        temp_path.unlink()
                    return False
                
                # Write chunk to temp file
                with open(temp_path, 'ab' if i > 0 else 'wb') as f:
                    f.write(chunk_data)
                
                # Update hash
                file_hash.update(chunk_data)
                
                # Report progress
                if progress_callback:
                    progress = (i + 1) / num_chunks
                    progress_callback(progress)
            
            # Verify file integrity
            calculated_hash = file_hash.hexdigest()
            expected_hash = file_info['hash']
            
            if calculated_hash != expected_hash:
                print(f"File integrity check failed:")
                print(f"  Expected: {expected_hash}")
                print(f"  Got: {calculated_hash}")
                temp_path.unlink()
                return False
            
            # Rename temp file to final filename
            if output_path.exists():
                output_path.unlink()
            temp_path.rename(output_path)
            
            # Re-index files
            self._index_files()
            
            return True
            
        except Exception as e:
            print(f"Error downloading file: {e}")
            return False
    
    def search_files(self, query):
        """Search for files matching query across all peers"""
        results = []
        
        # First check local files
        for filename in self.files:
            if query.lower() in filename.lower():
                results.append({
                    'filename': filename,
                    'peer': 'local',
                    'size': self.files[filename]['size']
                })
        
        # Then check peers
        for peer in self.peers:
            try:
                peer_files = self.request_file_list(peer)
                for filename in peer_files:
                    if query.lower() in filename.lower():
                        # Get file info
                        file_info = self.request_file_info(peer, filename)
                        if file_info:
                            results.append({
                                'filename': filename,
                                'peer': peer,
                                'size': file_info['size']
                            })
            except Exception as e:
                print(f"Error searching peer {peer}: {e}")
        
        return results