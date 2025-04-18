#!/usr/bin/env python3
"""
Utility function for P2P file sharing application
"""
import socket

def find_free_port():
    """Find available port"""
    # https://docs.python.org/3/library/socket.html sockname
    # https://docs.python.org/3/howto/sockets.html INET
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))  # random port
        return s.getsockname()[1]