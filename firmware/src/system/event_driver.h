/**
 * @file event_driver.h
 * @brief Event-Driven Architecture برای سیستم
 * @version 0.1.0
 * 
 * این ماژول یک سیستم event-driven برای کاهش مصرف انرژی و بهبود
 * پاسخگویی سیستم فراهم می‌کند.
 */

#ifndef EVENT_DRIVER_H
#define EVENT_DRIVER_H

#include <stdint.h>
#include <stdbool.h>
#include "config.h"

// ============================================================================
// تعریف رویدادها
// ============================================================================

typedef enum {
    // رویدادهای سنسور
    EVENT_SENSOR_DATA_READY = 0,
    EVENT_SENSOR_ERROR,
    EVENT_SENSOR_TIMEOUT,
    
    // رویدادهای EEG/ECoG
    EVENT_EEG_SAMPLE_READY,
    EVENT_EEG_BUFFER_FULL,
    EVENT_EEG_ERROR,
    
    // رویدادهای پردازش
    EVENT_PROCESSING_COMPLETE,
    EVENT_FEATURE_EXTRACTION_DONE,
    EVENT_ML_INFERENCE_DONE,
    
    // رویدادهای درمان
    EVENT_STIMULATION_COMPLETE,
    EVENT_DRUG_DELIVERY_COMPLETE,
    EVENT_TREATMENT_ERROR,
    
    // رویدادهای ارتباطی
    EVENT_BLE_CONNECTED,
    EVENT_BLE_DISCONNECTED,
    EVENT_BLE_DATA_RECEIVED,
    EVENT_BLE_DATA_SENT,
    EVENT_BLE_ERROR,
    
    // رویدادهای سیستم
    EVENT_TIMER_EXPIRED,
    EVENT_WATCHDOG_WARNING,
    EVENT_LOW_BATTERY,
    EVENT_CRITICAL_ERROR,
    EVENT_EMERGENCY_STOP,
    
    // رویدادهای کاربر
    EVENT_USER_BUTTON_PRESSED,
    EVENT_USER_BUTTON_LONG_PRESS,
    
    EVENT_COUNT
} event_type_t;

// ============================================================================
// ساختار رویداد
// ============================================================================

typedef struct {
    event_type_t type;        // نوع رویداد
    uint32_t timestamp;       // زمان وقوع رویداد (ms)
    uint16_t source_id;       // شناسه منبع رویداد
    uint16_t data_size;       // اندازه داده (bytes)
    void* data;               // داده رویداد (اختیاری)
    uint32_t priority;        // اولویت (0 = پایین، 255 = بالا)
} event_t;

// ============================================================================
// تعریف Event Handler
// ============================================================================

/**
 * @brief تابع handler برای پردازش رویداد
 * @param event رویداد دریافتی
 * @return true اگر رویداد پردازش شد
 */
typedef bool (*event_handler_t)(const event_t *event);

// ============================================================================
// ساختار Event Listener
// ============================================================================

typedef struct event_listener {
    event_type_t event_type;      // نوع رویداد مورد علاقه
    event_handler_t handler;      // تابع handler
    uint32_t priority;            // اولویت handler (بالاتر = زودتر اجرا)
    bool enabled;                 // فعال/غیرفعال
    struct event_listener *next;   // برای لیست پیوندی
} event_listener_t;

// ============================================================================
// API عمومی
// ============================================================================

/**
 * @brief مقداردهی اولیه سیستم event-driven
 * @return true در صورت موفقیت
 */
bool event_driver_init(void);

/**
 * @brief ثبت یک event listener
 * @param listener اشاره‌گر به listener
 * @param event_type نوع رویداد
 * @param handler تابع handler
 * @param priority اولویت
 * @return true در صورت موفقیت
 */
bool event_driver_register_listener(event_listener_t *listener,
                                   event_type_t event_type,
                                   event_handler_t handler,
                                   uint32_t priority);

/**
 * @brief حذف یک event listener
 * @param listener اشاره‌گر به listener
 * @return true در صورت موفقیت
 */
bool event_driver_unregister_listener(event_listener_t *listener);

/**
 * @brief فعال/غیرفعال کردن listener
 * @param listener اشاره‌گر به listener
 * @param enabled true برای فعال، false برای غیرفعال
 */
void event_driver_set_listener_enabled(event_listener_t *listener, bool enabled);

/**
 * @brief ارسال رویداد به سیستم
 * @param event رویداد
 * @return true در صورت موفقیت
 */
bool event_driver_post_event(const event_t *event);

/**
 * @brief ارسال رویداد ساده (بدون داده)
 * @param type نوع رویداد
 * @param source_id شناسه منبع
 * @param priority اولویت
 * @return true در صورت موفقیت
 */
bool event_driver_post_simple_event(event_type_t type, uint16_t source_id, uint32_t priority);

/**
 * @brief پردازش رویدادهای در صف (باید در main loop فراخوانی شود)
 * @return تعداد رویدادهای پردازش شده
 */
uint32_t event_driver_process_events(void);

/**
 * @brief بررسی اینکه آیا رویدادی در صف وجود دارد
 * @return true اگر رویدادی وجود دارد
 */
bool event_driver_has_pending_events(void);

/**
 * @brief دریافت تعداد رویدادهای در صف
 * @return تعداد رویدادها
 */
uint32_t event_driver_get_pending_count(void);

/**
 * @brief پاک کردن تمام رویدادهای در صف
 */
void event_driver_clear_queue(void);

/**
 * @brief تنظیم اندازه صف رویدادها
 * @param size اندازه جدید
 * @return true در صورت موفقیت
 */
bool event_driver_set_queue_size(uint32_t size);

/**
 * @brief دریافت آمار سیستم event-driven
 * @param total_events تعداد کل رویدادهای ارسال شده
 * @param processed_events تعداد رویدادهای پردازش شده
 * @param dropped_events تعداد رویدادهای از دست رفته (صف پر)
 */
void event_driver_get_statistics(uint32_t *total_events,
                                uint32_t *processed_events,
                                uint32_t *dropped_events);

#endif // EVENT_DRIVER_H

