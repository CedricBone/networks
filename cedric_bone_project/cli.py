"""
Command-line interface for P2P file sharing app
"""
import sys
import threading
import utils

class CommandLine:
    """Simple command-line interface for the P2P application"""
    
    def __init__(self, node):
        self.node = node
        self.commands = {
            'help': (self.cmd_help, 'Show available commands'),
            'search': (self.cmd_search, 'Search for files (usage: search <query>)'),
            'list': (self.cmd_list, 'List local files'),
            'peers': (self.cmd_peers, 'List connected peers'),
            'connect': (self.cmd_connect, 'Connect to a peer (usage: connect <ip> <port>)'),
            'disconnect': (self.cmd_disconnect, 'Disconnect from a peer (usage: disconnect <ip> <port>)'),
            'download': (self.cmd_download, 'Download a file (usage: download <result_index>)'),
            'quit': (self.cmd_quit, 'Exit the application')
        }
        self.search_results = []
    
    def start(self):
        """Start the CLI"""
        print("\nP2P File Sharing Application")
        print("============================")
        print("Type 'help' for available commands")
        print("Use 'connect' to connect to other peers")
        
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
                        print("Type 'help' for available commands")
                except EOFError:
                    break
        except KeyboardInterrupt:
            print("\nExiting...")
        finally:
            self.node.stop()
    
    def cmd_help(self, args):
        """Show help"""
        print("\nAvailable commands:")
        for cmd, (_, desc) in self.commands.items():
            print(f"  {cmd:<10} - {desc}")
    
    def cmd_search(self, args):
        """Search for files"""
        if not args:
            print("Usage: search <query>")
            return
        
        query = ' '.join(args)
        print(f"Searching for '{query}'...")
        self.search_results = self.node.search_files(query)
        
        if not self.search_results:
            print("No results found")
            return
        
        print("\nSearch results:")
        for i, result in enumerate(self.search_results):
            peer_str = "Local" if result['peer'] == 'local' else f"{result['peer'][0]}:{result['peer'][1]}"
            size_str = result['size']
            print(f"  [{i}] {result['filename']} ({size_str}) - {peer_str}")
    
    def cmd_list(self, args):
        """List local files"""
        files = self.node.get_files()
        
        if not files:
            print("No local files")
            return
        
        print("\nLocal files:")
        for filename in files:
            size_str = self.node.files[filename]['size']
            print(f"  {filename} ({size_str})")
    
    def cmd_peers(self, args):
        """List peers"""
        peers = self.node.get_peers()
        
        if not peers:
            print("No peers connected")
            return
        
        print("\nConnected peers:")
        for i, peer in enumerate(peers):
            print(f"  [{i}] {peer[0]}:{peer[1]}")
    
    def cmd_connect(self, args):
        """Connect to a peer"""
        if len(args) != 2:
            print("Usage: connect <ip> <port>")
            return
        
        ip, port = args
        try:
            port = int(port)
            if self.node.add_peer(ip, port):
                print(f"Connected to peer: {ip}:{port}")
            else:
                print(f"Already connected to peer: {ip}:{port}")
        except ValueError:
            print("Port must be a number")
    
    def cmd_disconnect(self, args):
        """Disconnect from a peer"""
        if len(args) != 2:
            print("Usage: disconnect <ip> <port>")
            return
        
        ip, port = args
        try:
            port = int(port)
            if self.node.remove_peer(ip, port):
                print(f"Disconnected from peer: {ip}:{port}")
            else:
                print(f"Not connected to peer: {ip}:{port}")
        except ValueError:
            print("Port must be a number")
    
    def cmd_download(self, args):
        """Download a file"""
        if not args:
            print("Usage: download <result_index>")
            return
        
        try:
            index = int(args[0])
            
            if index < 0 or index >= len(self.search_results):
                print(f"Invalid result index: {index}")
                return
            
            result = self.search_results[index]
            
            if result['peer'] == 'local':
                print(f"File '{result['filename']}' is already local")
                return
            
            print(f"Downloading '{result['filename']}' from {result['peer'][0]}:{result['peer'][1]}...")
            
            # Start download in a separate thread
            threading.Thread(
                target=self._download_thread,
                args=(result['peer'], result['filename']),
                daemon=True
            ).start()
            
        except ValueError:
            print("Invalid index. Please provide a number.")
    
    def _download_thread(self, peer, filename):
        """Thread function for downloading"""
        success = self.node.download_file(peer, filename)
        
        if success:
            print(f"\nDownload completed successfully: {filename}")
        else:
            print(f"\nDownload failed: {filename}")
    
    def cmd_quit(self, args):
        """Exit the application"""
        raise KeyboardInterrupt()