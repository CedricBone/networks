"""
Packet

Implements a packet with sequence number, data, and checksum.
"""
import random
import math
import time

# https://abdesol.medium.com/udp-protocol-with-a-header-implementation-in-python-b3d8dae9a74b
class Packet:
    """
    A packet with sequence number, data, and checksum.

    Attributes:
        seq_num (int): Sequence number
        data (str): Data
        ack_num (int): Ack number
        checksum (int): Checksum
    """
    def __init__(self, seq_num, data, ack_num=None, checksum=None):
        self.seq_num = seq_num
        self.data = data
        self.ack_num = ack_num
        if checksum is None:
            self.checksum = self.calculate_checksum()
        else:
            self.checksum = checksum
    
    # UDP 16-bit checksum
    # https://www.geeksforgeeks.org/how-checksum-computed-in-udp/
    def calculate_checksum(self):
        """
        Calculate checksum (UDP style)
        """

        # Convert data to bytes
        seq_bytes = str(self.seq_num).encode()
        data_bytes = self.data.encode()
        all_bytes = seq_bytes + data_bytes
        
        # if odd len, pad
        if len(all_bytes) % 2 == 1:
            all_bytes += b'\x00'
            
        # sum 16-bit words
        total = 0
        for i in range(0, len(all_bytes), 2):
            # two bytes -> 16-bit word
            word = (all_bytes[i] << 8) + all_bytes[i+1]
            total += word
            
            # overflow
            if total > 0xFFFF:
                total = (total & 0xFFFF) + 1
        
        # One's complement
        checksum = ~total & 0xFFFF
        return checksum