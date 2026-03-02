"""
Update devices.json from CSV file - v3 (Unicode NFC fix)
"""

import json
import csv
import unicodedata
from pathlib import Path

DEVICES_FILE = Path(__file__).parent / "devices.json"
CSV_FILE = Path(__file__).parent / "ds.csv"

def normalize(s):
    """Normalize unicode to NFC and lowercase."""
    s = unicodedata.normalize('NFC', s)
    return s.strip().lower()

def main():
    with open(DEVICES_FILE, 'r', encoding='utf-8') as f:
        devices = json.load(f)
    
    csv_data = []
    with open(CSV_FILE, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Normalize all values to NFC
            normalized_row = {}
            for k, v in row.items():
                nk = unicodedata.normalize('NFC', k.strip())
                nv = unicodedata.normalize('NFC', v.strip()) if v else ''
                normalized_row[nk] = nv
            csv_data.append(normalized_row)
    
    print(f"📋 CSV: {len(csv_data)} dòng")
    print(f"📱 Devices: {len(devices)} thiết bị")
    print()
    
    type_map = {
        'Đèn': 'bulb', 'Công Tắc': 'switch',
        'Cảm biến': 'sensor', 'Quạt': 'fan', 'Rèm': 'cover',
    }
    
    updated = 0
    used_csv = set()
    
    for dev in devices:
        dev_name = unicodedata.normalize('NFC', dev['name'].strip())
        dev_norm = normalize(dev_name)
        
        best_match = None
        best_idx = -1
        best_score = 0
        
        for idx, row in enumerate(csv_data):
            if idx in used_csv:
                continue
            
            csv_name = row.get('Thiết bị', '').strip()
            csv_norm = normalize(csv_name)
            
            if not csv_name:
                continue
            
            # Exact match
            if dev_norm == csv_norm:
                best_match = row
                best_idx = idx
                best_score = 100
                break
            
            # Contains match
            if dev_norm in csv_norm or csv_norm in dev_norm:
                score = 80
                if score > best_score:
                    best_match = row
                    best_idx = idx
                    best_score = score
            
            # Word overlap
            dev_words = set(dev_norm.replace('-', ' ').replace('_', ' ').split())
            csv_words = set(csv_norm.replace('-', ' ').replace('_', ' ').split())
            overlap = len(dev_words & csv_words)
            total = max(len(dev_words), len(csv_words), 1)
            if overlap > 0:
                score = int((overlap / total) * 70)
                if score > best_score:
                    best_match = row
                    best_idx = idx
                    best_score = score
        
        if best_match and best_score >= 30:
            used_csv.add(best_idx)
            
            new_name = best_match.get('Đổi tên', '').strip()
            dev_type = best_match.get('Loại', '').strip()
            house = best_match.get('Nhà', '').strip()
            room = best_match.get('Phòng', '').strip()
            full_room = f"{house} - {room}" if house and room else "Mặc định"
            
            old_name = dev['name']
            if new_name:
                dev['name'] = new_name
            dev['room'] = full_room
            dev['house'] = house
            
            if dev_type in type_map:
                dev['type'] = type_map[dev_type]
            
            csv_name = best_match.get('Thiết bị', '')
            print(f"  ✅ [{old_name}] → {new_name or old_name} | {full_room}")
            updated += 1
        else:
            print(f"  ❌ [{dev_name}] → Không khớp CSV")
    
    with open(DEVICES_FILE, 'w', encoding='utf-8') as f:
        json.dump(devices, f, indent=2, ensure_ascii=False)
    
    print()
    print("=" * 60)
    print(f"  ✅ Đã cập nhật: {updated}/{len(devices)} thiết bị")
    if updated < len(devices):
        print(f"  ⚠️  {len(devices) - updated} thiết bị không khớp")
    print("=" * 60)
    print()
    print("🔄 Restart app (python app.py) để thấy thay đổi!")

if __name__ == '__main__':
    main()
