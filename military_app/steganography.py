from PIL import Image
import io

def text_to_binary(text):
    """Convert text to binary string"""
    return ''.join(format(ord(char), '08b') for char in text)

def binary_to_text(binary):
    """Convert binary string to text"""
    text = ''
    for i in range(0, len(binary), 8):
        byte = binary[i:i+8]
        if len(byte) == 8:
            text += chr(int(byte, 2))
    return text

def hide_message_in_image(image_file, message):
    """
    Hide a message inside an image using LSB (Least Significant Bit) steganography
    Returns: Modified image as bytes
    """
    # Open image
    img = Image.open(image_file)
    
    # Convert to RGB if necessary
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    # Add delimiter to know where message ends
    message = message + '###END###'
    binary_message = text_to_binary(message)
    
    # Get image data
    pixels = list(img.getdata())
    width, height = img.size
    
    # Check if image is large enough
    if len(binary_message) > len(pixels) * 3:
        raise ValueError("Image too small to hide this message")
    
    # Modify pixels
    new_pixels = []
    data_index = 0
    
    for pixel in pixels:
        if data_index < len(binary_message):
            # Modify R, G, B channels
            r, g, b = pixel
            
            # Modify R
            if data_index < len(binary_message):
                r = (r & 0xFE) | int(binary_message[data_index])
                data_index += 1
            
            # Modify G
            if data_index < len(binary_message):
                g = (g & 0xFE) | int(binary_message[data_index])
                data_index += 1
            
            # Modify B
            if data_index < len(binary_message):
                b = (b & 0xFE) | int(binary_message[data_index])
                data_index += 1
            
            new_pixels.append((r, g, b))
        else:
            new_pixels.append(pixel)
    
    # Create new image
    stego_img = Image.new(img.mode, img.size)
    stego_img.putdata(new_pixels)
    
    # Save to bytes
    img_bytes = io.BytesIO()
    stego_img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    return img_bytes.getvalue()

def extract_message_from_image(image_file):
    """
    Extract a hidden message from an image using LSB steganography
    Returns: Extracted message
    """
    # Open image
    img = Image.open(image_file)
    
    # Convert to RGB if necessary
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    # Get image data
    pixels = list(img.getdata())
    
    # Extract binary data
    binary_message = ''
    
    for pixel in pixels:
        r, g, b = pixel
        binary_message += str(r & 1)
        binary_message += str(g & 1)
        binary_message += str(b & 1)
    
    # Convert to text
    message = binary_to_text(binary_message)
    
    # Find delimiter
    delimiter = '###END###'
    end_index = message.find(delimiter)
    
    if end_index != -1:
        return message[:end_index]
    else:
        return "No hidden message found or message corrupted"
