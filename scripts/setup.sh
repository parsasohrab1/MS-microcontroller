#!/bin/bash
# اسکریپت راه‌اندازی محیط توسعه
# این اسکریپت محیط توسعه را برای تمام بخش‌های پروژه راه‌اندازی می‌کند

set -e  # در صورت خطا متوقف شود

echo "🚀 راه‌اندازی محیط توسعه سیستم نوروپلتفرم MS"
echo "================================================"

# بررسی Python
check_python() {
    echo "📦 بررسی Python..."
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        echo "✅ Python $PYTHON_VERSION نصب است"
    else
        echo "❌ Python 3 یافت نشد. لطفاً Python 3.9+ نصب کنید."
        exit 1
    fi
}

# راه‌اندازی Gateway Service
setup_gateway() {
    echo ""
    echo "📱 راه‌اندازی Gateway Service..."
    cd gateway/gateway-service
    
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        echo "✅ محیط مجازی ایجاد شد"
    fi
    
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    echo "✅ وابستگی‌های Gateway نصب شدند"
    
    deactivate
    cd ../..
}

# راه‌اندازی Cloud Backend
setup_backend() {
    echo ""
    echo "☁️  راه‌اندازی Cloud Backend..."
    cd cloud/backend
    
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        echo "✅ محیط مجازی ایجاد شد"
    fi
    
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    echo "✅ وابستگی‌های Backend نصب شدند"
    
    deactivate
    cd ../..
}

# راه‌اندازی ML Environment
setup_ml() {
    echo ""
    echo "🤖 راه‌اندازی ML Environment..."
    cd ml
    
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        echo "✅ محیط مجازی ایجاد شد"
    fi
    
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    echo "✅ وابستگی‌های ML نصب شدند"
    
    deactivate
    cd ..
}

# بررسی ابزارهای Firmware
check_firmware_tools() {
    echo ""
    echo "🔧 بررسی ابزارهای Firmware..."
    
    # بررسی CMake
    if command -v cmake &> /dev/null; then
        CMAKE_VERSION=$(cmake --version | head -n1 | cut -d' ' -f3)
        echo "✅ CMake $CMAKE_VERSION نصب است"
    else
        echo "⚠️  CMake یافت نشد. برای کامپایل Firmware نیاز است."
    fi
    
    # بررسی ARM GCC
    if command -v arm-none-eabi-gcc &> /dev/null; then
        GCC_VERSION=$(arm-none-eabi-gcc --version | head -n1)
        echo "✅ ARM GCC نصب است: $GCC_VERSION"
    else
        echo "⚠️  ARM GCC Toolchain یافت نشد. برای کامپایل Firmware نیاز است."
        echo "   دانلود از: https://developer.arm.com/tools-and-software/open-source-software/developer-tools/gnu-toolchain"
    fi
}

# ایجاد فایل‌های .env نمونه
create_env_files() {
    echo ""
    echo "📝 ایجاد فایل‌های .env نمونه..."
    
    # Gateway .env
    if [ ! -f "gateway/gateway-service/.env.example" ]; then
        cat > gateway/gateway-service/.env.example << EOF
# تنظیمات Gateway Service
BLE_SCAN_INTERVAL=5
CLOUD_API_URL=https://api.example.com
API_KEY=your_api_key_here
LOG_LEVEL=INFO
EOF
        echo "✅ فایل .env.example برای Gateway ایجاد شد"
    fi
    
    # Backend .env
    if [ ! -f "cloud/backend/.env.example" ]; then
        cat > cloud/backend/.env.example << EOF
# تنظیمات Backend
DATABASE_URL=postgresql://user:password@localhost:5432/ms_platform
REDIS_URL=redis://localhost:6379
SECRET_KEY=your_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
LOG_LEVEL=INFO
EOF
        echo "✅ فایل .env.example برای Backend ایجاد شد"
    fi
}

# اجرای توابع
main() {
    check_python
    setup_gateway
    setup_backend
    setup_ml
    check_firmware_tools
    create_env_files
    
    echo ""
    echo "================================================"
    echo "✅ راه‌اندازی محیط توسعه با موفقیت انجام شد!"
    echo ""
    echo "مراحل بعدی:"
    echo "1. فایل‌های .env.example را به .env کپی کنید و تنظیمات را پر کنید"
    echo "2. برای Gateway: cd gateway/gateway-service && source venv/bin/activate"
    echo "3. برای Backend: cd cloud/backend && source venv/bin/activate"
    echo "4. برای ML: cd ml && source venv/bin/activate"
    echo ""
    echo "برای اطلاعات بیشتر به DEVELOPMENT.md مراجعه کنید."
}

main

