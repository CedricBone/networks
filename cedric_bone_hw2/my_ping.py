"""
my_ping.py

Python implementation of ping command.
Sends ICMP echo requests and measures round-trip time.

Usage:
    python my_ping.py [-c COUNT] [-i WAIT] [-s PACKETSIZE] [-t TIMEOUT] destination
"""
#https://www.sphinx-doc.org/en/master/tutorial/describing-code.html


import argparse
import os
import sys
import time
import signal
import statistics
from scapy.all import IP, ICMP, sr1, conf 

def send_ping(dest_ip, timeout, packet_size, sent_count, received_count):
    """
    Send a ping and wait for response
    
    Parameters:
        dest_ip: Destination IP address
        timeout: Maximum wait time for response
        packet_size: Size
        sent_count: Number of packets sent
        received_count: Number of responses received
        
    Returns:
        tuple: (success_bool, rtt_ms)
    """
    # Payload of specified size
    payload = "A" * packet_size
    send_time = time.time()
    sent_count += 1
    response = sr1(IP(dst=dest_ip)/ICMP(type=8, code=0)/payload, timeout=timeout, verbose=0)
    
    # Return time
    recv_time = time.time()
    rtt = (recv_time - send_time) * 1000  # Convert to milliseconds
    
    if response:
        received_count += 1
        print(f"{len(response)} bytes from {dest_ip}: icmp_seq={sent_count} ttl={response.ttl} time={rtt:.3f} ms")
        return True, rtt
    else:
        print(f"Request timeout for icmp_seq {sent_count}")
        return False, None

def print_stats(sent_count, received_count, rtts, destination):
    """
    Print ping summary
    
    Parameters:
        sent_count: Total number sent
        received_count: Total number received
        rtts: List of round-trip times
        destination: Target hostname or IP
    """
    if sent_count == 0:
        return
    
    loss_percent = 100.0 - (received_count / sent_count * 100.0)
    
    print(f"\n--- {destination} ping statistics ---")
    print(f"{sent_count} packets transmitted, {received_count} received, {loss_percent}% packet loss")
    
    if received_count > 0:
        min_time = min(rtts)
        max_time = max(rtts)
        avg_time = statistics.mean(rtts)
        print(f"round-trip min/avg/max = {min_time}/{avg_time}/{max_time} ms")

def handle_interrupt(signum, frame, sent_count, received_count, rtts, destination):
    """
    Handle Ctrl+C
    
    Parameters:
        signum: Signal number
        frame: Current frame
        sent_count: Total packets sent
        received_count: Total responses received
        rtts: List of round-trip times
        destination: Target IP
    """
    print_stats(sent_count, received_count, rtts, destination)
    sys.exit(0)

# Function to parse command line arguments and run ping
# https://docs.python.org/3/library/argparse.html
def main():
    """
    Parse command line arguments and do ping.
    ICMP echo requests and displays results.
    """
    parser = argparse.ArgumentParser(description="A Python implementation of the ping command")
    parser.add_argument("destination", help="Destination hostname or IP address")
    parser.add_argument("-c", "--count", type=int, help="Stop after sending COUNT packets")
    parser.add_argument("-i", "--wait", type=float, default=1.0, help="Wait WAIT seconds between sending each packet (default: 1)")
    parser.add_argument("-s", "--packetsize", type=int, default=56, help="Send PACKETSIZE data bytes in each packet (default: 56)")
    parser.add_argument("-t", "--timeout", type=float, default=2.0, help="Specify a timeout in seconds for packet response (default: 2)")
    args = parser.parse_args()
    
    sent_count = 0
    received_count = 0
    rtts = []
    destination = ""
    seq = 0
    
    destination = args.destination
    
    # handler for Ctrl+C
    signal.signal(signal.SIGINT, handle_interrupt)

    # not check for IP spoofing (source IP address)
    conf.checkIPsrc = False

    print(f"PING {args.destination} ({args.destination}) {args.packetsize} data bytes")
    start_time = time.time()
    
    # ping loop
    while args.count is None or seq < args.count:
        # Send ping and record rtt
        success, rtt = send_ping(args.destination, args.timeout, args.packetsize, sent_count, received_count)
        if success and rtt is not None:
            rtts.append(rtt)
        
        seq += 1

        if args.count is None or seq < args.count:
            elapsed = time.time() - start_time
            sleep_time = max(0, (seq * args.wait) - elapsed)
            if sleep_time > 0:
                time.sleep(sleep_time)
    
    print_stats(sent_count, received_count, rtts, destination)

if __name__ == "__main__":
    main()