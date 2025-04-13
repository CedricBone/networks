# P2P File Sharing Application

A lightweight BitTorrent-inspired peer-to-peer file-sharing application that allows users to share and download files directly through a decentralized network.

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

## Features

- Peer Discovery via tracker
- File Indexing and searching
- Direct file transfer
- File integrity verification (SHA-256)
- Multi-threaded connections
- Decentralized architecture

## Setup

```bash
pip install -r requirements.txt
python main.py
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

When prompted, enter:
```
tracker 8000
```

You should see a confirmation that the tracker is running.

### 2. Share a File (Terminal 2)

```bash
# Create a test file if needed
echo "This is a test file for sharing" > test_file.txt

# Start a client
python main.py
```

When prompted, enter:
```
share test_file.txt localhost:8000
```

This will:
- Create a torrent file (`test_file.txt.torrent`)
- Register the file with the tracker
- Make the file available for other peers to download

### 3. Download the File (Terminal 3)

```bash
# Start another client
python main.py
```

When prompted, enter:
```
download test_file.txt.torrent
```

If successful, you'll see a confirmation message and the file will be downloaded as `downloaded_test_file.txt`.

### 4. Verify the Results

```bash
# Compare the original and downloaded files
cat test_file.txt
cat downloaded_test_file.txt
```

The content should be identical, confirming successful P2P file transfer.

### Troubleshooting

If you encounter issues:
- Make sure the tracker is running before sharing or downloading
- Verify that the file paths are correct
- Check that port 8000 is not already in use (try a different port if needed)
- Restart the clients if connections fail
