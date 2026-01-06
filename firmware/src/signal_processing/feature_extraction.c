/**
 * @file feature_extraction.c
 * @brief پیاده‌سازی استخراج ویژگی
 * @version 0.1.0
 */

#include "feature_extraction.h"
#include <string.h>
#include <math.h>

// ============================================================================
// توابع داخلی
// ============================================================================

/**
 * @brief محاسبه میانگین
 */
static float calculate_mean(const int16_t *samples, uint16_t length)
{
    int32_t sum = 0;
    for (uint16_t i = 0; i < length; i++) {
        sum += samples[i];
    }
    return (float)sum / (float)length;
}

/**
 * @brief محاسبه واریانس
 */
static float calculate_variance(const int16_t *samples, uint16_t length, float mean)
{
    float sum_sq_diff = 0.0f;
    for (uint16_t i = 0; i < length; i++) {
        float diff = (float)samples[i] - mean;
        sum_sq_diff += diff * diff;
    }
    return sum_sq_diff / (float)length;
}

/**
 * @brief محاسبه قدرت باند فرکانسی با استفاده از FFT ساده
 */
static float calculate_band_power(const int16_t *samples, uint16_t length,
                                  uint16_t sampling_rate, float low_freq, float high_freq)
{
    // برای سادگی، از روش ساده‌تر استفاده می‌کنیم
    // در پیاده‌سازی کامل، باید FFT استفاده شود
    
    // محاسبه RMS برای تخمین قدرت
    float rms = 0.0f;
    for (uint16_t i = 0; i < length; i++) {
        float sample = (float)samples[i];
        rms += sample * sample;
    }
    rms = sqrtf(rms / (float)length);
    
    // TODO: استفاده از FFT واقعی برای محاسبه دقیق‌تر
    // این یک تخمین ساده است
    
    return rms;
}

/**
 * @brief محاسبه نرخ عبور از صفر
 */
static float calculate_zero_crossing_rate(const int16_t *samples, uint16_t length)
{
    uint16_t crossings = 0;
    
    for (uint16_t i = 1; i < length; i++) {
        if ((samples[i-1] >= 0 && samples[i] < 0) ||
            (samples[i-1] < 0 && samples[i] >= 0)) {
            crossings++;
        }
    }
    
    return (float)crossings / (float)length;
}

// ============================================================================
// توابع API عمومی
// ============================================================================

bool extract_features(const int16_t *samples, uint16_t length, 
                      uint16_t sampling_rate, eeg_features_t *features)
{
    if (!samples || !features || length == 0) {
        return false;
    }
    
    memset(features, 0, sizeof(eeg_features_t));
    
    // محاسبه ویژگی‌های آماری
    features->mean = calculate_mean(samples, length);
    features->variance = calculate_variance(samples, length, features->mean);
    features->std_dev = sqrtf(features->variance);
    
    // محاسبه RMS
    float sum_sq = 0.0f;
    for (uint16_t i = 0; i < length; i++) {
        float sample = (float)samples[i];
        sum_sq += sample * sample;
    }
    features->rms = sqrtf(sum_sq / (float)length);
    
    // محاسبه قدرت باندهای فرکانسی
    features->power_delta = calculate_band_power(samples, length, sampling_rate, 0.5f, 4.0f);
    features->power_theta = calculate_band_power(samples, length, sampling_rate, 4.0f, 8.0f);
    features->power_alpha = calculate_band_power(samples, length, sampling_rate, 8.0f, 13.0f);
    features->power_beta = calculate_band_power(samples, length, sampling_rate, 13.0f, 30.0f);
    features->power_gamma = calculate_band_power(samples, length, sampling_rate, 30.0f, 100.0f);
    
    // محاسبه نرخ عبور از صفر
    features->zero_crossing_rate = calculate_zero_crossing_rate(samples, length);
    
    features->valid = true;
    return true;
}

uint8_t extract_features_all_channels(const eeg_frame_t *frame, 
                                      eeg_features_t *features_array)
{
    if (!frame || !features_array) {
        return 0;
    }
    
    uint8_t success_count = 0;
    
    // برای هر کانال، نیاز به بافر نمونه‌ها داریم
    // در اینجا فرض می‌کنیم که از یک فریم استفاده می‌کنیم
    // در واقعیت، نیاز به چندین فریم برای استخراج ویژگی داریم
    
    // TODO: جمع‌آوری نمونه‌های کافی از چندین فریم
    // برای استخراج ویژگی نیاز به window size مناسب داریم (مثلاً 1 ثانیه)
    
    for (uint16_t i = 0; i < EEG_CHANNELS; i++) {
        // برای سادگی، از یک نمونه استفاده می‌کنیم
        // در پیاده‌سازی کامل، باید window از نمونه‌ها جمع‌آوری شود
        int16_t sample = frame->channels[i].sample_value;
        
        // استخراج ویژگی (با window size = 1 برای مثال)
        if (extract_features(&sample, 1, SAMPLING_RATE_EEG, &features_array[i])) {
            success_count++;
        }
    }
    
    return success_count;
}

bool compute_fft(const int16_t *samples, uint16_t length, float *fft_output)
{
    if (!samples || !fft_output || length == 0) {
        return false;
    }
    
    // بررسی اینکه length توان 2 باشد
    if ((length & (length - 1)) != 0) {
        return false;  // length باید توان 2 باشد
    }
    
    // TODO: پیاده‌سازی FFT
    // برای میکروکنترلر، می‌توان از FFT fixed-point استفاده کرد
    // یا از کتابخانه‌های بهینه شده
    
    // Placeholder - باید با FFT واقعی جایگزین شود
    // این یک پیاده‌سازی ساده DFT است (کند اما کار می‌کند)
    
    uint16_t N = length;
    for (uint16_t k = 0; k < N; k++) {
        float real = 0.0f;
        float imag = 0.0f;
        
        for (uint16_t n = 0; n < N; n++) {
            float angle = 2.0f * 3.14159265359f * k * n / N;
            float sample = (float)samples[n];
            real += sample * cosf(angle);
            imag -= sample * sinf(angle);
        }
        
        // ذخیره magnitude
        fft_output[k] = sqrtf(real * real + imag * imag);
    }
    
    return true;
}

