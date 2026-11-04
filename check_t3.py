import json

with open('lines_geometry.json', 'r', encoding='utf-8') as f:
    d = json.load(f)

print(f"T3: {len(d['T3'])} points")
print(f"Premier: {d['T3'][0]}")
print(f"Dernier: {d['T3'][-1]}")