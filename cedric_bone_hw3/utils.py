import random
import math


class Packet:
    def __init__(self, seq_num, data, checksum=None, ack_num=None):
        self.seq_num = seq_num
        self.data = data 
        self.checksum = checksum
        self.ack_num = ack_num 
    
    def calculate_checksum(self):
        return sum(self.data)

    

class Sender:
    def __init__(self, window_size):
        self.window_size = window_size
        self.window = []
        self.seq_num = 0
        self.ack_num = 0
    
    def send_packet(self, data):
        pass

class Receiver:
    def __init__(self, window_size):
        self.window_size = window_size
        self.window = []
        self.ack_num = 0
        self.seq_num = 0
    
    def receive_packet(self, packet):
        pass

class NetworkSimulator:
    def __init__(self, loss_rate, corruption_rate, delay):
        self.loss_rate = loss_rate
        self.corruption_rate = corruption_rate
        self.delay = delay

