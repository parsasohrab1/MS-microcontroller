#!/bin/bash
# اسکریپت ساخت Firmware

set -e

BUILD_TYPE=${1:-Release}
BUILD_DIR="firmware/build"

echo "🔨 ساخت Firmware (نوع: $BUILD_TYPE)"
echo "======================================"

# ایجاد پوشه build
mkdir -p $BUILD_DIR
cd $BUILD_DIR

# اجرای CMake
echo "📋 پیکربندی با CMake..."
cmake -DCMAKE_BUILD_TYPE=$BUILD_TYPE ../

# کامپایل
echo "⚙️  کامپایل..."
make -j$(nproc)

echo ""
echo "✅ ساخت با موفقیت انجام شد!"
echo "فایل خروجی: $BUILD_DIR/firmware.elf"

