"""
Tuya Smart Home Controller v2
- Local control cho thiết bị WiFi có IP
- Cloud API control cho thiết bị Zigbee/không có IP
- Real-time status updates via WebSocket

Requires: pip install tinytuya flask flask-socketio eventlet
"""

import json
import os
import threading
import time
import hmac
import hashlib
import requests
from pathlib import Path

import tinytuya
from flask import Flask, jsonify, render_template, request
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'tuya-smart-home-secret'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Config file paths
CONFIG_FILE = Path(__file__).parent / "devices.json"
SETTINGS_FILE = Path(__file__).parent / "settings.json"
CLOUD_CONFIG_FILE = Path(__file__).parent / "cloud_config.json"

# ============================================================
# Cloud API Client
# ============================================================

class TuyaCloudAPI:
    """Tuya Cloud API client for controlling devices without local IP."""
    
    def __init__(self):
        self.config = self._load_config()
        self.token = None
        self.token_expiry = 0
    
    def _load_config(self):
        if CLOUD_CONFIG_FILE.exists():
            with open(CLOUD_CONFIG_FILE, 'r') as f:
                return json.load(f)
        return {}
    
    def save_config(self, api_id, api_secret, api_region='us'):
        config = {
            "api_id": api_id,
            "api_secret": api_secret,
            "api_region": api_region
        }
        with open(CLOUD_CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        self.config = config
        self.token = None
        self.token_expiry = 0
    
    def _get_base_url(self):
        region = self.config.get('api_region', 'us')
        urls = {
            'us': 'https://openapi.tuyaus.com',
            'eu': 'https://openapi.tuyaeu.com',
            'in': 'https://openapi.tuyain.com',
            'cn': 'https://openapi.tuyacn.com',
            'ue': 'https://openapi-ueaz.tuyaus.com',
        }
        return urls.get(region, urls['us'])
    
    def _sign_request(self, method, path, body='', headers=None):
        """Generate Tuya API signature."""
        api_id = self.config.get('api_id', '')
        api_secret = self.config.get('api_secret', '')
        t = str(int(time.time() * 1000))
        
        # String to sign
        content_hash = hashlib.sha256((body or '').encode()).hexdigest()
        string_to_sign = f"{method}\n{content_hash}\n\n{path}"
        
        if self.token:
            sign_str = api_id + self.token + t + string_to_sign
        else:
            sign_str = api_id + t + string_to_sign
        
        sign = hmac.new(
            api_secret.encode(),
            sign_str.encode(),
            hashlib.sha256
        ).hexdigest().upper()
        
        return {
            'client_id': api_id,
            'sign': sign,
            'sign_method': 'HMAC-SHA256',
            't': t,
            'access_token': self.token or '',
        }
    
    def _get_token(self):
        """Get or refresh access token."""
        if self.token and time.time() < self.token_expiry:
            return self.token
        
        if not self.config.get('api_id'):
            return None
        
        path = '/v1.0/token?grant_type=1'
        base_url = self._get_base_url()
        
        sign_headers = self._sign_request('GET', path)
        
        headers = {
            'client_id': sign_headers['client_id'],
            'sign': sign_headers['sign'],
            'sign_method': sign_headers['sign_method'],
            't': sign_headers['t'],
        }
        
        try:
            resp = requests.get(f"{base_url}{path}", headers=headers, timeout=10)
            data = resp.json()
            
            if data.get('success'):
                result = data['result']
                self.token = result['access_token']
                self.token_expiry = time.time() + result.get('expire_time', 7200) - 60
                return self.token
            else:
                print(f"Token error: {data.get('msg')}")
                return None
        except Exception as e:
            print(f"Token request failed: {e}")
            return None
    
    def _api_request(self, method, path, body=None):
        """Make authenticated API request."""
        token = self._get_token()
        if not token:
            return {"success": False, "error": "Cannot get API token"}
        
        base_url = self._get_base_url()
        body_str = json.dumps(body) if body else ''
        
        sign_headers = self._sign_request(method, path, body_str)
        
        headers = {
            'client_id': sign_headers['client_id'],
            'sign': sign_headers['sign'],
            'sign_method': sign_headers['sign_method'],
            't': sign_headers['t'],
            'access_token': token,
            'Content-Type': 'application/json',
        }
        
        try:
            if method == 'GET':
                resp = requests.get(f"{base_url}{path}", headers=headers, timeout=10)
            elif method == 'POST':
                resp = requests.post(f"{base_url}{path}", headers=headers, data=body_str, timeout=10)
            
            return resp.json()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_device_status(self, device_id):
        """Get device status from cloud."""
        result = self._api_request('GET', f'/v1.0/devices/{device_id}/status')
        if result.get('success') and result.get('result'):
            dps = {}
            for item in result['result']:
                code = item.get('code', '')
                value = item.get('value')
                dp_id = item.get('dp_id')
                if dp_id:
                    dps[str(dp_id)] = value
                # Map common codes to dp numbers
                code_dp_map = {
                    'switch_1': '1', 'switch_2': '2', 'switch_3': '3',
                    'switch_led': '1', 'switch': '1',
                    'bright_value': '3', 'bright_value_v2': '3',
                    'temp_value': '4', 'temp_value_v2': '4',
                    'colour_data': '5', 'colour_data_v2': '5',
                }
                if code in code_dp_map and str(code_dp_map[code]) not in dps:
                    dps[code_dp_map[code]] = value
                # Store by code name as well
                dps[code] = value
            return {"online": True, "dps": dps, "source": "cloud"}
        return {"online": False, "dps": {}, "source": "cloud"}
    
    def control_device(self, device_id, commands):
        """Send commands to device via cloud."""
        body = {"commands": commands}
        result = self._api_request('POST', f'/v1.0/devices/{device_id}/commands', body)
        return result
    
    def get_device_functions(self, device_id):
        """Get available functions for a device."""
        result = self._api_request('GET', f'/v1.0/devices/{device_id}/functions')
        if result.get('success'):
            return result.get('result', {}).get('functions', [])
        return []
    
    def get_device_info(self, device_id):
        """Get device details from cloud."""
        result = self._api_request('GET', f'/v1.0/devices/{device_id}')
        if result.get('success'):
            return result.get('result', {})
        return {}
    
    @property
    def is_configured(self):
        return bool(self.config.get('api_id') and self.config.get('api_secret'))


# Global cloud API instance
cloud_api = TuyaCloudAPI()

# ============================================================
# Device Management
# ============================================================

def load_devices():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_devices(devices):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(devices, f, indent=2, ensure_ascii=False)

def get_device_connection(device_info):
    dev_type = device_info.get('type', 'switch')
    if dev_type == 'bulb':
        d = tinytuya.BulbDevice(
            dev_id=device_info['id'],
            address=device_info['ip'],
            local_key=device_info['local_key']
        )
    else:
        d = tinytuya.OutletDevice(
            dev_id=device_info['id'],
            address=device_info['ip'],
            local_key=device_info['local_key']
        )
    d.set_version(float(device_info.get('version', '3.3')))
    return d

def get_device_status(device_info):
    """Get device status - try local first, fallback to cloud."""
    ip = device_info.get('ip', '').strip()
    
    # Try local first if IP exists
    if ip:
        try:
            d = get_device_connection(device_info)
            d.set_socketTimeout(3)
            status = d.status()
            if status and 'dps' in status:
                return {"online": True, "dps": status['dps'], "source": "local"}
        except Exception:
            pass
    
    # Fallback to cloud API
    if cloud_api.is_configured:
        try:
            return cloud_api.get_device_status(device_info['id'])
        except Exception:
            pass
    
    return {"online": False, "dps": {}, "source": "none"}

def control_device(device_info, dp_index, value):
    """Control device - try local first, fallback to cloud."""
    ip = device_info.get('ip', '').strip()
    
    # Try local first
    if ip:
        try:
            d = get_device_connection(device_info)
            d.set_socketTimeout(3)
            d.set_value(dp_index, value)
            time.sleep(0.3)
            status = d.status()
            if status and 'dps' in status:
                return {"success": True, "dps": status['dps'], "source": "local"}
        except Exception:
            pass
    
    # Fallback to cloud
    if cloud_api.is_configured:
        try:
            # Try to find the function code for this DP
            code = _dp_to_code(device_info, dp_index, value)
            commands = [{"code": code, "value": value}]
            result = cloud_api.control_device(device_info['id'], commands)
            
            if result.get('success'):
                time.sleep(0.5)
                status = cloud_api.get_device_status(device_info['id'])
                return {"success": True, "dps": status.get('dps', {}), "source": "cloud"}
            else:
                # Try with switch_dp format
                commands = [{"code": f"switch_{dp_index}", "value": value}]
                result = cloud_api.control_device(device_info['id'], commands)
                if result.get('success'):
                    time.sleep(0.5)
                    status = cloud_api.get_device_status(device_info['id'])
                    return {"success": True, "dps": status.get('dps', {}), "source": "cloud"}
                
                return {"success": False, "error": result.get('msg', 'Cloud control failed')}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    return {"success": False, "error": "No local IP and cloud not configured"}

def _dp_to_code(device_info, dp_index, value):
    """Convert DP index to Tuya function code."""
    dev_type = device_info.get('type', 'switch')
    
    # Common mappings
    if isinstance(value, bool):
        if dp_index == 1:
            if dev_type == 'bulb':
                return 'switch_led'
            return 'switch_1'
        return f'switch_{dp_index}'
    
    if isinstance(value, int):
        if dp_index == 3:
            return 'bright_value_v2'
        if dp_index == 4:
            return 'temp_value_v2'
    
    return f'switch_{dp_index}'

# ============================================================
# Background Status Polling
# ============================================================

device_states = {}
polling_active = True

def poll_devices():
    global device_states, polling_active
    while polling_active:
        devices = load_devices()
        for dev in devices:
            try:
                status = get_device_status(dev)
                device_states[dev['id']] = status
                socketio.emit('device_status', {
                    'device_id': dev['id'],
                    'status': status
                })
            except Exception:
                pass
            time.sleep(0.2)  # Small delay between devices
        time.sleep(15)  # Poll every 15 seconds

# ============================================================
# API Routes
# ============================================================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/devices', methods=['GET'])
def api_get_devices():
    devices = load_devices()
    for dev in devices:
        dev['status'] = device_states.get(dev['id'], {"online": False, "dps": {}})
    return jsonify(devices)

@app.route('/api/devices', methods=['POST'])
def api_add_device():
    data = request.json
    devices = load_devices()
    
    required = ['id', 'name']
    for field in required:
        if field not in data:
            return jsonify({"error": f"Missing field: {field}"}), 400
    
    new_device = {
        "id": data['id'],
        "ip": data.get('ip', ''),
        "local_key": data.get('local_key', ''),
        "name": data['name'],
        "type": data.get('type', 'switch'),
        "version": data.get('version', '3.3'),
        "room": data.get('room', 'Mặc định'),
        "icon": data.get('icon', 'power'),
        "category": data.get('category', ''),
        "dps_config": data.get('dps_config', [{"dp": 1, "name": "Switch", "type": "bool"}])
    }
    
    for d in devices:
        if d['id'] == new_device['id']:
            return jsonify({"error": "Device ID already exists"}), 400
    
    devices.append(new_device)
    save_devices(devices)
    
    status = get_device_status(new_device)
    device_states[new_device['id']] = status
    
    return jsonify({"success": True, "device": new_device})

@app.route('/api/devices/<device_id>', methods=['PUT'])
def api_update_device(device_id):
    data = request.json
    devices = load_devices()
    
    for i, dev in enumerate(devices):
        if dev['id'] == device_id:
            devices[i].update(data)
            save_devices(devices)
            return jsonify({"success": True})
    
    return jsonify({"error": "Device not found"}), 404

@app.route('/api/devices/<device_id>', methods=['DELETE'])
def api_delete_device(device_id):
    devices = load_devices()
    devices = [d for d in devices if d['id'] != device_id]
    save_devices(devices)
    device_states.pop(device_id, None)
    return jsonify({"success": True})

@app.route('/api/devices/<device_id>/control', methods=['POST'])
def api_control_device(device_id):
    data = request.json
    devices = load_devices()
    
    device = None
    for dev in devices:
        if dev['id'] == device_id:
            device = dev
            break
    
    if not device:
        return jsonify({"error": "Device not found"}), 404
    
    dp_index = int(data.get('dp', 1))
    value = data.get('value')
    
    if isinstance(value, str):
        if value.lower() == 'true':
            value = True
        elif value.lower() == 'false':
            value = False
        elif value.isdigit():
            value = int(value)
    
    result = control_device(device, dp_index, value)
    
    if result.get('success'):
        device_states[device_id] = {
            "online": True,
            "dps": result.get('dps', {}),
            "source": result.get('source', 'unknown')
        }
        socketio.emit('device_status', {
            'device_id': device_id,
            'status': device_states[device_id]
        })
    
    return jsonify(result)

@app.route('/api/devices/<device_id>/status', methods=['GET'])
def api_device_status(device_id):
    devices = load_devices()
    device = None
    for dev in devices:
        if dev['id'] == device_id:
            device = dev
            break
    
    if not device:
        return jsonify({"error": "Device not found"}), 404
    
    status = get_device_status(device)
    device_states[device_id] = status
    return jsonify(status)

@app.route('/api/devices/<device_id>/functions', methods=['GET'])
def api_device_functions(device_id):
    """Get available cloud functions for a device."""
    if not cloud_api.is_configured:
        return jsonify({"error": "Cloud API not configured"}), 400
    functions = cloud_api.get_device_functions(device_id)
    return jsonify(functions)

@app.route('/api/devices/<device_id>/cloud-control', methods=['POST'])
def api_cloud_control(device_id):
    """Direct cloud control with specific command code."""
    if not cloud_api.is_configured:
        return jsonify({"error": "Cloud API not configured"}), 400
    
    data = request.json
    commands = data.get('commands', [])
    
    if not commands:
        return jsonify({"error": "No commands provided"}), 400
    
    result = cloud_api.control_device(device_id, commands)
    
    if result.get('success'):
        time.sleep(0.5)
        status = cloud_api.get_device_status(device_id)
        device_states[device_id] = status
        socketio.emit('device_status', {
            'device_id': device_id,
            'status': status
        })
    
    return jsonify(result)

@app.route('/api/scan', methods=['GET'])
def api_scan_network():
    try:
        devices = tinytuya.deviceScan(verbose=False, maxretry=2)
        found = []
        for ip, info in devices.items():
            found.append({
                "ip": ip,
                "id": info.get('gwId', ''),
                "version": info.get('version', '3.3'),
                "name": info.get('name', 'Unknown')
            })
        return jsonify(found)
    except Exception as e:
        return jsonify({"error": str(e), "devices": []})

@app.route('/api/cloud/config', methods=['GET'])
def api_get_cloud_config():
    if CLOUD_CONFIG_FILE.exists():
        with open(CLOUD_CONFIG_FILE, 'r') as f:
            config = json.load(f)
            # Hide secret
            if config.get('api_secret'):
                config['api_secret'] = config['api_secret'][:6] + '***'
            return jsonify(config)
    return jsonify({})

@app.route('/api/cloud/config', methods=['POST'])
def api_set_cloud_config():
    data = request.json
    cloud_api.save_config(
        api_id=data.get('api_id', ''),
        api_secret=data.get('api_secret', ''),
        api_region=data.get('api_region', 'us')
    )
    # Test connection
    token = cloud_api._get_token()
    if token:
        return jsonify({"success": True, "message": "Cloud API connected!"})
    return jsonify({"success": False, "error": "Failed to connect. Check credentials."}), 400

@app.route('/api/cloud/refresh-all', methods=['POST'])
def api_cloud_refresh_all():
    """Refresh status of all devices via cloud."""
    if not cloud_api.is_configured:
        return jsonify({"error": "Cloud API not configured"}), 400
    
    devices = load_devices()
    updated = 0
    for dev in devices:
        try:
            status = get_device_status(dev)
            device_states[dev['id']] = status
            socketio.emit('device_status', {
                'device_id': dev['id'],
                'status': status
            })
            if status.get('online'):
                updated += 1
        except Exception:
            pass
        time.sleep(0.3)
    
    return jsonify({"success": True, "updated": updated, "total": len(devices)})

# Scenes
@app.route('/api/scenes', methods=['GET'])
def api_get_scenes():
    scenes_file = Path(__file__).parent / "scenes.json"
    if scenes_file.exists():
        with open(scenes_file, 'r', encoding='utf-8') as f:
            return jsonify(json.load(f))
    return jsonify([])

@app.route('/api/scenes', methods=['POST'])
def api_add_scene():
    data = request.json
    scenes_file = Path(__file__).parent / "scenes.json"
    scenes = []
    if scenes_file.exists():
        with open(scenes_file, 'r', encoding='utf-8') as f:
            scenes = json.load(f)
    scenes.append(data)
    with open(scenes_file, 'w', encoding='utf-8') as f:
        json.dump(scenes, f, indent=2, ensure_ascii=False)
    return jsonify({"success": True})

@app.route('/api/scenes/<int:scene_index>/execute', methods=['POST'])
def api_execute_scene(scene_index):
    scenes_file = Path(__file__).parent / "scenes.json"
    if not scenes_file.exists():
        return jsonify({"error": "No scenes found"}), 404
    
    with open(scenes_file, 'r', encoding='utf-8') as f:
        scenes = json.load(f)
    
    if scene_index >= len(scenes):
        return jsonify({"error": "Scene not found"}), 404
    
    scene = scenes[scene_index]
    devices = load_devices()
    results = []
    
    for action in scene.get('actions', []):
        device = None
        for dev in devices:
            if dev['id'] == action['device_id']:
                device = dev
                break
        if device:
            result = control_device(device, int(action['dp']), action['value'])
            results.append({
                "device_id": action['device_id'],
                "result": result
            })
    
    return jsonify({"success": True, "results": results})

@app.route('/api/scenes/<int:scene_index>', methods=['DELETE'])
def api_delete_scene(scene_index):
    scenes_file = Path(__file__).parent / "scenes.json"
    if not scenes_file.exists():
        return jsonify({"error": "No scenes found"}), 404
    
    with open(scenes_file, 'r', encoding='utf-8') as f:
        scenes = json.load(f)
    
    if scene_index >= len(scenes):
        return jsonify({"error": "Scene not found"}), 404
    
    scenes.pop(scene_index)
    with open(scenes_file, 'w', encoding='utf-8') as f:
        json.dump(scenes, f, indent=2, ensure_ascii=False)
    return jsonify({"success": True})

# ============================================================
# WebSocket Events
# ============================================================

@socketio.on('connect')
def handle_connect():
    devices = load_devices()
    for dev in devices:
        status = device_states.get(dev['id'], {"online": False, "dps": {}})
        emit('device_status', {
            'device_id': dev['id'],
            'status': status
        })

@socketio.on('request_status')
def handle_request_status(data):
    device_id = data.get('device_id')
    if device_id in device_states:
        emit('device_status', {
            'device_id': device_id,
            'status': device_states[device_id]
        })

# ============================================================
# Main
# ============================================================

if __name__ == '__main__':
    if not CONFIG_FILE.exists():
        save_devices([])
    
    # Auto-configure cloud if config exists
    if cloud_api.is_configured:
        print("  ☁️  Cloud API: Configured")
    else:
        print("  ☁️  Cloud API: Not configured (set in Settings)")
    
    # Start background polling
    poll_thread = threading.Thread(target=poll_devices, daemon=True)
    poll_thread.start()
    
    print("=" * 60)
    print("  🏠 Tuya Smart Home Controller v2")
    print("  📡 Local + Cloud API support")
    print("  🌐 Truy cập: http://localhost:5000")
    print("=" * 60)
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
