import re
import pathlib

path = pathlib.Path(r'C:\Users\Acer\Downloads\BilimGo_TOLIQ\frontend\src\services\api.ts')
text = path.read_text(encoding='utf-8')

# 1. Chop off mock data
mock_idx = text.find('/* =========================================================================\n   Mock In-Memory Data')
if mock_idx != -1:
    text = text[:mock_idx]

# 2. Clean up request definition
text = re.sub(r'fallbackGenerator\?:\s*\(\)\s*=>\s*Promise<T>\s*\|\s*T', '', text)
text = re.sub(r'if\s*\(useMockFallbackWhenOffline && fallbackGenerator\)\s*\{[^\}]+\}', '', text)
text = re.sub(r'let useMockFallbackWhenOffline = false;\n?', '', text)
text = re.sub(r'useMockFallback: useMockFallbackWhenOffline,', '', text)
text = re.sub(r'export function setMockFallback[^\}]+\}\n?', '', text)

# 3. Use regex to strip the 3rd argument for `request` calls.
# Match `, \n    () => mock...`
text = re.sub(r',\s*\(\)\s*=>\s*mock[a-zA-Z0-9_]+', '', text)
text = re.sub(r',\s*\(\)\s*=>\s*getSavedCabinets\(\)', '', text)
text = re.sub(r',\s*\(\)\s*=>\s*getDefaultUserProfile\(tgUser\)', '', text)
text = re.sub(r',\s*\(\)\s*=>\s*updated', '', text)
text = re.sub(r',\s*\(\)\s*=>\s*default[a-zA-Z0-9_]+\([^)]*\)', '', text)
text = re.sub(r',\s*\(\)\s*=>\s*\([^)]+\)\s*=>\s*[^,)]+', '', text)
text = re.sub(r',\s*\(\)\s*=>\s*\(\{[^\}]+\}\)', '', text)

# Block fallbacks:
# find `, \n    () => {` and remove it and everything until matching `}`
def remove_blocks(s):
    lines = s.split('\n')
    out = []
    skip = False
    brace = 0
    for line in lines:
        if re.search(r',\s*\(\)\s*=>\s*\{', line):
            skip = True
            brace = 1
            if '{' in line:
                pass
            continue
        if skip:
            brace += line.count('{')
            brace -= line.count('}')
            if brace <= 0:
                skip = False
            continue
        out.append(line)
    return '\n'.join(out)

text = remove_blocks(text)

# Final cleanup of empty lines
text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)

path.write_text(text, encoding='utf-8')
print("api.ts cleaned!")
