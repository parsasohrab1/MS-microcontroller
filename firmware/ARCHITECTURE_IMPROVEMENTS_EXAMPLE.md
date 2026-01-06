# مثال استفاده از بهبودهای معماری

این فایل مثال‌های عملی استفاده از State Machine، Event Driver و Memory Pool را نشان می‌دهد.

---

## مثال 1: استفاده از State Machine در main.c

```c
#include "config.h"
#include "system/state_machine.h"
#include "monitoring/sensors.h"
#include "signal_processing/filters.h"
#include "ml/prediction.h"
#include "stimulation/adbs_controller.h"

// Callback برای ورود به حالت
bool on_state_enter(system_state_t state, system_event_t event)
{
    switch(state)
    {
        case SYSTEM_STATE_MONITORING:
            // شروع نظارت
            sensors_start();
            break;
            
        case SYSTEM_STATE_PROCESSING:
            // شروع پردازش
            break;
            
        case SYSTEM_STATE_STIMULATING:
            // شروع تحریک
            adbs_start();
            break;
            
        default:
            break;
    }
    return true;
}

// Callback برای خروج از حالت
bool on_state_exit(system_state_t state, system_event_t event)
{
    switch(state)
    {
        case SYSTEM_STATE_MONITORING:
            // توقف نظارت
            sensors_stop();
            break;
            
        case SYSTEM_STATE_STIMULATING:
            // توقف تحریک
            adbs_stop();
            break;
            
        default:
            break;
    }
    return true;
}

int main(void)
{
    // مقداردهی اولیه سیستم
    system_init();
    
    // مقداردهی State Machine
    state_machine_t *sm = state_machine_get_instance();
    state_machine_init(sm);
    
    // تنظیم callbacks
    state_machine_set_on_enter(sm, on_state_enter);
    state_machine_set_on_exit(sm, on_state_exit);
    
    // شروع از حالت INIT
    state_machine_force_transition(sm, SYSTEM_STATE_INIT);
    
    // حلقه اصلی
    while(1)
    {
        // پردازش رویدادها و انتقال حالت
        // (رویدادها از ماژول‌های دیگر می‌آیند)
        
        // مثال: اگر داده سنسور آماده است
        if (sensors_data_ready())
        {
            state_machine_process_event(sm, EVENT_DATA_READY);
        }
        
        // مثال: اگر پردازش کامل شد
        if (processing_complete())
        {
            state_machine_process_event(sm, EVENT_PROCESSING_COMPLETE);
        }
        
        // مثال: اگر پیش‌بینی نشان داد نیاز به تحریک است
        if (prediction_indicates_stimulation())
        {
            state_machine_process_event(sm, EVENT_STIMULATION_NEEDED);
        }
        
        delay_ms(10);
    }
    
    return 0;
}
```

---

## مثال 2: استفاده از Event Driver

```c
#include "system/event_driver.h"
#include "monitoring/sensors.h"
#include "monitoring/eeg_ecog.h"

// Handler برای رویداد داده سنسور
bool handle_sensor_data_ready(const event_t *event)
{
    sensor_data_t data;
    
    // خواندن داده
    if (sensors_read(&data))
    {
        // پردازش یا ارسال به صف
        // ...
        return true;
    }
    
    return false;
}

// Handler برای رویداد خطا
bool handle_sensor_error(const event_t *event)
{
    // مدیریت خطا
    // ...
    return true;
}

// Handler برای رویداد EEG
bool handle_eeg_sample_ready(const event_t *event)
{
    eeg_sample_t sample;
    
    // خواندن نمونه EEG
    if (eeg_read_sample(&sample))
    {
        // پردازش
        // ...
        return true;
    }
    
    return false;
}

int main(void)
{
    // مقداردهی اولیه
    system_init();
    event_driver_init();
    
    // ثبت listeners
    static event_listener_t sensor_listener;
    event_driver_register_listener(&sensor_listener, 
                                   EVENT_SENSOR_DATA_READY,
                                   handle_sensor_data_ready,
                                   10);  // اولویت بالا
    
    static event_listener_t error_listener;
    event_driver_register_listener(&error_listener,
                                   EVENT_SENSOR_ERROR,
                                   handle_sensor_error,
                                   255);  // اولویت بسیار بالا
    
    static event_listener_t eeg_listener;
    event_driver_register_listener(&eeg_listener,
                                   EVENT_EEG_SAMPLE_READY,
                                   handle_eeg_sample_ready,
                                   5);
    
    // حلقه اصلی
    while(1)
    {
        // پردازش رویدادها
        event_driver_process_events();
        
        // سایر کارها...
        
        delay_ms(1);
    }
    
    return 0;
}
```

---

## مثال 3: استفاده از Memory Pool

```c
#include "system/memory_pool.h"
#include "monitoring/sensors.h"

// تعریف memory pool برای داده‌های سنسور
static memory_pool_t *sensor_data_pool;

int main(void)
{
    // مقداردهی اولیه
    system_init();
    
    // ایجاد memory pool
    // 20 بلوک، هر کدام به اندازه sensor_data_t
    sensor_data_pool = memory_pool_create(sizeof(sensor_data_t), 20, 4);
    if (!sensor_data_pool)
    {
        // خطا
        return -1;
    }
    
    // حلقه اصلی
    while(1)
    {
        // تخصیص حافظه از pool
        sensor_data_t *data = (sensor_data_t*)memory_pool_alloc(sensor_data_pool);
        if (data)
        {
            // استفاده از داده
            sensors_read(data);
            
            // پردازش...
            
            // آزاد کردن حافظه
            memory_pool_free(sensor_data_pool, data);
        }
        else
        {
            // Pool پر است - مدیریت خطا
        }
        
        delay_ms(10);
    }
    
    // پاک کردن pool (در صورت نیاز)
    memory_pool_destroy(sensor_data_pool);
    
    return 0;
}
```

---

## مثال 4: ترکیب State Machine + Event Driver

```c
#include "system/state_machine.h"
#include "system/event_driver.h"

// تبدیل رویداد Event Driver به رویداد State Machine
bool convert_event_to_state_machine(const event_t *event)
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
            
        case EVENT_ML_INFERENCE_DONE:
            state_machine_process_event(sm, EVENT_PREDICTION_READY);
            break;
            
        case EVENT_CRITICAL_ERROR:
            state_machine_process_event(sm, EVENT_ERROR_DETECTED);
            break;
            
        default:
            break;
    }
    
    return true;
}

int main(void)
{
    // مقداردهی اولیه
    system_init();
    event_driver_init();
    
    state_machine_t *sm = state_machine_get_instance();
    state_machine_init(sm);
    
    // ثبت listener برای تبدیل رویدادها
    static event_listener_t converter_listener;
    event_driver_register_listener(&converter_listener,
                                   EVENT_SENSOR_DATA_READY,
                                   convert_event_to_state_machine,
                                   100);
    
    // حلقه اصلی
    while(1)
    {
        // پردازش رویدادها (که خودشان State Machine را به‌روز می‌کنند)
        event_driver_process_events();
        
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
        
        delay_ms(10);
    }
    
    return 0;
}
```

---

## مثال 5: استفاده با RTOS

```c
#include "FreeRTOS.h"
#include "task.h"
#include "queue.h"
#include "system/state_machine.h"
#include "system/event_driver.h"

// Task برای پردازش رویدادها
void vEventProcessorTask(void *pvParameters)
{
    event_driver_init();
    
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

// Task برای State Machine
void vStateMachineTask(void *pvParameters)
{
    state_machine_t *sm = state_machine_get_instance();
    state_machine_init(sm);
    
    TickType_t last_wake_time = xTaskGetTickCount();
    
    while(1)
    {
        // اجرای اقدامات حالت فعلی
        system_state_t current = state_machine_get_current_state(sm);
        
        // اقدامات بر اساس حالت...
        
        vTaskDelayUntil(&last_wake_time, pdMS_TO_TICKS(10));
    }
}

int main(void)
{
    // مقداردهی اولیه سخت‌افزار
    system_init();
    
    // ایجاد tasks
    xTaskCreate(vEventProcessorTask, "EventProc", 512, NULL, 2, NULL);
    xTaskCreate(vStateMachineTask, "StateMachine", 512, NULL, 3, NULL);
    
    // شروع scheduler
    vTaskStartScheduler();
    
    return 0;
}
```

---

## نکات مهم

1. **اولویت‌بندی:** Event handlers با اولویت بالاتر زودتر اجرا می‌شوند
2. **Memory Safety:** همیشه بررسی کنید که memory pool پر نشده باشد
3. **State Transitions:** فقط از جدول انتقال استفاده کنید، انتقال مستقیم فقط در موارد اضطراری
4. **Error Handling:** همیشه خطاها را مدیریت کنید

---

**آخرین به‌روزرسانی:** 2024

