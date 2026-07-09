# ตั้งค่า GitHub Actions ให้ส่งรายงานเข้า Discord

โปรเจกต์นี้มี workflow พร้อมใช้งานอยู่แล้วที่ `.github/workflows/00-daily-analysis.yml`
โดยจะรันอัตโนมัติวันจันทร์ถึงศุกร์เวลา 10:00 UTC หรือ 17:00 น. เวลาไทย และสามารถกดรันเองได้จากหน้า Actions

## 1. เอาโปรเจกต์ขึ้น GitHub

วิธีง่ายที่สุดคือกด Fork จาก repo ต้นทาง:

https://github.com/ZhuLinsen/daily_stock_analysis

หรือถ้าจะใช้โฟลเดอร์นี้ push ไป repo ของคุณเอง:

```powershell
git remote set-url origin https://github.com/<your-user>/<your-repo>.git
git push -u origin main
```

## 2. สร้าง Discord Webhook

ใน Discord ไปที่:

`Server Settings` -> `Integrations` -> `Webhooks` -> `New Webhook`

เลือก channel ที่ต้องการรับรายงาน แล้ว copy Webhook URL ที่หน้าตาประมาณนี้:

```text
https://discord.com/api/webhooks/xxxxxxxx/yyyyyyyy
```

## 3. ตั้งค่า GitHub Secrets

ไปที่ repo ของคุณบน GitHub:

`Settings` -> `Secrets and variables` -> `Actions` -> `New repository secret`

เพิ่มอย่างน้อย:

| Name | Value |
| --- | --- |
| `DISCORD_WEBHOOK_URL` | Discord Webhook URL |
| `GEMINI_API_KEY` หรือ `OPENAI_API_KEY` หรือ `DEEPSEEK_API_KEY` | API key ของ LLM ที่จะใช้ |

ถ้าใช้ OpenAI-compatible provider ให้ตั้งเพิ่มตาม provider:

| Name | Type | Value |
| --- | --- | --- |
| `OPENAI_BASE_URL` | Variable หรือ Secret | base URL ของ provider |
| `OPENAI_MODEL` | Variable | model name |

## 4. ตั้งค่า GitHub Variables

ไปที่:

`Settings` -> `Secrets and variables` -> `Actions` -> `Variables` -> `New repository variable`

ค่าขั้นต่ำที่แนะนำ:

| Name | Value ตัวอย่าง |
| --- | --- |
| `STOCK_LIST` | `AAPL,MSFT,NVDA` |
| `NOTIFICATION_REPORT_CHANNELS` | `discord` |
| `ANALYSIS_TIMEOUT_MINUTES` | `30` |

ถ้าต้องการหุ้นไทย/ตลาดอื่น ให้ใส่ตามรูปแบบที่โปรเจกต์รองรับในเอกสารต้นทาง

## 5. เปิดและทดสอบ Actions

1. ไปที่แท็บ `Actions`
2. ถ้า GitHub ถาม ให้กด enable workflows
3. เลือก workflow `每日股票分析`
4. กด `Run workflow`
5. เลือก `force_run = true` สำหรับทดสอบนอกวัน/เวลาตลาด

ถ้าสำเร็จ รายงานจะถูกส่งเข้า Discord channel ที่ผูก webhook ไว้

## หมายเหตุ

- GitHub Pages ใช้กับโปรเจกต์นี้ไม่ได้ เพราะนี่เป็น Python workflow/backend ไม่ใช่ static site
- Webhook URL ต้องเก็บใน Secrets เท่านั้น อย่า commit ลงไฟล์
- ถ้า workflow รันผ่านแต่ Discord ไม่ได้รับ ให้เช็กว่า `NOTIFICATION_REPORT_CHANNELS=discord` และ `DISCORD_WEBHOOK_URL` ถูกต้อง
