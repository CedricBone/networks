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
python src/main.py
```

```
tracker 8000
```

You should see a confirmation that the tracker is running.

### 2. Share a File (Terminal 2)

```bash
echo "This is a test file for sharing" > test_file.txt
python src/main.py
```

```
share test_file.txt localhost:8000
```
- Create a torrent file (`test_file.txt.torrent`)
- Register the file with the tracker
- Make the file available for other peers to download

### 3. Download the File (Terminal 3)

```bash
python src/main.py
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

## Comparison to Standard BitTorrent

This project implements a custom peer-to-peer file sharing protocol inspired by BitTorrent but **does not strictly follow the official BitTorrent specification**. It utilizes similar concepts like a tracker, peers, and `.torrent` metainfo files, but deviates in several key ways:

*   **Encoding:** Uses standard **JSON** for all network communication (tracker and peer messages) and for the `.torrent` file format, instead of BitTorrent's **Bencoding**.
*   **Protocols:** 
    *   Uses a custom **TCP-based protocol with JSON messages** for both tracker and peer communication.
    *   Standard BitTorrent uses HTTP GET requests (with Bencoded responses) for tracker communication and a specific binary peer wire protocol (with messages like `choke`, `have`, `request`, `piece`).
*   **File Transfer:** This is the most significant simplification. This project uses **direct whole-file transfers** between peers. A client requests the entire file, and the serving peer sends the entire file content back. 
    *   Standard BitTorrent breaks files into **pieces**, which are requested, transferred, and verified individually using SHA1 hashes. This allows downloading from multiple peers simultaneously and ensures piece integrity during transfer.
*   **Metainfo (`.torrent`) File:** While structurally similar (using `announce` and `info` keys), the format is JSON, uses different hashing (SHA256 likely), and lacks the standard `pieces` (concatenated SHA1 hashes) field used for piece-by-piece verification during download.
*   **Peer Messages & Logic:** Lacks standard BitTorrent peer messages (`choke`, `unchoke`, `interested`, `not interested`, `have`, `bitfield`, `request`, `piece`, `cancel`) and associated logic like choking algorithms (tit-for-tat, optimistic unchoking).

In essence, this project provides a functional P2P file sharing system using a simplified, custom approach, rather than being a BitTorrent-compatible client.
