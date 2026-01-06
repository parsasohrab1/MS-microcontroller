/**
 * @file pid_control.h
 * @brief کنترلر PID برای تنظیم تطبیقی تحریک
 * @version 0.1.0
 */

#ifndef PID_CONTROL_H
#define PID_CONTROL_H

#include <stdint.h>
#include <stdbool.h>

// ============================================================================
// ساختار کنترلر PID
// ============================================================================

typedef struct {
    float kp;              // ضریب تناسبی
    float ki;              // ضریب انتگرالی
    float kd;              // ضریب مشتقی
    
    float setpoint;        // مقدار هدف
    float last_error;      // خطای قبلی
    float integral;        // انتگرال خطا
    
    float output_min;      // حداقل خروجی
    float output_max;      // حداکثر خروجی
    
    bool initialized;
} pid_controller_t;

// ============================================================================
// توابع API
// ============================================================================

/**
 * @brief مقداردهی اولیه کنترلر PID
 * @param pid اشاره‌گر به کنترلر
 * @param kp ضریب تناسبی
 * @param ki ضریب انتگرالی
 * @param kd ضریب مشتقی
 */
void pid_init(pid_controller_t *pid, float kp, float ki, float kd);

/**
 * @brief محاسبه خروجی PID
 * @param pid اشاره‌گر به کنترلر
 * @param setpoint مقدار هدف
 * @param current_value مقدار فعلی
 * @return خروجی کنترلر
 */
float pid_compute(pid_controller_t *pid, float setpoint, float current_value);

/**
 * @brief تنظیم محدودیت‌های خروجی
 * @param pid اشاره‌گر به کنترلر
 * @param min حداقل
 * @param max حداکثر
 */
void pid_set_limits(pid_controller_t *pid, float min, float max);

/**
 * @brief ریست کردن کنترلر
 * @param pid اشاره‌گر به کنترلر
 */
void pid_reset(pid_controller_t *pid);

#endif // PID_CONTROL_H

