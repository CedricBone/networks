"""
pktsniffer.py

packet sniffer that:
1. Reads packets from a .pcap file using Scapy
2. Filters by host, IP, port, network, or protocol
3. Prints packet details

Usage:
    python pktsniffer.py -r file.pcap [filters...]
"""
#https://www.sphinx-doc.org/en/master/tutorial/describing-code.html

import argparse
import os
import scapy.all as scapy
import json

# Function to parse command line arguments
# https://docs.python.org/3/library/argparse.html
def arguments():
    """
    Parse command line arguments.

    :return: Parsed arguments from command line
    :rtype: argparse.Namespace
    """
    parser = argparse.ArgumentParser(description="Packet Sniffer")
    parser.add_argument("-r", required=True, help="Path to pcap")
    parser.add_argument("-c", type=int, help="Limit number of packets")
    parser.add_argument("-host", help="Filter by host")
    parser.add_argument("-port", type=int, help="Filter by TCP/UDP port")
    parser.add_argument("-ip", help="Filter by IP (same as host, but kept for clarity)")
    parser.add_argument("-tcp", action="store_true", help="Filter TCP packets")
    parser.add_argument("-udp", action="store_true", help="Filter UDP packets")
    parser.add_argument("-icmp", action="store_true", help="Filter ICMP packets")
    parser.add_argument("-net", help="Filter by network address")

    return parser.parse_args()

# Function to read pcap file
# https://scapy.readthedocs.io/en/latest/usage.html#reading-pcap-files
def read_file(args):
    """
    Read packets from the .pcap file and convert each into a JSON dict.

    :param args: arguments from command line
    :type args: argparse.Namespace
    :return: List of packet JSON dicts
    :rtype: list
    """
    if os.path.exists(args.r) and args.r.endswith('.pcap'):
        scapy_packets = scapy.rdpcap(args.r)
        packet_list = []
        for packet in scapy_packets:
            packet_list.append(json.loads(packet.json()))
        return packet_list
    else:
        print("Not a valid .pcap file.")
        return []

# Function to filter packets
# https://0xbharath.github.io/art-of-packet-crafting-with-scapy/networking/packet_headers/index.html
# https://en.wikipedia.org/wiki/List_of_IP_protocol_numbers
def packet_filter(packets, args):
    """
    Filter packets based on arguments

    :param packets: List of packet dictionaries
    :type packets: list
    :param args: arguments specifying filters
    :type args: argparse
    :return: List of filtered packets
    :rtype: list
    """
    filtered_packets = []
    count = 0

    for packet in packets:
        # checks filtered packets len
        if args.c is not None and count >= args.c:
            break

        # info
        ip_data = packet["payload"]
        ip_src = ip_data.get("src", "")
        ip_dst = ip_data.get("dst", "")
        proto = ip_data.get("proto", None)
        sport = None
        dport = None
        if "payload" in ip_data and isinstance(ip_data["payload"], dict):
            sport = ip_data["payload"].get("sport")
            dport = ip_data["payload"].get("dport")

        match_any = False
        no_filters_used = True

        # Filter by host
        if args.host:
            no_filters_used = False
            if ip_src == args.host:
                match_any = True

        # Filter by port
        if args.port:
            no_filters_used = False
            if sport == args.port or dport == args.port:
                match_any = True

        # Filter by IP
        if args.ip:
            no_filters_used = False
            if ip_src == args.ip or ip_dst == args.ip:
                match_any = True

        # Filter by TCP
        if args.tcp:
            no_filters_used = False
            if proto == 6:
                match_any = True

        # Filter by UDP
        if args.udp:
            no_filters_used = False
            if proto == 17:
                match_any = True

        # Filter by ICMP
        if args.icmp:
            no_filters_used = False
            if proto == 1:
                match_any = True

        # Filter by network
        if args.net:
            no_filters_used = False
            if (args.net in ip_src) or (args.net in ip_dst):
                match_any = True

        # no filters or match any
        if no_filters_used or match_any:
            filtered_packets.append(packet)
            count += 1

    return filtered_packets

def print_packet(packet):
    """
    Print the details of a single packet:
      1. Ethernet layer 
      2. IP layer
      3. Encapsulated protocols

    :param packet: dictionary parsed packet
    :type packet: dict
    """
    next_layer = ip_header.get("payload", {})
    sport = next_layer.get("sport", "N/A")
    dport = next_layer.get("dport", "N/A")

    # Ethernet Header: Packet size, Destination MAC address, Source MAC address, Ethertype.
    print("Ethernet Header:")
    print(f"Packet size: {packet.get('payload', {}).get('len', 'N/A')}")
    print(f"Destination MAC address: {packet.get('dst', 'N/A')}")
    print(f"Source MAC address: {packet.get('src', 'N/A')}")
    print(f"Ethertype: {packet.get('type', 'N/A')}")
    print("-" * 50)

    #IP Header: Version, Header length, Type of service, Total length, Identification, Flags, Fragment offset, Time to live, Protocol, Header checksum, Source and Destination IP addresses.
    ip_header = packet.get("payload", {})
    print("IP Header:")
    print(f"Version: {ip_header.get('version', 'N/A')}")
    print(f"Header length: {ip_header.get('ihl', 'N/A')}")
    print(f"Type of service: {ip_header.get('tos', 'N/A')}")
    print(f"Total length: {ip_header.get('len', 'N/A')}")
    print(f"Identification: {ip_header.get('id', 'N/A')}")
    print(f"Flags: {ip_header.get('flags', 'N/A')}")
    print(f"Fragment offset: {ip_header.get('frag', 'N/A')}")
    print(f"Time to live: {ip_header.get('ttl', 'N/A')}")
    print(f"Protocol: {ip_header.get('proto', 'N/A')}")
    print(f"Header checksum: {ip_header.get('chksum', 'N/A')}")
    print(f"Source IP address: {ip_header.get('src', 'N/A')}")
    print(f"Destination IP address: {ip_header.get('dst', 'N/A')}")
    print("-" * 50)

    #Encapsulated Packets: TCP, UDP, or ICMP headers
    print("Encapsulated Packets:")
    print(f"Source Port: {sport}")
    print(f"Destination Port: {dport}")
    print("#" * 50, "\n")

def main():
    """
    Main for pktsniffer.py
    1. Parse arguments
    2. Read pcap file
    3. Filter packets
    4. Print results
    """
    args = arguments()
    packets = read_file(args)
    if packets == []:
        return

    filtered_packets = packet_filter(packets, args)

    for packet in filtered_packets:
        print_packet(packet)

if __name__ == "__main__":
    main()
