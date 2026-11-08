# รายงานการดาวน์โหลดภาพ — บทที่ 1: มอเอง; ความลับแห่งวงล้อเวลาใหญ่

สภาพแวดล้อม: sandbox (Talk) ซึ่ง `bash` เข้าถึงเฉพาะโดเมน `github.*` เท่านั้น `upload.wikimedia.org`、`thumb.wikimedia.org`、`raw.githubusercontent.com` และเว็บไซต์พิพิธภัณฑ์ (Met, British Museum, Bodleian, NASA ฯลฯ) ถูกบล็อกทั้งหมด `fetch_page` เข้าถึงหน้า HTML และ API ของวิกิมีเดียคอมมอนส์ได้ แต่คืนค่า HTTP 500 เมื่อขอ URL รูปภาพโดยตรง

ดังนั้น **ไม่มีไฟล์ภาพใดถูกดาวน์โหลดในสภาพแวดล้อมนี้** และไม่มีไฟล์ปลอมถูกสร้างขึ้นแต่อย่างใด

---

## H01 — วงล้ออันติกีเธรา (รหัส H01, บทที่ 1)

### การค้นหา
- คำค้นหลัก: `"Antikythera mechanism Fragment A original museum photograph"`
- คำค้นสำรอง 1: `"National Archaeological Museum Athens Antikythera gear fragment"`
- คำค้นสำรอง 2: `"Antikythera Mechanism NAMA 2017 Peulle Wikimedia Commons"`
- ผลที่พบ: `File:Antikythera Mechanism (NAMA) 2017.jpg` บน Wikimedia Commons

### แหล่งที่มาเลือก
- เหตุผล: เป็นภาพถ่ายจริงของชิ้นส่วนต้นฉบับกลไกอันติกีเธรา (Fragment A) แสดงฟันเฟือง สนิม และข้อความภาษากรีก มาจากพิพิธภัณฑ์โบราณคดีแห่งชาติ เอเธนส์ (NAMA) ตรงตามเกณฑ์ทั้งหมดของบทที่ 1
- ไม่เลือก: รีเอนเดอร์จำลองเครื่องทั้งหมด, whatnot モเดลสมัยใหม่, หรือภาพตกแต่งที่ไม่เกี่ยวข้อง

### ลิงก์
- หน้าหลักฐานต้นทาง: https://commons.wikimedia.org/wiki/File:Antikythera_Mechanism_(NAMA)_2017.jpg
- ลิงก์ไฟล์ภาพโดยตรง: https://upload.wikimedia.org/wikipedia/commons/6/63/Antikythera_Mechanism_%28NAMA%29_2017.jpg

### ผลการดาวน์โหลดและเปิดไฟล์
- สถานะ: `failed_download` — ไม่สามารถดาวน์โหลดไบนารีจาก sandbox (HTTP 000 / SSL_ERROR_SYSCall)
- ไม่มีไฟล์ถูกสร้างใน `book/chapters/ch01/images/historical/`

### ขนาดจริงและลิขสิทธิ์
- รูปแบบ: JPEG (ยืนยันจาก Commons API)
- ขนาด: 4928 × 3264 พิกเซล, 8,428,364 ไบต์ (8.43 MB)
- ลิขสิทธิ์: CC BY-SA 4.0 (ต้องแสดงเครดิต, ShareAlike)
- ผู้สร้าง: Peulle
- วันที่สร้าง: 22 กันยายน 2017
- พิพิธภัณฑ์: พิพิธภัณฑ์โบราณคดีแห่งชาติ เอเธนส์ (NAMA)

### การยืนยัน
- ยืนยันผ่าน Commons API (`action=query&prop=imageinfo&iiprop=url|size|extmetadata`) แล้ว
- ต้องดาวน์โหลดด้วยตนเองจากเครื่องที่มีอินเทอร์เน็ตเต็มรูปแบบ แล้วนำมาใส่ในโฟลเดอร์นี้ด้วยชื่อ `H01_CH01_antikythera-mechanism.jpg`

---

## H45 — แผนที่ดาวดันหว่าง (รหัส H45, บทที่ 1)

### การค้นหา
- คำค้นหลัก: `"Dunhuang star chart Or.8210 S.3326 British Library"`
- คำค้นสำรอง 1: `"Dunhuang manuscript star atlas Tang dynasty"`
- คำค้นสำรอง 2: `"International Dunhuang Programme S.3326 star chart"`
- ผลที่พบ: `File:Dunhuang star map.jpg` (Wikimedia Commons), `File:Dunhuang Star Chart BLX273 OR8210S3326R2 8.jpg`, `Dunhuang Star Atlas - complete.jpg`

### แหล่งที่มาเลือก
- เหตุผล: `Dunhuang star map.jpg` แสดงรายละเอียดของแผนที่ดาวดันหว่าง (British Library Or.8210/S.3326) รวมถึงกลุ่มดาวและเส้นภาพกลุ่มดาว ต้นฉบับยุคราชวงศ์ถัง (~ค.ศ. 700) ถูก digitaliz โดย International Dunhuang Project (IDP)
- ข้อจำกัด: ความกว้าง 2128 พิกเซล ต่ำกว่าเกณฑ์ขั้นต่ำ 2400 พิกเซล แต่สูงกว่า 1600 พิกเซล ยอมรับได้กับเหตุผลที่บันทึกไว้ เนื่องจากไม่พบเวอร์ชันความละเอียดสูงกว่าที่ดาวน์โหลดได้จาก sandbox

### ลิงก์
- หน้าหลักฐานต้นทาง: https://commons.wikimedia.org/wiki/File:Dunhuang_star_map.jpg
- ลิงก์ไฟล์ภาพโดยตรง: https://upload.wikimedia.org/wikipedia/commons/4/42/Dunhuang_star_map.jpg

### ผลการดาวน์โหลดและเปิดไฟล์
- สถานะ: `failed_download` — ไม่สามารถดาวน์โหลดไบนารีจาก sandbox เช่นเดียวกัน
- ไม่มีไฟล์ถูกสร้าง

### ขนาดจริงและลิขสิทธิ์
- รูปแบบ: JPEG
- ขนาด: 2128 × 2136 พิกเซล, 1,206,902 ไบต์ (1.21 MB)
- ลิขสิทธิ์: สาธารณสมบัติ (Public Domain, PD-old-100-expired / CC-PD-Mark) — ไม่ต้องแสดงเครดิตบังคับ
- ผู้สร้าง: ไม่ระบุ / ไม่ทราบชื่อ (สแกนจากคัมภีร์โบราณ)
- แหล่งที่มา: British Library Or.8210/S.3326 (ผ่าน IDP)

### การยืนยัน
- ยืนยันผ่าน Commons API แล้ว
- ต้องดาวน์โหลดด้วยตนเอง แล้วนำมาใส่ด้วยชื่อ `H45_CH01_dunhuang-star-chart.jpg`

---

## H46 — หน้าปัดนาฬิกาดาราศาสตร์ปรกร (รหัส H46, บทที่ 1)

### การค้นหา
- คำค้นหลัก: `"Prague astronomical clock Orloj astronomical dial photograph"`
- คำค้นสำรอง 1: `"Praha Astronomical Clock Dial 01 Uoaei1 Wikimedia Commons"`
- คำค้นสำรอง 2: `"Old Town Hall Prague astronomical clock dial high resolution"`
- ผลที่พบ: `File:Praha Astronomical Clock Dial 01.jpg` (Wikimedia Commons, featured image)

### แหล่งที่มาเลือก
- เหตุผล: เป็นภาพถ่ายหน้าปัดดาราศาสตร์ของนาฬิกาดาราศาสตร์ปรกร (Orloj) มุมมองตรง ชัดเจน ไม่มีผู้คนเบียดเสียด มีป้ายกำกับและวงแหวนเวลา อัปโหลดโดย Uoaei1 วันที่ 1 พฤษภาคม 2017 ประเมินคุณภาพเป็น featured image บน Wikimedia Commons
- ไม่เลือก: ภาพทั่วไปของจัตุรัสที่นาฬิกาเล็กเกินไป, ภาพตกแต่ง, หรือรีเอนเดอร์

### ลิงก์
- หน้าหลักฐานต้นทาง: https://commons.wikimedia.org/wiki/File:Praha_Astronomical_Clock_Dial_01.jpg
- ลิงก์ไฟล์ภาพโดยตรง: https://upload.wikimedia.org/wikipedia/commons/4/43/Praha_Astronomical_Clock_Dial_01.jpg

### ผลการดาวน์โหลดและเปิดไฟล์
- สถานะ: `failed_download` — ไม่สามารถดาวน์โหลดไบนารีจาก sandbox (HTTP 000 / SSL_ERROR_SYSCall)
- ไม่มีไฟล์ถูกสร้าง

### ขนาดจริงและลิขสิทธิ์
- รูปแบบ: JPEG (ยืนยันจาก Commons API)
- ขนาด: 5221 × 3481 พิกเซล, 11,384,838 ไบต์ (11.38 MB)
- ลิขสิทธิ์: CC BY-SA 4.0 (ต้องแสดงเครดิต, ShareAlike)
- ผู้สร้าง: Uoaei1
- วันที่สร้าง: 1 พฤษภาคม 2017
- สถานที่: Old Town Hall, Prague, Czech Republic (พิกัด 50.086817°N, 14.420822°E)

### การยืนยัน
- ยืนยันผ่าน Commons API (`action=query&prop=imageinfo&iiprop=url|size|extmetadata`) แล้ว
- ต้องดาวน์โหลดด้วยตนเองจากเครื่องที่มีอินเทอร์เน็ตเต็มรูปแบบ แล้วนำมาใส่ในโฟลเดอร์นี้ด้วยชื่อ `H46_CH01_prague-astronomical-clock.jpg`

---

## สรุปสถานะทั้งหมด

| รหัส | ชื่อไฟล์เป้าหมาย | download_status | สาเหตุ |
|------|-------------------|-----------------|---------|
| H01 | H01_CH01_antikythera-mechanism.jpg | failed_download | upload.wikimedia.org ถูกบล็อกจาก sandbox; fetch_page คืนค่า HTTP 500 |
| H45 | H45_CH01_dunhuang-star-chart.jpg | failed_download | เหตุผลเดียวกันกับ H01 |
| H46 | H46_CH01_prague-astronomical-clock.jpg | failed_download | เหตุผลเดียวกันกับ H01 |

## ขั้นตอนถัดไป (ต้องดำเนินการนอก sandbox)

1. ใช้เครื่องที่มีการเชื่อมต่ออินเทอร์เน็ตเต็มรูปแบบ
2. ดาวน์โหลดไฟล์จาก `image_file_url` ใน `image-manifest.csv` สำหรับแต่ละรหัส
3. ตรวจสอบรูปแบบไฟล์ ขนาดพิกเซล และขนาดไฟล์จากตัวไฟล์จริง (เช่น ด้วยคำสั่ง `identify` หรือ Python PIL)
4. คำนวณ sha256 และบันทึกลงใน `image-manifest.csv`
5. เปลี่ยน `download_status` เป็น `downloaded_verified_locally` เมื่อยืนยันแล้ว
6. วางไฟล์ภาพในโฟลเดอร์ `book/chapters/ch01/images/historical/` ด้วยชื่อที่ระบุไว้

**หมายเหตุ:** ไม่มีภาพใดถูกทำเครื่องหมายว่า “ลงทะเบียนแล้ว” (final approval) การตรวจสอบขั้นสุดท้ายอยู่กับผู้ใช้งาน