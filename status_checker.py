import streamlit as st
import requests
import subprocess
import platform
import re

# ฟังก์ชันสำหรับเช็คสถานะ Website (HTTP Status)
def check_website(url):
    """ส่ง GET request ไปยัง URL และคืนค่า status code และ reason phrase."""
    try:
        # เพิ่ม http:// ถ้ายังไม่มี เพื่อให้ requests ทำงานได้ถูกต้อง
        if not url.startswith('http://') and not url.startswith('https://'):
            url = 'https://' + url
        
        response = requests.get(url, timeout=10) # กำหนด timeout 10 วินาที
        return response.status_code, response.reason
    except requests.ConnectionError:
        return None, "Connection Error"
    except requests.Timeout:
        return None, "Timeout"
    except requests.RequestException as e:
        return None, f"Error: {str(e)}"

# ฟังก์ชันสำหรับเช็ค Ping (ICMP)
def check_ping(host):
    """Ping ไปยัง Host (IP หรือ Domain) และคืนค่า True ถ้าสำเร็จ, False ถ้าไม่สำเร็จ."""
    # แยกเอาเฉพาะ domain/ip ออกมาจาก url
    host_only = re.sub(r'^https?:\/\/', '', host).split('/')[0]

    try:
        # กำหนด parameter ของคำสั่ง ping ตาม OS
        param = '-n' if platform.system().lower() == 'windows' else '-c'
        command = ['ping', param, '1', host_only]
        
        # ใช้ subprocess.run เพื่อไม่ให้แสดงผลลัพธ์ของ ping ใน terminal
        response = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5)
        
        # ถ้า returncode เป็น 0 หมายความว่า ping สำเร็จ
        return response.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False

# ----- หน้าตาของ Dashboard (UI) -----

st.set_page_config(page_title="Website Status Checker", page_icon="📡")

st.title('📡 Website & IP Status Checker')
st.caption('สร้างโดย Gemini')

st.write("""
ป้อนรายชื่อ Website หรือ IP Address ที่ต้องการตรวจสอบ โดยใส่หนึ่งชื่อต่อหนึ่งบรรทัด 
จากนั้นกดปุ่ม "เริ่มตรวจสอบ" เพื่อดูสถานะ
""")

# กล่องข้อความสำหรับใส่รายชื่อเป้าหมาย
targets_input = st.text_area(
    'ใส่ Website หรือ IP ที่นี่ (หนึ่งรายการต่อบรรทัด)', 
    height=150,
    value="google.com\nfacebook.com\n8.8.8.8\n192.168.1.255" # ตัวอย่าง
)

targets = [target.strip() for target in targets_input.split('\n') if target.strip()]

# ปุ่มสำหรับเริ่มการตรวจสอบ
if st.button('🚀 เริ่มตรวจสอบ'):
    if not targets:
        st.warning('กรุณาใส่ Website หรือ IP ที่ต้องการตรวจสอบ')
    else:
        st.subheader('ผลการตรวจสอบ:')
        progress_bar = st.progress(0)
        
        for i, target in enumerate(targets):
            with st.spinner(f'กำลังตรวจสอบ {target}...'):
                # ตรวจสอบ Ping
                is_pingable = check_ping(target)
                
                if is_pingable:
                    ping_status = "✅ Ping สำเร็จ"
                else:
                    ping_status = "❌ Ping ไม่สำเร็จ"

                # ตรวจสอบ Website Status (เฉพาะที่ไม่ใช่ IP Address)
                # เช็คง่ายๆ ว่ามีตัวอักษรหรือไม่
                if any(c.isalpha() for c in target):
                    status_code, reason = check_website(target)
                    if status_code:
                        if 200 <= status_code < 300:
                            http_status = f"✅ Website Online (Code: {status_code} {reason})"
                        else:
                            http_status = f"⚠️ Website มีปัญหา (Code: {status_code} {reason})"
                    else:
                        http_status = f"❌ Website Offline ({reason})"
                else:
                    # ถ้าเป็น IP จะไม่เช็ค HTTP
                    http_status = "⚪️ (เป็น IP Address)"

            # แสดงผลลัพธ์
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**{target}**")
            with col2:
                st.write(f"{ping_status} | {http_status}")

            # อัปเดต Progress Bar
            progress_bar.progress((i + 1) / len(targets))
        
        st.success('ตรวจสอบเสร็จสิ้น!')
        st.balloons()