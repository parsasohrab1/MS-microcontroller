# راهنمای نصب و راه‌اندازی FreeRTOS

## وضعیت فعلی

✅ **فایل‌های RTOS ایجاد شده:**
- `include/FreeRTOSConfig.h` - تنظیمات FreeRTOS
- `src/system/rtos_tasks.h` - تعریف tasks و structures
- `src/system/rtos_tasks.c` - پیاده‌سازی tasks
- `src/main.c` - به‌روزرسانی شده برای استفاده از RTOS

⏳ **نیاز به انجام:**
- نصب FreeRTOS
- به‌روزرسانی CMakeLists.txt
- تست و اعتبارسنجی

---

## مراحل نصب

### روش 1: استفاده از Git Submodule (پیشنهادی)

```bash
cd MS-microcontroller/firmware
git submodule add https://github.com/FreeRTOS/FreeRTOS-Kernel.git third_party/FreeRTOS
git submodule update --init --recursive
```

### روش 2: استفاده از nRF Connect SDK

اگر از nRF Connect SDK استفاده می‌کنید، FreeRTOS به صورت پیش‌فرض موجود است:

```bash
# nRF Connect SDK شامل FreeRTOS است
# فقط باید در CMakeLists.txt فعال شود
```

---

## فعال‌سازی در CMakeLists.txt

بعد از نصب FreeRTOS، بخش زیر را در `CMakeLists.txt` فعال کنید:

```cmake
# مسیر FreeRTOS
set(FREERTOS_DIR "${FIRMWARE_ROOT}/third_party/FreeRTOS")

# فایل‌های FreeRTOS
file(GLOB FREERTOS_SOURCES
    "${FREERTOS_DIR}/*.c"
    "${FREERTOS_DIR}/portable/GCC/ARM_CM4F/*.c"
    "${FREERTOS_DIR}/portable/MemMang/heap_4.c"
)

# Include directories
target_include_directories(${PROJECT_NAME}.elf PRIVATE
    ${FREERTOS_DIR}/include
    ${FREERTOS_DIR}/portable/GCC/ARM_CM4F
)

# اضافه کردن FreeRTOS به target
target_sources(${PROJECT_NAME}.elf PRIVATE ${FREERTOS_SOURCES})

# تعریف ماکرو برای فعال‌سازی FreeRTOS
target_compile_definitions(${PROJECT_NAME}.elf PRIVATE FREERTOS_AVAILABLE=1)
```

---

## ساختار Tasks

### اولویت‌ها:

| Task | اولویت | Stack Size | توضیحات |
|------|--------|------------|----------|
| ML Task | 4 (Critical) | 2048 bytes | اجرای مدل ML |
| Stimulation Task | 3 (High) | 512 bytes | کنترل تحریک |
| Monitoring Task | 3 (High) | 512 bytes | خواندن سنسورها |
| Processing Task | 2 (Normal) | 1024 bytes | پردازش سیگنال |
| Communication Task | 1 (Low) | 512 bytes | ارتباط BLE |
| Power Management | 1 (Low) | 256 bytes | مدیریت انرژی |
| Watchdog | 1 (Low) | 256 bytes | Watchdog |

### Queues:

- `g_sensor_queue` - داده‌های سنسور (10 items)
- `g_processed_queue` - داده‌های پردازش شده (5 items)
- `g_ml_queue` - نتایج ML (5 items)
- `g_stimulation_queue` - دستورات تحریک (5 items)

### Mutexes:

- `g_ml_mutex` - محافظت از ML inference
- `g_stimulation_mutex` - محافظت از تحریک
- `g_communication_mutex` - محافظت از ارتباطات

---

## تست

### 1. تست اولیه (بدون FreeRTOS)

```bash
# کامپایل بدون FreeRTOS (fallback mode)
cmake -B build
cmake --build build
```

### 2. تست با FreeRTOS

```bash
# بعد از نصب FreeRTOS و فعال‌سازی در CMakeLists.txt
cmake -B build -DFREERTOS_AVAILABLE=1
cmake --build build
```

### 3. Debug با Segger SystemView

1. نصب Segger SystemView
2. فعال‌سازی trace در FreeRTOSConfig.h:
   ```c
   #define configUSE_TRACE_FACILITY 1
   ```
3. اتصال debugger و مشاهده timeline

---

## تنظیمات مهم

### FreeRTOSConfig.h

- `configTOTAL_HEAP_SIZE`: 16 KB (قابل تنظیم)
- `configMAX_PRIORITIES`: 5
- `configTICK_RATE_HZ`: 1000 (1ms tick)
- `configUSE_TICKLESS_IDLE`: 1 (صرفه‌جویی انرژی)

### بهینه‌سازی Stack

برای کاهش مصرف حافظه، می‌توانید اندازه stack را تنظیم کنید:

```c
// در rtos_tasks.h
#define TASK_STACK_MONITORING 256  // کاهش از 512
#define TASK_STACK_PROCESSING 512  // کاهش از 1024
```

⚠️ **هشدار:** کاهش بیش از حد stack می‌تواند باعث stack overflow شود.

---

## یکپارچه‌سازی با ماژول‌های موجود

### State Machine

```c
// در task
state_machine_t *sm = state_machine_get_instance();
system_state_t current = state_machine_get_current_state(sm);
```

### Event Driver

```c
// ارسال event از task
event_driver_post_simple_event(EVENT_SENSOR_DATA_READY, 0, 5);

// پردازش events در task
event_driver_process_events();
```

### Memory Pool

```c
// استفاده از memory pool در task
memory_pool_t *pool = memory_pool_create(sizeof(data_t), 20, 4);
void *data = memory_pool_alloc(pool);
// ...
memory_pool_free(pool, data);
```

---

## عیب‌یابی

### Stack Overflow

اگر `vApplicationStackOverflowHook` فراخوانی شد:

1. اندازه stack را افزایش دهید
2. استفاده از stack را کاهش دهید (کاهش متغیرهای محلی)
3. از heap به جای stack استفاده کنید

### Malloc Failed

اگر `vApplicationMallocFailedHook` فراخوانی شد:

1. `configTOTAL_HEAP_SIZE` را افزایش دهید
2. استفاده از memory pool به جای malloc
3. بررسی memory leaks

### Task Not Running

1. بررسی اولویت task
2. بررسی blocking در task
3. بررسی stack size

---

## منابع

- [FreeRTOS Documentation](https://www.freertos.org/Documentation/RTOS_book.html)
- [FreeRTOS API Reference](https://www.freertos.org/a00106.html)
- [nRF Connect SDK](https://developer.nordicsemi.com/nRF_Connect_SDK/doc/latest/nrf/index.html)
- [Segger SystemView](https://www.segger.com/products/development-tools/systemview/)

---

**آخرین به‌روزرسانی:** 2024

