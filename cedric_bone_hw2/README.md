# Ping and Traceroute Implementation

## my_ping.py

```bash
sudo python3 my_ping.py [-c COUNT] [-i WAIT] [-s PACKETSIZE] [-t TIMEOUT] DESTINATION
```

Options:
- `-c COUNT`: Stop after sending COUNT packets
- `-i WAIT`: Wait WAIT seconds between packets (default: 1)
- `-s PACKETSIZE`: Specify data bytes to send (default: 56)
- `-t TIMEOUT`: Specify timeout in seconds (default: 2)

Example:
```bash
sudo python3 my_ping.py -c 5 google.com
```

## my_traceroute.py

```bash
sudo python3 my_traceroute.py [-n] [-q NQUERIES] [-S] [-f FIRST_TTL] [-m MAX_TTL] [-w WAIT] DESTINATION
```

Options:
- `-n`: Print addresses numerically only
- `-q NQUERIES`: Set probes per TTL (default: 3)
- `-S`: Print summary of unanswered probes

Example:
```bash
sudo python3 my_traceroute.py -n -q 2 google.com
```

## References
- https://linux.die.net/man/8/ping
- https://www.geeksforgeeks.org/ping-in-c/

## Notes

- Must run with root privileges