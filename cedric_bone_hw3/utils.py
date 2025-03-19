import random
import math
import time

class Packet:
    def __init__(self, seq_num, data, time_sent=None, checksum=None, ack_num=None, resend_timer=3):
        self.seq_num = seq_num
        self.data = data 
        self.time_sent = time_sent
        self.checksum = checksum
        self.ack_num = ack_num 
        self.resend_timer = resend_timer
    
    def calculate_checksum(self):
        return sum([ord(x) for x in self.data]) % 256

    

class Sender:
    def __init__(self, window_size):
        self.window_size = window_size
        self.window = []
        self.seq_num = 0
    
    def prepare_packet(self, data):
        # Create packet
        packet = Packet(seq_num=self.seq_num, data=data, time_sent=time.time())
        self.seq_num += 1
        # Add packet to window
        self.window.append(packet)
        return packet
    
    def send_packet(self, packet):
        # Send packet to network
        pass

    def receive_ack(self, ack_num):
        # Remove packet from window
        pass

    def check_timeout(self):
        for packet in self.window:
            if (time.time() - packet.time_sent) > self.resend_timer:
                self.send_packet(packet)


class Receiver:
    def __init__(self, window_size):
        self.buffer = []
    
    def receive_packet(self, packet):
        # Check if packet is corrupted
        # If not, check if packet is in order
        # If in order, send ack
        # If not in order, buffer packet
        pass

class NetworkSimulator:
    def __init__(self, loss_rate, corruption_rate, delay):
        self.loss_rate = loss_rate
        self.corruption_rate = corruption_rate
        self.delay = delay


def main():

    #send packet
    sender = Sender(window_size=5)
    if len(sender.window) < sender.window_size:
        packet = sender.prepare_packet("Hello")
        sender.send_packet(packet)
    else:
        print("Window is full")

    #receive packet
    receiver = Receiver(window_size=5)

