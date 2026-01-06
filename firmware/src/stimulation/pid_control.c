/**
 * @file pid_control.c
 * @brief پیاده‌سازی کنترلر PID
 * @version 0.1.0
 */

#include "pid_control.h"
#include <string.h>

void pid_init(pid_controller_t *pid, float kp, float ki, float kd)
{
    if (!pid) {
        return;
    }
    
    memset(pid, 0, sizeof(pid_controller_t));
    
    pid->kp = kp;
    pid->ki = ki;
    pid->kd = kd;
    
    pid->output_min = -1.0f;
    pid->output_max = 1.0f;
    
    pid->initialized = true;
}

float pid_compute(pid_controller_t *pid, float setpoint, float current_value)
{
    if (!pid || !pid->initialized) {
        return 0.0f;
    }
    
    pid->setpoint = setpoint;
    
    // محاسبه خطا
    float error = setpoint - current_value;
    
    // بخش تناسبی
    float p_term = pid->kp * error;
    
    // بخش انتگرالی
    pid->integral += error;
    
    // محدود کردن انتگرال برای جلوگیری از Windup
    float i_term = pid->ki * pid->integral;
    if (i_term > pid->output_max) {
        i_term = pid->output_max;
        pid->integral = pid->output_max / pid->ki;
    } else if (i_term < pid->output_min) {
        i_term = pid->output_min;
        pid->integral = pid->output_min / pid->ki;
    }
    
    // بخش مشتقی (استفاده از تغییر خطا)
    float d_term = pid->kd * (error - pid->last_error);
    pid->last_error = error;
    
    // محاسبه خروجی
    float output = p_term + i_term + d_term;
    
    // محدود کردن خروجی
    if (output > pid->output_max) {
        output = pid->output_max;
    } else if (output < pid->output_min) {
        output = pid->output_min;
    }
    
    return output;
}

void pid_set_limits(pid_controller_t *pid, float min, float max)
{
    if (!pid) {
        return;
    }
    
    pid->output_min = min;
    pid->output_max = max;
}

void pid_reset(pid_controller_t *pid)
{
    if (!pid) {
        return;
    }
    
    pid->last_error = 0.0f;
    pid->integral = 0.0f;
}

