# Peer implementation for P2P file sharing
import socket
import threading
import json
import os
import hashlib


class Peer:
    
    def __init__(self, host='localhost', port=0):
        self.host = host
        self.port = port
        self.files = {}  # Dictionary to store file information
        self.peers = set()  # Set to store other peers
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((host, port))
        self.socket.listen(5)
        self.running = True
        self.interested = {}  # Peers interested in our content
        self.choked = {}      # Peers we're choking
    
    def start(self):
        self.port = self.socket.getsockname()[1]
        print(f"Peer started on {self.host}:{self.port}")
        
        # Start listening for connections
        threading.Thread(target=self.listen_for_connections, daemon=True).start()
    
    def listen_for_connections(self):
        while self.running:
            try:
                client, address = self.socket.accept()
                threading.Thread(target=self.handle_connection, args=(client,), daemon=True).start()
            except Exception as e:
                if self.running:
                    print(f"Error accepting connection: {e}")
                break
    
    def handle_connection(self, client):
        try:
            request = json.loads(client.recv(1024).decode())
            
            if request['type'] == 'handshake':
                # Respond to handshake
                response = {'type': 'handshake_response', 'peer_id': id(self)}
                client.send(json.dumps(response).encode())
                
            elif request['type'] == 'search':
                # Handle file search request
                response = {'files': [f for f in self.files if request['query'] in f]}
                client.send(json.dumps(response).encode())
                
            elif request['type'] == 'download':
                # Handle file download request - simplified to send file directly
                filename = request['filename']
                if filename in self.files:
                    filepath = self.files[filename]['path']
                    try:
                        with open(filepath, 'r') as f:
                            content = f.read()
                            client.send(content.encode())
                            print(f"Sent file {filename} to peer ({len(content)} bytes)")
                    except Exception as e:
                        print(f"Error reading file {filepath}: {e}")
                        error = {'error': f'Could not read file: {str(e)}'}
                        client.send(json.dumps(error).encode())
                else:
                    error = {'error': 'File not found'}
                    client.send(json.dumps(error).encode())
                
            elif request['type'] == 'interested':
                # Peer is interested in our content
                peer_id = request.get('peer_id')
                self.interested[peer_id] = True
                
            elif request['type'] == 'not_interested':
                # Peer is not interested in our content
                peer_id = request.get('peer_id')
                if peer_id in self.interested:
                    del self.interested[peer_id]
                
        except Exception as e:
            print(f"Error handling connection: {e}")
        finally:
            client.close()
    
    def connect_to_peer(self, host, port):
        try:
            # Store peer info
            self.peers.add((host, port))
            
            # Perform handshake
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((host, port))
                handshake = {'type': 'handshake', 'peer_id': id(self)}
                s.send(json.dumps(handshake).encode())
                response = json.loads(s.recv(1024).decode())
                
                if response['type'] == 'handshake_response':
                    print(f"Connected to peer at {host}:{port}")
                    return True
                return False
        except Exception as e:
            print(f"Failed to connect to peer at {host}:{port}: {e}")
            return False
    
    def search_file(self, query):
        results = []
        for peer in self.peers:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect(peer)
                    request = {'type': 'search', 'query': query}
                    s.send(json.dumps(request).encode())
                    response = json.loads(s.recv(1024).decode())
                    for filename in response['files']:
                        # Store source peer info with each result
                        results.append((filename, peer[0], peer[1]))
            except Exception as e:
                print(f"Could not search peer {peer}: {e}")
        return results
    
    def share_file(self, filepath):
        # Convert to absolute path to ensure file access works from any directory
        abs_filepath = os.path.abspath(filepath)
        
        if os.path.exists(abs_filepath):
            filename = os.path.basename(abs_filepath)
            file_size = os.path.getsize(abs_filepath)
            
            # Calculate piece size (default to 256KB)
            piece_size = 2**18  # 256KB
            
            # Calculate number of pieces
            num_pieces = (file_size + piece_size - 1) // piece_size
            
            # Calculate hashes for each piece
            pieces = []
            with open(abs_filepath, 'rb') as f:
                for i in range(num_pieces):
                    piece_data = f.read(piece_size)
                    piece_hash = hashlib.sha1(piece_data).hexdigest()
                    pieces.append(piece_hash)
            
            self.files[filename] = {
                'path': abs_filepath,  # Store absolute path
                'size': file_size,
                'piece_size': piece_size,
                'pieces': pieces,
                'hash': self.calculate_file_hash(abs_filepath)
            }
            print(f"Now sharing: {filename} (size: {file_size} bytes, pieces: {num_pieces})")
        else:
            print(f"File not found: {abs_filepath}")
    
    def download_file(self, peer_host, peer_port, filename):
        try:
            # Verify peer is connected
            found = False
            for peer in self.peers:
                if peer[0] == peer_host and peer[1] == peer_port:
                    found = True
                    break
            
            if not found:
                print(f"Peer at {peer_host}:{peer_port} is not connected")
                return False
            
            # Connect to peer to download file
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((peer_host, peer_port))
                
                # Request the file directly
                request = {
                    'type': 'download',
                    'filename': filename
                }
                s.send(json.dumps(request).encode())
                
                # Receive file content
                response = s.recv(1024).decode()
                try:
                    data = json.loads(response)
                    if 'error' in data:
                        print(f"Download error: {data['error']}")
                        return False
                except json.JSONDecodeError:
                    # If not JSON, it's the file content directly
                    with open(f"downloaded_{filename}", 'w') as f:
                        f.write(response)
                    print("File downloaded successfully")
                    return True
            
            print("File downloaded successfully")
            return True
                
        except Exception as e:
            print(f"Download failed: {e}")
            return False
    
    def send_file(self, client, filename):
        if filename in self.files:
            file_info = self.files[filename]
            filepath = file_info['path']
            file_size = file_info['size']
            
            # Send file info
            info = {
                'size': file_size,
                'piece_size': file_info['piece_size'],
                'pieces': file_info['pieces'],
                'hash': file_info['hash']
            }
            client.send(json.dumps(info).encode())
            
            # Wait for piece requests
            while True:
                try:
                    request = json.loads(client.recv(1024).decode())
                    if request['type'] == 'request':
                        piece_index = request['index']
                        begin = request['begin']
                        length = request['length']
                        
                        # Send the piece - ensure we can access the file
                        try:
                            print(f"Reading file {filepath} for piece {piece_index}")
                            with open(filepath, 'rb') as f:
                                f.seek(piece_index * file_info['piece_size'] + begin)
                                piece_data = f.read(length)
                                print(f"Read {len(piece_data)} bytes for piece {piece_index}")
                        except Exception as e:
                            print(f"Error reading file {filepath}: {e}")
                            piece_data = b''
                            
                            # Make sure we have data to send
                            if len(piece_data) > 0:
                                # Send piece size first - ensure it's exactly 10 bytes
                                size_str = f"{len(piece_data):010d}"
                                client.send(size_str.encode())
                                
                                # Wait for client to be ready
                                client.recv(5)
                                
                                # Send the piece data
                                client.send(piece_data)
                            else:
                                # Handle empty piece case
                                client.send("0000000000".encode())
                                client.recv(5)  # Wait for ready signal
                                # Send empty data
                                client.send(b'')
                    
                    elif request['type'] == 'not_interested':
                        break
                        
                except Exception as e:
                    print(f"Error sending file: {e}")
                    break
                    
        else:
            client.send(json.dumps({'error': 'File not found'}).encode())
    
    @staticmethod
    def calculate_file_hash(filepath):
        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def stop(self):
        self.running = False
        try:
            # Connect to self to break accept() loop
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((self.host, self.port))
                s.send(b'')
        except:
            pass
        self.socket.close()
        print("Peer stopped")
