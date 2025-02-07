# pktsniffer

A Python-based packet sniffer that reads `.pcap` files, parses Ethernet/IP/TCP/UDP/ICMP headers, and provides various filtering options.

---

## Features

- **Reads a `.pcap` file** using Scapy.
- **Displays headers** (Ethernet, IP, and encapsulated TCP/UDP/ICMP).
- **Filters:** `-host`, `-port`, `-ip`, `-tcp`, `-udp`, `-icmp`, and `-net`.
- **Limit the number of packets**  with `-c`.

---
## Usage

```bash
python pktsniffer.py -r <path_to_pcap> [optional_filters]
```

### Arguments

| Argument         | Description                                               | Example                                  |
|------------------|-----------------------------------------------------------|------------------------------------------|
| `-r`             | **Required**. Path to the `.pcap` file.                  | `-r mycapture.pcap`                      |
| `-c`             | Limit the number of packets to process (integer).        | `-c 5`                                   |
| `-host`          | Filter by host IP address.                               | `-host 192.168.0.10`                     |
| `-port`          | Filter by TCP/UDP port (integer).                        | `-port 80`                               |
| `-ip`            | Filter by IP address (same as `-host`, but included for clarity). | `-ip 10.0.0.5`                 |
| `-tcp`           | Filter only TCP packets.                                 | `-tcp`                                   |
| `-udp`           | Filter only UDP packets.                                 | `-udp`                                   |
| `-icmp`          | Filter only ICMP packets.                                | `-icmp`                                  |
| `-net`           | Filter by network address (substring match).            | `-net 192.168.1`                         |

---

## Example Commands

1. **no filtering**:
   ```
   python pktsniffer.py -r capture.pcap
   ```
2. **Limit to 5 packets**:
   ```
   python pktsniffer.py -r capture.pcap -c 5
   ```
3. **Filter by TCP**:
   ```
   python pktsniffer.py -r capture.pcap -tcp
   ```
