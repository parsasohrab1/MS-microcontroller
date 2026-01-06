cmake_minimum_required(VERSION 3.20)
project(MS_Neuroplatform_Firmware C CXX ASM)

# تنظیمات کامپایلر
set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)

# مسیرهای اصلی
set(FIRMWARE_ROOT ${CMAKE_CURRENT_SOURCE_DIR})
set(SOURCE_DIR ${FIRMWARE_ROOT}/src)
set(INCLUDE_DIR ${FIRMWARE_ROOT}/include)

# تنظیمات nRF52840
set(CPU_FLAGS "-mcpu=cortex-m4 -mthumb -mfloat-abi=hard -mfpu=fpv4-sp-d16")

# TODO: اضافه کردن تنظیمات SDK nRF5
# TODO: اضافه کردن کتابخانه‌های مورد نیاز

# فایل‌های منبع
file(GLOB_RECURSE SOURCES
    "${SOURCE_DIR}/*.c"
    "${SOURCE_DIR}/*.cpp"
    "${SOURCE_DIR}/system/power_management.c"
    "${SOURCE_DIR}/system/hardware_accelerators.c"
    "${SOURCE_DIR}/system/dma_manager.c"
    "${SOURCE_DIR}/system/parallel_processor.c"
    "${SOURCE_DIR}/signal_processing/optimized_filters.c"
    "${SOURCE_DIR}/ml/optimized_prediction.c"
    "${SOURCE_DIR}/storage/data_compression.c"
    "${SOURCE_DIR}/storage/data_streaming.c"
    "${SOURCE_DIR}/storage/external_flash.c"
    "${SOURCE_DIR}/security/secure_boot.c"
    "${SOURCE_DIR}/security/fota.c"
    "${SOURCE_DIR}/security/hsm.c"
    "${SOURCE_DIR}/security/anti_tampering.c"
)

# فایل‌های هدر
file(GLOB_RECURSE HEADERS
    "${SOURCE_DIR}/*.h"
    "${INCLUDE_DIR}/*.h"
    "${SOURCE_DIR}/system/power_management.h"
    "${SOURCE_DIR}/system/hardware_accelerators.h"
    "${SOURCE_DIR}/system/dma_manager.h"
    "${SOURCE_DIR}/system/parallel_processor.h"
    "${SOURCE_DIR}/signal_processing/optimized_filters.h"
    "${SOURCE_DIR}/ml/optimized_prediction.h"
    "${SOURCE_DIR}/storage/data_compression.h"
    "${SOURCE_DIR}/storage/data_streaming.h"
    "${SOURCE_DIR}/storage/external_flash.h"
    "${SOURCE_DIR}/storage/optimized_data_structures.h"
    "${SOURCE_DIR}/security/secure_boot.h"
    "${SOURCE_DIR}/security/fota.h"
    "${SOURCE_DIR}/security/hsm.h"
    "${SOURCE_DIR}/security/anti_tampering.h"
)

# ایجاد executable
add_executable(${PROJECT_NAME}.elf ${SOURCES} ${HEADERS})

# تنظیمات کامپایلر
target_compile_options(${PROJECT_NAME}.elf PRIVATE
    ${CPU_FLAGS}
    -Wall
    -Wextra
    -Werror
    -Os
)

target_include_directories(${PROJECT_NAME}.elf PRIVATE
    ${SOURCE_DIR}
    ${INCLUDE_DIR}
)

# TODO: اضافه کردن لینک به کتابخانه‌های nRF SDK

