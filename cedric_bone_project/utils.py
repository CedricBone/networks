#!/usr/bin/env python3
"""
Utility functions for P2P file sharing application
"""
import socket

def find_free_port():
    """Find an available port on the system"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))  # Bind to a random port
        return s.getsockname()[1]

def format_size(size_bytes):
    """Format file size in human-readable form"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024 or unit == 'TB':
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024