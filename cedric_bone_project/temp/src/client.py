# Client for P2P file sharing
import socket
import json
import os
import random
import peer
import metainfo as M
import hashlib
import time
import traceback

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
        self.trackers = []
        # shared files
        self.shared_files = []
    
    def calculate_file_hash(self, filepath):
        """Calculate SHA1 hash of file contents"""
        hash_obj = hashlib.sha1()
        with open(filepath, 'rb') as f:
            while chunk := f.read(4096):  # Read in 4KB chunks
                hash_obj.update(chunk)
        return hash_obj.hexdigest()
    
    def verify_file_hash(self, filepath, expected_hash):
        """Verify file hash matches expected hash"""
        # Calculate hash
        actual_hash = self.calculate_file_hash(filepath)
        
        # Compare (case-insensitive)
        return actual_hash.lower() == expected_hash.lower()
    
    # connect to tracker
    def add_tracker(self, host, port):
        try:
            # add tracker info
            tracker = {"host": host, "port": port}
            self.trackers.append(tracker)
            return True
        except:
            return False
    
    # get peers from tracker
    def get_peers_from_tracker(self, tracker_url, info_hash):
        host, port = tracker_url.split(":")
        port = int(port)
        
        try:
            # Create socket
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(5)  # 5 seconds timeout
            s.connect((host, port))
            
            # Create request
            req = {
                "type": "get_peers",
                "peer_id": self.peer_id,
                "ip": socket.gethostbyname(socket.gethostname()),
                "port": self.peer.get_port(),
                "info_hash": info_hash  # Changed from torrent_hash to info_hash to match tracker expectations
            }
            
            # Send request
            s.sendall(json.dumps(req).encode())
            
            # Receive response
            response = json.loads(s.recv(4096).decode())
            s.close()
            
            # Extract peers from response
            if "peers" in response:
                # Tracker successfully returned peers
                return response["peers"]
            elif "status" in response and response["status"] == "error":
                # Error response from tracker
                message = response.get("message", "Unknown error")
                print(f"Error getting peers: {message}")
                return []
            else:
                # Empty or unexpected response format
                print("Warning: Unexpected response format from tracker")
                return []
                
        except Exception as e:
            print(f"Error connecting to tracker: {e}")
            return []
    
    # share file
    def share_file(self, filepath, tracker_url=None):
        try:
            # Check if file exists and is readable
            if not os.path.isfile(filepath):
                print(f"Error: File '{filepath}' does not exist.")
                return False
                
            # Create directory if it doesn't exist
            os.makedirs("shared", exist_ok=True)
                
            # Copy file to shared directory with a stable method
            filename = os.path.basename(filepath)
            shared_filepath = os.path.join("shared", filename)
                
            # Use a more reliable copy method instead of simple rename/move
            with open(filepath, 'rb') as src_file:
                with open(shared_filepath, 'wb') as dest_file:
                    # Copy in chunks to handle large files
                    chunk_size = 1024 * 1024  # 1MB chunks
                    while True:
                        chunk = src_file.read(chunk_size)
                        if not chunk:
                            break
                        dest_file.write(chunk)
            
            # Create torrent
            if tracker_url:
                # Create torrent file
                torrent_path = self.create_torrent(shared_filepath, tracker_url)
                if torrent_path:
                    # Load the metainfo file
                    metainfo = M.load_metainfo(torrent_path)
                    if not metainfo:
                        print("Error: Could not load created torrent file.")
                        return False
                        
                    print(f"Created torrent file: {torrent_path}")
                    # Register with tracker
                    print(f"Attempting to register {os.path.basename(filepath)} with tracker at {tracker_url}...")
                    if self.register_with_tracker(tracker_url, metainfo):
                        print(f"Successfully registered {os.path.basename(filepath)} with tracker")
                    else:
                        print(f"ERROR: Failed to register {os.path.basename(filepath)} with tracker. File may not be discoverable.")
                        # Optionally return False here if registration is critical
                        # return False 
                else:
                    print("Failed to create torrent file.")
                    return False
            
            # Add to peer's shared files
            self.peer.add_shared_file(filename, shared_filepath)
            print(f"Now sharing: {filename}")
            return True
            
        except Exception as e:
            print(f"Error sharing file: {e}")
            traceback.print_exc()
            return False
    
    def download_from_torrent(self, torrent_path, output_dir="."):
        metainfo = None
        output_path = None
        output_file = None
        download_successful = False  # Flag for cleanup logic
        num_pieces = 0
        downloaded_pieces = {}
        peer_pool = []
        filename = "unknown_file"
        
        try:  # Outer try for overall process and cleanup
            try:  # --- Setup Phase --- 
                metainfo = M.load_metainfo(torrent_path)
                if not metainfo:
                    print(f"Error: Unable to load torrent file: {torrent_path}")
                    return False
                
                # Extract torrent info
                info = metainfo.get("info", {})
                filename = info.get("name", "unknown_file")
                file_length = info.get("length", 0)
                piece_length = info.get("piece length", 0)
                piece_hashes = info.get("piece_hashes", [])
                file_hash = metainfo.get("file_hash", None)
                tracker_url = metainfo.get("announce", "")
                torrent_hash = metainfo.get("info_hash", "unknown")
                
                if not file_length or not piece_length:
                    print("Error: Invalid torrent file (missing length information).")
                    return False
                
                num_pieces = (file_length + piece_length - 1) // piece_length
                if piece_hashes and len(piece_hashes) != num_pieces:
                    print(f"Warning: Mismatched piece count in torrent file: {len(piece_hashes)} hashes for {num_pieces} pieces")
                
                # Prepare output file
                output_path = os.path.join(output_dir, filename)
                output_file = open(output_path, "wb")
                
                # Pre-allocate file space (optional)
                output_file.truncate(file_length)  # Allocate space
                
                # Initialize download tracking
                pieces_needed = list(range(num_pieces))
                total_bytes_downloaded = 0
                total_bytes_expected = file_length
                
                # --- Get Peers Phase ---
                print(f"Getting peers for {filename}...")
                info_hash = metainfo.get("info_hash", "unknown")
                peers = self.get_peers_from_tracker(tracker_url, info_hash)
                if not peers:
                    print("Error: No peers available.")
                    return False
                
                # Create peer pool
                print(f"Found {len(peers)} potential peers: {peers}")
                for peer_info in peers:
                    # Handle different peer info formats
                    ip = peer_info.get("ip") 
                    port = peer_info.get("port")
                    
                    if not ip or not port:
                        print(f"Warning: Invalid peer info format: {peer_info}")
                        continue
                        
                    peer_pool.append({
                        "host": ip,
                        "port": port
                    })
                
                print(f"Found {len(peer_pool)} peers.")
                
                # --- Download Phase ---
                all_pieces_present = False
                print(f"Downloading {filename} ({file_length} bytes, {num_pieces} pieces)...")
                
                # Main download loop
                while pieces_needed and peer_pool:
                    # Get the next piece to download
                    piece_index = pieces_needed[0]
                    
                    # Determine piece size (last piece might be smaller)
                    piece_size = piece_length
                    if piece_index == num_pieces - 1 and file_length % piece_length != 0:
                        piece_size = file_length % piece_length
                    
                    print(f"Downloading piece {piece_index+1}/{num_pieces} ({piece_size} bytes)...")
                    
                    # Try getting piece from available peers
                    attempts = 0
                    max_attempts_per_piece = len(peer_pool) * 2  # Try each peer twice per piece
                    piece_downloaded = False
                    
                    while attempts < max_attempts_per_piece and not piece_downloaded:
                        if not peer_pool:  # Check if peer_pool became empty
                            print("Error: No more peers available to try.")
                            break  # Exit inner attempt loop
                        
                        # Get a peer from the pool (round-robin)
                        peer_info = peer_pool.pop(0)  # Take from front
                        peer_pool.append(peer_info)  # Put back at end
                        peer_host = peer_info["host"]
                        peer_port = peer_info["port"]
                        
                        attempts += 1
                        print(f"  Attempt {attempts}/{max_attempts_per_piece} from {peer_host}:{peer_port}...", end=" ")
                        
                        try:
                            # Create socket and connect to peer
                            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            client_socket.settimeout(10)  # 10 second timeout
                            client_socket.connect((peer_host, peer_port))
                            
                            # Prepare request
                            request = {
                                "type": "request_piece",
                                "filename": filename,
                                "piece_index": piece_index,
                                "piece_length": piece_size,
                                "peer_id": self.peer_id
                            }
                            
                            # Send request
                            client_socket.sendall(json.dumps(request).encode())
                            
                            # Receive piece data directly (binary)
                            piece_data = b""
                            while len(piece_data) < piece_size:
                                chunk = client_socket.recv(4096)
                                if not chunk:
                                    break
                                piece_data += chunk
                                
                            client_socket.close()
                            
                            # Check if we received the full piece
                            if len(piece_data) == piece_size:
                                # --- Piece Verification (Optional) ---
                                piece_valid = True
                                if piece_hashes and piece_index < len(piece_hashes):
                                    expected_piece_hash = piece_hashes[piece_index]
                                    
                                    # Calculate piece hash
                                    actual_piece_hash_obj = hashlib.sha1()
                                    actual_piece_hash_obj.update(piece_data)
                                    actual_hexdigest = actual_piece_hash_obj.hexdigest()
                                    
                                    # Compare hex strings directly
                                    if actual_hexdigest == expected_piece_hash:
                                        print(f"Piece {piece_index} hash verified successfully.")
                                    else:
                                        print(f"Failed (Piece {piece_index} hash mismatch!). Retrying...")
                                        piece_valid = False
                                else:
                                    print("Note: No hash verification performed for this piece.")
                                    # No hashes provided or index out of bounds
                                
                                if piece_valid:
                                    print(f"Success ({len(piece_data)} bytes).")
                                    # Write piece to file at correct offset
                                    offset = piece_index * piece_length
                                    output_file.seek(offset)
                                    output_file.write(piece_data)
                                    total_bytes_downloaded += len(piece_data)
                                    # Record piece as downloaded (can store data or just True)
                                    downloaded_pieces[piece_index] = True 
                                    pieces_needed.pop(0)  # Remove from needed list
                                    piece_downloaded = True  # Exit attempt loop for this piece
                                else:
                                    # Piece failed verification, loop continues to try next peer/attempt
                                    pass 
                                    
                            else:
                                print(f"Failed (Received {len(piece_data)}/{piece_size} bytes only).")
                                # Incomplete data, try another peer
                                    
                        except socket.timeout:
                            print(f"Failed (Timeout connecting to {peer_host}:{peer_port}).")
                            # Optionally remove peer from pool after timeout?
                        except ConnectionRefusedError:
                            print(f"Failed (Connection refused by {peer_host}:{peer_port}).")
                            # Optionally remove peer from pool
                        except Exception as piece_e:
                            print(f"Failed (Error communicating with {peer_host}:{peer_port}: {piece_e})")
                            # Consider logging traceback here too if needed
                            # traceback.print_exc()

                    # End of attempts loop for one piece
                    if not piece_downloaded:
                        print(f"Error: Failed to download piece {piece_index} after {max_attempts_per_piece} attempts.")
                        break  # Exit the main while pieces_needed loop
                
                # Check if all pieces were downloaded
                if not pieces_needed:
                    all_pieces_present = True
                    # Close file before verification
                    output_file.close()
                    output_file = None  # So it's not closed again in finally
                    
                    # All pieces downloaded, do final verification
                    if file_hash:
                        print("Verifying downloaded file hash...")
                        if self.verify_file_hash(output_path, file_hash):
                            print("File verification successful!")
                            download_successful = True
                        else:
                            print("Error: File hash verification failed!")
                            download_successful = False
                    else:
                        print("No file hash available to verify. Download assumed successful.")
                        download_successful = True
                else:
                    print(f"Download incomplete. Missing {len(pieces_needed)} pieces.")
                    download_successful = False
            
            except Exception as e:
                print(f"Error during download: {e}")
                traceback.print_exc()
                download_successful = False
                
        finally:
            # Cleanup
            try:
                if output_file:
                    output_file.close()
            except:
                pass
                
            # Handle download completion or failure
            if not download_successful and output_path and os.path.exists(output_path):
                print("Removing incomplete download file...")
                try:
                    os.remove(output_path)
                except Exception as remove_e:
                    print(f"Error removing partial file: {remove_e}")
            elif download_successful:
                print(f"Download complete: {output_path}")
                
        return download_successful

    def create_torrent(self, filepath, tracker_url, output_path=None):
        # Generate metainfo
        print(f"Creating metainfo for {filepath}...")
        metainfo = M.create_metainfo(filepath, tracker_url)
        
        # Check if metainfo generation failed
        if metainfo is None:
            print(f"ERROR: M.create_metainfo failed for {filepath}")
            return None
        
        print(f"Metainfo created successfully. Saving to torrent file...")

        # Set default output path if not provided
        if not output_path:
            output_path = os.path.basename(filepath) + '.torrent'
        
        # Write to file
        try:
            with open(output_path, 'w') as f:
                json.dump(metainfo, f, indent=4)
            print(f"Torrent file saved to {output_path}")
            return output_path
        except Exception as e:
            print(f"Error creating torrent file during save: {e}")
            return None
    
    def register_with_tracker(self, tracker_url, metainfo):
        host, port = tracker_url.split(":")
        port = int(port)
        
        # Create socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)  # 5 seconds timeout
        
        try:
            # Connect to tracker
            s.connect((host, port))
            
            # Prepare request
            request = {
                "type": "announce",  # Changed from 'register' to 'announce' to match tracker expectation
                "peer_id": self.peer_id,
                "ip": socket.gethostbyname(socket.gethostname()),
                "port": self.peer.get_port(),
                "info_hash": metainfo["info_hash"],  # Added info_hash for tracker to track the file
                "files": [metainfo["info"]["name"]]  # Simplified to match tracker's expected format
            }
            
            # Send request
            request_json = json.dumps(request)
            print(f"Sending announce request to tracker: {request_json}")
            s.sendall(request_json.encode())
            
            # Receive response
            print("Waiting for tracker response...")
            response_data = s.recv(4096)
            print(f"Received tracker response: {response_data.decode()}")
            response = json.loads(response_data.decode())
            
            # Check response
            if response.get("status") == "ok":  # Changed to match tracker's 'ok' response
                print(f"Successfully registered with tracker at {tracker_url}")
                return True
            else:
                print(f"Error registering with tracker: {response['message']}")
                return False
                
        except socket.timeout:
            print(f"Error communicating with tracker: Connection timed out after 5 seconds.")
            return False
        except ConnectionRefusedError:
            print(f"Error communicating with tracker: Connection refused by {tracker_url}.")
            return False
        except Exception as e:
            print(f"Error communicating with tracker: {e}")
            return False
            
        finally:
            s.close()
            
    def stop(self):
        """Stop the client and clean up resources"""
        if hasattr(self, 'peer') and self.peer:
            self.peer.stop()
        print("Client stopped")
