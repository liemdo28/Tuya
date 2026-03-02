# Tuya Smart Home + Imou (Termux TV Box)

Tài liệu nhanh để chạy dự án **Tuya Smart Home + Imou** trên Android TV Box bằng **Termux**.

## 1) Chuẩn bị môi trường trong Termux

```bash
# Cập nhật package
pkg update && pkg upgrade -y

# Cài Python
pkg install python -y

# (Khuyến nghị) cài các gói nền để tránh lỗi build cryptography/cffi
pkg install rust clang openssl libffi -y

# Nâng cấp công cụ pip
python -m pip install --upgrade pip setuptools wheel

# Cài thư viện cần thiết
pip install flask flask-socketio tinytuya eventlet requests

# Tạo thư mục dự án
mkdir -p ~/tuya-smart-home/templates
cd ~/tuya-smart-home
```

### Nếu bị lỗi `Failed to build cryptography`

Một số máy Termux sẽ báo lỗi khi chạy:

```bash
pip install flask flask-socketio tinytuya eventlet requests
```

Lý do thường gặp: thiếu toolchain build (Rust/clang/OpenSSL/libffi) khi `pip` cài phụ thuộc của `cryptography`.

Chạy lần lượt:

```bash
pkg update
pkg install rust clang openssl libffi python-cryptography -y
python -m pip install --upgrade pip setuptools wheel
pip install cffi
pip install flask flask-socketio tinytuya eventlet requests
```

Nếu vẫn lỗi, thử cài theo từng gói để xác định gói nào gây lỗi:

```bash
pip install flask
pip install flask-socketio
pip install tinytuya
pip install eventlet
pip install requests
```

### Nếu bị lỗi khi `pip install tinytuya`

Lỗi thường gặp trên Termux:
- `Failed building wheel ...`
- lỗi liên quan `cryptography`, `cffi`, `pycryptodome`

Thử quy trình sau:

```bash
pkg update
pkg install rust clang openssl libffi python-cryptography -y
python -m pip install --upgrade pip setuptools wheel
pip install cffi pycryptodome
pip install tinytuya
```

Nếu vẫn lỗi, cài bản ổn định cụ thể:

```bash
pip install "tinytuya==1.13.2"
```

Kiểm tra đã import được chưa:

```bash
python -c "import tinytuya; print(tinytuya.__version__)"
```

## 2) Copy file dự án vào TV Box

Các file chính cần copy:
- `app.py`
- `templates/index.html`
- `devices.json`
- `cloud_config.json`

### Cách A: Copy qua USB

```bash
cp /storage/emulated/0/Download/app.py ~/tuya-smart-home/
cp /storage/emulated/0/Download/index.html ~/tuya-smart-home/templates/
cp /storage/emulated/0/Download/devices.json ~/tuya-smart-home/
cp /storage/emulated/0/Download/cloud_config.json ~/tuya-smart-home/
```

### Cách B: Copy qua mạng (SCP)

Trong Termux (TV Box):

```bash
pkg install openssh -y
sshd
whoami
passwd
ifconfig
```

Từ máy tính (PowerShell ví dụ):

```powershell
scp -P 8022 C:\Users\liemdo\tuya-smart-home\* user@IP_TVBOX:~/tuya-smart-home/
```

> Thay `user` bằng username Termux (`whoami`) và `IP_TVBOX` bằng IP TV Box.

## 3) Chạy app

```bash
cd ~/tuya-smart-home
python app.py
```

Mở dashboard từ thiết bị cùng Wi‑Fi:

```text
http://IP_TV_BOX:5000
```

## 4) Tự chạy khi TV Box khởi động

```bash
mkdir -p ~/.termux/boot
nano ~/.termux/boot/start-smarthome.sh
```

Dán nội dung script:

```bash
#!/data/data/com.termux/files/usr/bin/bash
termux-wake-lock
cd ~/tuya-smart-home
python app.py &
```

Cấp quyền chạy và cài service:

```bash
chmod +x ~/.termux/boot/start-smarthome.sh
pkg install termux-services -y
```

Cài ứng dụng **Termux:Boot** từ F-Droid để script tự chạy khi bật TV Box.

## 5) Tài liệu dự án đầy đủ

Thông tin tổng quan kiến trúc, tiến độ, cấu hình và kế hoạch xem tại:
- `PROJECT_SUMMARY.md`
