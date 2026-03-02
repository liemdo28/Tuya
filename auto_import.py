"""
Tuya Auto Import - Tự động lấy tất cả thiết bị từ Tuya Cloud
và thêm vào Tuya Smart Home Controller.

Cách dùng:
  python auto_import.py

Sẽ hỏi bạn nhập:
  - Access ID (Client ID) từ Tuya IoT Platform
  - Access Secret (Client Secret)
  - Data Center region
"""

import json
import os
import sys

try:
    import tinytuya
except ImportError:
    print("Đang cài tinytuya...")
    os.system("pip install tinytuya")
    import tinytuya

from pathlib import Path

CONFIG_FILE = Path(__file__).parent / "devices.json"

def load_existing_devices():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_devices(devices):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(devices, f, indent=2, ensure_ascii=False)

def guess_device_type(category):
    """Đoán loại thiết bị từ category code của Tuya."""
    mapping = {
        'dj': 'bulb',       # đèn LED
        'dd': 'bulb',       # đèn strip
        'fwd': 'bulb',      # đèn downlight
        'dc': 'bulb',       # đèn string light
        'xdd': 'bulb',      # đèn ceiling
        'kg': 'switch',     # công tắc
        'tdq': 'switch',    # công tắc đèn
        'pc': 'switch',     # power strip
        'cz': 'switch',     # ổ cắm
        'dlq': 'switch',    # circuit breaker
        'cl': 'cover',      # rèm cửa
        'clkg': 'cover',    # công tắc rèm
        'fs': 'fan',        # quạt
        'fsd': 'fan',       # quạt trần
        'kfj': 'fan',       # quạt sưởi
        'pir': 'sensor',    # cảm biến PIR
        'mcs': 'sensor',    # cảm biến cửa
        'wsdcg': 'sensor',  # cảm biến nhiệt độ
        'rqbj': 'sensor',   # cảm biến gas
        'ywbj': 'sensor',   # cảm biến khói
        'ldcg': 'sensor',   # cảm biến ánh sáng
        'sp': 'sensor',     # camera (dùng sensor làm placeholder)
    }
    return mapping.get(category, 'switch')

def guess_dps_config(category):
    """Đoán DPS config dựa trên loại thiết bị."""
    configs = {
        'bulb': [
            {"dp": 1, "name": "Bật/Tắt", "type": "bool"},
            {"dp": 2, "name": "Chế độ", "type": "str"},
            {"dp": 3, "name": "Độ sáng", "type": "int", "min": 10, "max": 1000},
            {"dp": 4, "name": "Nhiệt độ màu", "type": "int", "min": 0, "max": 1000},
        ],
        'switch': [
            {"dp": 1, "name": "Công tắc", "type": "bool"},
        ],
        'cover': [
            {"dp": 1, "name": "Mở/Đóng/Dừng", "type": "str"},
            {"dp": 2, "name": "Vị trí (%)", "type": "int", "min": 0, "max": 100},
        ],
        'fan': [
            {"dp": 1, "name": "Bật/Tắt", "type": "bool"},
            {"dp": 3, "name": "Tốc độ", "type": "int", "min": 1, "max": 6},
        ],
        'sensor': [
            {"dp": 1, "name": "Trạng thái", "type": "bool"},
        ],
    }
    return configs.get(category, [{"dp": 1, "name": "Switch", "type": "bool"}])

def main():
    print("=" * 60)
    print("  🏠 Tuya Auto Import Tool")
    print("  Tự động thêm tất cả thiết bị vào Smart Home Controller")
    print("=" * 60)
    print()

    # Nhập thông tin API
    print("📋 Nhập thông tin từ Tuya IoT Platform (tab Overview):")
    print()
    
    api_id = input("  Access ID/Client ID: ").strip()
    api_secret = input("  Access Secret/Client Secret: ").strip()
    
    print()
    print("  Chọn Data Center:")
    print("    1. Western America (us)")
    print("    2. Central Europe (eu)")
    print("    3. India (in)")
    print("    4. Eastern America (ue)")
    print("    5. China (cn)")
    
    dc_choice = input("  Chọn (1-5): ").strip()
    dc_map = {'1': 'us', '2': 'eu', '3': 'in', '4': 'ue', '5': 'cn'}
    api_region = dc_map.get(dc_choice, 'us')
    
    print()
    print(f"  ✅ Region: {api_region}")
    print()
    
    # Tạo file tinytuya.json để wizard sử dụng
    tinytuya_json = {
        "apiKey": api_id,
        "apiSecret": api_secret,
        "apiRegion": api_region,
        "apiDeviceID": "scan"
    }
    
    with open("tinytuya.json", 'w') as f:
        json.dump(tinytuya_json, f, indent=2)
    
    print("📡 Đang kết nối Tuya Cloud và lấy danh sách thiết bị...")
    print()
    
    # Kết nối Tuya Cloud API
    try:
        c = tinytuya.Cloud(
            apiRegion=api_region,
            apiKey=api_id,
            apiSecret=api_secret
        )
        
        # Lấy danh sách thiết bị
        devices = c.getdevices()
        
        if not devices:
            print("❌ Không tìm thấy thiết bị nào. Kiểm tra lại:")
            print("   - Access ID/Secret có đúng không?")
            print("   - Đã Link App Account chưa?")
            print("   - Data Center có đúng không?")
            return
        
        print(f"✅ Tìm thấy {len(devices)} thiết bị từ Tuya Cloud!")
        print()
        
        # Quét mạng LAN để tìm IP
        print("📡 Đang quét mạng LAN để tìm IP thiết bị...")
        print("   (Có thể mất 10-30 giây)")
        print()
        
        scan_results = {}
        try:
            scanned = tinytuya.deviceScan(verbose=False, maxretry=3)
            for ip, info in scanned.items():
                dev_id = info.get('gwId', '')
                if dev_id:
                    scan_results[dev_id] = {
                        'ip': ip,
                        'version': info.get('version', '3.3')
                    }
            print(f"✅ Tìm thấy {len(scan_results)} thiết bị trên mạng LAN")
        except Exception as e:
            print(f"⚠️  Không thể quét mạng LAN: {e}")
            print("   Bạn cần tự nhập IP sau.")
        
        print()
        
        # Load existing devices
        existing_devices = load_existing_devices()
        existing_ids = {d['id'] for d in existing_devices}
        
        new_devices = []
        skipped = 0
        no_ip = 0
        
        for dev in devices:
            dev_id = dev.get('id', '')
            dev_name = dev.get('name', 'Unknown')
            local_key = dev.get('key', '')
            category = dev.get('category', '')
            
            # Skip nếu đã tồn tại
            if dev_id in existing_ids:
                skipped += 1
                continue
            
            # Tìm IP từ scan results
            scan_info = scan_results.get(dev_id, {})
            ip = scan_info.get('ip', '')
            version = scan_info.get('version', '3.3')
            
            if not ip:
                no_ip += 1
            
            dev_type = guess_device_type(category)
            dps_config = guess_dps_config(dev_type)
            
            new_device = {
                "id": dev_id,
                "name": dev_name,
                "ip": ip,
                "local_key": local_key,
                "type": dev_type,
                "version": str(version),
                "room": "Mặc định",
                "icon": dev_type,
                "category": category,
                "dps_config": dps_config
            }
            
            new_devices.append(new_device)
            
            status = f"🟢 IP: {ip}" if ip else "🔴 Chưa có IP"
            print(f"  ＋ {dev_name}")
            print(f"    ID: {dev_id[:8]}... | Type: {dev_type} | {status}")
        
        print()
        print("-" * 60)
        print(f"  📊 Tổng kết:")
        print(f"     Thiết bị mới:    {len(new_devices)}")
        print(f"     Đã có sẵn:       {skipped}")
        print(f"     Có IP (local):   {len(new_devices) - no_ip}")
        print(f"     Chưa có IP:      {no_ip}")
        print("-" * 60)
        
        if no_ip > 0:
            print()
            print(f"  ⚠️  {no_ip} thiết bị chưa tìm được IP trên mạng LAN.")
            print("     Có thể do: thiết bị offline, dùng Zigbee gateway,")
            print("     hoặc khác subnet. Bạn có thể sửa IP sau trong dashboard.")
        
        if not new_devices:
            print()
            print("✅ Tất cả thiết bị đã có trong hệ thống!")
            return
        
        print()
        confirm = input(f"  ➡️  Thêm {len(new_devices)} thiết bị vào hệ thống? (y/n): ").strip().lower()
        
        if confirm in ['y', 'yes', '']:
            all_devices = existing_devices + new_devices
            save_devices(all_devices)
            print()
            print(f"  ✅ Đã thêm {len(new_devices)} thiết bị thành công!")
            print(f"  📱 Mở http://localhost:5000 để xem và điều khiển")
            print()
            
            if no_ip > 0:
                print("  📝 Việc cần làm:")
                print(f"     - Cập nhật IP cho {no_ip} thiết bị chưa có IP")
                print("     - Vào dashboard → sửa thông tin thiết bị")
                print("     - Hoặc chạy lại script này khi thiết bị online")
        else:
            print("  ❌ Đã hủy.")
    
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        print()
        print("Kiểm tra lại:")
        print("  - Access ID/Secret có đúng không?")
        print("  - Đã Link App Account trên Tuya IoT Platform chưa?")
        print("  - Data Center có đúng không? (bạn chọn: {})".format(api_region))
        
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
