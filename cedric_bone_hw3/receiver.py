import socket
from packet import Packet

class Receiver:
    def __init__(self, port=22222, window_size=4):
        self.expected_seq = 0
        self.window_size = window_size
        # Buffer for out-of-order packets
        self.buffer = {}  
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
            
            # dict = {"seq_num": seq_num, "data": data, "ack_num": ack_num, "checksum": checksum}
            packet_dict = eval(data.decode())
            packet = Packet(
                seq_num=packet_dict.get('seq_num'),
                data=packet_dict.get('data'),
                ack_num=packet_dict.get('ack_num'),
                checksum=packet_dict.get('checksum')
            )
            
            print(f"Received packet {packet.seq_num}")
            
            # packet integrity 
            if not (packet.checksum == packet.calculate_checksum()):
                print(f"Packet {packet.seq_num} corrupted")
                self.send_ack(self.expected_seq - 1, addr)
                continue
                
            # Check if end
            if packet.data == "END":
                self.send_ack(packet.seq_num, addr)
                print("Received END packet")
                break
            
            # Check order
            if packet.seq_num == self.expected_seq:
                self.received_data.append(packet.data)
                self.expected_seq += 1
                
                # Process buffered packets
                while self.expected_seq in self.buffer:
                    self.received_data.append(self.buffer.pop(self.expected_seq))
                    self.expected_seq += 1
                    
            elif packet.seq_num > self.expected_seq:
                self.buffer[packet.seq_num] = packet.data
            
            # Send ACK 
            self.send_ack(self.expected_seq - 1, addr)
                
        return ''.join(self.received_data)