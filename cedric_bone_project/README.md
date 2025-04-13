# Simple P2P File Sharing Application

A simple peer-to-peer (P2P) file-sharing application that allows users to share files without relying on a central server. This application is designed to be as simple as possible while still meeting all the core requirements of a P2P system.

## Features

- **Manual Peer Discovery**: Manually connect to known peers by IP and port
- **File Indexing and Searching**: Search for files across all connected peers
- **Chunked File Transfer**: Files are split into 1MB chunks for efficient transfer
- **File Integrity Verification**: SHA-256 hashing ensures files are not corrupted
- **Multi-threaded Architecture**: Handle multiple connections simultaneously
- **Simple Command-line Interface**: Easy-to-use CLI for all operations

## Requirements

- Python 3.6 or higher
- No external libraries required - uses only Python standard library

## Installation

Simply clone or download the repository to your local machine.

## Usage

1. Start the application:
   ```
   python main.py --dir ./shared
   ```
   This will start the P2P node and share files from the specified directory. If the directory doesn't exist, it will be created.

2. Note the port number displayed after startup (e.g., "Node initialized on port: 58811")

3. In another terminal, start another instance:
   ```
   python main.py --dir ./shared2
   ```

4. Connect the nodes to each other (replace XXXXX with the appropriate port numbers):
   - In the first terminal: `connect 127.0.0.1 XXXXX` (where XXXXX is the port of the second node)
   - In the second terminal: `connect 127.0.0.1 XXXXX` (where XXXXX is the port of the first node)

5. Use the available commands:
   - `help`: Display available commands
   - `search <query>`: Search for files across all connected peers
   - `list`: List local files
   - `peers`: Show connected peers
   - `connect <ip> <port>`: Connect to a peer
   - `disconnect <ip> <port>`: Disconnect from a peer
   - `download <index>`: Download a file from search results
   - `quit`: Exit the application

## Testing the Application

You can test the basic functionality by running two instances (peers) of the application locally and transferring a file between them.

**Preparation:**

1.  **Create Shared Directories:** In your project folder (`p2p`), create two directories for the peers to share files from:
    ```bash
    mkdir shared1 shared2
    ```
2.  **Create a Sample File:** Create a test file in the first shared directory:
    ```bash
    echo "This is a test file for P2P sharing." > shared1/sample.txt
    ```

**Running the Test:**

1.  **Start Peer 1:** Open a terminal, navigate to the `p2p` directory, and run:
    ```bash
    python main.py --dir ./shared1
    ```
    Note the port number displayed (e.g., `Node initialized on port: 5XXXX`). Let's call this `PORT1`.

2.  **Start Peer 2:** Open a *second* terminal, navigate to the `p2p` directory, and run:
    ```bash
    python main.py --dir ./shared2
    ```
    Note the port number displayed. Let's call this `PORT2`.

3.  **Connect Peers:**
    *   In Peer 1's terminal, connect to Peer 2:
        ```
        > connect 127.0.0.1 PORT2 
        ```
        (Replace `PORT2` with the actual port number of Peer 2).
    *   In Peer 2's terminal, connect to Peer 1:
        ```
        > connect 127.0.0.1 PORT1
        ```
        (Replace `PORT1` with the actual port number of Peer 1).
    *   You can verify the connection in either terminal using the `peers` command.

4.  **Search for the File:** In Peer 2's terminal, search for the sample file:
    ```
    > search sample.txt
    ```
    You should see output similar to:
    ```
    Search results:
      [0] sample.txt (X bytes) - 127.0.0.1:PORT1 
    ```
    Note the index number (e.g., `[0]`).

5.  **Download the File:** In Peer 2's terminal, download the file using the index from the search results:
    ```
    > download 0 
    ```
    (Use the correct index if it's not 0). You will see download progress.

6.  **Verify Download:**
    *   After the download completes, check the `shared2` directory. The `sample.txt` file should now exist there.
    *   You can compare the contents of `shared1/sample.txt` and `shared2/sample.txt` to confirm they are identical. The application automatically performs an integrity check using SHA-256 hashes during the download.

This test confirms:
*   Peers can connect (Manual Discovery).
*   Files are indexed locally.
*   Peers can search for files on other connected peers (Indexing & Searching).
*   Files can be transferred between peers in chunks (Data Transfer, Chunking).
*   File integrity is verified after transfer (Integrity Verification).
*   Multiple instances run concurrently (Concurrency).
*   Interaction happens via the CLI (User Interface).

## Project Structure

The application is built with a modular architecture:

- **node.py**: Core P2P node functionality including file management, peer connections, and file transfer
- **cli.py**: Command-line interface for user interaction
- **utils.py**: Utility functions
- **main.py**: Application entry point

## How It Works

### Peer Discovery

Unlike traditional P2P applications that use automatic peer discovery, this application uses manual peer connections. Users need to explicitly connect to other peers using the `connect` command with the IP address and port of the remote peer.

### File Transfer Protocol

Files are transferred in chunks using a simple protocol:

1. Client requests file information (size, hash, number of chunks)
2. Client requests each chunk separately
3. After all chunks are downloaded, file integrity is verified using SHA-256 hash
4. If verification succeeds, the file is saved to the shared directory

### Network Protocol

The application uses a simple JSON-based protocol for communication:

- **File List Request**: `{"type": "list"}`
- **File Info Request**: `{"type": "info", "filename": "example.txt"}`
- **Chunk Request**: `{"type": "chunk", "filename": "example.txt", "chunk_index": 0}`

## Technical Requirements Met

1. **Peer Discovery**: Manual mechanism for peers to discover and connect to each other
2. **Indexing and Searching**: Maintains and searches lists of available files across peers
3. **Data Transfer**: Peers can request and download files from each other
4. **Concurrency**: Multi-threading handles multiple connections simultaneously
5. **Chunked File Transfer**: Files are transferred in 1MB chunks
6. **File Integrity**: SHA-256 hashing verifies downloaded files aren't corrupted
7. **User Interface**: Simple command-line interface for all operations

## Limitations and Future Improvements

- No automatic peer discovery (peers must be manually connected)
- No NAT traversal (works only on local networks or with port forwarding)
- No encryption or authentication (not secure for public networks)
- No resume of interrupted downloads

Future versions could implement:
- Automatic peer discovery using UPnP or DHT
- NAT traversal for internet-wide usage
- Data encryption and peer authentication
- Download resumption for interrupted transfers
- Graphical user interface (GUI)

## Comparison to BitTorrent Protocol

While this application achieves peer-to-peer file sharing, similar in *concept* to protocols like BitTorrent, its implementation differs significantly:

*   **Peer Discovery:** This app uses manual IP/port connection (`connect` command), whereas BitTorrent uses trackers or DHT for largely automatic peer discovery based on a `.torrent` file's `info_hash`.
*   **Metadata:** This app exchanges basic file info (size, hash) directly via JSON. BitTorrent relies on standardized, bencoded `.torrent` (metainfo) files containing tracker URLs, piece hashes (SHA-1), file structure, etc.
*   **Protocol:** This app uses a custom, simple JSON-based text protocol over TCP. BitTorrent uses a complex, standardized binary peer wire protocol with specific message types (handshake, choke, interested, piece, etc.) and bencoding for tracker communication.
*   **Piece/Chunk Strategy:** This app downloads chunks sequentially. BitTorrent typically employs more sophisticated piece selection strategies (e.g., rarest first) and choking algorithms (tit-for-tat) to optimize transfer speed and fairness across many peers.
*   **Hashing:** This app uses SHA-256 for whole-file integrity checks. BitTorrent uses SHA-1 hashes for individual *pieces* listed in the `.torrent` file.

In essence, this project implements a simplified P2P model focusing on the core requirements without adopting the specific complexities and standards of the full BitTorrent protocol.

## Meeting Project Requirements

This application successfully meets all the technical requirements outlined for the project:
1.  **Peer Discovery**: Implemented via the manual `connect` command.
2.  **Indexing and Searching**: Local files are indexed, and peers can be searched.
3.  **Data Transfer Mechanism**: Peers request and download files directly.
4.  **Concurrency and Threading**: Multi-threading handles the server, client requests, and downloads.
5.  **Chunked File Transfer**: Files are transferred in fixed-size chunks (1MB).
6.  **Verifying File Integrity**: SHA-256 hashing verifies downloaded file integrity.
7.  **User Interface**: A functional command-line interface is provided.