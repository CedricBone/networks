import argparse
import os
import scapy.all as scapy
import json

# Function to parse command line arguments
# https://docs.python.org/3/library/argparse.html
def arguments():
    parser = argparse.ArgumentParser(description="Network Packet Sniffer")
    parser.add_argument("-r", required=True, help="Path to pcap file")
    parser.add_argument("-c", type=int, help="Limit number of packets analyzed")
    parser.add_argument("-host", help="Filter by host")
    parser.add_argument("-port", type=int, help="Filter by port")
    parser.add_argument("-ip", help="Filter by IP")
    parser.add_argument("-tcp", action="store_true", help="Filter TCP")
    parser.add_argument("-udp", action="store_true", help="Filter UDP")
    parser.add_argument("-icmp", action="store_true", help="Filter ICMP")
    parser.add_argument("-net", help="Filter by network")

    return parser.parse_args()


# Function to read pcap file
# https://scapy.readthedocs.io/en/latest/usage.html#reading-pcap-files
def read_file(args):
    if os.path.exists(args.r) and (args.r.endswith('.pcap') ):
        temp = []
        packets = scapy.rdpcap(args.r)
        for packet in packets:
            #print(packet.summary())
            temp.append(json.loads(packet.json()))
        packets = temp
        return packets
    else:
        print("File not found")
        return -1
    
# Function to filter packets
# https://0xbharath.github.io/art-of-packet-crafting-with-scapy/networking/packet_headers/index.html
def packet_filter(packets, args):
    filtered_packets = []

    for packet in packets:
        print(packet)
        # checks if filtered packets is equal to the number of packets requested
        if args.c and len(filtered_packets) == args.c:
            break

        # filters by host
        if args.host:
            if (args.host == packet['payload']['src']):
                filtered_packets.append(packet)
        
        # filters by port
        if args.port:
            if (args.port == packet['payload']['payload']['sport']) or (args.port == packet['payload']['payload']['dport']):
                filtered_packets.append(packet)
        
        # filters by IP
        if args.ip:
            if (args.ip == packet['payload']['src']) or (args.ip == packet['payload']['dst']):
                filtered_packets.append(packet)
        
        # filters by TCP
        if args.tcp:
            if packet['payload']['proto'] == 6:
                filtered_packets.append(packet)
        
        # filters by UDP
        if args.udp:
            if packet['payload']['proto'] == 17:
                filtered_packets.append(packet)

        # filters by ICMP
        if args.icmp:
            if packet['payload']['proto'] == 1:
                filtered_packets.append(packet)
        
        # filters by network
        if args.net:
            if (args.net in packet['payload']['src']) or (args.net in packet['payload']['dst']):
                filtered_packets.append(packet)

        # if no arguments are passed, just add the packet
        if (not args.host) and (not args.port) and (not args.ip) and (not args.tcp) and (not args.udp) and (not args.icmp) and (not args.net):
            filtered_packets.append(packet)
    
    return filtered_packets


def print_packet(packet):
    # Ethernet Header: Packet size, Destination MAC address, Source MAC address, Ethertype.
    print("Ethernet Header:")
    print(f"Packet size: {packet['payload']['len']}")
    print(f"Destination MAC address: {packet['dst']}")
    print(f"Source MAC address: {packet['src']}")
    print(f"Ethertype: {packet['type']}")
    print(f"{'-' * 50}\n")

    #IP Header: Version, Header length, Type of service, Total length, Identification, Flags, Fragment offset, Time to live, Protocol, Header checksum, Source and Destination IP addresses.
    print("IP Header:")
    print(f"Version: {packet['payload']['version']}")
    print(f"Header length: {packet['payload']['ihl']}")
    print(f"Type of service: {packet['payload']['tos']}")
    print(f"Total length: {packet['payload']['len']}")
    print(f"Identification: {packet['payload']['id']}")
    print(f"Flags: {packet['payload']['flags']}")
    print(f"Fragment offset: {packet['payload']['frag']}")
    print(f"Time to live: {packet['payload']['ttl']}")
    print(f"Protocol: {packet['payload']['proto']}")
    print(f"Header checksum: {packet['payload']['chksum']}")
    print(f"Source IP address: {packet['payload']['src']}")
    print(f"Destination IP address: {packet['payload']['dst']}")
    print(f"{'-' * 50}\n")

    #Encapsulated Packets: TCP, UDP, or ICMP headers
    print("Encapsulated Packets:")
    print(f"Source Port: {packet['payload']['payload']['sport']}")
    print(f"Destination Port: {packet['payload']['payload']['dport']}")

    print(f"\n{'#' * 50}\n")
    
def main():
    args = arguments()
    packets = read_file(args)
    if packets == -1:
        return
    else:
        filtered_packets = packet_filter(packets, args)

    for packet in filtered_packets:
        print_packet(packet)
        #print(packet)


if __name__ == "__main__":
    main()
