from flask import Flask, request, jsonify
import json
import os
import datetime

app = Flask(__name__)
DATA_FILE = 'licenses.json'

# --- โหลดข้อมูล Key ---
def load_licenses():
    if not os.path.exists(DATA_FILE):
        # สร้างไฟล์ตัวอย่างถ้ายังไม่มี
        default_data = {
            "VIP-001": {"status": "unused", "type": "lifetime", "owner": None},
            "DEMO-888": {"status": "unused", "type": "trial", "owner": None}
        }
        with open(DATA_FILE, 'w') as f: json.dump(default_data, f, indent=4)
        return default_data
    
    with open(DATA_FILE, 'r') as f: return json.load(f)

def save_licenses(data):
    with open(DATA_FILE, 'w') as f: json.dump(data, f, indent=4)

# --- API สำหรับเช็ค Key (ลูกค้าจะยิงมาที่นี่) ---
@app.route('/api/verify', methods=['POST'])
def verify_license():
    key = request.json.get('license_key')
    shop_name = request.json.get('shop_name')
    
    licenses = load_licenses()
    
    if key not in licenses:
        return jsonify({'valid': False, 'message': '❌ License Key ไม่ถูกต้อง!'})
    
    info = licenses[key]
    
    if info['status'] == 'banned':
         return jsonify({'valid': False, 'message': '🚫 Key นี้ถูกระงับการใช้งาน'})

    # ถ้า Key ยังว่าง -> ทำการผูกกับร้านนี้เลย
    if info['status'] == 'unused':
        info['status'] = 'active'
        info['owner'] = shop_name
        info['activated_date'] = str(datetime.datetime.now())
        save_licenses(licenses)
        return jsonify({'valid': True, 'message': '✅ ลงทะเบียนสำเร็จ! ขอบคุณที่อุดหนุนครับ'})

    # ถ้า Key ถูกใช้แล้ว -> เช็คว่าเป็นร้านเดิมไหม
    if info['status'] == 'active':
        # (ในอนาคตอาจเช็ค Hardware ID เพิ่มเติมได้ เพื่อกันเอาไปลงหลายเครื่อง)
        return jsonify({'valid': True, 'message': '✅ ยืนยันสิทธิ์เรียบร้อย'})
        
    return jsonify({'valid': False, 'message': '⚠️ เกิดข้อผิดพลาด'})

@app.route('/')
def index():
    return "<h1>🔐 Blythe License Server is Running...</h1>"

if __name__ == '__main__':
    # รันพอร์ต 8080 (คนละพอร์ตกับ Dashboard ลูกค้า)
    app.run(host='0.0.0.0', port=8080, debug=True)