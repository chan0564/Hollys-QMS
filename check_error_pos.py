import os

def check_error_pos():
    path = r'c:\Users\LG\Desktop\Hollys_QMS\app.py'
    with open(path, 'r', encoding='utf-8-sig') as f:
        content = f.read()
    b = content.encode('iso-8859-1')
    
    pos = 233872
    start = max(0, pos - 20)
    end = min(len(b), pos + 20)
    
    chunk = b[start:end]
    print(f"Bytes at {start}-{end}: {chunk.hex()}")
    
    # Try decode UTF-8 carefully
    res = ""
    for bb in chunk:
        res += f"{bb:02x}"
    print(f"Hex: {res}")
    
    try:
        print(f"Utf-8 decode attempt: {chunk.decode('utf-8', errors='replace')}")
    except:
        pass

    try:
        print(f"CP949 decode attempt: {chunk.decode('cp949', errors='replace')}")
    except:
        pass

if __name__ == "__main__":
    check_error_pos()
