# راهنمای یکپارچه‌سازی RTOS

## مقدمه

این راهنما نحوه یکپارچه‌سازی FreeRTOS یا Zephyr RTOS با سیستم نوروپلتفرم MS را توضیح می‌دهد.

---

## انتخاب RTOS

### FreeRTOS
**مزایا:**
- ساده و سبک
- پشتیبانی گسترده
- مستندات خوب
- رایگان و open-source

**معایب:**
- ویژگی‌های محدودتر نسبت به Zephyr
- نیاز به پیکربندی دستی بیشتر

### Zephyr RTOS
**مزایا:**
- ویژگی‌های پیشرفته‌تر
- پشتیبانی بهتر از nRF52840
- Device Tree support
- پشتیبانی از networking و BLE

**معایب:**
- پیچیده‌تر
- منحنی یادگیری بالاتر

**توصیه:** برای شروع، FreeRTOS پیشنهاد می‌شود.

---

## یکپارچه‌سازی FreeRTOS

### 1. نصب FreeRTOS

#### روش 1: استفاده از FreeRTOS Kernel
```bash
# دانلود از https://www.freertos.org/
# یا استفاده از git submodule
git submodule add https://github.com/FreeRTOS/FreeRTOS-Kernel.git firmware/third_party/FreeRTOS
```

#### روش 2: استفاده از nRF Connect SDK (شامل FreeRTOS)
```bash
# nRF Connect SDK شامل FreeRTOS است
```

### 2. تنظیم CMakeLists.txt

```cmake
# اضافه کردن FreeRTOS
set(FREERTOS_DIR "${CMAKE_CURRENT_SOURCE_DIR}/third_party/FreeRTOS")

# فایل‌های FreeRTOS
file(GLOB FREERTOS_SOURCES
    "${FREERTOS_DIR}/*.c"
    "${FREERTOS_DIR}/portable/GCC/ARM_CM4F/*.c"
)

# Include directories
include_directories(
    ${FREERTOS_DIR}/include
    ${FREERTOS_DIR}/portable/GCC/ARM_CM4F
)

# اضافه کردن به target
target_sources(${PROJECT_NAME}.elf PRIVATE ${FREERTOS_SOURCES})
```

### 3. تنظیم FreeRTOSConfig.h

ایجاد فایل `firmware/include/FreeRTOSConfig.h`:

```c
#ifndef FREERTOS_CONFIG_H
#define FREERTOS_CONFIG_H

// تنظیمات CPU
#define configUSE_PREEMPTION                1
#define configUSE_IDLE_HOOK                0
#define configUSE_TICK_HOOK                0
#define configCPU_CLOCK_HZ                64000000  // 64 MHz برای nRF52840
#define configTICK_RATE_HZ                1000      // 1 ms tick
#define configMAX_PRIORITIES              5
#define configMINIMAL_STACK_SIZE           128
#define configTOTAL_HEAP_SIZE              8192      // 8 KB heap

// Memory management
#define configUSE_MALLOC_FAILED_HOOK      1
#define configUSE_MUTEXES                 1
#define configUSE_RECURSIVE_MUTEXES       1
#define configUSE_COUNTING_SEMAPHORES     1

// Task management
#define configMAX_TASK_NAME_LEN           16
#define configUSE_TRACE_FACILITY          1
#define configUSE_STATS_FORMATTING_FUNCTIONS 1

// Interrupt nesting
#define configKERNEL_INTERRUPT_PRIORITY   0
#define configMAX_SYSCALL_INTERRUPT_PRIORITY 4

// Port specific
#define configPRIO_BITS                   3
#define configLIBRARY_LOWEST_INTERRUPT_PRIORITY 7

// Hook functions
extern void vApplicationStackOverflowHook(TaskHandle_t xTask, char *pcTaskName);
extern void vApplicationMallocFailedHook(void);

#endif // FREERTOS_CONFIG_H
```

### 4. به‌روزرسانی main.c

```c
#include "FreeRTOS.h"
#include "task.h"
#include "queue.h"
#include "semphr.h"

// تعریف وظایف
void vMonitoringTask(void *pvParameters);
void vProcessingTask(void *pvParameters);
void vMLTask(void *pvParameters);
void vStimulationTask(void *pvParameters);
void vCommunicationTask(void *pvParameters);

int main(void)
{
    // مقداردهی اولیه سخت‌افزار
    system_init();
    
    // ایجاد صف‌ها
    QueueHandle_t sensor_queue = xQueueCreate(10, sizeof(sensor_data_t));
    QueueHandle_t processed_queue = xQueueCreate(5, sizeof(processed_data_t));
    
    // ایجاد Semaphore ها
    SemaphoreHandle_t ml_mutex = xSemaphoreCreateMutex();
    
    // ایجاد وظایف
    xTaskCreate(vMonitoringTask, "Monitoring", 512, sensor_queue, 3, NULL);
    xTaskCreate(vProcessingTask, "Processing", 1024, processed_queue, 2, NULL);
    xTaskCreate(vMLTask, "ML", 2048, ml_mutex, 4, NULL);
    xTaskCreate(vStimulationTask, "Stimulation", 512, NULL, 3, NULL);
    xTaskCreate(vCommunicationTask, "Comm", 512, NULL, 1, NULL);
    
    // شروع scheduler
    vTaskStartScheduler();
    
    // این خط هرگز نباید اجرا شود
    while(1);
    return 0;
}
```

### 5. پیاده‌سازی وظایف

```c
void vMonitoringTask(void *pvParameters)
{
    QueueHandle_t queue = (QueueHandle_t)pvParameters;
    sensor_data_t data;
    TickType_t last_wake_time = xTaskGetTickCount();
    
    while(1)
    {
        // خواندن داده از سنسورها
        if (sensors_read(&data))
        {
            // ارسال به صف
            xQueueSend(queue, &data, 0);
        }
        
        // منتظر ماندن تا زمان نمونه‌برداری بعدی (10ms)
        vTaskDelayUntil(&last_wake_time, pdMS_TO_TICKS(10));
    }
}

void vProcessingTask(void *pvParameters)
{
    QueueHandle_t input_queue = (QueueHandle_t)pvParameters;
    QueueHandle_t output_queue = xQueueCreate(5, sizeof(processed_data_t));
    sensor_data_t sensor_data;
    processed_data_t processed_data;
    
    while(1)
    {
        // دریافت داده از صف
        if (xQueueReceive(input_queue, &sensor_data, portMAX_DELAY))
        {
            // پردازش داده
            process_signal(&sensor_data, &processed_data);
            
            // ارسال به صف بعدی
            xQueueSend(output_queue, &processed_data, 0);
        }
    }
}
```

---

## یکپارچه‌سازی با State Machine

```c
#include "state_machine.h"
#include "FreeRTOS.h"
#include "task.h"

void vStateMachineTask(void *pvParameters)
{
    state_machine_t *sm = state_machine_get_instance();
    TickType_t last_wake_time = xTaskGetTickCount();
    
    while(1)
    {
        // اجرای اقدامات حالت فعلی
        system_state_t current = state_machine_get_current_state(sm);
        
        switch(current)
        {
            case SYSTEM_STATE_MONITORING:
                // اقدامات نظارت
                break;
                
            case SYSTEM_STATE_PROCESSING:
                // اقدامات پردازش
                break;
                
            // ...
        }
        
        vTaskDelayUntil(&last_wake_time, pdMS_TO_TICKS(10));
    }
}
```

---

## یکپارچه‌سازی با Event Driver

```c
#include "event_driver.h"
#include "FreeRTOS.h"
#include "task.h"

void vEventProcessorTask(void *pvParameters)
{
    while(1)
    {
        // پردازش رویدادها
        uint32_t processed = event_driver_process_events();
        
        if (processed == 0)
        {
            // اگر رویدادی نبود، منتظر بمان
            vTaskDelay(pdMS_TO_TICKS(1));
        }
    }
}
```

---

## مدیریت حافظه با RTOS

```c
// استفاده از FreeRTOS heap
void* pvPortMalloc(size_t xWantedSize);
void vPortFree(void *pv);

// یا استفاده از Memory Pool خودمان
#include "memory_pool.h"

static memory_pool_t *sensor_data_pool;

void init_memory_pools(void)
{
    sensor_data_pool = memory_pool_create(sizeof(sensor_data_t), 20, 4);
}
```

---

## نکات مهم

### 1. اولویت‌بندی وظایف
- **اولویت بالا (4-5):** وظایف بحرانی (ML, Stimulation)
- **اولویت متوسط (2-3):** وظایف مهم (Monitoring, Processing)
- **اولویت پایین (1):** وظایف غیربحرانی (Communication)

### 2. اندازه Stack
- وظایف ساده: 256-512 bytes
- وظایف پردازشی: 1024-2048 bytes
- وظایف ML: 4096+ bytes

### 3. استفاده از Mutex
```c
SemaphoreHandle_t ml_mutex = xSemaphoreCreateMutex();

// در task
if (xSemaphoreTake(ml_mutex, portMAX_DELAY))
{
    // استفاده از منابع مشترک
    ml_inference(&data);
    xSemaphoreGive(ml_mutex);
}
```

### 4. Watchdog با RTOS
```c
void vWatchdogTask(void *pvParameters)
{
    while(1)
    {
        // Feed watchdog
        watchdog_feed();
        
        // بررسی سلامت وظایف
        check_task_health();
        
        vTaskDelay(pdMS_TO_TICKS(1000));
    }
}
```

---

## تست و Debug

### استفاده از FreeRTOS Trace
```c
#define configUSE_TRACE_FACILITY 1
#define configUSE_STATS_FORMATTING_FUNCTIONS 1

// در کد
vTaskList(buffer);  // لیست وظایف
vTaskGetRunTimeStats(buffer);  // آمار زمان اجرا
```

### استفاده از Segger SystemView
- نصب Segger SystemView
- فعال‌سازی trace در FreeRTOS
- مشاهده timeline وظایف

---

## منابع

- [FreeRTOS Documentation](https://www.freertos.org/Documentation/RTOS_book.html)
- [nRF Connect SDK](https://developer.nordicsemi.com/nRF_Connect_SDK/doc/latest/nrf/index.html)
- [FreeRTOS on nRF52840](https://devzone.nordicsemi.com/f/nordic-q-a/45642/freertos-on-nrf52840)

---

**آخرین به‌روزرسانی:** 2024

