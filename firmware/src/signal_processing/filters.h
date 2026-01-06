/**
 * @file filters.h
 * @brief ماژول فیلترهای دیجیتال برای پردازش سیگنال
 * @version 0.1.0
 */

#ifndef FILTERS_H
#define FILTERS_H

#include <stdint.h>
#include <stdbool.h>
#include "../config.h"

// ============================================================================
// انواع فیلتر
// ============================================================================

typedef enum {
    FILTER_TYPE_LOW_PASS = 0,
    FILTER_TYPE_HIGH_PASS,
    FILTER_TYPE_BAND_PASS,
    FILTER_TYPE_NOTCH
} filter_type_t;

// ============================================================================
// ساختار فیلتر
// ============================================================================

typedef struct {
    filter_type_t type;
    float cutoff_freq;          // فرکانس قطع (Hz)
    float sampling_freq;         // نرخ نمونه‌برداری (Hz)
    float *coefficients;        // ضرایب فیلتر
    float *state_buffer;        // بافر حالت (برای IIR)
    uint16_t order;             // مرتبه فیلتر
    bool initialized;
} filter_t;

// ============================================================================
// توابع API
// ============================================================================

/**
 * @brief ایجاد و مقداردهی اولیه فیلتر
 * @param filter اشاره‌گر به ساختار فیلتر
 * @param type نوع فیلتر
 * @param cutoff_freq فرکانس قطع (Hz)
 * @param sampling_freq نرخ نمونه‌برداری (Hz)
 * @param order مرتبه فیلتر
 * @return true در صورت موفقیت
 */
bool filter_init(filter_t *filter, filter_type_t type, 
                 float cutoff_freq, float sampling_freq, uint16_t order);

/**
 * @brief اعمال فیلتر روی یک نمونه
 * @param filter اشاره‌گر به فیلتر
 * @param input نمونه ورودی
 * @param output اشاره‌گر به نمونه خروجی
 * @return true در صورت موفقیت
 */
bool filter_process(filter_t *filter, float input, float *output);

/**
 * @brief اعمال فیلتر روی آرایه نمونه‌ها
 * @param filter اشاره‌گر به فیلتر
 * @param input آرایه ورودی
 * @param output آرایه خروجی
 * @param length تعداد نمونه‌ها
 * @return تعداد نمونه‌های پردازش شده
 */
uint16_t filter_process_array(filter_t *filter, const float *input, 
                              float *output, uint16_t length);

/**
 * @brief ایجاد فیلتر Notch برای حذف نویز 50/60Hz
 * @param filter اشاره‌گر به فیلتر
 * @param notch_freq فرکانس Notch (50 یا 60 Hz)
 * @param sampling_freq نرخ نمونه‌برداری (Hz)
 * @return true در صورت موفقیت
 */
bool filter_create_notch(filter_t *filter, float notch_freq, float sampling_freq);

/**
 * @brief حذف فیلتر و آزادسازی حافظه
 * @param filter اشاره‌گر به فیلتر
 */
void filter_deinit(filter_t *filter);

#endif // FILTERS_H

