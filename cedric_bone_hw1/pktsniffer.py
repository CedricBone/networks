import argparse
import os
import scapy.all as scapy

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
def read_file(args):
    if os.path.exists(args.r) and (args.r.endswith('.pcap') ):
        packets = scapy.rdpcap(args.r)
        return packets
    else:
        print("File not found")
        return -1
    
# Function to filter packets
def packet_filter(packets, args):
    filtered_packets = []
    
    for packet in packets:
        #print(packet.summary())
        # checks if filtered packets is equal to the number of packets requested
        if args.c and len(filtered_packets) == args.c:
            break

        # filters by host
        if args.host:
            if args.host in packet.summary():
                filtered_packets.append(packet)
        
        # filters by port
        if args.port:
            if packet.haslayer(scapy.TCP) and args.port == packet[scapy.TCP].dport:
                filtered_packets.append(packet)
            elif packet.haslayer(scapy.UDP) and args.port == packet[scapy.UDP].dport:
                filtered_packets.append(packet)
        
        # filters by IP
        if args.ip:
            if args.ip in packet.summary():
                filtered_packets.append(packet)

        # if no arguments are passed, just add the packet
        if (not args.host) and (not args.port) and (not args.ip) and (not args.tcp) and (not args.udp) and (not args.icmp) and (not args.net):
            filtered_packets.append(packet)
    
    return filtered_packets
    
def main():
    args = arguments()
    packets = read_file(args)
    if packets == -1:
        return
    else:
        filtered_packets = packet_filter(packets, args)

    for packet in filtered_packets:
        print(packet.show())
        print("\n\n")



if __name__ == "__main__":
    main()
