from flask import Flask, request, jsonify
import json
import os
import datetime

app = Flask(__name__)
DATA_FILE = 'licenses.json'

# --- โหลดข้อมูล Key ---
def load_licenses():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_licenses(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# --- API สำหรับเช็ค Key ---
@app.route('/api/verify', methods=['POST'])
def verify_license():
    data = request.json
    key = data.get('license_key')
    shop_name = data.get('shop_name')
    current_ip = request.headers.get('X-Forwarded-For', request.remote_addr) # รองรับ Cloudflare/Render
    
    licenses = load_licenses()
    
    # 1. เช็คว่ามี Key นี้ในระบบไหม?
    if key not in licenses:
        return jsonify({'valid': False, 'message': '❌ License Key ไม่ถูกต้อง!'})
    
    info = licenses[key]
    
    # 2. เช็คว่า Key โดนแบนไหม?
    if info.get('status') == 'banned':
         return jsonify({'valid': False, 'message': '🚫 Key นี้ถูกระงับการใช้งาน (Banned)'})

    # 3. กรณี Key ใหม่ (ยังไม่เคยใช้) -> ✅ ยอมให้ผ่าน และบันทึกเจ้าของ
    if info['status'] == 'unused':
        info['status'] = 'active'
        info['owner'] = shop_name  # ผูกชื่อร้าน
        info['ip'] = current_ip    # ผูก IP (เผื่อเช็ค)
        info['activated_date'] = str(datetime.datetime.now())
        
        save_licenses(licenses) # 💾 บันทึกทันที! (สำคัญมาก)
        return jsonify({'valid': True, 'message': '✅ ลงทะเบียนสำเร็จ!'})

    # 4. กรณี Key นี้ "ถูกใช้ไปแล้ว" (Active)
    if info['status'] == 'active':
        # เช็คว่าเป็นร้านเดิมเจ้าเดิมไหม? (เผื่อเขาลง Windows ใหม่)
        if info.get('owner') == shop_name:
            return jsonify({'valid': True, 'message': '✅ ยืนยันตัวตนสำเร็จ (Re-Login)'})
        else:
            # ❌ ถ้าคนละชื่อร้าน แสดงว่ามีคนแอบเอา Key ไปใช้ซ้ำ
            masked_owner = info.get('owner')[:3] + "***" if info.get('owner') else "Unknown"
            return jsonify({'valid': False, 'message': f'⚠️ Key นี้ถูกใช้ไปแล้ว โดยร้าน: {masked_owner}'})

    return jsonify({'valid': False, 'message': '⚠️ Error: สถานะ Key ไม่ถูกต้อง'})

@app.route('/')
def index():
    return "<h1>🔐 Blythe License Server is Running (Secured)</h1>"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)