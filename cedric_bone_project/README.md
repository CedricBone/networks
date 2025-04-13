# P2P File Sharing Application

## Project Structure

```
./
├── src/           # Core implementation
│   ├── peer.py    # Peer functionality
│   ├── tracker.py # Tracker for discovery
│   ├── client.py  # Client interface
│   └── metainfo.py# Torrent file handling
├── tests/         # Test suite
├── main.py        # Entry point
└── requirements.txt
```

## Commands

```
tracker [port]         - Start tracker server
create <file> <url>    - Create torrent file
share <file> <url>     - Share file
download <torrent>     - Download file
search <query>         - Search for files
peers                  - List connected peers
files                  - List shared files
connect <host> <port>  - Connect to peer
```

## Testing

```bash
python -m unittest discover tests
```

## Testing the Application

Follow these steps to manually test the P2P file sharing functionality:

### 1. Start a Tracker (Terminal 1)

```bash
python main.py
```

```
tracker 8000
```

You should see a confirmation that the tracker is running.

### 2. Share a File (Terminal 2)

```bash
echo "This is a test file for sharing" > test_file.txt
python main.py
```

```
share test_file.txt localhost:8000
```
- Create a torrent file (`test_file.txt.torrent`)
- Register the file with the tracker
- Make the file available for other peers to download

### 3. Download the File (Terminal 3)

```bash
python main.py
```

```
download test_file.txt.torrent
```

The content should be identical, confirming successful P2P file transfer.

### Troubleshooting

- Make sure the tracker is running before sharing or downloading
- Check that the file paths are correct
- Check that the port is not already used
- Restart the clients 
