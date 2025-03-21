import socket
import random
import time
from packet import Packet

class NetworkSimulator:
    def __init__(self, sender_port=11111, receiver_port=22222, loss_rate=0.3, corruption_rate=0.3):
        self.loss_rate = loss_rate
        self.corruption_rate = corruption_rate
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(('localhost', 33333))
        self.sender_port = sender_port
        self.receiver_port = receiver_port
        
        print(f"Network simulator started")
        
    def run(self):
        print("Waiting for packets...")

        while True:
            recv_num = 4096
            # addr = (IP address, port number) 
            # data = packet data
            data, addr = self.socket.recvfrom(recv_num)
            
            # packet loss
            if random.random() < self.loss_rate:
                print(f"Dropping packet from port {addr[1]}")
                continue
                
            # dict = {"seq_num": seq_num, "data": data, "ack_num": ack_num, "checksum": checksum}
            packet_dict = eval(data.decode())
            packet = Packet(
                seq_num=packet_dict.get('seq_num'),
                data=packet_dict.get('data'),
                ack_num=packet_dict.get('ack_num'),
                checksum=packet_dict.get('checksum')
            )

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

                
            # Forward
            if addr[1] == self.sender_port:
                dest_port = self.receiver_port
            else:
                dest_port = self.sender_port
            self.socket.sendto(str(packet.__dict__).encode(), ('localhost', dest_port))
   
if __name__ == "__main__":
    simulator = NetworkSimulator()
    simulator.run()
