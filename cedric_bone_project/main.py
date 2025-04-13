#!/usr/bin/env python3
"""
Main entry point for P2P file sharing application
"""
import argparse
from node import P2PNode
from cli import CommandLine

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Basic P2P File Sharing Application")
    parser.add_argument("--dir", default="./shared", help="Directory to share files from")
    
    args = parser.parse_args()
    
    node = P2PNode(args.dir)
    cli = CommandLine(node)
    cli.start()

if __name__ == "__main__":
    main()