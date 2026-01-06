/**
 * @file safety_limits.h
 * @brief محدودیت‌های ایمنی برای سیستم تحریک
 * @version 0.1.0
 */

#ifndef SAFETY_LIMITS_H
#define SAFETY_LIMITS_H

#include <stdint.h>
#include <stdbool.h>
#include "../config.h"

// ============================================================================
// توابع API
// ============================================================================

/**
 * @brief بررسی محدودیت دامنه تحریک
 * @param amplitude دامنه (mA)
 * @return true اگر ایمن است
 */
bool safety_check_amplitude(float amplitude);

/**
 * @brief بررسی محدودیت فرکانس
 * @param frequency فرکانس (Hz)
 * @return true اگر ایمن است
 */
bool safety_check_frequency(float frequency);

/**
 * @brief بررسی محدودیت زمان تحریک مداوم
 * @param duration مدت زمان (ms)
 * @return true اگر ایمن است
 */
bool safety_check_duration(uint32_t duration);

/**
 * @brief بررسی محدودیت دما
 * @param temperature دما (درجه سانتی‌گراد)
 * @return true اگر ایمن است
 */
bool safety_check_temperature(float temperature);

#endif // SAFETY_LIMITS_H

