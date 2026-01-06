/**
 * @file power_management.c
 * @brief پیاده‌سازی مدیریت پیشرفته مصرف انرژی
 * @version 1.0.0
 */

#include "power_management.h"
#include "hal.h"
#include "event_driver.h"
#include <string.h>

// ============================================================================
// متغیرهای داخلی
// ============================================================================

static bool power_management_initialized = false;
static power_config_t power_config;
static power_stats_t power_stats;
static uint32_t last_wake_time = 0;
static uint32_t total_active_ticks = 0;
static uint32_t total_sleep_ticks = 0;

// ============================================================================
// توابع داخلی
// ============================================================================

/**
 * @brief تنظیم فرکانس CPU در سطح HAL
 */
static void hal_set_cpu_frequency(cpu_frequency_t freq)
{
    // Map به مقادیر واقعی HAL
    uint32_t hal_freq;
    switch (freq) {
        case CPU_FREQ_64MHZ: hal_freq = 64000000; break;
        case CPU_FREQ_32MHZ: hal_freq = 32000000; break;
        case CPU_FREQ_16MHZ: hal_freq = 16000000; break;
        case CPU_FREQ_8MHZ:  hal_freq = 8000000;  break;
        case CPU_FREQ_4MHZ:  hal_freq = 4000000;  break;
        default: hal_freq = 16000000; break;
    }
    
    hal_clock_set_cpu_frequency(hal_freq);
}

/**
 * @brief تنظیم ولتاژ CPU در سطح HAL
 */
static void hal_set_cpu_voltage(cpu_voltage_t voltage)
{
    // Map به مقادیر واقعی HAL
    uint32_t hal_voltage_mv;
    switch (voltage) {
        case CPU_VOLTAGE_1V8: hal_voltage_mv = 1800; break;
        case CPU_VOLTAGE_2V0: hal_voltage_mv = 2000; break;
        case CPU_VOLTAGE_2V5: hal_voltage_mv = 2500; break;
        case CPU_VOLTAGE_3V0: hal_voltage_mv = 3000; break;
        case CPU_VOLTAGE_3V3: hal_voltage_mv = 3300; break;
        default: hal_voltage_mv = 3000; break;
    }
    
    hal_power_set_voltage(hal_voltage_mv);
}

/**
 * @brief محاسبه مصرف انرژی بر اساس تنظیمات فعلی
 */
static uint32_t calculate_current_power_consumption(void)
{
    uint32_t base_consumption = 0;
    
    // مصرف پایه بر اساس حالت
    switch (power_config.current_mode) {
        case POWER_MODE_ACTIVE:
            base_consumption = 5000;  // 5 mA
            break;
        case POWER_MODE_IDLE:
            base_consumption = 2000;  // 2 mA
            break;
        case POWER_MODE_SLEEP:
            base_consumption = 100;   // 100 uA
            break;
        case POWER_MODE_DEEP_SLEEP:
            base_consumption = 10;    // 10 uA
            break;
        case POWER_MODE_ULTRA_LOW_POWER:
            base_consumption = 1;     // 1 uA
            break;
    }
    
    // اضافه کردن مصرف بر اساس فرکانس CPU
    uint32_t freq_factor = 0;
    switch (power_config.cpu_freq) {
        case CPU_FREQ_64MHZ: freq_factor = 1000; break;
        case CPU_FREQ_32MHZ: freq_factor = 500;  break;
        case CPU_FREQ_16MHZ: freq_factor = 250;  break;
        case CPU_FREQ_8MHZ:  freq_factor = 125;  break;
        case CPU_FREQ_4MHZ:  freq_factor = 62;  break;
    }
    
    // اضافه کردن مصرف peripherals
    uint32_t peripheral_consumption = 0;
    for (uint8_t i = 0; i < 16; i++) {
        if (power_config.peripherals_enabled[i]) {
            peripheral_consumption += 50;  // 50 uA per peripheral
        }
    }
    
    return base_consumption + freq_factor + peripheral_consumption;
}

/**
 * @brief بهینه‌سازی تنظیمات بر اساس workload
 */
static void optimize_dvfs_for_workload(uint8_t workload_percent)
{
    if (workload_percent > 80) {
        // Workload بالا - نیاز به عملکرد بالا
        power_set_cpu_frequency(CPU_FREQ_64MHZ);
        power_set_cpu_voltage(CPU_VOLTAGE_3V3);
    } else if (workload_percent > 50) {
        // Workload متوسط
        power_set_cpu_frequency(CPU_FREQ_32MHZ);
        power_set_cpu_voltage(CPU_VOLTAGE_3V0);
    } else if (workload_percent > 20) {
        // Workload پایین
        power_set_cpu_frequency(CPU_FREQ_16MHZ);
        power_set_cpu_voltage(CPU_VOLTAGE_2V5);
    } else {
        // Workload بسیار پایین
        power_set_cpu_frequency(CPU_FREQ_8MHZ);
        power_set_cpu_voltage(CPU_VOLTAGE_2V0);
    }
}

// ============================================================================
// توابع API عمومی
// ============================================================================

bool power_management_init(void)
{
    if (power_management_initialized) {
        return true;
    }
    
    // مقداردهی اولیه تنظیمات
    memset(&power_config, 0, sizeof(power_config_t));
    power_config.current_mode = POWER_MODE_ACTIVE;
    power_config.cpu_freq = CPU_FREQ_16MHZ;
    power_config.cpu_voltage = CPU_VOLTAGE_3V0;
    power_config.wake_on_interrupt = true;
    power_config.wake_on_timer = true;
    
    // فعال کردن همه peripherals به صورت پیش‌فرض
    for (uint8_t i = 0; i < 16; i++) {
        power_config.peripherals_enabled[i] = true;
    }
    
    // مقداردهی اولیه آمار
    memset(&power_stats, 0, sizeof(power_stats_t));
    power_stats.battery_level_percent = 100;
    
    // تنظیم HAL
    hal_set_cpu_frequency(power_config.cpu_freq);
    hal_set_cpu_voltage(power_config.cpu_voltage);
    
    last_wake_time = hal_rtc_get_time_ms();
    
    power_management_initialized = true;
    return true;
}

bool power_set_mode(power_mode_t mode)
{
    if (!power_management_initialized) {
        return false;
    }
    
    // ذخیره زمان قبل از تغییر حالت
    uint32_t current_time = hal_rtc_get_time_ms();
    uint32_t elapsed = current_time - last_wake_time;
    
    if (power_config.current_mode == POWER_MODE_ACTIVE) {
        total_active_ticks += elapsed;
    } else {
        total_sleep_ticks += elapsed;
    }
    
    // تغییر حالت
    power_config.current_mode = mode;
    
    // اعمال تنظیمات HAL
    switch (mode) {
        case POWER_MODE_ACTIVE:
            hal_power_set_mode_active();
            break;
        case POWER_MODE_IDLE:
            hal_power_set_mode_idle();
            break;
        case POWER_MODE_SLEEP:
            hal_power_set_mode_sleep();
            break;
        case POWER_MODE_DEEP_SLEEP:
            hal_power_set_mode_deep_sleep();
            break;
        case POWER_MODE_ULTRA_LOW_POWER:
            hal_power_set_mode_ultra_low_power();
            break;
    }
    
    last_wake_time = hal_rtc_get_time_ms();
    
    // به‌روزرسانی آمار
    power_stats.current_power_consumption_uA = calculate_current_power_consumption();
    
    return true;
}

power_mode_t power_get_current_mode(void)
{
    return power_config.current_mode;
}

bool power_set_cpu_frequency(cpu_frequency_t freq)
{
    if (!power_management_initialized) {
        return false;
    }
    
    power_config.cpu_freq = freq;
    hal_set_cpu_frequency(freq);
    
    // به‌روزرسانی آمار
    power_stats.current_power_consumption_uA = calculate_current_power_consumption();
    
    return true;
}

bool power_set_cpu_voltage(cpu_voltage_t voltage)
{
    if (!power_management_initialized) {
        return false;
    }
    
    power_config.cpu_voltage = voltage;
    hal_set_cpu_voltage(voltage);
    
    // به‌روزرسانی آمار
    power_stats.current_power_consumption_uA = calculate_current_power_consumption();
    
    return true;
}

bool power_set_peripheral_enabled(uint8_t peripheral_id, bool enabled)
{
    if (!power_management_initialized || peripheral_id >= 16) {
        return false;
    }
    
    power_config.peripherals_enabled[peripheral_id] = enabled;
    
    // اعمال در HAL
    hal_peripheral_set_enabled(peripheral_id, enabled);
    
    // به‌روزرسانی آمار
    power_stats.current_power_consumption_uA = calculate_current_power_consumption();
    
    return true;
}

bool power_enter_sleep(uint32_t duration_ms)
{
    if (!power_management_initialized) {
        return false;
    }
    
    // غیرفعال کردن peripherals غیرضروری
    for (uint8_t i = 0; i < 16; i++) {
        // فقط BLE و RTC را فعال نگه می‌داریم
        if (i != 0 && i != 1) {  // فرض: 0=BLE, 1=RTC
            hal_peripheral_set_enabled(i, false);
        }
    }
    
    // تنظیم wake timer
    if (duration_ms > 0) {
        hal_rtc_set_wake_timer(duration_ms);
    }
    
    // ورود به sleep
    power_set_mode(POWER_MODE_DEEP_SLEEP);
    
    // اینجا CPU متوقف می‌شود و با interrupt یا timer بیدار می‌شود
    hal_cpu_wait_for_interrupt();
    
    // بعد از بیدار شدن
    power_wake_up();
    
    return true;
}

void power_wake_up(void)
{
    // فعال کردن مجدد peripherals
    for (uint8_t i = 0; i < 16; i++) {
        if (power_config.peripherals_enabled[i]) {
            hal_peripheral_set_enabled(i, true);
        }
    }
    
    // بازگشت به حالت active
    power_set_mode(POWER_MODE_ACTIVE);
    
    last_wake_time = hal_rtc_get_time_ms();
}

bool power_optimize_for_workload(uint8_t workload_percent)
{
    if (!power_management_initialized || workload_percent > 100) {
        return false;
    }
    
    // بهینه‌سازی DVFS
    optimize_dvfs_for_workload(workload_percent);
    
    // تنظیم حالت power بر اساس workload
    if (workload_percent == 0) {
        power_set_mode(POWER_MODE_DEEP_SLEEP);
    } else if (workload_percent < 10) {
        power_set_mode(POWER_MODE_SLEEP);
    } else if (workload_percent < 50) {
        power_set_mode(POWER_MODE_IDLE);
    } else {
        power_set_mode(POWER_MODE_ACTIVE);
    }
    
    return true;
}

bool power_get_stats(power_stats_t *stats)
{
    if (!power_management_initialized || !stats) {
        return false;
    }
    
    // به‌روزرسانی آمار
    uint32_t current_time = hal_rtc_get_time_ms();
    uint32_t elapsed = current_time - last_wake_time;
    
    if (power_config.current_mode == POWER_MODE_ACTIVE) {
        total_active_ticks += elapsed;
    } else {
        total_sleep_ticks += elapsed;
    }
    
    stats->total_active_time_ms = total_active_ticks;
    stats->total_sleep_time_ms = total_sleep_ticks;
    stats->current_power_consumption_uA = calculate_current_power_consumption();
    
    // محاسبه میانگین
    uint32_t total_time = total_active_ticks + total_sleep_ticks;
    if (total_time > 0) {
        uint32_t active_avg = (total_active_ticks * 5000) / total_time;  // 5mA active
        uint32_t sleep_avg = (total_sleep_ticks * 10) / total_time;       // 10uA sleep
        stats->average_power_consumption_uA = active_avg + sleep_avg;
    }
    
    // خواندن سطح باتری از HAL
    stats->battery_level_percent = hal_battery_get_level();
    
    // تخمین عمر باتری
    stats->estimated_days_remaining = power_estimate_battery_life_days();
    
    *stats = power_stats;
    
    return true;
}

uint32_t power_estimate_battery_life_days(void)
{
    if (!power_management_initialized) {
        return 0;
    }
    
    // فرض: باتری 1000 mAh
    const uint32_t battery_capacity_mAh = 1000;
    
    // محاسبه مصرف متوسط (uA)
    power_stats_t stats;
    power_get_stats(&stats);
    
    if (stats.average_power_consumption_uA == 0) {
        return 0;
    }
    
    // تبدیل به mAh/day
    uint32_t consumption_mAh_per_day = (stats.average_power_consumption_uA * 24) / 1000;
    
    if (consumption_mAh_per_day == 0) {
        return 9999;  // تقریباً نامحدود
    }
    
    // محاسبه روزهای باقی‌مانده
    uint32_t remaining_mAh = (battery_capacity_mAh * stats.battery_level_percent) / 100;
    uint32_t days_remaining = remaining_mAh / consumption_mAh_per_day;
    
    return days_remaining;
}

bool power_enable_hardware_accelerator(uint8_t task_id)
{
    if (!power_management_initialized) {
        return false;
    }
    
    // فعال کردن hardware accelerator مناسب
    switch (task_id) {
        case 0:  // FFT
            hal_hw_accelerator_enable(0);  // FFT accelerator
            break;
        case 1:  // Encryption
            hal_hw_accelerator_enable(1);  // Crypto accelerator
            break;
        case 2:  // ML Inference
            hal_hw_accelerator_enable(2);  // ML accelerator
            break;
        default:
            return false;
    }
    
    return true;
}

void power_management_deinit(void)
{
    if (!power_management_initialized) {
        return;
    }
    
    // بازگشت به حالت پیش‌فرض
    power_set_mode(POWER_MODE_ACTIVE);
    power_set_cpu_frequency(CPU_FREQ_16MHZ);
    power_set_cpu_voltage(CPU_VOLTAGE_3V0);
    
    power_management_initialized = false;
}

