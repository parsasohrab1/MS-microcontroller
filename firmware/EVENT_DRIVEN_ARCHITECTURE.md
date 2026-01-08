# راهنمای Event-Driven Architecture

## مقدمه

Event-Driven Architecture یک الگوی معماری است که در آن سیستم بر اساس رویدادها (events) عمل می‌کند. این رویکرد مزایای زیر را دارد:

- **کاهش مصرف انرژی**: به جای polling مداوم، سیستم فقط در زمان وقوع رویداد فعال می‌شود
- **بهبود پاسخگویی**: رویدادها بلافاصله پردازش می‌شوند
- **Decoupling**: ماژول‌ها از طریق رویدادها ارتباط برقرار می‌کنند
- **قابلیت گسترش**: افزودن listener جدید آسان است

---

## معماری

### ساختار کلی

```
[Interrupt/ISR] → [Event Queue] → [Event Processor] → [Event Listeners] → [Handlers]
```

### کامپوننت‌ها

1. **Event Queue**: صف رویدادها (Circular Buffer)
2. **Priority Queue**: صف رویدادهای با اولویت بالا
3. **Event Listeners**: ثبت‌نام کنندگان برای رویدادها
4. **Event Handlers**: توابع پردازش رویدادها

---

## استفاده پایه

### 1. مقداردهی اولیه

```c
#include "system/event_driver.h"

// در main یا initialization
event_driver_init();
```

### 2. ثبت Event Listener

```c
// تعریف handler
bool my_event_handler(const event_t *event)
{
    // پردازش رویداد
    switch(event->type)
    {
        case EVENT_SENSOR_DATA_READY:
            // انجام کار
            break;
        default:
            break;
    }
    return true;
}

// ثبت listener
static event_listener_t my_listener;
event_driver_register_listener(&my_listener,
                               EVENT_SENSOR_DATA_READY,
                               my_event_handler,
                               100);  // اولویت بالا
```

### 3. ارسال رویداد

```c
// ارسال رویداد ساده
event_driver_post_simple_event(EVENT_SENSOR_DATA_READY, 0, 50);

// ارسال رویداد با داده
uint32_t sensor_value = 1234;
event_driver_post_event_with_data(EVENT_SENSOR_DATA_READY,
                                  0,      // source_id
                                  200,    // اولویت بالا
                                  &sensor_value,
                                  sizeof(sensor_value));
```

### 4. پردازش رویدادها

```c
// در main loop یا task
while(1)
{
    uint32_t processed = event_driver_process_events();
    
    if (processed == 0)
    {
        // اگر رویدادی نبود، sleep کنید
        vTaskDelay(pdMS_TO_TICKS(1));
    }
}
```

---

## یکپارچه‌سازی با RTOS

### استفاده در Task

```c
void vEventProcessorTask(void *pvParameters)
{
    while(1)
    {
        // پردازش رویدادها
        uint32_t processed = event_driver_process_events();
        
        if (processed == 0)
        {
            // منتظر بمان
            vTaskDelay(pdMS_TO_TICKS(1));
        }
    }
}
```

### ارسال از ISR

```c
// در interrupt handler
void ADC_IRQHandler(void)
{
    // ارسال رویداد از ISR (ISR-safe)
    event_driver_post_event_from_isr(EVENT_SENSOR_DATA_READY,
                                     0,      // source_id
                                     255);   // اولویت بسیار بالا
}
```

---

## یکپارچه‌سازی با State Machine

```c
// Handler که State Machine را به‌روز می‌کند
bool event_to_state_machine_handler(const event_t *event)
{
    state_machine_t *sm = state_machine_get_instance();
    
    switch(event->type)
    {
        case EVENT_SENSOR_DATA_READY:
            state_machine_process_event(sm, EVENT_DATA_READY);
            break;
            
        case EVENT_PROCESSING_COMPLETE:
            state_machine_process_event(sm, EVENT_PROCESSING_COMPLETE);
            break;
            
        default:
            break;
    }
    
    return true;
}

// ثبت listener
static event_listener_t sm_listener;
event_driver_register_listener(&sm_listener,
                               EVENT_SENSOR_DATA_READY,
                               event_to_state_machine_handler,
                               200);  // اولویت بالا
```

---

## اولویت‌بندی رویدادها

### سطوح اولویت

- **0-99**: اولویت پایین (رویدادهای عادی)
- **100-199**: اولویت متوسط
- **200-255**: اولویت بالا (رویدادهای بحرانی)

### مثال

```c
// رویداد بحرانی (اولویت بالا)
event_driver_post_simple_event(EVENT_CRITICAL_ERROR, 0, 255);

// رویداد عادی
event_driver_post_simple_event(EVENT_SENSOR_DATA_READY, 0, 50);
```

رویدادهای با اولویت بالا در `priority_queue` ذخیره می‌شوند و زودتر پردازش می‌شوند.

---

## استفاده از Memory Pool

برای رویدادهای با داده بزرگ، از memory pool استفاده می‌شود:

```c
// ارسال رویداد با داده (استفاده خودکار از memory pool)
float sensor_data[32];
event_driver_post_event_with_data(EVENT_SENSOR_DATA_READY,
                                  0,
                                  50,
                                  sensor_data,
                                  sizeof(sensor_data));
```

داده به صورت خودکار از memory pool تخصیص می‌یابد و بعد از پردازش آزاد می‌شود.

---

## Thread-Safety

Event Driver به صورت thread-safe طراحی شده است:

- استفاده از mutex برای محافظت از صف‌ها
- ISR-safe functions برای استفاده در interrupt handlers
- پشتیبانی از FreeRTOS

### مثال استفاده در چند task

```c
// Task 1: ارسال رویداد
void vSensorTask(void *pvParameters)
{
    while(1)
    {
        // خواندن سنسور
        // ...
        
        // ارسال رویداد (thread-safe)
        event_driver_post_simple_event(EVENT_SENSOR_DATA_READY, 0, 50);
    }
}

// Task 2: پردازش رویدادها
void vEventProcessorTask(void *pvParameters)
{
    while(1)
    {
        // پردازش (thread-safe)
        event_driver_process_events();
        vTaskDelay(pdMS_TO_TICKS(1));
    }
}
```

---

## آمار و مانیتورینگ

```c
uint32_t total, processed, dropped, high_priority;
event_driver_get_statistics(&total, &processed, &dropped, &high_priority);

printf("Total: %lu, Processed: %lu, Dropped: %lu, High Priority: %lu\n",
       total, processed, dropped, high_priority);
```

---

## بهترین روش‌ها

### 1. استفاده از اولویت‌ها

- رویدادهای بحرانی: اولویت 200+
- رویدادهای عادی: اولویت 50-100
- رویدادهای غیرضروری: اولویت <50

### 2. جلوگیری از Blocking در Handlers

```c
// ❌ بد - blocking در handler
bool bad_handler(const event_t *event)
{
    hal_delay_ms(100);  // Blocking!
    return true;
}

// ✅ خوب - فقط علامت‌گذاری
bool good_handler(const event_t *event)
{
    g_processing_needed = true;  // Flag
    return true;
}
```

### 3. استفاده از Event Data

برای داده‌های کوچک (<64 bytes) از memory pool استفاده کنید:

```c
// ✅ خوب
event_driver_post_event_with_data(EVENT_DATA, 0, 50, &data, sizeof(data));

// ❌ بد - برای داده‌های بزرگ
uint8_t huge_data[1024];
event_driver_post_event_with_data(EVENT_DATA, 0, 50, huge_data, 1024);
```

### 4. مدیریت خطا

```c
bool error_handler(const event_t *event)
{
    if (event->type == EVENT_CRITICAL_ERROR)
    {
        // Log error
        // Enter safe mode
        // Notify user
    }
    return true;
}
```

---

## مثال کامل

```c
#include "system/event_driver.h"
#include "system/state_machine.h"
#include "FreeRTOS.h"
#include "task.h"

// Handler برای رویدادهای سنسور
bool sensor_event_handler(const event_t *event)
{
    if (event->type == EVENT_SENSOR_DATA_READY)
    {
        // پردازش داده سنسور
        // ...
        return true;
    }
    return false;
}

// Handler برای State Machine
bool state_machine_event_handler(const event_t *event)
{
    state_machine_t *sm = state_machine_get_instance();
    
    switch(event->type)
    {
        case EVENT_SENSOR_DATA_READY:
            state_machine_process_event(sm, EVENT_DATA_READY);
            break;
        // ...
    }
    return true;
}

int main(void)
{
    // مقداردهی اولیه
    event_driver_init();
    state_machine_init(state_machine_get_instance());
    
    // ثبت listeners
    static event_listener_t sensor_listener;
    static event_listener_t sm_listener;
    
    event_driver_register_listener(&sensor_listener,
                                   EVENT_SENSOR_DATA_READY,
                                   sensor_event_handler,
                                   100);
    
    event_driver_register_listener(&sm_listener,
                                   EVENT_SENSOR_DATA_READY,
                                   state_machine_event_handler,
                                   200);
    
    // ایجاد task برای پردازش رویدادها
    xTaskCreate(vEventProcessorTask, "EventProc", 512, NULL, 2, NULL);
    
    // شروع scheduler
    vTaskStartScheduler();
    
    return 0;
}

void vEventProcessorTask(void *pvParameters)
{
    while(1)
    {
        event_driver_process_events();
        vTaskDelay(pdMS_TO_TICKS(1));
    }
}
```

---

## عیب‌یابی

### رویدادها پردازش نمی‌شوند

1. بررسی کنید که `event_driver_process_events()` فراخوانی می‌شود
2. بررسی کنید که listener ثبت شده است
3. بررسی کنید که listener فعال است (`enabled = true`)

### رویدادها از دست می‌روند

1. اندازه queue را افزایش دهید:
   ```c
   event_driver_set_queue_size(64);
   ```

2. اولویت رویداد را افزایش دهید

3. فرکانس پردازش را افزایش دهید

### مصرف حافظه بالا

1. از memory pool برای داده‌های کوچک استفاده کنید
2. اندازه queue را کاهش دهید
3. داده‌های بزرگ را در event ذخیره نکنید

---

## منابع

- `firmware/src/system/event_driver.h` - رابط API
- `firmware/src/system/event_driver.c` - پیاده‌سازی
- `firmware/ARCHITECTURE_IMPROVEMENTS_EXAMPLE.md` - مثال‌های بیشتر

---

**آخرین به‌روزرسانی:** 2024

