import argparse
import os
from sender import Sender
from receiver import Receiver

def main():
    parser = argparse.ArgumentParser(description='transfer protocol')
    parser.add_argument('mode', choices=['send', 'receive'])
    parser.add_argument('file')
    args = parser.parse_args()
    
    # send mode
    if args.mode == 'send': 
        if not os.path.exists(args.file):
            print("File not found:", args.file)
            return
            
        with open(args.file, 'r') as f:
            data = f.read()
            
        sender = Sender()
        sender.send_file(data)
    
    # receive mode
    else:
        receiver = Receiver()
        data = receiver.receive_file()
        
        with open(args.file, 'w') as f:
            f.write(data)
        print(f"Data saved to {args.file}")

if __name__ == "__main__":
    main()