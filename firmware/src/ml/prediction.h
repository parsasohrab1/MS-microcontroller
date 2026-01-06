/**
 * @file prediction.h
 * @brief ماژول پیش‌بینی حملات MS با استفاده از TinyML
 * @version 0.1.0
 */

#ifndef PREDICTION_H
#define PREDICTION_H

#include <stdint.h>
#include <stdbool.h>
#include "../config.h"

// ============================================================================
// انواع پیش‌بینی
// ============================================================================

typedef enum {
    PREDICTION_RESULT_NORMAL = 0,
    PREDICTION_RESULT_WARNING,
    PREDICTION_RESULT_ATTACK_IMMINENT,
    PREDICTION_RESULT_ATTACK_ACTIVE
} prediction_result_t;

// ============================================================================
// ساختار نتیجه پیش‌بینی
// ============================================================================

typedef struct {
    prediction_result_t result;
    float confidence;           // اطمینان (0.0 - 1.0)
    uint32_t timestamp;
    float risk_score;           // امتیاز خطر (0.0 - 1.0)
    bool valid;
} prediction_t;

// ============================================================================
// ساختار ویژگی‌های ورودی مدل
// ============================================================================

typedef struct {
    float eeg_features[32];     // ویژگی‌های استخراج شده از EEG
    float biomarker_values[BIOMARKER_COUNT];  // مقادیر بیومارکرها
    float physiological_params[5];  // پارامترهای فیزیولوژیک
    uint32_t timestamp;
} model_input_t;

// ============================================================================
// توابع API
// ============================================================================

/**
 * @brief مقداردهی اولیه ماژول پیش‌بینی
 * @return true در صورت موفقیت
 */
bool prediction_init(void);

/**
 * @brief بارگذاری مدل TinyML
 * @param model_data داده مدل (از حافظه فلش یا RAM)
 * @param model_size اندازه مدل (bytes)
 * @return true در صورت موفقیت
 */
bool prediction_load_model(const uint8_t *model_data, uint32_t model_size);

/**
 * @brief اجرای پیش‌بینی
 * @param input ویژگی‌های ورودی
 * @param output نتیجه پیش‌بینی
 * @return true در صورت موفقیت
 */
bool prediction_run(const model_input_t *input, prediction_t *output);

/**
 * @brief بررسی آماده بودن مدل
 * @return true اگر مدل بارگذاری شده است
 */
bool prediction_is_ready(void);

/**
 * @brief دریافت زمان اجرای آخرین پیش‌بینی (ms)
 * @return زمان اجرا
 */
uint32_t prediction_get_last_inference_time(void);

/**
 * @brief خاموش کردن ماژول
 */
void prediction_deinit(void);

#endif // PREDICTION_H

