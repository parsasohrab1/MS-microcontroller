/**
 * @file power_management.h
 * @brief مدیریت پیشرفته مصرف انرژی
 * @version 1.0.0
 */

#ifndef POWER_MANAGEMENT_H
#define POWER_MANAGEMENT_H

#include <stdint.h>
#include <stdbool.h>
#include "../config.h"

// ============================================================================
// انواع Sleep Mode
// ============================================================================

typedef enum {
    POWER_MODE_ACTIVE = 0,        // حالت فعال (تمام ماژول‌ها روشن)
    POWER_MODE_IDLE,              // حالت idle (CPU در wait)
    POWER_MODE_SLEEP,              // Sleep mode (CPU خاموش، RAM روشن)
    POWER_MODE_DEEP_SLEEP,        // Deep sleep (CPU و RAM خاموش)
    POWER_MODE_ULTRA_LOW_POWER    // Ultra low power (حداقل مصرف)
} power_mode_t;

// ============================================================================
// تنظیمات DVFS
// ============================================================================

typedef enum {
    CPU_FREQ_64MHZ = 0,   // 64 MHz (کمترین مصرف)
    CPU_FREQ_32MHZ,       // 32 MHz
    CPU_FREQ_16MHZ,       // 16 MHz
    CPU_FREQ_8MHZ,        // 8 MHz
    CPU_FREQ_4MHZ         // 4 MHz (کمترین مصرف)
} cpu_frequency_t;

typedef enum {
    CPU_VOLTAGE_1V8 = 0,  // 1.8V (کمترین مصرف)
    CPU_VOLTAGE_2V0,      // 2.0V
    CPU_VOLTAGE_2V5,      // 2.5V
    CPU_VOLTAGE_3V0,      // 3.0V (پیش‌فرض)
    CPU_VOLTAGE_3V3       // 3.3V (حداکثر عملکرد)
} cpu_voltage_t;

// ============================================================================
// ساختار تنظیمات Power Management
// ============================================================================

typedef struct {
    power_mode_t current_mode;
    cpu_frequency_t cpu_freq;
    cpu_voltage_t cpu_voltage;
    bool peripherals_enabled[16];  // وضعیت هر peripheral
    uint32_t sleep_duration_ms;    // مدت زمان sleep
    bool wake_on_interrupt;         // بیدار شدن با interrupt
    bool wake_on_timer;             // بیدار شدن با timer
} power_config_t;

// ============================================================================
// آمار مصرف انرژی
// ============================================================================

typedef struct {
    uint32_t total_active_time_ms;
    uint32_t total_sleep_time_ms;
    uint32_t current_power_consumption_uA;  // مصرف فعلی (microAmpere)
    uint32_t average_power_consumption_uA;
    uint32_t battery_level_percent;
    uint32_t estimated_days_remaining;    // تخمین روزهای باقی‌مانده
} power_stats_t;

// ============================================================================
// توابع API
// ============================================================================

/**
 * @brief مقداردهی اولیه Power Management
 * @return true در صورت موفقیت
 */
bool power_management_init(void);

/**
 * @brief تنظیم حالت power
 * @param mode حالت power مورد نظر
 * @return true در صورت موفقیت
 */
bool power_set_mode(power_mode_t mode);

/**
 * @brief دریافت حالت power فعلی
 * @return حالت فعلی
 */
power_mode_t power_get_current_mode(void);

/**
 * @brief تنظیم فرکانس CPU (DVFS)
 * @param freq فرکانس مورد نظر
 * @return true در صورت موفقیت
 */
bool power_set_cpu_frequency(cpu_frequency_t freq);

/**
 * @brief تنظیم ولتاژ CPU (DVFS)
 * @param voltage ولتاژ مورد نظر
 * @return true در صورت موفقیت
 */
bool power_set_cpu_voltage(cpu_voltage_t voltage);

/**
 * @brief فعال/غیرفعال کردن peripheral
 * @param peripheral_id شناسه peripheral (0-15)
 * @param enabled true برای فعال، false برای غیرفعال
 * @return true در صورت موفقیت
 */
bool power_set_peripheral_enabled(uint8_t peripheral_id, bool enabled);

/**
 * @brief ورود به sleep mode
 * @param duration_ms مدت زمان sleep (ms) - 0 برای sleep نامحدود
 * @return true در صورت موفقیت
 */
bool power_enter_sleep(uint32_t duration_ms);

/**
 * @brief بیدار شدن از sleep
 */
void power_wake_up(void);

/**
 * @brief محاسبه بهینه‌ترین تنظیمات بر اساس workload
 * @param workload_percent درصد workload (0-100)
 * @return true در صورت موفقیت
 */
bool power_optimize_for_workload(uint8_t workload_percent);

/**
 * @brief دریافت آمار مصرف انرژی
 * @param stats اشاره‌گر به ساختار آمار
 * @return true در صورت موفقیت
 */
bool power_get_stats(power_stats_t *stats);

/**
 * @brief تخمین عمر باتری
 * @return تعداد روزهای باقی‌مانده
 */
uint32_t power_estimate_battery_life_days(void);

/**
 * @brief فعال کردن hardware accelerator برای task مشخص
 * @param task_id شناسه task
 * @return true در صورت موفقیت
 */
bool power_enable_hardware_accelerator(uint8_t task_id);

/**
 * @brief خاموش کردن ماژول
 */
void power_management_deinit(void);

#endif // POWER_MANAGEMENT_H

