# PKS_SERVICE

บริการ Backend (API Server) สำหรับระบบของ **PKSOFTTECH.ORG** พัฒนาด้วย **FastAPI** รองรับการทำงานหลายด้าน เช่น ระบบจัดการที่จอดรถ (Parking), การอ่านป้ายทะเบียนรถ (LPR - License Plate Recognition), การแจ้งเตือนผ่าน LINE, การรับส่งข้อความผ่าน MQTT และ WebSocket รวมถึงการชำระเงินผ่าน Stripe

---

## 🚀 Features

- **REST API** ด้วย FastAPI (อัตโนมัติ Swagger UI ที่ `/docs`)
- **WebSocket** สำหรับการส่งข้อความแบบ Real-time
- **License Plate Recognition (LPR)** ด้วย PaddleOCR และ Gemini Vision
- **MQTT Integration** สำหรับอุปกรณ์ IoT
- **LINE Notify** สำหรับการแจ้งเตือน
- **Stripe Payment** integration
- **JWT Authentication** (HS256)
- **CORS Middleware** (เปิดทุก origin)
- **Process-time middleware** สำหรับวัดประสิทธิภาพ
- **Jinja2 Templates** สำหรับหน้าเว็บ UI
- **Scheduler (APScheduler)** สำหรับ background tasks
- **Docker support** พร้อม image ที่ optimize แล้ว

---

## 📋 Requirements

- **Python** 3.11+
- **Docker** (optional - สำหรับรันใน container)
- **System packages** (สำหรับ PaddleOCR / OpenCV):
  - `libgl1`
  - `libglib2.0-0`
  - `libgomp1`

---

## 🛠️ Installation

### 1. Clone Repository

```bash
git clone <repository-url>
cd PKS_SERVICE
```

### 2. สร้าง Virtual Environment (แนะนำ)

```bash
python3 -m venv .venv
source .venv/bin/activate   # Linux / macOS
# .venv\Scripts\activate    # Windows
```

### 3. ติดตั้ง Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. ตั้งค่า Environment Variables

สร้างไฟล์ `.env` ที่ root ของโปรเจค:

```env
# Gemini API (สำหรับ LPR Service)
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-1.5-flash

# JWT (ถ้าต้องการ override ค่า default)
```

---

## 🐳 Docker

### Build Image

```bash
docker build -t pks-service .
```

### Run Container

```bash
docker run -d \
  --name pks-service \
  -p 8000:8000 \
  --env-file .env \
  pks-service
```

เข้าใช้งานได้ที่ `http://localhost:8000`

---

## ▶️ Running

### Development Mode (Auto-reload)

```bash
python start_server.py
```

Server จะรันที่: **http://0.0.0.0:8000**

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health check: http://localhost:8000/ping

### Production Mode

แก้ไขใน `start_server.py` เปลี่ยน `reload=True` เป็น `reload=False` และเพิ่มจำนวน workers ตามต้องการ:

```python
uvicorn.run(
    "app.main:app",
    host="0.0.0.0",
    port=8000,
    workers=4,
    reload=False,
    log_level=logging.INFO,
)
```

---

## 📂 Project Structure

```
PKS_SERVICE/
├── app/                              # Application source code
│   ├── main.py                       # FastAPI app entry point (lifespan, middleware, routers)
│   ├── stdio.py                      # Custom debug/print utilities (colored logs)
│   ├── core/                         # Core configuration & utilities
│   │   ├── config.py                 # App-level constants (APP_TITLE, JWT settings)
│   │   └── utility.py                # Helper functions
│   ├── routes/                       # API endpoints (routers)
│   │   ├── api.py                    # Public REST endpoints (LINE Notify, Stripe, Pages)
│   │   ├── api_lpr_service.py        # License Plate Recognition endpoints
│   │   └── websocket.py              # WebSocket connection manager (/ws)
│   └── service/                      # Background services
│       └── mqtt_service.py           # MQTT client + APScheduler jobs
├── templates/                        # Jinja2 HTML templates (server-rendered pages)
│   ├── home.html
│   ├── login.html
│   ├── pks_parking.html
│   ├── pks_dev.html
│   ├── qpks.html
│   ├── system_config.html
│   ├── transection_report.html
│   ├── 403.html
│   └── 404.html
├── static/                           # Static files (CSS, JS, images)
├── start_server.py                   # Uvicorn entry script (debug logging)
├── requirements.txt                  # Python dependencies
├── Dockerfile                        # Docker image definition
├── .dockerignore                     # Docker build exclusions
├── .gitignore                        # Git exclusions
├── main.css                          # Stylesheet
├── tailwind.config.js                # Tailwind config
├── pymakr.conf                       # PyMakr (VSCode) device config
├── applog.log                        # Application runtime log
└── README.md                         # เอกสารนี้
```

---

## 🔌 API Endpoints

### Public APIs (`app/routes/api.py`)

| Method | Endpoint           | Description                                                       |
| ------ | ------------------ | ----------------------------------------------------------------- |
| GET    | `/`              | Redirect ไปยัง`/docs`                                      |
| GET    | `/ping`          | Health check (returns current datetime)                           |
| GET    | `/page_404`      | หน้า 404 (Jinja2 template)                                    |
| POST   | `/line/notify`   | ส่งแจ้งเตือนผ่าน LINE Notify                      |
| POST   | `/stripe/charge` | สร้างรายการชำระเงินผ่าน Stripe (PromptPay) |

### LPR Service (`app/routes/api_lpr_service.py`)

| Method | Endpoint                | Description                                               |
| ------ | ----------------------- | --------------------------------------------------------- |
| POST   | `/lpr/lpr_read_plate` | อ่านป้ายทะเบียนจากภาพ (image upload) |

- รองรับไฟล์ภาพสูงสุด **5 MB**
- ใช้ **PaddleOCR** (ภาษาไทย) และ **Gemini Vision API**
- Response schema: `license_plate`, `province`, `confidence_score`

### WebSocket (`app/routes/websocket.py`)

| Endpoint | Description                                                   |
| -------- | ------------------------------------------------------------- |
| `/ws`  | WebSocket connection สำหรับ broadcast / targeted notify |

### MQTT Service (`app/service/mqtt_service.py`)

- **Broker**: `broker.hivemq.com:1883` (default)
- **Subscribe topic**: `/pks_mqtt/server/#`
- **Publish topic**: `/pks_mqtt/device/broadcast`
- **Background job**: publish heartbeat ทุก 60 วินาที (ผ่าน APScheduler)

> ค่า MQTT broker/port/topics สามารถแก้ไขได้ที่ `app/service/mqtt_service.py`

---

## ⚙️ Configuration

ไฟล์คอนฟิกหลัก: `app/core/config.py`

```python
APP_TITLE = "PKS_LPR"
API_SECRET_KEY = "pksofttech@gmail.com"   # JWT secret
API_ALGORITHM = "HS256"
API_ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 8  # 8 hours
IMAGE_MAX_SIZE = (200, 200)
```

แนะนำให้ย้าย secrets ไปอยู่ใน **environment variables** สำหรับ production

---

## 📦 Tech Stack

| Layer         | Technology                        |
| ------------- | --------------------------------- |
| Web Framework | FastAPI 0.139 + Starlette 0.46    |
| ASGI Server   | Uvicorn 0.50                      |
| Validation    | Pydantic 2.x                      |
| ORM / Models  | SQLModel 0.0.39 + SQLAlchemy      |
| Auth          | PyJWT + passlib[bcrypt]           |
| HTTP Client   | httpx 0.28                        |
| MQTT          | paho-mqtt + APScheduler           |
| WebSocket     | FastAPI native WebSocket          |
| Image / OCR   | Pillow + PaddleOCR (paddlepaddle) |
| AI Vision     | Google Gemini (via REST)          |
| Templates     | Jinja2                            |
| CSS           | Tailwind CSS                      |
| Container     | Docker (python:3.11-slim)         |

---

## 🧪 Development Notes

- **Debug logging** — `app/stdio.py` ให้ logger แบบมีสี (`print_debug`, `print_success`, `print_warning`, `print_error`) ใช้ `PrintDebug`
- **PaddleOCR** — ปิด MKLDNN ผ่าน `FLAGS_use_mkldnn=0` ที่ `app/routes/api_lpr_service.py` เพื่อหลีกเลี่ยง `NotImplementedError` บน CPU
- **VSCode + PyMakr** — ไฟล์ `pymakr.conf` รองรับการ deploy/remote debug ผ่าน PyMakr extension
- **MQTT reconnect** — ปัจจุบัน reconnect logic เป็นพื้นฐาน ควรเพิ่ม retry/exp backoff หากใช้ใน production
- **CORS** — เปิด `allow_origins=["*"]` เหมาะสำหรับ development ควรจำกัด origin ใน production

---

## 🛣️ Roadmap / TODO

- [ ] ย้าย secrets ทั้งหมดไปอยู่ใน environment variables
- [ ] เพิ่ม `pytest` สำหรับ unit/integration tests
- [ ] เพิ่ม CI/CD pipeline (GitHub Actions)
- [ ] เพิ่ม MQTT reconnect / health check
- [ ] เพิ่ม rate-limiting middleware
- [ ] จำกัด CORS origins ใน production
- [ ] เพิ่ม health endpoint (`/healthz`) แบบ dependency-aware
- [ ] Logging structured (JSON) สำหรับ production

---

## 📝 License

Internal project — © PKSOFTTECH.ORG

---

## 👥 Maintainer

**PKSOFTTECH.ORG** — [pksofttech@gmail.com](mailto:pksofttech@gmail.com)
