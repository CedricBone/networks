# Metainfo handling for P2P file sharing
import hashlib
import json
import os


def create_metainfo(filepath, tracker_url, piece_length=262144):
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    
    file_size = os.path.getsize(filepath)
    
    # Calculate number of pieces
    num_pieces = (file_size + piece_length - 1) // piece_length
    
    # Calculate SHA1 hash for each piece
    pieces = []
    with open(filepath, 'rb') as f:
        for _ in range(num_pieces):
            piece_data = f.read(piece_length)
            piece_hash = hashlib.sha1(piece_data).hexdigest()
            pieces.append(piece_hash)
    
    # Create info dictionary
    info = {
        'name': os.path.basename(filepath),
        'piece length': piece_length,
        'pieces': pieces,
        'length': file_size
    }
    
    # Calculate info_hash
    info_str = json.dumps(info, sort_keys=True).encode()
    info_hash = hashlib.sha1(info_str).hexdigest()
    
    # Create metainfo dictionary
    metainfo = {
        'info': info,
        'announce': tracker_url,
        'info_hash': info_hash
    }
    
    return metainfo


def save_metainfo(metainfo, output_path):
    with open(output_path, 'w') as f:
        json.dump(metainfo, f, indent=2)


def load_metainfo(filepath):
    with open(filepath, 'r') as f:
        return json.load(f)
