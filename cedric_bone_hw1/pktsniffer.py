import argparse
import os
import pcapkit
import json

# Function to parse command line arguments
# https://docs.python.org/3/library/argparse.html
def arguments():
    parser = argparse.ArgumentParser(description="Network Packet Sniffer")
    parser.add_argument("-r", required=True, help="Path to pcap file")
    parser.add_argument("-c", type=int, help="Limit number of packets analyzed")
    parser.add_argument("-host", help="Filter packets by host IP address")
    parser.add_argument("-port", type=int, help="Filter packets by port number")
    parser.add_argument("-ip", help="Filter packets by IP address")
    parser.add_argument("-tcp", action="store_true", help="Filter TCP packets")
    parser.add_argument("-udp", action="store_true", help="Filter UDP packets")
    parser.add_argument("-icmp", action="store_true", help="Filter ICMP packets")
    parser.add_argument("-net", help="Filter packets by network (e.g., 192.168.1.0)")

    return parser.parse_args()


# Function to read pcap file
def read_file(args):
    if os.path.exists(args.r):
        #print(args.r)
        json = pcapkit.extract(fin=args.r, fout='out.json', format='json', extension=False)
        return json
    else:
        print("File not found")
        return -1
    
def main():
    args = arguments()
    packets = read_file(args)
    print(packets)



if __name__ == "__main__":
    main()
