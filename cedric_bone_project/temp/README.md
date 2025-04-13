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

## Usage

This application operates using a command-line interface. You can run multiple instances on your machine (using different ports if necessary) to simulate a P2P network.

**1. Start the Tracker:**

   The tracker coordinates peer discovery. Start it in one terminal:

   ```bash
   python src/main.py --tracker --host localhost --port 8000 
   ```
   *   `--tracker`: Specifies running in tracker mode.
   *   `--host`: (Optional) Host address for the tracker (default: `localhost`).
   *   `--port`: (Optional) Port for the tracker (default: `8000`).

   Keep this terminal running.

**2. Start a Peer Client (Sharer):**

   Open a *new* terminal and start a client instance. This client will share a file.

   ```bash
   python src/main.py 
   ```
   *   This starts the client in interactive mode, listening on a random available port.

   Now, use the `share` command within this client's prompt:

   ```
   Enter command: share test_file.txt localhost:8000
   ```
   *   Replace `path/to/your/file.txt` with the actual path to the file you want to share.
   *   Replace `localhost:8000` with the tracker's address and port if you started it differently.
   *   This command will:
      *   Create a `.torrent` file (e.g., `file.txt.torrent`) in the *same directory* where you ran `src/main.py`.
      *   Add the file to the peer's list of shared files.
      *   Register the file (`info_hash`) with the tracker.

   Keep this client running to seed the file.

**3. Start another Peer Client (Downloader):**

   Open *another* new terminal and start a second client instance:

   ```bash
   python src/main.py
   ```

   Now, use the `download` command within this client's prompt, pointing to the `.torrent` file created in Step 2:

   ```
   Enter command: download test_file.txt.torrent
   ```
   *   Make sure `test_file.txt.torrent` is accessible from this client's current directory (or provide the full path).
   *   This command will:
      *   Read the `.torrent` file.
      *   Contact the tracker (`localhost:8000`) to find peers sharing this file.
      *   Connect to the sharing peer (from Step 2).
      *   Request the file piece by piece.
      *   Verify each piece's hash (SHA1) if available.
      *   Assemble the pieces into the final file in the current directory.
      *   Verify the complete file's hash (SHA256) against the hash in the `.torrent`.

**Other Commands:**

*   `create <file> <tracker_url>`: Only creates the `.torrent` file without automatically sharing or registering with the tracker.
*   `search <query>`: Attempts to search for filenames containing `<query>` on connected peers (Note: current search implementation might be basic).
*   `peers`: Lists the addresses of peers this client is currently aware of or connected to.
*   `files`: Lists the files currently being shared by this client instance.
*   `connect <host> <port>`: Manually attempts to establish a connection with another peer.
*   `help`: Displays the list of available commands.
*   `exit`: Stops the client and closes connections.

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
