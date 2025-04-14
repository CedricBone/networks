#!/usr/bin/env python3
"""
Main for P2P file sharing app
"""
import argparse
import node as N
import cli as C

def main():
    parser = argparse.ArgumentParser(description="Basic P2P File Sharing Application")
    parser.add_argument("--dir", default="./shared", help="Directory to share files from")
    
    args = parser.parse_args()
    
    node = N.P2PNode(args.dir)
    cli = C.CommandLine(node)
    cli.start()

if __name__ == "__main__":
    main()