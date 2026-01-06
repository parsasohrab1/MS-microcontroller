/**
 * @file adbs_controller.h
 * @brief کنترلر تحریک عمقی مغز تطبیقی (aDBS)
 * @version 0.1.0
 */

#ifndef ADBS_CONTROLLER_H
#define ADBS_CONTROLLER_H

#include <stdint.h>
#include <stdbool.h>
#include "../config.h"

// ============================================================================
// ساختار پارامترهای تحریک
// ============================================================================

typedef struct {
    float amplitude;        // دامنه (mA)
    float frequency;        // فرکانس (Hz)
    float pulse_width;      // عرض پالس (μs)
    uint16_t channel_mask;   // ماسک کانال‌ها (16 بیت)
} stimulation_params_t;

// ============================================================================
// ساختار وضعیت تحریک
// ============================================================================

typedef struct {
    bool active;
    stimulation_params_t current_params;
    uint32_t start_time;
    uint32_t total_stimulation_time;
} stimulation_status_t;

// ============================================================================
// توابع API
// ============================================================================

/**
 * @brief مقداردهی اولیه کنترلر aDBS
 * @return true در صورت موفقیت
 */
bool adbs_init(void);

/**
 * @brief تنظیم پارامترهای تحریک
 * @param params پارامترهای جدید
 * @return true در صورت موفقیت
 */
bool adbs_set_parameters(const stimulation_params_t *params);

/**
 * @brief شروع تحریک
 * @return true در صورت موفقیت
 */
bool adbs_start(void);

/**
 * @brief توقف تحریک
 */
void adbs_stop(void);

/**
 * @brief تنظیم تطبیقی پارامترها بر اساس فیدبک
 * @param feedback_value مقدار فیدبک (0.0 - 1.0)
 * @return true در صورت موفقیت
 */
bool adbs_adaptive_adjust(float feedback_value);

/**
 * @brief دریافت وضعیت فعلی
 * @param status اشاره‌گر به ساختار وضعیت
 * @return true در صورت موفقیت
 */
bool adbs_get_status(stimulation_status_t *status);

/**
 * @brief بررسی محدودیت‌های ایمنی
 * @param params پارامترهای مورد بررسی
 * @return true اگر پارامترها ایمن هستند
 */
bool adbs_check_safety_limits(const stimulation_params_t *params);

/**
 * @brief خاموش کردن کنترلر
 */
void adbs_deinit(void);

#endif // ADBS_CONTROLLER_H

