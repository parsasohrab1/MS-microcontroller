/**
 * @file anti_tampering.c
 * @brief Anti-Tampering Implementation
 */

#include "anti_tampering.h"
#include "../system/hal.h"
#include <string.h>
#include <stddef.h>

// ============================================================================
// Private Variables
// ============================================================================

static bool tampering_enabled = true;
static bool monitoring_active = false;
static tamper_event_t event_log[ANTI_TAMPERING_MAX_EVENTS];
static uint32_t event_count = 0;
static uint32_t event_index = 0;
static tamper_status_t tamper_status = {0};
static tamper_event_callback_t event_callback = NULL;

// Thresholds
static int16_t temp_min = -10;  // درجه سانتی‌گراد
static int16_t temp_max = 70;
static uint16_t voltage_min = 2700;  // میلی‌ولت
static uint16_t voltage_max = 3600;

// ============================================================================
// Private Functions
// ============================================================================

/**
 * @brief بررسی case sensor
 */
static bool check_case_sensor(void)
{
    // TODO: خواندن از hardware sensor
    bool case_open = hal_tamper_get_case_status();
    
    if (case_open) {
        anti_tampering_log_event(
            TAMPER_EVENT_CASE_OPENED,
            TAMPER_SEVERITY_HIGH,
            0
        );
        return true;
    }
    
    return false;
}

/**
 * @brief بررسی دما
 */
static bool check_temperature(void)
{
    int16_t temperature = hal_tamper_get_temperature();
    
    if (temperature < temp_min || temperature > temp_max) {
        anti_tampering_log_event(
            TAMPER_EVENT_TEMPERATURE_EXTREME,
            TAMPER_SEVERITY_MEDIUM,
            (uint32_t)temperature
        );
        return true;
    }
    
    return false;
}

/**
 * @brief بررسی ولتاژ
 */
static bool check_voltage(void)
{
    uint16_t voltage = hal_tamper_get_voltage();
    
    if (voltage < voltage_min || voltage > voltage_max) {
        anti_tampering_log_event(
            TAMPER_EVENT_VOLTAGE_ANOMALY,
            TAMPER_SEVERITY_MEDIUM,
            (uint32_t)voltage
        );
        return true;
    }
    
    return false;
}

/**
 * @brief بررسی clock manipulation
 */
static bool check_clock_manipulation(void)
{
    // TODO: بررسی تغییرات غیرعادی در clock
    // می‌توان از RTC و system clock استفاده کرد
    return false;
}

/**
 * @brief بررسی debug interface
 */
static bool check_debug_interface(void)
{
    // TODO: بررسی دسترسی به debug interface
    bool debug_accessed = hal_tamper_get_debug_status();
    
    if (debug_accessed) {
        anti_tampering_log_event(
            TAMPER_EVENT_DEBUG_INTERFACE_ACCESSED,
            TAMPER_SEVERITY_CRITICAL,
            0
        );
        return true;
    }
    
    return false;
}

/**
 * @brief بررسی physical impact
 */
static bool check_physical_impact(void)
{
    // TODO: استفاده از accelerometer برای تشخیص ضربه
    uint16_t impact_level = hal_tamper_get_impact_level();
    
    if (impact_level > 1000) {  // threshold
        anti_tampering_log_event(
            TAMPER_EVENT_PHYSICAL_IMPACT,
            TAMPER_SEVERITY_MEDIUM,
            (uint32_t)impact_level
        );
        return true;
    }
    
    return false;
}

/**
 * @brief پردازش رویداد tampering
 */
static void handle_tamper_event(const tamper_event_t *event)
{
    if (!event) {
        return;
    }
    
    // بر اساس severity اقدام مناسب
    switch (event->severity) {
        case TAMPER_SEVERITY_CRITICAL:
            // Lock device و erase data
            anti_tampering_lock_device();
            anti_tampering_erase_sensitive_data();
            break;
        
        case TAMPER_SEVERITY_HIGH:
            // Lock device
            anti_tampering_lock_device();
            break;
        
        case TAMPER_SEVERITY_MEDIUM:
            // فقط log
            break;
        
        case TAMPER_SEVERITY_LOW:
            // فقط log
            break;
    }
    
    // فراخوانی callback
    if (event_callback) {
        event_callback(event);
    }
}

// ============================================================================
// Public Functions
// ============================================================================

bool anti_tampering_init(void)
{
    if (!tampering_enabled) {
        return true;
    }
    
    // پاک کردن event log
    memset(event_log, 0, sizeof(event_log));
    event_count = 0;
    event_index = 0;
    
    // مقداردهی اولیه status
    memset(&tamper_status, 0, sizeof(tamper_status_t));
    tamper_status.device_locked = false;
    tamper_status.data_erased = false;
    
    // مقداردهی اولیه hardware sensors
    hal_tamper_init();
    
    return true;
}

bool anti_tampering_start_monitoring(void)
{
    if (!tampering_enabled) {
        return false;
    }
    
    monitoring_active = true;
    return true;
}

void anti_tampering_stop_monitoring(void)
{
    monitoring_active = false;
}

void anti_tampering_check(void)
{
    if (!tampering_enabled || !monitoring_active) {
        return;
    }
    
    // بررسی همه sensors
    check_case_sensor();
    check_temperature();
    check_voltage();
    check_clock_manipulation();
    check_debug_interface();
    check_physical_impact();
}

bool anti_tampering_log_event(
    tamper_event_type_t type,
    tamper_severity_t severity,
    uint32_t value
)
{
    if (!tampering_enabled) {
        return false;
    }
    
    // ایجاد رویداد
    tamper_event_t event = {
        .type = type,
        .severity = severity,
        .timestamp = hal_get_timestamp(),
        .value = value,
        .handled = false
    };
    
    // ذخیره در log
    event_log[event_index] = event;
    event_index = (event_index + 1) % ANTI_TAMPERING_MAX_EVENTS;
    
    if (event_count < ANTI_TAMPERING_MAX_EVENTS) {
        event_count++;
    }
    
    // به‌روزرسانی status
    tamper_status.total_events++;
    if (severity == TAMPER_SEVERITY_CRITICAL) {
        tamper_status.critical_events++;
    }
    tamper_status.last_event_timestamp = event.timestamp;
    
    // پردازش رویداد
    handle_tamper_event(&event);
    event.handled = true;
    
    return true;
}

bool anti_tampering_get_status(tamper_status_t *status)
{
    if (!status) {
        return false;
    }
    
    memcpy(status, &tamper_status, sizeof(tamper_status_t));
    return true;
}

uint32_t anti_tampering_get_recent_events(
    tamper_event_t *events,
    uint32_t max_events
)
{
    if (!events || max_events == 0) {
        return 0;
    }
    
    uint32_t count = (max_events < event_count) ? max_events : event_count;
    
    // کپی آخرین رویدادها
    uint32_t start_index = (event_index >= count) ? (event_index - count) : 0;
    
    for (uint32_t i = 0; i < count; i++) {
        uint32_t idx = (start_index + i) % ANTI_TAMPERING_MAX_EVENTS;
        events[i] = event_log[idx];
    }
    
    return count;
}

void anti_tampering_set_event_callback(tamper_event_callback_t callback)
{
    event_callback = callback;
}

bool anti_tampering_lock_device(void)
{
    if (tamper_status.device_locked) {
        return true;  // قبلاً lock شده
    }
    
    // TODO: Lock کردن دستگاه
    // - غیرفعال کردن I/O
    // - پاک کردن session keys
    // - غیرفعال کردن functions حساس
    
    tamper_status.device_locked = true;
    
    return true;
}

bool anti_tampering_erase_sensitive_data(void)
{
    if (tamper_status.data_erased) {
        return true;  // قبلاً erase شده
    }
    
    // TODO: Erase کردن داده‌های حساس
    // - Keys در HSM
    // - Patient data
    // - Configuration
    
    tamper_status.data_erased = true;
    
    return true;
}

bool anti_tampering_set_enabled(bool enable)
{
    tampering_enabled = enable;
    return true;
}

bool anti_tampering_is_enabled(void)
{
    return tampering_enabled;
}

bool anti_tampering_reset_status(void)
{
    // فقط در صورت نیاز (مثلاً بعد از service)
    memset(&tamper_status, 0, sizeof(tamper_status_t));
    return true;
}

