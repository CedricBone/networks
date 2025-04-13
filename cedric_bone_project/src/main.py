# Main CLI for P2P file-sharing application
import os
import sys
import argparse
import client as C
import tracker as T
import metainfo as M 


def print_help():
    print("\nP2P File Sharing Application")
    print("============================")
    print("\nAvailable commands:")
    print("  tracker - Start a tracker server")
    print("  create <file> <tracker_url> - Create a .torrent file")
    print("  share <file> <tracker_url> - Share a file with the network")
    print("  download <torrent_file> - Download a file from a .torrent file")
    print("  search <query> - Search for files across connected peers")
    print("  peers - List connected peers")
    print("  files - List shared files")
    print("  connect <host> <port> - Manually connect to a peer")
    print("  help - Show this help message")
    print("  exit - Exit the application")


def main():
    parser = argparse.ArgumentParser(description="P2P File Sharing Application")
    parser.add_argument('--tracker', action='store_true', help="Start as tracker")
    parser.add_argument('--client', action='store_true', help="Start as client")
    parser.add_argument('--host', default='localhost', help="Host to bind to")
    parser.add_argument('--port', type=int, default=0, help="Port to bind to")
    
    args = parser.parse_args()
    
    # Check if we should start as a tracker
    if args.tracker:
        tracker = T.Tracker(args.host, args.port or 8000)
        tracker.start()
        print(f"Tracker running at {tracker.host}:{tracker.port}")
        
        try:
            input("Press Enter to stop the tracker...")
        except KeyboardInterrupt:
            pass
        finally:
            tracker.stop()
        return
    
    # Create client
    client = C.Client()
    
    print(f"\nP2P client started on port {client.peer.port}")
    print_help()
    
    # Main loop
    try:
        while True:
            try:
                command = input("\nEnter command: ").strip().split()
                
                if not command:
                    continue
                
                if command[0] == "help":
                    print_help()
                
                elif command[0] == "tracker":
                    # Start a tracker in the background
                    tracker_port = 8000
                    if len(command) > 1:
                        tracker_port = int(command[1])
                    
                    tracker = T.Tracker(args.host, tracker_port)
                    tracker.start()
                    print(f"Tracker started on {args.host}:{tracker_port}")
                
                elif command[0] == "create":
                    if len(command) < 3:
                        print("Usage: create <file> <tracker_url>")
                        continue
                    
                    file_path = command[1]
                    tracker_url = command[2]
                    
                    if not os.path.exists(file_path):
                        print(f"File not found: {file_path}")
                        continue
                    
                    output_path = file_path + ".torrent"
                    metainfo = M.create_metainfo(file_path, tracker_url)
                    M.save_metainfo(metainfo, output_path)
                    print(f"Created torrent file: {output_path}")
                
                elif command[0] == "share":
                    if len(command) < 3:
                        print("Usage: share <file> <tracker_url>")
                        continue
                    
                    file_path = command[1]
                    tracker_url = command[2]
                    
                    if not os.path.exists(file_path):
                        print(f"File not found: {file_path}")
                        continue
                    
                    torrent_path = client.create_torrent(file_path, tracker_url)
                    print(f"File shared and torrent created: {torrent_path}")
                
                elif command[0] == "download":
                    if len(command) < 2:
                        print("Usage: download <torrent_file>")
                        continue
                    
                    torrent_path = command[1]
                    
                    if not os.path.exists(torrent_path):
                        print(f"Torrent file not found: {torrent_path}")
                        continue
                    
                    output_path = client.download_from_torrent(torrent_path)
                    if output_path:
                        print(f"Download complete: {output_path}")
                    else:
                        print("Download failed")
                
                elif command[0] == "search":
                    if len(command) < 2:
                        print("Usage: search <query>")
                        continue
                    
                    query = command[1]
                    results = client.peer.search_file(query)
                    
                    if results:
                        print("\nSearch results:")
                        for i, (filename, host, port) in enumerate(results, 1):
                            print(f"{i}. {filename} (from {host}:{port})")
                    else:
                        print("No files found")
                
                elif command[0] == "peers":
                    if not client.peer.peers:
                        print("No connected peers")
                    else:
                        print("\nConnected peers:")
                        for i, (host, port) in enumerate(client.peer.peers, 1):
                            print(f"{i}. {host}:{port}")
                
                elif command[0] == "files":
                    if not client.peer.files:
                        print("No shared files")
                    else:
                        print("\nShared files:")
                        for i, (filename, info) in enumerate(client.peer.files.items(), 1):
                            print(f"{i}. {filename} ({info['size']} bytes)")
                
                elif command[0] == "connect":
                    if len(command) < 3:
                        print("Usage: connect <host> <port>")
                        continue
                    
                    host = command[1]
                    port = int(command[2])
                    
                    if client.peer.connect_to_peer(host, port):
                        print(f"Connected to peer at {host}:{port}")
                    else:
                        print(f"Failed to connect to peer at {host}:{port}")
                
                elif command[0] == "exit":
                    break
                
                else:
                    print(f"Unknown command: {command[0]}")
                    print("Type 'help' for available commands")
                
            except Exception as e:
                print(f"Error: {str(e)}")
        
    except KeyboardInterrupt:
        print("\nExiting...")
    
    finally:
        client.stop()


if __name__ == "__main__":
    main()
