"""
my_traceroute.py

Python implementation of traceroute command that maps network path to destination.
Sends UDP probes with incrementing TTL values to discover intermediate routers.

Usage:
    sudo python my_traceroute.py [-n] [-q NQUERIES] [-S] destination
"""
#https://www.sphinx-doc.org/en/master/tutorial/describing-code.html

import argparse
import os
import select
import socket
import struct
import sys
import time
import random

def send_probe(send_socket, recv_socket, dest_ip, ttl, port, timeout):
    """
    Send a probe and wait for response
    
    Parameters:
        send_socket: Socket for probes
        recv_socket: Socket for responses
        dest_ip: Destination IP
        ttl: Time-to-live
        port: destination port
        timeout: Maximum wait time for response
        
    Returns:
        tuple: (responding_ip, elapsed_time_ms)
    """
    send_socket.setsockopt(socket.SOL_IP, socket.IP_TTL, ttl)
    send_time = time.time()

    try:
        send_socket.sendto(b'', (dest_ip, port))
    except socket.error:
        return None, None
        
    # Wait for response
    while True:
        ready = select.select([recv_socket], [], [], timeout)
        if not ready[0]:  # Timeout
            return None, None
            
        recv_time = time.time()
        elapsed = (recv_time - send_time) 
        elapsed = elapsed * 1000  # to ms

        # Received
        try:
            packet, addr = recv_socket.recvfrom(1024)
            #print("here1")
        except socket.error:
            continue
            
        # ICMP header
        icmp_type, icmp_code = struct.unpack_from('!BB', packet, 20)
        if icmp_type == 11:  # Time Exceeded
            udp_header = packet[48:56]
            udp_dst_port = struct.unpack_from('!H', udp_header, 2)[0]
            if udp_dst_port == port:
                return addr[0], elapsed
                
        elif icmp_type == 3:  # Unreachable
            udp_header = packet[48:56]
            udp_dst_port = struct.unpack_from('!H', udp_header, 2)[0]
            if udp_dst_port == port and addr[0] == dest_ip:
                return addr[0], elapsed

def main():
    """
    Parse arguments and execute traceroute
    Shows network path with response times for each hop
    """
    parser = argparse.ArgumentParser(description="A Python implementation of the traceroute command")
    parser.add_argument("destination", help="Destination hostname or IP address")
    parser.add_argument("-n", action="store_true", help="Print hop addresses numerically")
    parser.add_argument("-q", "--nqueries", type=int, default=3, help="Set the number of probes per TTL to NQUERIES (default: 3)")
    parser.add_argument("-S", action="store_true", help="Print a summary of unanswered probes for each hop")
    args = parser.parse_args()
    
    # root privileges (needed for for raw socket)
    if os.geteuid() != 0:
        print("Error: This program requires root privileges to create raw sockets.")
        sys.exit(1)
        
    try:
        dest_ip = socket.gethostbyname(args.destination)
    except socket.gaierror:
        print(f"Error: Could not resolve hostname '{args.destination}'")
        sys.exit(1)

    try:
        recv_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
    except socket.error:
        print("Error: Could not create raw socket.")
        sys.exit(1)
        
    try:
        send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    except socket.error:
        print("Error: Could not create UDP socket.")
        sys.exit(1)
    
    unanswered = {}
    port_base = 33434
    max_ttl = 30
    timeout = 2.0
    
    print(f"traceroute to {args.destination} ({dest_ip}), {max_ttl} hops max")
    destination_reached = False
    
    for ttl in range(1, max_ttl + 1):
        sys.stdout.write(f"{ttl:2d} ")
        sys.stdout.flush()

        responses = []
        unanswered[ttl] = 0
        
        for query in range(args.nqueries):
            port = port_base + (ttl * args.nqueries) + query
            resp_ip, resp_time = send_probe(send_socket, recv_socket, dest_ip, ttl, port, timeout)
            
            if resp_ip is None:
                # Timeout
                sys.stdout.write(" *")
                unanswered[ttl] += 1
            else:
                # Got a response
                responses.append(resp_ip)
                
                # Try to resolve hostname if not in numeric mode
                if not args.n and resp_ip != dest_ip:
                    try:
                        host = socket.gethostbyaddr(resp_ip)[0]
                    except socket.herror:
                        host = resp_ip
                else:
                    host = resp_ip
                    
                # Print response info
                if query == 0:
                    # First query for this TTL, print the hostname/IP
                    if not args.n and resp_ip != dest_ip and host != resp_ip:
                        sys.stdout.write(f" {host} ({resp_ip})")
                    else:
                        sys.stdout.write(f" {resp_ip}")
                        
                # Print the response time
                if resp_time is not None:
                    sys.stdout.write(f"  {resp_time:.3f} ms")
            
            sys.stdout.flush()
            
            # Check if we've reached the destination
            if resp_ip == dest_ip:
                destination_reached = True
                
        #print("here")
        print("")
        
        # destination
        if destination_reached:
            break
    
    # Print summary if requested
    if args.S:
        print("\nProbe Response Summary:")
        for ttl, count in sorted(unanswered.items()):
            if count > 0:
                percent = (count / args.nqueries) * 100
                print(f"  TTL {ttl}: {count}/{args.nqueries} unanswered ({percent}%)")


if __name__ == "__main__":
    main()