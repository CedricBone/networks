import random
import math


class Packet:
    def __init__(self, seq_num, data, checksum=None, ack_num=None):
        self.seq_num = seq_num
        self.data = data 
        self.checksum = checksum
        self.ack_num = ack_num 

class sender:
    ...

class receiver:
    ...

class NetworkSimulator:
    ...

