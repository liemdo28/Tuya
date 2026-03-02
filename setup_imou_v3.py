"""
Imou Camera Setup v3 - Fixed device discovery
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
    print("  📷 Imou Camera Setup v3")
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
        discovered = await discover.async_discover_devices()

        if not discovered:
            print("  ❌ Không tìm thấy camera nào.")
            await session.close()
            return

        print(f"  ✅ Tìm thấy {len(discovered)} thiết bị!")
        print()

        cameras = []
        for i, item in enumerate(discovered):
            try:
                # item might be string (device_id) or ImouDevice object
                if isinstance(item, str):
                    device_id = item
                    device = ImouDevice(api, device_id)
                    await device.async_initialize()
                elif isinstance(item, ImouDevice):
                    device = item
                    await device.async_initialize()
                    device_id = device.get_device_id()
                else:
                    # Try to get device_id from object
                    device_id = str(item)
                    device = ImouDevice(api, device_id)
                    await device.async_initialize()

                name = device.get_name() or f"Camera {i+1}"
                firmware = device.get_firmware() or "N/A"

                print(f"  {i+1}. {name}")
                print(f"     Device ID: {device_id}")
                print(f"     Firmware: {firmware}")

                # Get capabilities
                sensor_names = []
                switch_names = []
                try:
                    sensors = device.get_sensors() or []
                    switches = device.get_switches() or []
                    sensor_names = [s.get_description() for s in sensors]
                    switch_names = [s.get_description() for s in switches]
                    if sensor_names:
                        print(f"     Sensors: {', '.join(sensor_names)}")
                    if switch_names:
                        print(f"     Switches: {', '.join(switch_names)}")
                except:
                    pass

                cameras.append({
                    "device_id": device_id,
                    "name": name,
                    "firmware": firmware,
                    "status": "online",
                    "sensors": sensor_names,
                    "switches": switch_names,
                })

            except Exception as e:
                # Fallback: just save device_id
                device_id = str(item)
                print(f"  {i+1}. Device ID: {device_id} (chi tiết không lấy được: {e})")
                cameras.append({
                    "device_id": device_id,
                    "name": f"Camera {i+1}",
                    "firmware": "N/A",
                    "status": "online",
                    "sensors": [],
                    "switches": [],
                })

            print()

        # Assign rooms and names
        print("  🏠 Đặt tên và phân phòng cho camera:")
        print("  (Nhấn Enter để giữ tên mặc định)")
        print()
        for cam in cameras:
            new_name = input(f"    {cam['name']} → Đổi tên: ").strip()
            if new_name:
                cam['name'] = new_name
            room = input(f"    {cam['name']} → Nhà - Phòng (VD: 264A/6 - Sân): ").strip()
            cam["room"] = room or "Mặc định"
            print()

        # Save config
        config = {
            "app_id": app_id,
            "app_secret": app_secret,
            "cameras": cameras,
        }

        with open(IMOU_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

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
