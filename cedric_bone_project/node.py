"""
P2P node for file sharing
"""
import os
import socket
import threading
import json
import time
import hashlib
import utils


CHUNK_SIZE = 1024 * 1024  # 1MB chunk size

class P2PNode:
    """Simple version P2P file sharing from BitTorrent"""
    
    def __init__(self, shared_dir):
        """Init P2P node"""
        self.shared_dir = shared_dir
        os.makedirs(self.shared_dir, exist_ok=True)
        self.port = utils.find_free_port()
        
        # peer tracking (done manually)
        self.peers = []  # (ip, port)
        self.files = {}  # {filename: {size, hash, chunks}}
        # lock for making sure threads don't conflict
        self.lock = threading.Lock()
        self.running = False
    
    def start(self):
        """Start P2P node"""
        self.running = True
        self.index_files()
        
        # perform multiple tasks concurrently
        self.server_thread = threading.Thread(target=self.run_server)
        self.server_thread.daemon = True
        #print("Here")
        self.server_thread.start()
        # perform maintenance concurrently
        self.maintenance_thread = threading.Thread(target=self.maintenance)
        self.maintenance_thread.daemon = True
        self.maintenance_thread.start()
        
    
    def stop(self):
        """Stop P2P node"""
        self.running = False
        #print("STOPPING")
        time.sleep(1)
    
    def index_files(self):
        """Index files indirectory"""
        with self.lock:
            self.files = {}
            for file_path in os.listdir(self.shared_dir):
                if os.path.isfile(os.path.join(self.shared_dir, file_path)) and not file_path.startswith('.'):
                    file_info = self.get_file_info(file_path)
                    self.files[file_path] = file_info
            print(f"Indexed {len(self.files)} files")
    
    def get_file_info(self, file_path):
        """File metadata"""
        file_path_full = os.path.join(self.shared_dir, file_path)
        size = os.path.getsize(file_path_full)
        num_chunks = (size + CHUNK_SIZE - 1) // CHUNK_SIZE  # Ceiling division
        
        # Calc file hash
        file_hash = hashlib.sha256()
        with open(file_path_full, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                file_hash.update(chunk)
        
        return {
            'size': size,
            'hash': file_hash.hexdigest(),
            'num_chunks': num_chunks
        }
    
    def maintenance(self):
        """Periodic maintenance"""
        while self.running:
            # Refresh file index
            self.index_files()
            # Sleep because it's periodic
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
        """list of local files"""
        with self.lock:
            return list(self.files.keys())
    
    def request_file_list(self, peer):
        """Request file list from peer"""
        # Connect to peer
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5.0)
        s.connect(peer)
        
        # request
        request = {
            'type': 'list'
        }
        s.sendall(json.dumps(request).encode('utf-8'))
        
        # Read
        data = s.recv(4096)
        s.close()
        
        response = json.loads(data.decode('utf-8'))
        return response.get('files', [])
    
    def request_file_info(self, peer, filename):
        """Request file"""
        # Connect
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5.0)
        s.connect(peer)
    
        # request
        request = {
            'type': 'info',
            'filename': filename
        }
        s.sendall(json.dumps(request).encode('utf-8'))
        
        # Read
        data = s.recv(4096)
        s.close()
        
        response = json.loads(data.decode('utf-8'))
        return response.get('info')
    
    def download_chunk(self, peer, filename, chunk_index):
        """Download a file chunk"""
        # Connect to peer
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(10.0)
        s.connect(peer)
        request = {
            'type': 'chunk',
            'filename': filename,
            'chunk_index': chunk_index
        }
        s.sendall(json.dumps(request).encode('utf-8'))
        
        # header (size is 4 bytes)
        header_size_bytes = s.recv(4)
        if not header_size_bytes:
            return None
        header_size = int.from_bytes(header_size_bytes, byteorder='big')
        header_bytes = s.recv(header_size)
        if not header_bytes:
            return None
        header = json.loads(header_bytes.decode('utf-8'))
        
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

    def download_file(self, peer, filename):
        """Download file"""
        file_info = self.request_file_info(peer, filename)
        
        # output 
        output_path = os.path.join(self.shared_dir, filename)
        temp_path = os.path.join(self.shared_dir, f".temp_{filename}")
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        # Download chunks
        num_chunks = file_info['num_chunks']
        file_hash = hashlib.sha256()
        for i in range(num_chunks):
            chunk_data = self.download_chunk(peer, filename, i)
            print(f"Downloading chunk {i}...")
            if not chunk_data:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                return False
            
            # Write chunk
            with open(temp_path, 'ab' if i > 0 else 'wb') as f:
                f.write(chunk_data)
            file_hash.update(chunk_data)
        
        # File integrity!!!!!!!!!!!
        calculated_hash = file_hash.hexdigest()
        expected_hash = file_info['hash']
        print(f"calc hash: {calculated_hash} expected hash: {expected_hash}")
        
        if calculated_hash != expected_hash:
            os.remove(temp_path)
            return False
        if os.path.exists(output_path):
            os.remove(output_path)
        os.rename(temp_path, output_path)
        #print(f"Indexes = {self.files}")
        
        # index again
        self.index_files()
        
        return True

    def search_files(self, query):
        """Search for files matching query"""
        results = []
        
        # Check local files
        for filename in self.files:
            if query.lower() in filename.lower():
                results.append({
                    'filename': filename,
                    'peer': 'local',
                    'size': self.files[filename]['size']
                })
        
        # Check peers
        for peer in self.peers:
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
        
        return results



        #############################################################################################

    def run_server(self):
        """Run server to handle incoming requests"""
        # Server socket
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(('0.0.0.0', self.port))
        server.listen(5)
        server.settimeout(1.0)

        #####
        print(f"Listening on port {self.port}")
        #####

        while self.running:
            # connection and create client thread
            try:
                client, addr = server.accept()
                if not self.running:
                    break
                
                # Handle client in a new thread
                threading.Thread(target=self.handle_client, 
                                args=(client, addr),
                                daemon=True).start()
                
            except socket.timeout:
                pass
        
        # Clean up
        server.close()
    
    def handle_client(self, client, addr):
        """Handle client request"""
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
            self.handle_list_request(client)
        elif req_type == 'info':
            # Handle file info request
            self.handle_info_request(client, request)
        elif req_type == 'chunk':
            # Handle chunk request
            self.handle_chunk_request(client, request)

        client.close()
    
    def handle_list_request(self, client):
        """Request for file list"""
        response = {
            'type': 'list_response',
            'files': list(self.files.keys())
        }
        client.sendall(json.dumps(response).encode('utf-8'))
    
    def handle_info_request(self, client, request):
        """Handle file info request"""
        filename = request.get('filename')
        file_info = self.files.get(filename)
        
        response = {
            'type': 'info_response',
            'filename': filename,
            'info': file_info
        }
        client.sendall(json.dumps(response).encode('utf-8'))
    
    def handle_chunk_request(self, client, request):
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
        
        file_path = os.path.join(self.shared_dir, filename)
        file_size = os.path.getsize(file_path)
        
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
        # Send header size + header
        client.sendall(header_size)
        client.sendall(header_bytes)
        
        # Send
        with open(file_path, 'rb') as f:
            f.seek(chunk_offset)
            client.sendall(f.read(chunk_size))
    