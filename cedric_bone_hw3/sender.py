"""
Sender

Implements the sender side of the reliable data transfer protocol.
"""
import socket
import time
from packet import Packet

class Sender:
    """
    Implements a sliding window retransmission.

    Attributes:
        seq_num (int): Current sequence number
        window_size (int): Size of the sliding window
        window (dict): Buffer
        base (int): Sequence number of the oldest unacknowledged packet
    """
    def __init__(self, port=11111, window_size=4):
        self.seq_num = 0
        self.window_size = window_size
        self.window = {} 

        # Oldest unacked packet
        self.base = 0  
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(('localhost', port))
        self.socket.settimeout(1.0) 
        
    def send_packet(self, packet, addr):
        """
        Send a packet to address

        Args:
            packet (Packet): Packet to send
            addr (tuple): Destination address (host, port)
        """
        self.socket.sendto(str(packet.__dict__).encode(), addr)
        print(f"Sent packet {packet.seq_num}")
        
    def send_file(self, data, receiver_addr=('localhost', 33333)):
        """
        Send a file to address

        Args:
            data (str): Data to send
            receiver_addr (tuple): Destination address (host, port)
        """
        # 4 bytes = 32 bits per packet
        size = 4 
        chunks = []
        for i in range(0, len(data), size):
            chunks.append(data[i:i + size])
        
        while self.base < len(chunks):
            # Send window_size packets
            while self.seq_num < min(self.base + self.window_size, len(chunks)):
                packet = Packet(seq_num=self.seq_num, data=chunks[self.seq_num])
                self.window[self.seq_num] = packet
                self.send_packet(packet, receiver_addr)
                self.seq_num += 1
                time.sleep(0.1)  
            
            # ACKs
            try:
                recv_num = 4096
                data, addr = self.socket.recvfrom(recv_num)
                
                # dict = {"seq_num": seq_num, "data": data, "ack_num": ack_num, "checksum": checksum}
                packet_dict = eval(data.decode())
                ack_packet = Packet(
                    seq_num=packet_dict.get('seq_num'),
                    data=packet_dict.get('data'),
                    ack_num=packet_dict.get('ack_num'),
                    checksum=packet_dict.get('checksum')
                )

                print(f"Received ACK {ack_packet.ack_num}")
                
                if (ack_packet.checksum == ack_packet.calculate_checksum()):
                    # Move window forward
                    self.base = ack_packet.ack_num + 1
                    # Remove acknowledged packets
                    self.window = {seq: pkt for seq, pkt in self.window.items() 
                                if seq >= self.base}
            except socket.timeout:
                # resend all packets in window
                print("Timeout - resending window")
                for seq_num in range(self.base, self.seq_num):
                    if seq_num in self.window:
                        self.send_packet(self.window[seq_num], receiver_addr)
        
        # Send END
        end_packet = Packet(seq_num=self.seq_num, data="END")
        print("Sending END packet")
        received_ack = False
        self.send_packet(end_packet, receiver_addr)

        while not received_ack:
            try:
                recv_num = 4096
                data, addr = self.socket.recvfrom(recv_num)
                
                # dict = {"seq_num": seq_num, "data": data, "ack_num": ack_num, "checksum": checksum}
                packet_dict = eval(data.decode())
                ack_packet = Packet(
                    seq_num=packet_dict.get('seq_num'),
                    data=packet_dict.get('data'),
                    ack_num=packet_dict.get('ack_num'),
                    checksum=packet_dict.get('checksum')
                )
                
                if (ack_packet.checksum == ack_packet.calculate_checksum()):
                    received_ack = True
            except socket.timeout:
                self.send_packet(end_packet, receiver_addr)

        print("File transfer completed")