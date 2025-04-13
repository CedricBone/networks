# Tracker for P2P file-sharing peer discovery
import socket
import threading
import json
import time


class Tracker:
    
    def __init__(self, host='localhost', port=8000):
        self.host = host
        self.port = port
        self.peers = {}  # {info_hash: [(peer_id, ip, port, files), ...]}
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((host, port))
        self.socket.listen(5)
        self.running = True
    
    def start(self):
        print(f"Tracker started on {self.host}:{self.port}")
        
        # Start cleanup thread
        threading.Thread(target=self.cleanup_peers, daemon=True).start()
        
        # Start listening for connections
        threading.Thread(target=self.listen_for_connections, daemon=True).start()
    
    def listen_for_connections(self):
        while self.running:
            try:
                client, address = self.socket.accept()
                threading.Thread(target=self.handle_connection, 
                                args=(client, address), daemon=True).start()
            except Exception as e:
                if self.running:
                    print(f"Error accepting connection: {e}")
                break
    
    def handle_connection(self, client, address):
        try:
            request = json.loads(client.recv(1024).decode())
            
            if request['type'] == 'announce':
                # Handle announce request (peer registering with tracker)
                self.handle_announce(client, address, request)
                
            elif request['type'] == 'get_peers':
                # Handle get_peers request (peer looking for other peers)
                self.handle_get_peers(client, request)
                
        except Exception as e:
            print(f"Error handling connection: {e}")
        finally:
            client.close()
    
    def handle_announce(self, client, address, request):
        peer_id = request.get('peer_id')
        info_hash = request.get('info_hash')
        port = request.get('port')
        files = request.get('files', [])
        
        # Use client's real IP address
        ip = address[0]
        
        # Register the peer
        if info_hash not in self.peers:
            self.peers[info_hash] = []
        
        # Update peer info or add new peer
        peer_entry = (peer_id, ip, port, files, time.time())
        
        # Remove any existing entry for this peer_id
        self.peers[info_hash] = [p for p in self.peers[info_hash] 
                                if p[0] != peer_id]
        
        # Add the new peer entry
        self.peers[info_hash].append(peer_entry)
        
        # Send response
        response = {
            'interval': 120,  # Announce interval in seconds
            'peers': len(self.peers[info_hash])
        }
        client.send(json.dumps(response).encode())
    
    def handle_get_peers(self, client, request):
        info_hash = request.get('info_hash')
        
        # Get the peers for the requested info_hash
        peer_list = []
        if info_hash in self.peers:
            for peer_id, ip, port, files, _ in self.peers[info_hash]:
                peer_list.append({
                    'peer_id': peer_id,
                    'ip': ip,
                    'port': port,
                    'files': files
                })
        
        # Send response
        response = {
            'peers': peer_list
        }
        client.send(json.dumps(response).encode())
    
    def cleanup_peers(self):
        while self.running:
            now = time.time()
            for info_hash in list(self.peers.keys()):
                # Filter out peers that haven't announced in the last 5 minutes
                self.peers[info_hash] = [p for p in self.peers[info_hash] 
                                       if now - p[4] < 300]
                
                # Remove empty info_hash entries
                if not self.peers[info_hash]:
                    del self.peers[info_hash]
            
            # Sleep for 60 seconds before next cleanup
            time.sleep(60)
    
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
        print("Tracker stopped")
