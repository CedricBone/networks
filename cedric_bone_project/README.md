# P2P File Sharing App


## Usage

1. Start P2P node and share files from the dir:
   ```
   python main.py --dir ./shared
   ```

2. In another terminal, start another one:
   ```
   python main.py --dir ./shared2
   ```

3. Connect the nodes to each other:
   - First terminal: `connect 127.0.0.1 XXXXX` ( XXXXX = port of the second node)
   - Second terminal: `connect 127.0.0.1 XXXXX` ( XXXXX = port of the first node)

4. Use commands:

   - `search query`: Search for files across all connected peers
   - `list`: List local files
   - `peers`: Show connected peers
   - `connect ip port`: Connect to a peer
   - `download index`: Download a file from search results

## Testing

1.  Shared Directories:
    ```
    mkdir shared1 shared2
    ```
2.  Sample File:
    ```
    cp docs/Frankenstein.txt shared1
    ```

3.  Peer 1:
    ```
    python main.py --dir ./shared1
    ```
    (Note port number)

4.  Peer 2:
    ```
    python main.py --dir ./shared2
    ```
    (Note port number)

5.  Connect Peers:
    - First terminal: `connect 127.0.0.1 XXXXX` ( XXXXX = port of the second node)
    - Second terminal: `connect 127.0.0.1 XXXXX` ( XXXXX = port of the first node)

6.  Search for the File:
    - Second terminal: `search Frankenstein.txt`
    Note the index number (0 if it is the first)

7.  Download the File:
    - Second terminal: `download 0`


## Project Structure

- **node.py**: P2P node. Peer connections and file transfer
- **cli.py**: CLI
- **utils.py**: Utility function
- **main.py**: Main


## References
- https://docs.python.org/3/library/socket.html
- https://stackoverflow.com/questions/11865685/handling-a-timeout-error-in-python-sockets
- https://docs.python.org/3/howto/sockets.html
- https://docs.python.org/3/library/json.html
- https://docs.python.org/3/library/hashlib.html
- https://docs.python.org/3/library/threading.html
- https://docs.python.org/3/library/os.html
- https://docs.python.org/3/library/time.html
- https://docs.python.org/3/library/argparse.html
- https://docs.python.org/3/library/functions.html#input
- https://docs.python.org/3/library/cmd.html