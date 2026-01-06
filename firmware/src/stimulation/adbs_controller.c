/**
 * @file adbs_controller.c
 * @brief پیاده‌سازی کنترلر aDBS
 * @version 0.1.0
 */

#include "adbs_controller.h"
#include <string.h>
#include "pid_control.h"
#include "safety_limits.h"

// ============================================================================
// متغیرهای داخلی
// ============================================================================

static bool adbs_initialized = false;
static stimulation_status_t current_status;
static pid_controller_t pid_controller;

// ============================================================================
// توابع API عمومی
// ============================================================================

bool adbs_init(void)
{
    if (adbs_initialized) {
        return true;
    }
    
    memset(&current_status, 0, sizeof(stimulation_status_t));
    
    // مقداردهی اولیه کنترلر PID
    // TODO: تنظیم پارامترهای PID بر اساس نیاز
    pid_init(&pid_controller, 1.0f, 0.1f, 0.01f);  // Kp, Ki, Kd
    
    // TODO: مقداردهی اولیه سخت‌افزار تحریک
    // - تنظیم DAC برای دامنه
    // - تنظیم تایمر برای فرکانس
    // - تنظیم PWM برای عرض پالس
    
    adbs_initialized = true;
    return true;
}

bool adbs_set_parameters(const stimulation_params_t *params)
{
    if (!adbs_initialized || !params) {
        return false;
    }
    
    // بررسی محدودیت‌های ایمنی
    if (!adbs_check_safety_limits(params)) {
        return false;
    }
    
    // ذخیره پارامترها
    memcpy(&current_status.current_params, params, sizeof(stimulation_params_t));
    
    // TODO: اعمال پارامترها به سخت‌افزار
    // - تنظیم DAC
    // - تنظیم تایمر
    // - تنظیم PWM
    
    return true;
}

bool adbs_start(void)
{
    if (!adbs_initialized) {
        return false;
    }
    
    if (current_status.active) {
        return true;  // قبلاً فعال است
    }
    
    // بررسی مجدد محدودیت‌های ایمنی
    if (!adbs_check_safety_limits(&current_status.current_params)) {
        return false;
    }
    
    // TODO: فعال‌سازی سخت‌افزار تحریک
    // - فعال کردن DAC
    // - شروع تایمر
    // - فعال کردن خروجی
    
    current_status.active = true;
    current_status.start_time = 0;  // TODO: استفاده از RTC
    current_status.total_stimulation_time = 0;
    
    return true;
}

void adbs_stop(void)
{
    if (!adbs_initialized || !current_status.active) {
        return;
    }
    
    // TODO: غیرفعال‌سازی سخت‌افزار
    // - توقف تایمر
    // - خاموش کردن خروجی
    // - تنظیم DAC به صفر
    
    uint32_t current_time = 0;  // TODO: استفاده از RTC
    if (current_status.start_time > 0) {
        current_status.total_stimulation_time += (current_time - current_status.start_time);
    }
    
    current_status.active = false;
}

bool adbs_adaptive_adjust(float feedback_value)
{
    if (!adbs_initialized || !current_status.active) {
        return false;
    }
    
    // محدود کردن فیدبک به محدوده [0, 1]
    if (feedback_value < 0.0f) feedback_value = 0.0f;
    if (feedback_value > 1.0f) feedback_value = 1.0f;
    
    // استفاده از کنترلر PID برای تنظیم تطبیقی
    float setpoint = 0.5f;  // مقدار هدف (می‌تواند تنظیم شود)
    float output = pid_compute(&pid_controller, setpoint, feedback_value);
    
    // تبدیل خروجی PID به تغییر در دامنه
    float amplitude_adjustment = output * 0.1f;  // ضریب تنظیم
    float new_amplitude = current_status.current_params.amplitude + amplitude_adjustment;
    
    // محدود کردن دامنه جدید
    if (new_amplitude < 0.0f) new_amplitude = 0.0f;
    if (new_amplitude > STIMULATION_MAX_CURRENT) {
        new_amplitude = STIMULATION_MAX_CURRENT;
    }
    
    // اعمال تغییر
    stimulation_params_t new_params = current_status.current_params;
    new_params.amplitude = new_amplitude;
    
    return adbs_set_parameters(&new_params);
}

bool adbs_get_status(stimulation_status_t *status)
{
    if (!adbs_initialized || !status) {
        return false;
    }
    
    memcpy(status, &current_status, sizeof(stimulation_status_t));
    
    // به‌روزرسانی زمان تحریک
    if (current_status.active && current_status.start_time > 0) {
        uint32_t current_time = 0;  // TODO: استفاده از RTC
        status->total_stimulation_time = current_status.total_stimulation_time + 
                                        (current_time - current_status.start_time);
    }
    
    return true;
}

bool adbs_check_safety_limits(const stimulation_params_t *params)
{
    if (!params) {
        return false;
    }
    
    // بررسی محدودیت‌های تعریف شده در config.h
    if (params->amplitude > STIMULATION_MAX_CURRENT) {
        return false;
    }
    
    if (params->frequency > STIMULATION_MAX_FREQ) {
        return false;
    }
    
    // TODO: بررسی‌های اضافی
    // - بررسی محدودیت‌های ترکیبی
    // - بررسی زمان تحریک مداوم
    // - بررسی دما
    
    return true;
}

void adbs_deinit(void)
{
    if (!adbs_initialized) {
        return;
    }
    
    adbs_stop();
    
    // TODO: خاموش کردن سخت‌افزار
    // - غیرفعال کردن تمام خروجی‌ها
    // - خاموش کردن منبع تغذیه
    
    adbs_initialized = false;
}

