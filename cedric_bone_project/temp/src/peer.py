# Peer implementation for P2P file sharing
import socket
import threading
import json
import os
import hashlib
import traceback

class Peer:
    
    def __init__(self, host='localhost', port=0):
        self.host = host
        self.port = port
        self.shared_files = {}  # Dictionary to store file information
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
        
    def get_port(self):
        # Return the port this peer is listening on
        return self.port
    
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
            addr = client.getpeername()
            data = client.recv(4096)
            if not data:
                return

            request = json.loads(data.decode())
            print(f"Peer received request: {request['type'] if 'type' in request else 'unknown'}")

            if request['type'] == 'handshake':
                # Respond to handshake
                response = {'type': 'handshake_response', 'peer_id': id(self)}
                client.send(json.dumps(response).encode())
                
            elif request['type'] == 'search':
                # Handle file search request
                response = {'files': [f for f in self.shared_files if request['query'] in f]}
                client.send(json.dumps(response).encode())
                
            elif request['type'] == 'request_piece':
                try:
                    filename = request.get('filename')
                    piece_index = request.get('piece_index')

                    if filename is None or piece_index is None:
                        error = {'error': 'Missing filename or piece_index in request'}
                        client.sendall(json.dumps(error).encode())
                        return # Early exit on bad request

                    if filename in self.shared_files:
                        file_info = self.shared_files[filename]
                        filepath = file_info['path']
                        
                        # Verify the file still exists and is accessible
                        if not os.path.exists(filepath):
                            print(f"Error: Shared file '{filepath}' no longer exists")
                            error = {'error': f"File {filename} no longer exists on disk"}
                            client.sendall(json.dumps(error).encode())
                            # Remove from shared files
                            del self.shared_files[filename]
                            return
                            
                        file_size = file_info['size']
                        piece_size = file_info.get('piece_size', 262144)
                        num_pieces = (file_size + piece_size - 1) // piece_size

                        # Ensure piece_index is an integer
                        try:
                            piece_index = int(piece_index)
                        except (ValueError, TypeError):
                            print(f"Error: Invalid piece_index format: {piece_index}")
                            error = {'error': 'Invalid piece index format'}
                            client.sendall(json.dumps(error).encode())
                            return

                        if 0 <= piece_index < num_pieces:
                            offset = piece_index * piece_size
                            # Calculate how much data to read for this piece (handle last piece)
                            bytes_to_read = min(piece_size, file_size - offset)

                            # Verify file again just before reading in case it was deleted moments ago
                            if not os.path.exists(filepath):
                                print(f"Error: File disappeared just before reading piece: '{filepath}'")
                                error = {'error': f"File {filename} was deleted while trying to serve it"}
                                client.sendall(json.dumps(error).encode())
                                # Remove from shared files since it no longer exists
                                del self.shared_files[filename]
                                return
                                
                            try:
                                with open(filepath, 'rb') as f: # Open in binary read mode
                                    f.seek(offset)
                                    piece_data = f.read(bytes_to_read)
                                    
                                    # Don't proceed if we read 0 bytes
                                    if not piece_data or len(piece_data) == 0:
                                        print(f"Error: Read 0 bytes from {filepath} at offset {offset}")
                                        error = {'error': f"Failed to read data from file {filename}"}
                                        client.sendall(json.dumps(error).encode())
                                        return
                                        
                                    if len(piece_data) != bytes_to_read:
                                        print(f"Warning: Read {len(piece_data)} bytes when {bytes_to_read} were expected")
                                    
                                    print(f"Peer {self.host}:{self.port}: Attempting to send {len(piece_data)} bytes for piece {piece_index} to {client.getpeername()}")
                                    client.sendall(piece_data) # Send raw bytes
                                    print(f"Peer {self.host}:{self.port}: Successfully sent piece {piece_index} to {client.getpeername()}")
                            except IOError as e:
                                print(f"Error reading piece {piece_index} of file {filepath}: {e}")
                                error = {'error': f"IOError: {str(e)}"}
                                client.sendall(json.dumps(error).encode())
                        else:
                            print(f"Invalid piece index {piece_index} requested for {filename}")
                            error = {'error': f"Invalid piece index {piece_index}"}
                            client.sendall(json.dumps(error).encode())
                    else:
                        print(f"File {filename} not found for piece request")
                        error = {'error': f"File {filename} not shared by this peer"}
                        client.sendall(json.dumps(error).encode())

                except Exception as e:
                    print(f"\n--- Error handling 'request_piece' --- ")
                    traceback.print_exc() # Print the full traceback
                    print(f"--------------------------------------------------")
                    try:
                        error_response = {'status': 'error', 'message': f'Internal peer error: {str(e)}'}
                        client.sendall(json.dumps(error_response).encode())
                    except Exception: 
                        pass  # Ignore errors sending error response

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
            print(f"Peer {self.host}:{self.port}: Finished handling connection from {client.getpeername() if hasattr(client, 'getpeername') else 'unknown'}.")
            # Not immediately closing to allow data to be sent
            # connection will be closed by the operating system when the thread terminates
    
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
    
    def share_file(self, filename, piece_size=262144):
        """Register a file to be shared with the network."""
        # Get absolute path to ensure consistency
        abs_filepath = os.path.abspath(filename)
        
        # Check if file exists
        if not os.path.exists(abs_filepath):
            print(f"Error: File '{filename}' does not exist")
            return False

        # Check if file is readable
        if not os.access(abs_filepath, os.R_OK):
            print(f"Error: Cannot read file '{filename}'")
            return False
            
        # Get file size and divide into pieces
        file_size = os.path.getsize(abs_filepath)
        if file_size == 0:
            print(f"Error: File '{filename}' is empty")
            return False
            
        # Create shared directory if it doesn't exist
        shared_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'shared')
        os.makedirs(shared_dir, exist_ok=True)
        
        # Copy the file to the shared directory to ensure it remains available
        shared_filepath = os.path.join(shared_dir, os.path.basename(filename))
        try:
            with open(abs_filepath, 'rb') as src_file:
                file_content = src_file.read()
                with open(shared_filepath, 'wb') as dest_file:
                    dest_file.write(file_content)
            print(f"Created stable copy of {filename} at {shared_filepath}")
        except IOError as e:
            print(f"Error copying file to shared directory: {e}")
            return False
        
        num_pieces = (file_size + piece_size - 1) // piece_size  # Ceiling division

        # Calculate hash for each piece
        pieces = []
        with open(shared_filepath, 'rb') as f:
            for i in range(num_pieces):
                f.seek(i * piece_size)
                piece_data = f.read(min(piece_size, file_size - (i * piece_size)))
                if not piece_data:  # Safeguard against reading beyond EOF
                    break
                piece_hash = hashlib.sha1(piece_data).hexdigest()
                pieces.append(piece_hash)
        
        # Store file info with path to the copy in the shared directory
        self.shared_files[filename] = {
            'path': shared_filepath,  # Use path to the copy
            'original_path': abs_filepath,  # Keep original for reference
            'size': file_size,
            'piece_size': piece_size,
            'pieces': pieces,
            'hash': self.calculate_file_hash(shared_filepath)
        }
        print(f"Now sharing: {filename} (size: {file_size} bytes, pieces: {num_pieces})")
        return True
    
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
        if filename in self.shared_files:
            file_info = self.shared_files[filename]
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
