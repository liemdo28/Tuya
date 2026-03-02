"""
Imou Camera Setup v2 - Dùng thư viện imouapi
pip install imouapi aiohttp
"""

import asyncio
import json
from pathlib import Path

import aiohttp
from imouapi.api import ImouAPIClient
from imouapi.device import ImouDiscoverService, ImouDevice

IMOU_CONFIG_FILE = Path(__file__).parent / "imou_config.json"

async def main():
    print("=" * 60)
    print("  📷 Imou Camera Setup v2")
    print("=" * 60)
    print()

    app_id = input("  App ID [lca938b20270374441]: ").strip() or "lca938b20270374441"
    app_secret = input("  App Secret [0d7e5b3c...]: ").strip() or "0d7e5b3c216d4d2383e088bc65f2a4"

    print()
    print("  🔌 Đang kết nối Imou API...")

    session = aiohttp.ClientSession()
    try:
        api = ImouAPIClient(app_id, app_secret, session)
        await api.async_connect()
        print("  ✅ Kết nối thành công!")
        print()

        # Discover devices
        print("  📷 Đang tìm camera...")
        discover = ImouDiscoverService(api)
        discovered_devices = await discover.async_discover_devices()

        if not discovered_devices:
            print("  ❌ Không tìm thấy camera nào.")
            print("  Kiểm tra: camera đã được thêm vào app Imou Life chưa?")
            await session.close()
            return

        print(f"  ✅ Tìm thấy {len(discovered_devices)} thiết bị!")
        print()

        cameras = []
        for i, device in enumerate(discovered_devices):
            try:
                await device.async_initialize()
                
                name = device.get_name() or f"Camera {i+1}"
                device_id = device.get_device_id() or ""
                firmware = device.get_firmware() or ""
                
                print(f"  {i+1}. {name}")
                print(f"     Device ID: {device_id}")
                print(f"     Firmware: {firmware}")
                
                # Get sensors/switches info
                sensors = device.get_sensors()
                switches = device.get_switches()
                selects = device.get_selects()
                buttons = device.get_buttons()
                
                if sensors:
                    print(f"     Sensors: {', '.join(s.get_description() for s in sensors)}")
                if switches:
                    print(f"     Switches: {', '.join(s.get_description() for s in switches)}")
                
                camera_info = {
                    "device_id": device_id,
                    "name": name,
                    "firmware": firmware,
                    "status": "online",
                    "sensors": [s.get_description() for s in sensors] if sensors else [],
                    "switches": [s.get_description() for s in switches] if switches else [],
                }
                cameras.append(camera_info)
                
            except Exception as e:
                print(f"  {i+1}. Lỗi đọc thiết bị: {e}")
            
            print()

        # Assign rooms
        print("  🏠 Phân phòng cho camera:")
        for cam in cameras:
            room = input(f"    {cam['name']} → Nhà - Phòng (VD: 264A/6 - Sân): ").strip()
            cam["room"] = room or "Mặc định"

        # Save config
        config = {
            "app_id": app_id,
            "app_secret": app_secret,
            "cameras": cameras,
        }

        with open(IMOU_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

        print()
        print("=" * 60)
        print(f"  ✅ Đã lưu {len(cameras)} camera vào imou_config.json")
        print("  🔄 Restart app (python app.py) để xem camera trên dashboard!")
        print("=" * 60)

    except Exception as e:
        print(f"  ❌ Lỗi: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await session.close()

if __name__ == '__main__':
    asyncio.run(main())
