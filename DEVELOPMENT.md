# راهنمای توسعه سیستم نوروپلتفرم MS

## پیش‌نیازها

### برای توسعه Firmware (میکروکنترلر)

1. **ابزارهای کامپایل:**
   - ARM GCC Toolchain
   - CMake 3.20+
   - nRF5 SDK (Nordic Semiconductor)

2. **سخت‌افزار:**
   - nRF52840 Development Kit
   - Programmer/Debugger (J-Link یا nRF Connect)

3. **نرم‌افزار:**
   - VS Code با افزونه‌های C/C++
   - یا Keil/IAR (اختیاری)

### برای توسعه Gateway

1. **Python 3.9+**
2. **pip** یا **conda**
3. **Android Studio** (برای توسعه Android)
4. **Xcode** (برای توسعه iOS - فقط macOS)

### برای توسعه Cloud Backend

1. **Python 3.10+**
2. **PostgreSQL 14+**
3. **Redis** (برای کش)
4. **Docker** و **Docker Compose**

### برای توسعه ML

1. **Python 3.10+**
2. **CUDA Toolkit** (برای GPU - اختیاری)
3. **Jupyter Lab**

## راه‌اندازی محیط توسعه

### 1. کلون کردن پروژه

```bash
git clone <repository-url>
cd MS-microcontroller
```

### 2. راه‌اندازی Firmware

```bash
cd firmware
mkdir build
cd build
cmake ..
make
```

### 3. راه‌اندازی Gateway Service

```bash
cd gateway/gateway-service
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 4. راه‌اندازی Cloud Backend

```bash
cd cloud/backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# راه‌اندازی پایگاه داده
docker-compose up -d postgres redis

# اجرای مایگریشن‌ها
alembic upgrade head
```

### 5. راه‌اندازی ML Environment

```bash
cd ml
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# راه‌اندازی Jupyter
jupyter lab
```

## ساختار کدنویسی

### Firmware (C/C++)

- از استاندارد C11/C++17 استفاده کنید
- نام‌گذاری: `snake_case` برای توابع و متغیرها
- کامنت‌گذاری: Doxygen style
- هر فایل باید شامل header با توضیحات باشد

### Python

- از PEP 8 پیروی کنید
- Type hints استفاده کنید
- Docstrings برای تمام توابع
- از `black` برای فرمت کردن استفاده کنید

## تست

### تست Firmware

```bash
cd firmware
mkdir build-test
cd build-test
cmake -DTESTING=ON ..
make
ctest
```

### تست Gateway

```bash
cd gateway/gateway-service
pytest
```

### تست Backend

```bash
cd cloud/backend
pytest
```

## Git Workflow

### Branching Strategy

- `main`: کد پایدار و تست شده
- `develop`: شاخه توسعه اصلی
- `feature/*`: ویژگی‌های جدید
- `bugfix/*`: رفع باگ‌ها
- `release/*`: آماده‌سازی برای انتشار

### Commit Messages

از فرمت زیر استفاده کنید:

```
<type>(<scope>): <subject>

<body>

<footer>
```

انواع:
- `feat`: ویژگی جدید
- `fix`: رفع باگ
- `docs`: تغییرات مستندات
- `style`: تغییرات فرمت
- `refactor`: بازسازی کد
- `test`: اضافه کردن تست
- `chore`: کارهای نگهداری

## CI/CD

پایپ‌لاین CI/CD شامل:

1. **Lint و Format Check**
2. **Unit Tests**
3. **Integration Tests**
4. **Build**
5. **Deploy** (در صورت موفقیت)

## Debugging

### Firmware

- استفاده از GDB با J-Link
- Serial logging
- LED indicators برای وضعیت

### Python

- استفاده از `pdb` یا `ipdb`
- Logging با `loguru`
- Profiling با `cProfile`

## منابع مفید

- [nRF5 SDK Documentation](https://infocenter.nordicsemi.com/)
- [TinyML Documentation](https://www.tinyml.org/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [ISO 13485 Guide](https://www.iso.org/standard/59752.html)

## تماس و پشتیبانی

برای سوالات و مشکلات:
- Issue tracker در GitLab/GitHub
- تیم توسعه

