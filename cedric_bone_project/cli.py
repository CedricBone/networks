"""
Command-line interface for P2P file sharing app
"""
import sys
import threading
import utils

class CommandLine:
    """Command-line interface"""
    
    def __init__(self, node):
        self.node = node
        self.commands = {
            'search': (self.search, 'Search for files (usage: search <query>)'),
            'list': (self.list, 'List local files'),
            'peers': (self.peers, 'List connected peers'),
            'connect': (self.connect, 'Connect to a peer (usage: connect <ip> <port>)'),
            'download': (self.download, 'Download a file (usage: download <result_index>)'),
        }
        self.search_results = []
    
    def start(self):
        """Start the CLI"""
        print("\nP2P File Sharing Application")
        print("============================")
        print("Use 'connect' to connect to other peers")
        print("Use 'search' to search for files")
        print("Use 'list' to list local files")
        print("Use 'peers' to list connected peers")
        print("Use 'download' to download a file")
        self.node.start()
        
        try:
            while True:
                try:
                    command = input("\n> ").strip()
                    if not command:
                        continue
                    
                    parts = command.split()
                    cmd = parts[0].lower()
                    args = parts[1:] if len(parts) > 1 else []
                    
                    if cmd in self.commands:
                        self.commands[cmd][0](args)
                    else:
                        print(f"Unknown command: {cmd}")
                except EOFError:
                    break
        except KeyboardInterrupt:
            print("\nExiting...")
        finally:
            self.node.stop()

    
    def search(self, args):
        """Search for files"""

        # build query
        query = ' '.join(args)

        # search
        print(f"Searching for '{query}'...")
        self.search_results = self.node.search_files(query)

        # print results
        print("\nSearch results:")
        for i, result in enumerate(self.search_results):
            if result['peer'] == 'local':
                peer_str = 'Local'
            else:   
                peer_str = f"{result['peer'][0]}:{result['peer'][1]}"
            size_str = result['size']

            print(f"  [{i}] {result['filename']} ({size_str}) - {peer_str}")
    
    def list(self, args):
        """List local files"""
        files = self.node.get_files()
        print("\nLocal files:")
        for filename in files:
            size_str = self.node.files[filename]['size']
            print(f"  {filename} ({size_str})")
    
    def peers(self, args):
        """List peers"""
        peers = self.node.get_peers()
        print("\nConnected peers:")
        for i, peer in enumerate(peers):
            print(f"  [{i}] {peer[0]}:{peer[1]}")
    
    def connect(self, args):
        """Connect to peer"""
        ip, port = args
        port = int(port)
        if self.node.add_peer(ip, port):
            print(f"Connected to: {ip}:{port}")
        else:
            print(f"Already connected to: {ip}:{port}")


    
    def download(self, args):
        """Download a file"""
        index = int(args[0])
        if index < 0 or index >= len(self.search_results):
            print(f"Invalid index")
            return
        
        result = self.search_results[index]
        
        # already local
        if result['peer'] == 'local':
            return
        
        print(f"Downloading '{result['filename']}' from {result['peer'][0]}:{result['peer'][1]}...")
        
        # Download in anothher thread
        threading.Thread(
            target=self.download_thread,
            args=(result['peer'], result['filename']),
            daemon=True
        ).start()
    
    def download_thread(self, peer, filename):
        """Thread function for downloading"""
        self.node.download_file(peer, filename)
        print(f"\nDownloaded {filename}")