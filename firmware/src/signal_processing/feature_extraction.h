/**
 * @file feature_extraction.h
 * @brief استخراج ویژگی از سیگنال EEG/ECoG
 * @version 0.1.0
 */

#ifndef FEATURE_EXTRACTION_H
#define FEATURE_EXTRACTION_H

#include <stdint.h>
#include <stdbool.h>
#include "../monitoring/eeg_ecog.h"

// ============================================================================
// ساختار ویژگی‌های استخراج شده
// ============================================================================

typedef struct {
    // ویژگی‌های فرکانسی
    float power_delta;      // قدرت باند دلتا (0.5-4 Hz)
    float power_theta;      // قدرت باند تتا (4-8 Hz)
    float power_alpha;      // قدرت باند آلفا (8-13 Hz)
    float power_beta;       // قدرت باند بتا (13-30 Hz)
    float power_gamma;      // قدرت باند گاما (30-100 Hz)
    
    // ویژگی‌های آماری
    float mean;             // میانگین
    float std_dev;          // انحراف معیار
    float variance;         // واریانس
    float rms;              // Root Mean Square
    
    // ویژگی‌های زمانی
    float zero_crossing_rate; // نرخ عبور از صفر
    
    bool valid;
} eeg_features_t;

// ============================================================================
// توابع API
// ============================================================================

/**
 * @brief استخراج ویژگی از یک کانال EEG
 * @param samples آرایه نمونه‌ها
 * @param length تعداد نمونه‌ها
 * @param sampling_rate نرخ نمونه‌برداری (Hz)
 * @param features اشاره‌گر به ساختار ویژگی‌های خروجی
 * @return true در صورت موفقیت
 */
bool extract_features(const int16_t *samples, uint16_t length, 
                      uint16_t sampling_rate, eeg_features_t *features);

/**
 * @brief استخراج ویژگی از تمام کانال‌های یک فریم
 * @param frame فریم EEG
 * @param features_array آرایه ویژگی‌ها (باید 32 عنصر داشته باشد)
 * @return تعداد کانال‌های پردازش شده
 */
uint8_t extract_features_all_channels(const eeg_frame_t *frame, 
                                      eeg_features_t *features_array);

/**
 * @brief محاسبه FFT برای تحلیل فرکانسی
 * @param samples آرایه نمونه‌ها
 * @param length تعداد نمونه‌ها (باید توان 2 باشد)
 * @param fft_output آرایه خروجی FFT (complex)
 * @return true در صورت موفقیت
 */
bool compute_fft(const int16_t *samples, uint16_t length, float *fft_output);

#endif // FEATURE_EXTRACTION_H

