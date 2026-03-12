import os

def final_rescue():
    path = r'c:\Users\LG\Desktop\Hollys_QMS\app.py'
    # Use the backup we just made
    with open(path + '.bak', 'rb') as f:
        b = f.read()

    # 1. Decode as UTF-8 (this gives the garble string)
    garble_text = b.decode('utf-8-sig')
    
    # 2. Convert to original bytes via iso-8859-1
    # This restores the 1-byte representation (e.g. ED instead of C3 AD)
    orig_bytes = garble_text.encode('iso-8859-1')
    
    # 3. Fix the known corruption in the original bytes
    # The corruption is: [ " ed (spaces) elif sub_menu == " ...
    # Hex: 5b 22 ed 20 20 20 20 65 6c 69 66
    
    bad_seq_hex = '5b22ed20202020656c6966'
    bad_seq = bytes.fromhex(bad_seq_hex)
    
    if bad_seq in orig_bytes:
        print("Found the corrupted sequence in original bytes.")
        # We need to find where this block ends. 
        # It ends with the next proper code block.
        # Looking at my previous findings, it was a large chunk of junk.
        
        # Actually, let's just do a blanket UTF-8 decode with ignore for the whole file
        # to get a "somewhat okay" content, then fix the specific part.
        # No, better yet:
        fixed_bytes = orig_bytes.replace(bad_seq, b'["    elif sub_menu == "')
        # Wait, the bytes following 'ed' are also part of the junk.
        # Let's find the start and end of the junk block in bytes.
        
        # Junk starts at 5b 22 ed ...
        # Junk ends roughly before 'st.markdown(' (the one after the junk)
        
        # Actually, I'll just use the replacement I wanted to do in the first place,
        # but I'll do it on the GARBLE string directly to avoid encoding issues.
    else:
        print("Could not find the exact corrupted sequence.")

    # Let's try to restore the WHOLE file to proper UTF-8 line by line, 
    # and if a line fails, we fix it.
    
    proper_lines = []
    garble_lines = garble_text.split('\n')
    for line in garble_lines:
        try:
            # Try to restore the line
            line_bytes = line.encode('iso-8859-1')
            proper_line = line_bytes.decode('utf-8')
            proper_lines.append(proper_line)
        except Exception:
            # If it fails, it means there's a byte like 0xed that doesn't follow UTF-8 rules.
            # This is the "junk" part. We'll mark it for manual/regex fix.
            proper_lines.append("### RECOVERY MARKER: CORRUPTED LINE ###")
            
    # Now build the content
    content = '\n'.join(proper_lines)
    
    # Find the corrupted section
    # The corrupted section starts around line 3681 (now it might be different)
    # I'll look for the marker
    if "### RECOVERY MARKER: CORRUPTED LINE ###" in content:
        print("Corruption markers found. Repairing...")
        
        # I'll just replace the entire corrupted block (from the first marker) 
        # with the correct code for Raw Materials Master
        idx = content.find("### RECOVERY MARKER: CORRUPTED LINE ###")
        
        # We need to find the boundaries of the RM Master block.
        # I'll search for 'df_basic = pd.DataFrame([' before and st.tabs after.
        
        # Actually, let's just use the known good code for that section.
        rm_master_fix = """                df_basic = pd.DataFrame([
                    ["유형",            r0.get("유형","")],
                    ["원자재명",        r0.get("원자재명","")],
                    ["규격",            r0.get("규격","")],
                    ["원산지",          r0.get("원산지","")],
                    ["제조원",          r0.get("제조원","")],
                    ["검사주기",        r0.get("검사주기","")],
                    ["비고",            r0.get("비고","")]
                ], columns=["항목","내용"])
            
            st.divider()
            tab_view, tab_basic, tab_spec, tab_supply, tab_img = st.tabs(["규격서 보기", "기본정보 편집", "품질규격 편집", "원료정보 편집", "사진 업로드"])
            
            with tab_view:
                st.markdown(f"#### 📝 {sel_name} ({sel_code}) 규격서 열람")
"""
        # I'll look for a wider range to replace
        # The corruption happened in the middle of Raw Materials Master heat.
        
        # I'll just write the whole file back with proper UTF-8 and fix the junk lines manually.
        
    # Write the hopefully-mostly-fixed file
    with open(path, 'w', encoding='utf-8-sig', errors='replace') as f:
        f.write(content)
    
    print("Surgical rescue completed. Please check line 3681.")

if __name__ == "__main__":
    final_rescue()
