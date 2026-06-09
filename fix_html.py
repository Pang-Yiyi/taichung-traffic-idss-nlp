"""
Replace all st.markdown(..., unsafe_allow_html=True) that inject pure HTML
(i.e., content starts with '<') with st.html().
This is needed for Streamlit 1.31+ where st.html() is the proper way to inject HTML.
"""
import re

with open('app.py', encoding='utf-8') as f:
    content = f.read()

# Pattern: st.markdown( ... '<div...>...</div>' ..., unsafe_allow_html=True, )
# We need to handle both single-line and multi-line cases.

# Strategy: find all st.markdown calls with unsafe_allow_html=True
# and check if the content is pure HTML (starts with '<')

count = 0

# Pattern for single-line: st.markdown('...', unsafe_allow_html=True)
# and multi-line versions

def replace_html_markdown(text):
    global count

    # Single-line patterns: st.markdown('<...>', unsafe_allow_html=True)
    # Pattern 1: st.markdown('...html...', unsafe_allow_html=True,)
    pattern1 = r"st\.markdown\(\s*'(<[^']+)'\s*,\s*unsafe_allow_html=True\s*,?\s*\)"
    def repl1(m):
        global count
        count += 1
        return f"st.html('{m.group(1)}')"
    text = re.sub(pattern1, repl1, text, flags=re.DOTALL)

    # Pattern 2: st.markdown(f'...html...', unsafe_allow_html=True,)
    pattern2 = r"st\.markdown\(\s*f'(<[^']+)'\s*,\s*unsafe_allow_html=True\s*,?\s*\)"
    def repl2(m):
        global count
        count += 1
        return f"st.html(f'{m.group(1)}')"
    text = re.sub(pattern2, repl2, text, flags=re.DOTALL)

    return text

content = replace_html_markdown(content)

# Multi-line pattern: st.markdown(""" ... """, unsafe_allow_html=True,)
# Find these manually
import re

def replace_multiline_html_markdown(text):
    global count
    # Find st.markdown with triple-quoted strings
    pattern = r'st\.markdown\(\s*(?:f?)"""(.*?)"""\s*,\s*unsafe_allow_html=True\s*,?\s*\)'

    def repl(m):
        global count
        inner = m.group(1)
        stripped = inner.strip()
        # Only replace if content looks like HTML (starts with < or is f-string HTML)
        if stripped.startswith('<') or stripped.startswith('\n<') or stripped.startswith('\n            <') or stripped.startswith('\n        <') or stripped.startswith('\n                <') or stripped.startswith('\n            \n            <'):
            count += 1
            prefix = 'f' if m.group(0).startswith('st.markdown(\n        f"""') or 'f"""' in m.group(0)[:30] else ''
            return f'st.html({prefix}"""{m.group(1)}""")'
        return m.group(0)

    return re.sub(pattern, repl, text, flags=re.DOTALL)

content = replace_multiline_html_markdown(content)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print(f"Done. Replaced {count} st.markdown HTML calls with st.html()")

# Check for remaining unsafe_allow_html
remaining = content.count('unsafe_allow_html=True')
print(f"Remaining unsafe_allow_html=True: {remaining}")
