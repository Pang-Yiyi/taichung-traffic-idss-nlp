with open('app.py', encoding='utf-8') as f:
    content = f.read()

# Find old CSS block: it starts after the new st.html() block ends
# The new block ends with: </style>\n""")
# The old block starts with indented :root {
# and ends with: unsafe_allow_html=True,\n    )\n\n\ndef main()

end_of_new = '""")\n\n'
old_start_marker = '\n\n        :root {'

idx = content.find(end_of_new)
if idx == -1:
    print("ERROR: could not find end of new st.html block")
else:
    # After the new block ends
    after_new = content[idx + len(end_of_new):]
    # The old block starts here - find def main()
    def_main_idx = after_new.find('\ndef main()')
    if def_main_idx == -1:
        print("ERROR: could not find def main()")
    else:
        old_block = after_new[:def_main_idx]
        if ':root' in old_block or 'unsafe_allow_html' in old_block:
            # Remove the old block
            new_content = content[:idx + len(end_of_new)] + after_new[def_main_idx:]
            with open('app.py', 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"SUCCESS: removed {len(old_block)} chars of old CSS remnant")
            print(f"New file size: {len(new_content)} chars")
        else:
            print("Old block doesn't seem to contain CSS, skipping")
            print("First 200 chars after new block:", repr(after_new[:200]))
