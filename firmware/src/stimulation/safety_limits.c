/**
 * @file safety_limits.c
 * @brief پیاده‌سازی محدودیت‌های ایمنی
 * @version 0.1.0
 */

#include "safety_limits.h"

// محدودیت‌های اضافی ایمنی
#define MAX_CONTINUOUS_STIMULATION_MS  3600000  // 1 ساعت
#define MAX_TEMPERATURE_C              42.0f    // حداکثر دما

bool safety_check_amplitude(float amplitude)
{
    if (amplitude < 0.0f || amplitude > STIMULATION_MAX_CURRENT) {
        return false;
    }
    return true;
}

bool safety_check_frequency(float frequency)
{
    if (frequency < 1.0f || frequency > STIMULATION_MAX_FREQ) {
        return false;
    }
    return true;
}

bool safety_check_duration(uint32_t duration)
{
    if (duration > MAX_CONTINUOUS_STIMULATION_MS) {
        return false;
    }
    return true;
}

bool safety_check_temperature(float temperature)
{
    if (temperature > MAX_TEMPERATURE_C) {
        return false;
    }
    return true;
}

