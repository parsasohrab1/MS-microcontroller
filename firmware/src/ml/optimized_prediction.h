/**
 * @file optimized_prediction.h
 * @brief هدر پیش‌بینی بهینه‌سازی شده
 * @version 1.0.0
 */

#ifndef OPTIMIZED_PREDICTION_H
#define OPTIMIZED_PREDICTION_H

#include <stdint.h>
#include <stdbool.h>
#include "prediction.h"

#define ML_INPUT_SIZE 47   // 32 (EEG) + 10 (biomarkers) + 5 (physiological)
#define ML_OUTPUT_SIZE 4   // 4 classes

// ============================================================================
// توابع API
// ============================================================================

/**
 * @brief مقداردهی اولیه پیش‌بینی بهینه
 * @return true در صورت موفقیت
 */
bool optimized_prediction_init(void);

/**
 * @brief اجرای پیش‌بینی بهینه
 * @param input ویژگی‌های ورودی
 * @param output نتیجه پیش‌بینی
 * @return true در صورت موفقیت
 */
bool optimized_prediction_run(const model_input_t *input, prediction_t *output);

/**
 * @brief فعال/غیرفعال کردن parallel processing
 * @param enable true برای فعال
 * @return true در صورت موفقیت
 */
bool optimized_prediction_enable_parallel_processing(bool enable);

/**
 * @brief دریافت زمان آخرین inference
 * @return زمان (ms)
 */
uint32_t optimized_prediction_get_last_inference_time(void);

/**
 * @brief خاموش کردن ماژول
 */
void optimized_prediction_deinit(void);

#endif // OPTIMIZED_PREDICTION_H

