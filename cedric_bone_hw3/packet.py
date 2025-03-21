import random
import math
import time

# https://abdesol.medium.com/udp-protocol-with-a-header-implementation-in-python-b3d8dae9a74b
class Packet:
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
        # data -> bytes
        seq_bytes = str(self.seq_num).encode()
        data_bytes = self.data.encode()
        all_bytes = seq_bytes + data_bytes
        
        # If odd len pad 
        if len(all_bytes) % 2 == 1:
            all_bytes += b'\x00'
            
        # Sum
        words = [all_bytes[i:i+2] for i in range(0, len(all_bytes), 2)]
        total = 0
        for word in words:
            total += int.from_bytes(word, 'big')
        
        # carry bits
        while total >> 16:
            total = (total & 0xFFFF) + (total >> 16)
            
        # One's complement
        return (~total) & 0xFFFF