# Reliable Data Transfer Protocol

## Files

- **network_simulator.py**: Simulates network conditions including packet loss, corruption, and delay
- **sender.py**: Implements sliding window protocol with timeout-based retransmission
- **receiver.py**: Handles packet buffering, integrity verification, and sends acknowledgments
- **packet.py**: Defines the structure and checksumming for data packets

## How to Run

### 1. Start the Network Simulator

```bash
python network_simulator.py
```

### 2. Receive Mode

```bash
python main.py receive output_file.txt
```

### 3. Send Mode

```bash
python main.py send input_file.txt
```
