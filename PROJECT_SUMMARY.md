# 🏠 Tóm Tắt Dự Án: Tuya Smart Home + AI Assistant

## ✅ Đã hoàn thành

### 1. Hệ thống Smart Home Controller v2
- **46 thiết bị Tuya** đã được import tự động từ Tuya Cloud
- **6 thiết bị WiFi** điều khiển **local** (có IP)
- **40 thiết bị Zigbee** điều khiển qua **Tuya Cloud API**
- Dashboard web tại **http://localhost:5000**
- Hỗ trợ bật/tắt, điều chỉnh brightness, tạo kịch bản (scenes)
- Real-time status update qua WebSocket

### 2. Phân nhà/phòng
- **4 nhà**: 52, 264A/6, 264A/7, 124
- Đã phân phòng từ file CSV (ds.csv) dùng script update_rooms_v3.py
- Lưu ý: CSV dùng Unicode NFD, script dùng unicodedata.normalize('NFC') để match

### 3. Camera Imou (đang setup)
- **4 camera**: Cruiser Dual 10MP, Ranger Mini x2, Cue 2E
- Đã đăng ký Imou Open API, kết nối thành công
- Discover tìm thấy 4 camera
- Đang chạy setup_imou_v3.py để lưu config

---

## 📋 Thông tin kỹ thuật

### Tuya IoT Platform
- **Data Center**: Western America (US)
- **Access ID**: umw9h7f5njrt8qhfnn7d
- **Access Secret**: 47644e06d6c94226b305290214b4b3a4
- **Project**: TuyaSmarthome
- ⚠️ **NÊN ĐỔI** Access Secret vì đã hiện trong chat

### Imou Open API
- **App ID**: lca938b20270374441
- **App Secret**: 0d7e5b3c216d4d2383e088bc65f2a4
- **API URL**: https://openapi.easy4ip.com/openapi
- **Thư viện Python**: imouapi + aiohttp
- ⚠️ **NÊN ĐỔI** App Secret vì đã hiện trong chat

### Môi trường chạy hiện tại
- **Windows PC** (C:\Users\liemdo\tuya-smart-home\)
- **Python 3.13** cài trực tiếp trên Windows
- **WSL Ubuntu** đã cài nhưng chuyển sang Windows vì scan mạng LAN tốt hơn
- Thư viện: flask, flask-socketio, tinytuya, eventlet, requests, imouapi, aiohttp

### Cấu trúc thư mục hiện tại
```
C:\Users\liemdo\tuya-smart-home\
├── app.py                  # Server chính v2 (Local + Cloud API)
├── templates/
│   └── index.html          # Dashboard UI v2
├── devices.json            # 46 thiết bị Tuya (đã phân phòng)
├── cloud_config.json       # Tuya Cloud API config
├── imou_config.json        # Camera Imou config
├── ds.csv                  # File CSV phân phòng
├── auto_import.py          # Tự động import thiết bị Tuya
├── setup_imou.py           # Setup camera Imou (v1 - lỗi sign)
├── setup_imou_v3.py        # Setup camera Imou (v3 - dùng imouapi)
├── update_rooms.py         # Phân phòng (v1 - lỗi encoding)
├── update_rooms_v3.py      # Phân phòng (v3 - Unicode NFC fix)
├── tinytuya.json           # TinyTuya config
└── venv/                   # (nếu dùng WSL)
```

### Tính năng app.py v2
- **Local control**: TinyTuya cho thiết bị WiFi có IP
- **Cloud control**: Tuya Cloud API cho thiết bị Zigbee
- **Auto fallback**: thử local trước, nếu fail → dùng cloud
- **Tab Cài đặt**: cấu hình Cloud API từ dashboard
- **Nút "Cập nhật Cloud"**: refresh trạng thái tất cả thiết bị
- **Badge**: hiện 🟢 Local hoặc ☁️ Cloud cho từng thiết bị
- **Stats**: Tổng / Online / Local / Cloud / Offline

---

## 🎯 Kế hoạch tiếp theo (4 giai đoạn)

### Giai đoạn 1: Hoàn thiện Smart Home (đang làm)
- [x] Import 46 thiết bị Tuya
- [x] Local + Cloud control
- [x] Phân nhà/phòng từ CSV
- [ ] Tích hợp camera Imou vào dashboard (đang setup)
- [ ] Tạo kịch bản: Đi ngủ, Đi làm về, Rời nhà
- [ ] Migrate sang Android TV Box (Termux)
- [ ] Chạy tự động khi TV Box bật

### Giai đoạn 2: AI Voice Assistant
- [ ] STT: Whisper API hoặc Faster-Whisper (tiếng Việt)
- [ ] TTS: EdgeTTS giọng vi-VN-HoaiMyNeural
- [ ] LLM: DeepSeek/Qwen/Claude API
- [ ] Wake word detection
- [ ] Điều khiển thiết bị bằng giọng nói
- [ ] USB Microphone cho TV Box

### Giai đoạn 3: AI Face & Personality
- [ ] Gương mặt giả lập (mắt, miệng, mũi) bằng HTML5 Canvas
- [ ] Biểu cảm: vui, buồn, ngạc nhiên, đang nghe, đang nói, ngủ
- [ ] Lip sync với giọng nói
- [ ] Tính cách: dễ thương, hòa đồng, giọng ấm nhẹ
- [ ] Hiển thị full screen trên TV qua TV Box

### Giai đoạn 4: Nâng cao
- [ ] Phát nhạc/video (YouTube, Zing MP3)
- [ ] Tìm kiếm web
- [ ] Tự động hóa nâng cao (cron, sensor trigger)
- [ ] Điều khiển từ xa (Cloudflare Tunnel)
- [ ] Push notification

---

## 🔧 Lệnh quan trọng

### Chạy app
```powershell
cd C:\Users\liemdo\tuya-smart-home
python app.py
# Mở http://localhost:5000
```

### Import thiết bị Tuya
```powershell
python auto_import.py
# Chọn 1 (Western America), nhập Access ID + Secret
```

### Phân phòng
```powershell
python update_rooms_v3.py
```

### Setup camera Imou
```powershell
pip install imouapi aiohttp
python setup_imou_v3.py
```

### Setup TV Box (Termux)
```bash
pkg update && pkg upgrade -y
pkg install python -y
pip install flask flask-socketio tinytuya eventlet requests imouapi aiohttp
mkdir -p ~/tuya-smart-home/templates
# Copy files vào, rồi:
python app.py
```

### Chạy tự động trên TV Box
```bash
mkdir -p ~/.termux/boot
echo '#!/data/data/com.termux/files/usr/bin/bash
termux-wake-lock
cd ~/tuya-smart-home
python app.py &' > ~/.termux/boot/start-smarthome.sh
chmod +x ~/.termux/boot/start-smarthome.sh
# Cài Termux:Boot từ F-Droid
```

---

## 💡 Lưu ý quan trọng
1. **Đổi API keys** sau khi xong — đã hiện trong chat
2. **Cố định IP** thiết bị WiFi trên router (DHCP Reservation)
3. **TV Box cần WiFi 2.4GHz** cùng mạng với thiết bị Tuya
4. File CSV dùng **Unicode NFD** — cần normalize NFC khi xử lý
5. **imouapi** library dùng async — cần aiohttp session
6. Thiết bị Zigbee **chỉ control qua Cloud API**, không local được
