import json, pathlib

path = pathlib.Path('data/cookies/muktesh_cookies.json')
text = path.read_text(encoding='utf-8-sig').strip()  # utf-8-sig strips BOM
data = json.loads(text)
path.write_text(json.dumps(data, indent=2), encoding='utf-8')
print('Fixed.')

