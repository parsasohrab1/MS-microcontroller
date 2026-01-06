/**
 * @file anti_tampering.h
 * @brief Anti-Tampering Mechanisms
 * مکانیزم‌های تشخیص و جلوگیری از دستکاری فیزیکی
 */

#ifndef ANTI_TAMPERING_H
#define ANTI_TAMPERING_H

#include <stdint.h>
#include <stdbool.h>

// ============================================================================
// Constants
// ============================================================================

#define ANTI_TAMPERING_MAX_EVENTS 100
#define ANTI_TAMPERING_CHECK_INTERVAL_MS 1000

// ============================================================================
// Types
// ============================================================================

typedef enum {
    TAMPER_EVENT_NONE = 0,
    TAMPER_EVENT_CASE_OPENED,
    TAMPER_EVENT_TEMPERATURE_EXTREME,
    TAMPER_EVENT_VOLTAGE_ANOMALY,
    TAMPER_EVENT_CLOCK_MANIPULATION,
    TAMPER_EVENT_MEMORY_ACCESS_VIOLATION,
    TAMPER_EVENT_DEBUG_INTERFACE_ACCESSED,
    TAMPER_EVENT_UNAUTHORIZED_FIRMWARE,
    TAMPER_EVENT_PHYSICAL_IMPACT
} tamper_event_type_t;

typedef enum {
    TAMPER_SEVERITY_LOW = 0,
    TAMPER_SEVERITY_MEDIUM,
    TAMPER_SEVERITY_HIGH,
    TAMPER_SEVERITY_CRITICAL
} tamper_severity_t;

typedef struct {
    tamper_event_type_t type;
    tamper_severity_t severity;
    uint32_t timestamp;
    uint32_t value;  // مقدار مرتبط (مثلاً دما، ولتاژ)
    bool handled;
} tamper_event_t;

typedef struct {
    uint32_t total_events;
    uint32_t critical_events;
    uint32_t last_event_timestamp;
    bool device_locked;
    bool data_erased;
} tamper_status_t;

// ============================================================================
// Callbacks
// ============================================================================

typedef void (*tamper_event_callback_t)(const tamper_event_t *event);

// ============================================================================
// Functions
// ============================================================================

/**
 * @brief مقداردهی اولیه Anti-Tampering
 * @return true در صورت موفقیت
 */
bool anti_tampering_init(void);

/**
 * @brief شروع monitoring
 * @return true در صورت موفقیت
 */
bool anti_tampering_start_monitoring(void);

/**
 * @brief توقف monitoring
 */
void anti_tampering_stop_monitoring(void);

/**
 * @brief بررسی tampering (فراخوانی دوره‌ای)
 */
void anti_tampering_check(void);

/**
 * @brief ثبت رویداد tampering
 * @param type نوع رویداد
 * @param severity شدت رویداد
 * @param value مقدار مرتبط
 * @return true در صورت موفقیت
 */
bool anti_tampering_log_event(
    tamper_event_type_t type,
    tamper_severity_t severity,
    uint32_t value
);

/**
 * @brief دریافت وضعیت tampering
 * @param status خروجی وضعیت
 * @return true در صورت موفقیت
 */
bool anti_tampering_get_status(tamper_status_t *status);

/**
 * @brief دریافت آخرین رویدادها
 * @param events خروجی رویدادها
 * @param max_events حداکثر تعداد رویدادها
 * @return تعداد رویدادهای برگردانده شده
 */
uint32_t anti_tampering_get_recent_events(
    tamper_event_t *events,
    uint32_t max_events
);

/**
 * @brief تنظیم callback برای رویدادها
 * @param callback تابع callback
 */
void anti_tampering_set_event_callback(tamper_event_callback_t callback);

/**
 * @brief Lock کردن دستگاه در صورت tampering
 * @return true در صورت موفقیت
 */
bool anti_tampering_lock_device(void);

/**
 * @brief Erase کردن داده‌های حساس
 * @return true در صورت موفقیت
 */
bool anti_tampering_erase_sensitive_data(void);

/**
 * @brief فعال/غیرفعال کردن tamper detection
 * @param enable فعال/غیرفعال
 * @return true در صورت موفقیت
 */
bool anti_tampering_set_enabled(bool enable);

/**
 * @brief بررسی فعال بودن tamper detection
 * @return true اگر فعال است
 */
bool anti_tampering_is_enabled(void);

/**
 * @brief Reset کردن tamper status
 * @return true در صورت موفقیت
 */
bool anti_tampering_reset_status(void);

#endif // ANTI_TAMPERING_H

