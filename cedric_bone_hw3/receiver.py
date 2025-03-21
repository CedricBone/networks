import socket
from packet import Packet

class Receiver:
    def __init__(self, port=12348, window_size=4):
        self.expected_seq = 0
        self.window_size = window_size
        self.buffer = {}  # Buffer for out-of-order packets
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(('localhost', port))
        self.received_data = []
        
    def send_ack(self, ack_num, addr):
        ack_packet = Packet(seq_num=None, data="", ack_num=ack_num)
        self.socket.sendto(str(ack_packet.__dict__).encode(), addr)
        print(f"Sent ACK {ack_num}")
        
    def receive_file(self):
        print("Waiting for data...")
        while True:
            data, addr = self.socket.recvfrom(4096)
            packet_dict = eval(data.decode())
            packet = Packet(**packet_dict)
            
            print(f"Received packet {packet.seq_num}")
            
            # Check packet integrity using checksum
            if not (packet.checksum == packet.calculate_checksum()):
                print(f"Packet {packet.seq_num} corrupted")
                self.send_ack(self.expected_seq - 1, addr)
                continue
                
            # Check if this is the end marker
            if packet.data == "END":
                self.send_ack(packet.seq_num, addr)
                break
            
            # Check if packet is in order
            if packet.seq_num == self.expected_seq:
                self.received_data.append(packet.data)
                self.expected_seq += 1
                
                # Process any buffered packets
                while self.expected_seq in self.buffer:
                    self.received_data.append(self.buffer.pop(self.expected_seq))
                    self.expected_seq += 1
                    
            elif packet.seq_num > self.expected_seq:
                # Future packet, buffer it
                self.buffer[packet.seq_num] = packet.data
            
            # Send ACK for highest in-order packet received
            self.send_ack(self.expected_seq - 1, addr)
                
        return ''.join(self.received_data)