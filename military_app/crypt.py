import string

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
