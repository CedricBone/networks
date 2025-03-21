import socket
import time
from packet import Packet

class Sender:
    def __init__(self, port=12347, window_size=4):
        self.seq_num = 0
        self.window_size = window_size
        self.window = {}  # Map of seq_num to packets
        self.base = 0  # Oldest unacked packet
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(('localhost', port))
        self.socket.settimeout(1.0)  # 1 second timeout
        
    def send_packet(self, packet, addr):
        self.socket.sendto(str(packet.__dict__).encode(), addr)
        print(f"Sent packet {packet.seq_num}")
        
    def send_file(self, data, receiver_addr=('localhost', 12345)):
        # Split data into chunks and convert to bits
        chunk_size = 4  # 4 bytes = 32 bits per packet for low rate
        chunks = [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]
        
        while self.base < len(chunks):
            # Send up to window_size packets
            while self.seq_num < min(self.base + self.window_size, len(chunks)):
                packet = Packet(seq_num=self.seq_num, data=chunks[self.seq_num])
                self.window[self.seq_num] = packet
                self.send_packet(packet, receiver_addr)
                self.seq_num += 1
                time.sleep(0.1)  
            
            # Wait for ACKs
            try:
                data, _ = self.socket.recvfrom(4096)
                ack_packet = Packet(**eval(data.decode()))
                print(f"Received ACK {ack_packet.ack_num}")
                
                if (ack_packet.checksum == ack_packet.calculate_checksum()):
                    # Move window forward
                    self.base = ack_packet.ack_num + 1
                    # Remove acknowledged packets
                    self.window = {seq: pkt for seq, pkt in self.window.items() 
                                if seq >= self.base}
            except socket.timeout:
                # Timeout: resend all packets in window
                print("Timeout - resending window")
                for seq_num in range(self.base, self.seq_num):
                    if seq_num in self.window:
                        self.send_packet(self.window[seq_num], receiver_addr)
        
        # Send END marker
        end_packet = Packet(seq_num=self.seq_num, data="END")
        self.send_packet(end_packet, receiver_addr)
