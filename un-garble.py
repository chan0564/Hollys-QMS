import os

def ungarble_byte(b):
    # If the byte char is <= 127, it's just ASCII
    if b < 128:
        return bytes([b])
    # If it's 128-255, it was likely double encoded
    # The UTF-8 sequence for character U+00XX is:
    # C2 XX for XX in 80-BF
    # C3 (XX-40) for XX in C0-FF
    # But wait, my file ALREADY HAS these UTF-8 sequences.
    return None

def fix_file():
    path = r'c:\Users\LG\Desktop\Hollys_QMS\app.py'
    
    with open(path, 'rb') as f:
        b = f.read()

    # The file is UTF-8. Let's decode it.
    try:
        content = b.decode('utf-8-sig')
    except UnicodeDecodeError:
        content = b.decode('utf-8', errors='replace')

    # We want to identify and fix "double-encoded" characters.
    # A double-encoded character is a character U+0080 to U+00FF that should have been a byte in a UTF-8 sequence.
    
    res_bytes = bytearray()
    i = 0
    while i < len(content):
        c = content[i]
        o = ord(c)
        if o < 128:
            res_bytes.append(o)
            i += 1
        elif 128 <= o <= 255:
            # This is a byte that was part of the original UTF-8 (or CP949)
            res_bytes.append(o)
            i += 1
        else:
            # This is a REAL character (like Korean) that was added later
            # We need to encode it back to UTF-8
            res_bytes.extend(c.encode('utf-8'))
            i += 1
    
    # Now res_bytes should be the "original" bytes
    # Try to decode them
    try:
        final_text = res_bytes.decode('utf-8')
        print("Successfully ungarbled as UTF-8")
    except UnicodeDecodeError:
        try:
            final_text = res_bytes.decode('cp949')
            print("Successfully ungarbled as CP949")
        except UnicodeDecodeError:
            print("Failed to ungarble. Trying with replacement...")
            final_text = res_bytes.decode('utf-8', errors='replace')

    with open(path, 'w', encoding='utf-8-sig') as f:
        f.write(final_text)
    print("Saved fixed file.")

if __name__ == "__main__":
    fix_file()
