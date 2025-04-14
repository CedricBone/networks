#!/usr/bin/env python3
"""
Utility functions for P2P file sharing application
"""
import socket

def find_free_port():
    """Find available port"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))  # random port
        return s.getsockname()[1]