import os

def rescue_encoding():
    path = r'c:\Users\LG\Desktop\Hollys_QMS\app.py'
    backup = path + '.bak'
    
    # Read as bytes
    with open(path, 'rb') as f:
        b = f.read()
    
    # 1. Back up
    with open(backup, 'wb') as f:
        f.write(b)
    print(f"Backup created at {backup}")

    # 2. Decode as UTF-8 (this gives the garbled string containing U+008C etc.)
    try:
        content = b.decode('utf-8-sig')
    except UnicodeDecodeError:
        content = b.decode('utf-8', errors='replace')
    
    # 3. Check if it's double-encoded. 
    # If all characters are <= 255, it's highly likely it was read as Latin-1 and written as UTF-8.
    if all(ord(c) < 256 for c in content):
        print("Double encoding detected. Fixing...")
        # Encode as Latin-1 to get the original bytes
        # ISO-8859-1 maps U+0000-U+00FF to 0x00-0xFF 1-to-1.
        original_bytes = content.encode('iso-8859-1')
        
        # Now decode the original bytes as UTF-8
        try:
            proper_content = original_bytes.decode('utf-8')
            print("Successfully restored UTF-8 content.")
        except UnicodeDecodeError as e:
            print(f"Error decoding original bytes as UTF-8: {e}")
            # Try CP949 as a fallback if the user's file was CP949 before I touched it
            try:
                proper_content = original_bytes.decode('cp949')
                print("Successfully restored CP949 content.")
            except UnicodeDecodeError:
                print("Failed to decode original bytes as UTF-8 or CP949. Aborting.")
                return

        # 4. Save as UTF-8 with BOM
        with open(path, 'w', encoding='utf-8-sig') as f:
            f.write(proper_content)
        print("Restored file saved.")
    else:
        print("No double encoding (chars > 255 found). File might be partially corrupted or already rescued.")

if __name__ == "__main__":
    rescue_encoding()
