import socket
import random
import time
from packet import Packet

class NetworkSimulator:
    def __init__(self, sender_port=12347, receiver_port=12348, loss_rate=0.3, corruption_rate=0.3):
        self.loss_rate = loss_rate
        self.corruption_rate = corruption_rate
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(('localhost', 12345))
        print(f"Network simulator started")
        
    def run(self):
        print("Waiting for packets...")
        while True:
            data, addr = self.socket.recvfrom(4096)
            
            # packet loss
            if random.random() < self.loss_rate:
                print(f"Dropping packet from port {addr[1]}")
                continue
                
            packet_dict = eval(data.decode())
            packet = Packet(**packet_dict)
            print(f"Forwarding packet {packet.seq_num} from port {addr[1]}")
            
            # corruption by changing a random char
            if random.random() < self.corruption_rate:
                print(f"Corrupting packet {packet.seq_num}")
                if packet.data:
                    pos = random.randint(0, len(packet.data)-1)
                    rand_char = chr(random.randint(0, 127))
                    chars = list(packet.data)
                    chars[pos] = rand_char
                    packet.data = ''.join(chars)
                    packet.checksum = packet.calculate_checksum()
                
            # Forward
            dest_port = 12348 if addr[1] == 12347 else 12347
            self.socket.sendto(str(packet.__dict__).encode(), ('localhost', dest_port))
                
        self.socket.close()

if __name__ == "__main__":
    simulator = NetworkSimulator()
    simulator.run()
