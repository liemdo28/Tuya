&nbsp;(cd "$(git rev-parse --show-toplevel)" \&\& git apply --3way <<'EOF' 

diff --git a/README.md b/README.md

index a8c6d24d87f3fd9608352e5aff51cabb48ae2f34..dedc28d1b97830addc990c3f6576e91ed396af90 100644

--- a/README.md

+++ b/README.md

@@ -1 +1,100 @@

-"# Tuya" 

+# Tuya Smart Home + Imou (Termux TV Box)

\+

+Tài liệu nhanh để chạy dự án \*\*Tuya Smart Home + Imou\*\* trên Android TV Box bằng \*\*Termux\*\*.

\+

+## 1) Chuẩn bị môi trường trong Termux

\+

+```bash

+# Cập nhật package

+pkg update \&\& pkg upgrade -y

\+

+# Cài Python

+pkg install python -y

\+

+# Cài thư viện cần thiết

+pip install flask flask-socketio tinytuya eventlet requests

\+

+# Tạo thư mục dự án

+mkdir -p ~/tuya-smart-home/templates

+cd ~/tuya-smart-home

+```

\+

+## 2) Copy file dự án vào TV Box

\+

+Các file chính cần copy:

+- `app.py`

+- `templates/index.html`

+- `devices.json`

+- `cloud\_config.json`

\+

+### Cách A: Copy qua USB

\+

+```bash

+cp /storage/emulated/0/Download/app.py ~/tuya-smart-home/

+cp /storage/emulated/0/Download/index.html ~/tuya-smart-home/templates/

+cp /storage/emulated/0/Download/devices.json ~/tuya-smart-home/

+cp /storage/emulated/0/Download/cloud\_config.json ~/tuya-smart-home/

+```

\+

+### Cách B: Copy qua mạng (SCP)

\+

+Trong Termux (TV Box):

\+

+```bash

+pkg install openssh -y

+sshd

+whoami

+passwd

+ifconfig

+```

\+

+Từ máy tính (PowerShell ví dụ):

\+

+```powershell

+scp -P 8022 C:\\Users\\liemdo\\tuya-smart-home\\\* user@IP\_TVBOX:~/tuya-smart-home/

+```

\+

+> Thay `user` bằng username Termux (`whoami`) và `IP\_TVBOX` bằng IP TV Box.

\+

+## 3) Chạy app

\+

+```bash

+cd ~/tuya-smart-home

+python app.py

+```

\+

+Mở dashboard từ thiết bị cùng Wi‑Fi:

\+

+```text

+http://IP\_TV\_BOX:5000

+```

\+

+## 4) Tự chạy khi TV Box khởi động

\+

+```bash

+mkdir -p ~/.termux/boot

+nano ~/.termux/boot/start-smarthome.sh

+```

\+

+Dán nội dung script:

\+

+```bash

+#!/data/data/com.termux/files/usr/bin/bash

+termux-wake-lock

+cd ~/tuya-smart-home

+python app.py \&

+```

\+

+Cấp quyền chạy và cài service:

\+

+```bash

+chmod +x ~/.termux/boot/start-smarthome.sh

+pkg install termux-services -y

+```

\+

+Cài ứng dụng \*\*Termux:Boot\*\* từ F-Droid để script tự chạy khi bật TV Box.

\+

+## 5) Tài liệu dự án đầy đủ

\+

+Thông tin tổng quan kiến trúc, tiến độ, cấu hình và kế hoạch xem tại:

+- `PROJECT\_SUMMARY.md`

&nbsp;

EOF

)

