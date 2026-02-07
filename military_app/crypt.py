import string
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad
import base64

def vigenereEncryption(plain_text, key):
    """Encrypt a message using Vigenere cipher"""
    encrypted_text = ""
    key_length = len(key)
    key_as_int = [ord(i) for i in key]
    plain_text_int = [ord(i) for i in plain_text]
    
    for i in range(len(plain_text_int)):
        if plain_text[i].isalpha():
            value = (plain_text_int[i] + key_as_int[i % key_length]) % 26
            encrypted_text += chr(value + 65)
        else:
            encrypted_text += plain_text[i]
    return encrypted_text

def vigenereDecryption(encrypted_text, key):
    """Decrypt a message using Vigenere cipher"""
    decrypted_text = ""
    key_length = len(key)
    key_as_int = [ord(i) for i in key]
    encrypted_text_int = [ord(i) for i in encrypted_text]
    
    for i in range(len(encrypted_text_int)):
        if encrypted_text[i].isalpha():
            value = (encrypted_text_int[i] - key_as_int[i % key_length]) % 26
            decrypted_text += chr(value + 65)
        else:
            decrypted_text += encrypted_text[i]
    return decrypted_text

# Polybius Square
#   1 2 3 4 5
# 1 A B C D E
# 2 F G H I K
# 3 L M N O P
# 4 Q R S T U
# 5 V W X Y Z
# J is treated as I

POLYBIUS_SQUARE = {
    'A': '11', 'B': '12', 'C': '13', 'D': '14', 'E': '15',
    'F': '21', 'G': '22', 'H': '23', 'I': '24', 'J': '24', 'K': '25',
    'L': '31', 'M': '32', 'N': '33', 'O': '34', 'P': '35',
    'Q': '41', 'R': '42', 'S': '43', 'T': '44', 'U': '45',
    'V': '51', 'W': '52', 'X': '53', 'Y': '54', 'Z': '55'
}

REVERSE_POLYBIUS = {v: k for k, v in POLYBIUS_SQUARE.items() if k != 'J'}

def polybiusEncryption(plain_text):
    """Encrypt a message using Polybius cipher"""
    encrypted_text = ""
    for char in plain_text:
        if char.upper() in POLYBIUS_SQUARE:
            encrypted_text += POLYBIUS_SQUARE[char.upper()]
        else:
            encrypted_text += char
    return encrypted_text

def polybiusDecryption(encrypted_text):
    """Decrypt a message using Polybius cipher"""
    decrypted_text = ""
    i = 0
    while i < len(encrypted_text):
        # Check if we have a pair of digits
        if i + 1 < len(encrypted_text) and encrypted_text[i].isdigit() and encrypted_text[i+1].isdigit():
            pair = encrypted_text[i:i+2]
            if pair in REVERSE_POLYBIUS:
                decrypted_text += REVERSE_POLYBIUS[pair]
                i += 2
            else:
                # Handle cases where digits might not be valid pairs or just single digits
                decrypted_text += encrypted_text[i]
                i += 1
        else:
            decrypted_text += encrypted_text[i]
            i += 1
    return decrypted_text

def aes_encrypt(plain_text, key):
    """Encrypt a message using AES-256 CBC"""
    # Ensure key is 32 bytes for AES-256
    if len(key) < 32:
        key = key.ljust(32, '0')
    else:
        key = key[:32]
    
    key_bytes = key.encode('utf-8')
    cipher = AES.new(key_bytes, AES.MODE_CBC)
    
    # Pad the plaintext to be a multiple of 16 bytes
    padded_text = pad(plain_text.encode('utf-8'), AES.block_size)
    
    # Encrypt
    cipher_text = cipher.encrypt(padded_text)
    
    # Prepend IV (initialization vector) to the ciphertext
    iv_and_cipher = cipher.iv + cipher_text
    
    # Encode to base64 for safe storage
    return base64.b64encode(iv_and_cipher).decode('utf-8')

def aes_decrypt(cipher_text, key):
    """Decrypt a message using AES-256 CBC"""
    # Ensure key is 32 bytes for AES-256
    if len(key) < 32:
        key = key.ljust(32, '0')
    else:
        key = key[:32]
    
    key_bytes = key.encode('utf-8')
    
    # Decode from base64
    iv_and_cipher = base64.b64decode(cipher_text)
    
    # Extract IV (first 16 bytes) and ciphertext
    iv = iv_and_cipher[:16]
    cipher_bytes = iv_and_cipher[16:]
    
    # Decrypt
    cipher = AES.new(key_bytes, AES.MODE_CBC, iv)
    padded_text = cipher.decrypt(cipher_bytes)
    
    # Unpad the plaintext
    plain_text = unpad(padded_text, AES.block_size)
    
    return plain_text.decode('utf-8')

def generate_aes_key(length=32):
    """Generate a random AES key"""
    import random
    import string
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def hybrid_encrypt(message, vigenere_key):
    """
    Triple-layer hybrid encryption
    Layer 1: Vigenere cipher
    Layer 2: Polybius cipher
    Layer 3: AES-256 encryption
    Returns: (encrypted_message, aes_key)
    """
    # Layer 1: Vigenere
    vigenere_encrypted = vigenereEncryption(message, vigenere_key)
    
    # Layer 2: Polybius
    polybius_encrypted = polybiusEncryption(vigenere_encrypted)
    
    # Layer 3: AES-256
    aes_key = generate_aes_key()
    aes_encrypted = aes_encrypt(polybius_encrypted, aes_key)
    
    return aes_encrypted, aes_key

def hybrid_decrypt(encrypted_message, vigenere_key, aes_key):
    """
    Triple-layer hybrid decryption (reverse order)
    Layer 1: AES-256 decryption
    Layer 2: Polybius decryption
    Layer 3: Vigenere decryption
    """
    # Layer 1: AES decryption
    aes_decrypted = aes_decrypt(encrypted_message, aes_key)
    
    # Layer 2: Polybius decryption
    polybius_decrypted = polybiusDecryption(aes_decrypted)
    
    # Layer 3: Vigenere decryption
    vigenere_decrypted = vigenereDecryption(polybius_decrypted, vigenere_key)
    
    return vigenere_decrypted
