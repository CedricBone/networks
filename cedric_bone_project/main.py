#!/usr/bin/env python3
"""
Main for P2P file sharing app
"""
import argparse
import node as N
import cli as C

def main():
    # https://docs.python.org/3/library/argparse.html
    parser = argparse.ArgumentParser(description="P2P")
    parser.add_argument("--dir", default="./shared", help="Dir to share from")
    
    args = parser.parse_args()
    
    node = N.P2PNode(args.dir)
    cli = C.CommandLine(node)
    cli.start()

if __name__ == "__main__":
    main()