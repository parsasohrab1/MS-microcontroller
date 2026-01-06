/**
 * @file optimized_filters.h
 * @brief هدر فیلترهای بهینه‌سازی شده
 * @version 1.0.0
 */

#ifndef OPTIMIZED_FILTERS_H
#define OPTIMIZED_FILTERS_H

#include <stdint.h>
#include <stdbool.h>

#define FILTER_BUFFER_SIZE 256

// ============================================================================
// توابع API
// ============================================================================

/**
 * @brief مقداردهی اولیه فیلترهای بهینه
 * @return true در صورت موفقیت
 */
bool optimized_filters_init(void);

/**
 * @brief فیلتر lowpass بهینه
 * @param input داده ورودی
 * @param output داده خروجی
 * @param size اندازه داده
 * @param cutoff_freq فرکانس قطع
 * @param sampling_rate نرخ نمونه‌برداری
 * @return true در صورت موفقیت
 */
bool optimized_lowpass_filter(
    const float *input,
    float *output,
    uint32_t size,
    float cutoff_freq,
    uint32_t sampling_rate
);

/**
 * @brief فیلتر bandpass بهینه
 */
bool optimized_bandpass_filter(
    const float *input,
    float *output,
    uint32_t size,
    float low_freq,
    float high_freq,
    uint32_t sampling_rate
);

/**
 * @brief فیلتر highpass بهینه
 */
bool optimized_highpass_filter(
    const float *input,
    float *output,
    uint32_t size,
    float cutoff_freq,
    uint32_t sampling_rate
);

/**
 * @brief بهینه‌سازی adaptive sampling rate
 * @param signal سیگنال
 * @param current_rate نرخ فعلی
 * @param optimized_rate نرخ بهینه شده
 * @return true در صورت موفقیت
 */
bool adaptive_sampling_rate_optimization(
    const float *signal,
    uint32_t current_rate,
    uint32_t *optimized_rate
);

/**
 * @brief خاموش کردن ماژول
 */
void optimized_filters_deinit(void);

#endif // OPTIMIZED_FILTERS_H

