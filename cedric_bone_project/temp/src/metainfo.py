# Metainfo handling for P2P file sharing
import hashlib
import json
import os
import time

def create_metainfo(filepath, tracker_url, piece_length=262144):
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    
    # Get file info
    file_size = os.path.getsize(filepath)
    filename = os.path.basename(filepath)
    
    # Calculate number of pieces
    num_pieces = (file_size + piece_length - 1) // piece_length  # Ceiling division
    
    # Calculate hash for each piece
    pieces = b''  # Concatenated binary piece hashes for legacy compatibility
    piece_hashes = []  # List of string hashes for easier access
    
    # Calculate hash for the whole file
    file_hash_obj = hashlib.sha256()
    
    with open(filepath, 'rb') as f:
        for i in range(num_pieces):
            f.seek(i * piece_length)  # Make sure we're at the right position
            piece_size = min(piece_length, file_size - (i * piece_length)) # Handle last piece
            piece_data = f.read(piece_size)
            if not piece_data:
                break
            
            # Update file hash
            file_hash_obj.update(piece_data)
            
            # Calculate piece hash (SHA1) - store as string for consistency
            piece_hash_binary = hashlib.sha1(piece_data).digest()
            piece_hash_hex = hashlib.sha1(piece_data).hexdigest()
            
            # Store binary concatenated hashes for backward compatibility
            pieces += piece_hash_binary
            
            # Store hex string hashes for our verification
            piece_hashes.append(piece_hash_hex)
    
    # Generate info dictionary
    info = {
        'name': filename,
        'piece length': piece_length,
        'pieces_binary': pieces.hex(),  # Convert binary to hex string for JSON serialization
        'piece_hashes': piece_hashes,   # Already string format
        'length': file_size
    }
    
    # Calculate info hash - make a copy to avoid modifying the original
    info_hash_calc = info.copy()
    info_hash = hashlib.sha1(json.dumps(info_hash_calc, sort_keys=True).encode()).hexdigest()
    
    # Get SHA256 hash of entire file
    whole_file_hash = file_hash_obj.hexdigest()
    
    # Create metainfo dictionary
    metainfo = {
        'info': info,
        'announce': tracker_url,
        'info_hash': info_hash,
        'file_hash': whole_file_hash
    }
    
    return metainfo


def save_metainfo(metainfo, output_path):
    with open(output_path, 'w') as f:
        json.dump(metainfo, f, indent=2)


def load_metainfo(filepath):
    with open(filepath, 'r') as f:
        return json.load(f)
