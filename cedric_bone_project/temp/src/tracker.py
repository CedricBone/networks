# Tracker for P2P file-sharing peer discovery
import socket
import threading
import json
import time
import datetime


class Tracker:
    
    def __init__(self, host='localhost', port=8000):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((host, port))
        self.files = {}  # info_hash -> list of peers
        self.peers = {}  # peer_id -> {address, last_seen, files}
        self.peer_cleanup_interval = 300  # seconds to consider a peer offline
        self.running = False
        self.cleanup_thread = None
    
    def start(self):
        self.socket.listen(5)
        self.running = True
        print(f"Tracker started on {self.host}:{self.port}")
        print(f"Tracker running at {self.host}:{self.port}")
        
        # Start peer cleanup thread
        self.cleanup_thread = threading.Thread(target=self.cleanup_stale_peers)
        self.cleanup_thread.daemon = True
        self.cleanup_thread.start()

        while self.running:
            try:
                client, addr = self.socket.accept()
                client_thread = threading.Thread(target=self.handle_client, args=(client, addr))
                client_thread.daemon = True
                client_thread.start()
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error accepting connection: {e}")
                break
    
    def handle_client(self, client, addr):
        try:
            # Receive data with proper error handling
            data = client.recv(4096)
            print(f"Tracker received raw data from {addr}: {data[:100]}...")
            if not data:
                # No data received, client disconnected
                return
                
            try:
                request = json.loads(data.decode())
                print(f"Tracker received request: {request}")
            except json.JSONDecodeError as e:
                print(f"Invalid JSON received from {addr}: {e}")
                error_response = {"status": "error", "message": "Invalid JSON data"}
                client.send(json.dumps(error_response).encode())
                return
                
            if 'type' not in request:
                print(f"Missing 'type' field in request from {addr}")
                error_response = {"status": "error", "message": "Missing type field"}
                client.send(json.dumps(error_response).encode())
                return
                
            if request['type'] == 'announce':
                # Peer announcing a file
                peer_id = request.get('peer_id', 'unknown')
                # Handle both info_hash and torrent_hash for backward compatibility
                info_hash = request.get('info_hash') or request.get('torrent_hash')
                port = request.get('port', addr[1])
                file_list = request.get('files', [])
                
                # Debug logging
                print(f"Peer {peer_id} announcing file with hash {info_hash}, files: {file_list}")
                
                peer_addr = (addr[0], port)
                
                # Update peer information with timestamp
                self.peers[peer_id] = {
                    'address': peer_addr,
                    'last_seen': datetime.datetime.now(),
                    'files': file_list
                }
                
                # Register file with this peer
                if info_hash not in self.files:
                    self.files[info_hash] = []
                
                # Remove old entries for this peer if they exist
                self.files[info_hash] = [p for p in self.files[info_hash] if p.get('peer_id') != peer_id]
                
                # Add the updated peer info
                peer_info = {'peer_id': peer_id, 'ip': addr[0], 'port': port, 'files': file_list}
                self.files[info_hash].append(peer_info)
                
                response = {'status': 'ok'}
                client.send(json.dumps(response).encode())
                
            elif request['type'] == 'get_peers':
                # Peer looking for other peers with a file
                # Handle both info_hash and torrent_hash for backward compatibility
                info_hash = request.get('info_hash') or request.get('torrent_hash')
                requesting_peer_id = request.get('peer_id', 'unknown')
                
                # Update requesting peer's last_seen timestamp
                if requesting_peer_id in self.peers:
                    self.peers[requesting_peer_id]['last_seen'] = datetime.datetime.now()
                
                if info_hash in self.files:
                    # Filter out the requesting peer from the response
                    response = {'peers': [p for p in self.files[info_hash] 
                                          if p.get('peer_id') != requesting_peer_id]}
                else:
                    response = {'peers': []}
                
                client.send(json.dumps(response).encode())
        except Exception as e:
            print(f"Error handling connection: {e}")
        finally:
            client.close()
    
    def cleanup_stale_peers(self):
        """Periodically check for and remove peers that haven't been seen recently"""
        while self.running:
            try:
                now = datetime.datetime.now()
                stale_peer_ids = []
                
                # Identify stale peers
                for peer_id, peer_data in self.peers.items():
                    last_seen = peer_data['last_seen']
                    if (now - last_seen).total_seconds() > self.peer_cleanup_interval:
                        stale_peer_ids.append(peer_id)
                
                # Remove stale peers from peers dictionary
                for peer_id in stale_peer_ids:
                    if peer_id in self.peers:
                        print(f"Removing stale peer: {peer_id}")
                        del self.peers[peer_id]
                
                # Remove stale peers from file listings
                for info_hash in self.files:
                    self.files[info_hash] = [p for p in self.files[info_hash] 
                                           if p.get('peer_id') not in stale_peer_ids]
            except Exception as e:
                print(f"Error in cleanup thread: {e}")
            
            time.sleep(60)  # Check every minute

    def stop(self):
        self.running = False
        if self.cleanup_thread and self.cleanup_thread.is_alive():
            self.cleanup_thread.join(timeout=2)
        self.socket.close()
        print("Tracker stopped")
