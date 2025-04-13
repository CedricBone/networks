# Client for P2P file sharing
import socket
import json
import os
import random
import peer
import metainfo as M

chars = 'abcdefghijklmnopqrstuvwxyz0123456789'

class Client:
    
    def __init__(self, download_dir="downloads"):
        # download directory
        self.download_dir = download_dir
        os.makedirs(download_dir, exist_ok=True)

        # random peer_id
        peerid = ""
        for char in range(20):
            randindex = random.randint(0, 35)
            peerid += chars[randindex]
        self.peer_id = peerid
        
        # peer
        self.peer = peer.Peer()
        self.peer.start()
        # trackers
        self.trackers = set()
        # torrents
        self.torrents = {}  # info_hash -> metainfo
    
    def register_with_tracker(self, tracker_url, info_hash, files=[]):
        # tracker URL
        host, port = tracker_url.split(':')
        port = int(port)
        
        # Connect to tracker
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((host, port))
            request = {
                'type': 'announce',
                'peer_id': self.peer_id,
                'info_hash': info_hash,
                'port': self.peer.port,
                'files': files
            }
            s.send(json.dumps(request).encode())
            
            # response
            response = json.loads(s.recv(1024).decode())
            self.trackers.add(tracker_url)
            
            return True
                
    
    def get_peers_from_tracker(self, tracker_url, info_hash):
        # tracker URL
        host, port = tracker_url.split(':')
        port = int(port)
        
        # Connect tracker
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((host, port))
            request = {
                'type': 'get_peers',
                'info_hash': info_hash
            }
            s.send(json.dumps(request).encode())
            
            # response
            response = json.loads(s.recv(1024).decode())
            
            return response.get('peers', [])
    
    def open_torrent(self, torrent_path):
        # Load 
        metainfo = M.load_metainfo(torrent_path)
        info_hash = metainfo['info_hash']
        
        # Store 
        self.torrents[info_hash] = metainfo
        tracker_url = metainfo['announce']
        self.register_with_tracker(tracker_url, info_hash)
        
        # Get peers
        peers = self.get_peers_from_tracker(tracker_url, info_hash)
        # Connect peers
        count = 0
        for peer in peers:
            if self.peer.connect_to_peer(peer['ip'], peer['port']):
                count += 1
        
        return metainfo
    
    def download_from_torrent(self, torrent_path):
        metainfo = self.open_torrent(torrent_path)
        if not metainfo:
            return None
        
        info_hash = metainfo['info_hash']
        info = metainfo['info']
        filename = info['name']
        file_length = info['length']
        piece_length = info['piece length']
        pieces = info['pieces']
        
        # Get peers
        tracker_url = metainfo['announce']
        peers = self.get_peers_from_tracker(tracker_url, info_hash)
        
        # Check if we have any peers
        if not peers:
            print("No peers available for download")
            return None
        
        # Choose a peer to download from
        peer = peers[0]
        
        # Download the file
        output_path = os.path.join(self.download_dir, filename)
        
        # Connect to the peer
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((peer['ip'], peer['port']))
            
            # Send download request
            request = {
                'type': 'download',
                'filename': filename
            }
            s.send(json.dumps(request).encode())
            
            # Receive response/file content
            # A large buffer size might be needed for larger files
            # In a real implementation, streaming/chunking would be better.
            received_data = b""
            while True:
                chunk = s.recv(4096)
                if not chunk:
                    break
                received_data += chunk
            
            # Try to decode as JSON first (for error messages)
            try:
                response_text = received_data.decode()
                data = json.loads(response_text)
                if 'error' in data:
                    print(f"Download error from peer: {data['error']}")
                    return None
                else:
                    # This case shouldn't happen with current peer logic
                    # but handle it defensively.
                    print("Received unexpected JSON response instead of file data.")
                    return None
            except json.JSONDecodeError:
                # If JSON decoding fails, assume it's the raw file data
                try:
                    with open(output_path, 'wb') as f: # Use 'wb' for binary write
                        f.write(received_data)
                    print(f"Download complete, file saved to: {output_path}")
                    return output_path
                except Exception as e:
                    print(f"Error writing downloaded file {output_path}: {e}")
                    return None
            except UnicodeDecodeError:
                # If decoding fails, it's likely binary data (the file)
                try:
                    with open(output_path, 'wb') as f: # Use 'wb' for binary write
                        f.write(received_data)
                    print(f"Download complete, file saved to: {output_path}")
                    return output_path
                except Exception as e:
                    print(f"Error writing downloaded file {output_path}: {e}")
                    return None
            except Exception as e:
                print(f"An unexpected error occurred during download: {e}")
                return None
    
    def create_torrent(self, filepath, tracker_url, output_path=None):
        # Generate metainfo
        metainfo = M.create_metainfo(filepath, tracker_url)
        
        # Set default output path if not provided
        if not output_path:
            output_path = os.path.basename(filepath) + '.torrent'
        
        # Save to file
        M.save_metainfo(metainfo, output_path)
        
        # Share the file
        self.peer.share_file(filepath)
        
        # Register with tracker
        info_hash = metainfo['info_hash']
        self.register_with_tracker(tracker_url, info_hash, [os.path.basename(filepath)])
        
        return output_path
    
    def stop(self):
        self.peer.stop()
