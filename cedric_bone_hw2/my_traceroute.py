import argparse
import os
import select
import socket
import struct
import sys
import time
import random

# Send a single traceroute probe and wait for response
def send_probe(send_socket, recv_socket, dest_ip, ttl, port, timeout):

    # Set the TTL on the UDP socket
    send_socket.setsockopt(socket.SOL_IP, socket.IP_TTL, ttl)
    
    # Mark the send time
    send_time = time.time()
    
    # Send a UDP packet to an unlikely port at the destination
    try:
        send_socket.sendto(b'', (dest_ip, port))
    except socket.error:
        return None, None
        
    # Wait for response
    while True:
        # Check if socket is ready for reading
        ready = select.select([recv_socket], [], [], timeout)
        
        if not ready[0]:  # Timeout
            return None, None
            
        # Calculate response time
        recv_time = time.time()
        elapsed_ms = (recv_time - send_time) * 1000  # Convert to milliseconds
        
        # Receive the packet
        try:
            packet, addr = recv_socket.recvfrom(1024)
        except socket.error:
            continue
            
        # Parse the ICMP header from the packet
        icmp_type, icmp_code = struct.unpack_from('!BB', packet, 20)
        
        # Check if this is an ICMP Time Exceeded or Destination Unreachable
        if icmp_type == 11:  # Time Exceeded
            # Extract the original packet headers (inside the ICMP error message)
            udp_header = packet[48:56]
            
            # Extract destination port from UDP header
            udp_dst_port = struct.unpack_from('!H', udp_header, 2)[0]
            
            # Check if this response matches our probe
            if udp_dst_port == port:
                return addr[0], elapsed_ms
                
        elif icmp_type == 3:  # Destination Unreachable
            # Extract the original packet headers
            udp_header = packet[48:56]
            
            # Extract destination port from UDP header
            udp_dst_port = struct.unpack_from('!H', udp_header, 2)[0]
            
            # Check if this response matches our probe and it's from the destination
            if udp_dst_port == port and addr[0] == dest_ip:
                return addr[0], elapsed_ms

def main():
    """
    Main function to parse arguments and run the traceroute utility.
    """
    parser = argparse.ArgumentParser(description="A Python implementation of the traceroute command")
    parser.add_argument("destination", help="Destination hostname or IP address")
    parser.add_argument("-n", action="store_true", help="Print hop addresses numerically")
    parser.add_argument("-q", "--nqueries", type=int, default=3, help="Set the number of probes per TTL to NQUERIES (default: 3)")
    parser.add_argument("-S", action="store_true", help="Print a summary of unanswered probes for each hop")
    parser.add_argument("-f", "--first-ttl", type=int, default=1, help="Start from the first_ttl hop (default: 1)")
    parser.add_argument("-m", "--max-ttl", type=int, default=30, help="Set the max number of hops (default: 30)")
    parser.add_argument("-w", "--wait", type=float, default=2.0, help="Wait WAIT seconds for response (default: 2.0)")
    args = parser.parse_args()
    
    # Ensure root privileges for raw socket
    if os.geteuid() != 0:
        print("Error: This program requires root privileges to create raw sockets.")
        sys.exit(1)
        
    # Resolve destination hostname to IP address
    try:
        dest_ip = socket.gethostbyname(args.destination)
    except socket.gaierror:
        print(f"Error: Could not resolve hostname '{args.destination}'")
        sys.exit(1)

    # Create raw socket for receiving ICMP messages
    try:
        recv_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
    except socket.error:
        print("Error: Could not create raw socket.")
        sys.exit(1)
        
    # Create UDP socket for sending probes
    try:
        send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    except socket.error:
        print("Error: Could not create UDP socket.")
        sys.exit(1)
    
    # Track unanswered probes for summary
    unanswered = {}
    
    # Base port number for UDP probes
    port_base = 33434
    
    print(f"traceroute to {args.destination} ({dest_ip}), {args.max_ttl} hops max")
    
    destination_reached = False
    
    # Iterate through TTL values
    for ttl in range(args.first_ttl, args.max_ttl + 1):
        # Print the hop number
        sys.stdout.write(f"{ttl:2d} ")
        sys.stdout.flush()
        
        # Track responses for this hop
        responses = []
        unanswered[ttl] = 0
        
        # Send multiple queries for this TTL
        for query in range(args.nqueries):
            # Calculate port for this probe
            port = port_base + (ttl * args.nqueries) + query
            
            # Send probe and get response
            resp_ip, resp_time = send_probe(send_socket, recv_socket, dest_ip, ttl, port, args.wait)
            
            # Format the output
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
                
        # End of line for this TTL
        print("")
        
        # If we've reached the destination with any query, we're done
        if destination_reached:
            break
    
    # Print summary if requested
    if args.S:
        print("\nProbe Response Summary:")
        for ttl, count in sorted(unanswered.items()):
            if count > 0:
                percent = (count / args.nqueries) * 100
                print(f"  TTL {ttl:2d}: {count}/{args.nqueries} unanswered ({percent:.1f}%)")


if __name__ == "__main__":
    main()