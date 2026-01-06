/**
 * @file optimized_filters.c
 * @brief فیلترهای بهینه‌سازی شده برای کاهش مصرف انرژی
 * @version 1.0.0
 */

#include "optimized_filters.h"
#include "../system/hardware_accelerators.h"
#include "../system/power_management.h"
#include "../system/hal.h"
#include <string.h>
#include <math.h>

// ============================================================================
// متغیرهای داخلی
// ============================================================================

static bool optimized_filters_initialized = false;
static float filter_buffer[FILTER_BUFFER_SIZE];
static uint32_t buffer_index = 0;

// ============================================================================
// توابع داخلی
// ============================================================================

/**
 * @brief محاسبه workload برای بهینه‌سازی DVFS
 */
static uint8_t calculate_workload(uint32_t samples_per_second)
{
    // Map samples/sec به workload (0-100)
    if (samples_per_second > 1000) {
        return 100;
    } else if (samples_per_second > 500) {
        return 80;
    } else if (samples_per_second > 100) {
        return 50;
    } else if (samples_per_second > 10) {
        return 20;
    } else {
        return 5;
    }
}

/**
 * @brief بهینه‌سازی adaptive sampling rate
 */
static uint32_t optimize_sampling_rate(uint32_t current_rate, float signal_variance)
{
    // اگر variance پایین است، sampling rate را کاهش می‌دهیم
    if (signal_variance < 0.01) {
        return current_rate / 2;  // نصف کردن
    } else if (signal_variance < 0.1) {
        return (current_rate * 3) / 4;  // 75%
    }
    
    return current_rate;  // بدون تغییر
}

// ============================================================================
// توابع API عمومی
// ============================================================================

bool optimized_filters_init(void)
{
    if (optimized_filters_initialized) {
        return true;
    }
    
    memset(filter_buffer, 0, sizeof(filter_buffer));
    buffer_index = 0;
    
    // فعال کردن FFT accelerator
    hw_accelerator_enable(HW_ACCEL_FFT);
    
    optimized_filters_initialized = true;
    return true;
}

bool optimized_lowpass_filter(
    const float *input,
    float *output,
    uint32_t size,
    float cutoff_freq,
    uint32_t sampling_rate
)
{
    if (!optimized_filters_initialized || !input || !output || size == 0) {
        return false;
    }
    
    // محاسبه workload
    uint8_t workload = calculate_workload(sampling_rate);
    
    // بهینه‌سازی DVFS
    power_optimize_for_workload(workload);
    
    // استفاده از hardware accelerator برای FFT (اگر ممکن باشد)
    if (size >= 64 && hw_accelerator_is_enabled(HW_ACCEL_FFT)) {
        // استفاده از FFT-based filtering (سریع‌تر)
        float fft_input[FILTER_BUFFER_SIZE];
        float fft_output[FILTER_BUFFER_SIZE];
        
        // کپی داده
        memcpy(fft_input, input, size * sizeof(float));
        
        // اجرای FFT
        if (hw_accel_fft_execute(fft_input, fft_output, size)) {
            // اعمال lowpass filter در frequency domain
            uint32_t cutoff_bin = (cutoff_freq * size) / sampling_rate;
            
            for (uint32_t i = cutoff_bin; i < size; i++) {
                fft_output[i] = 0.0f;
            }
            
            // Inverse FFT (با accelerator)
            // TODO: پیاده‌سازی IFFT
            
            // کپی به output
            memcpy(output, fft_output, size * sizeof(float));
            
            return true;
        }
    }
    
    // Fallback به software filter (IIR)
    // استفاده از IIR filter که مصرف انرژی کمتری دارد
    static float prev_output = 0.0f;
    float alpha = cutoff_freq / sampling_rate;
    
    for (uint32_t i = 0; i < size; i++) {
        output[i] = alpha * input[i] + (1.0f - alpha) * prev_output;
        prev_output = output[i];
    }
    
    return true;
}

bool optimized_bandpass_filter(
    const float *input,
    float *output,
    uint32_t size,
    float low_freq,
    float high_freq,
    uint32_t sampling_rate
)
{
    if (!optimized_filters_initialized || !input || !output || size == 0) {
        return false;
    }
    
    // محاسبه workload
    uint8_t workload = calculate_workload(sampling_rate);
    power_optimize_for_workload(workload);
    
    // استفاده از cascade lowpass و highpass
    float temp[FILTER_BUFFER_SIZE];
    
    // Highpass filter
    optimized_highpass_filter(input, temp, size, low_freq, sampling_rate);
    
    // Lowpass filter
    optimized_lowpass_filter(temp, output, size, high_freq, sampling_rate);
    
    return true;
}

bool optimized_highpass_filter(
    const float *input,
    float *output,
    uint32_t size,
    float cutoff_freq,
    uint32_t sampling_rate
)
{
    if (!optimized_filters_initialized || !input || !output || size == 0) {
        return false;
    }
    
    // محاسبه workload
    uint8_t workload = calculate_workload(sampling_rate);
    power_optimize_for_workload(workload);
    
    // استفاده از IIR highpass filter
    static float prev_input = 0.0f;
    static float prev_output = 0.0f;
    float alpha = cutoff_freq / sampling_rate;
    
    for (uint32_t i = 0; i < size; i++) {
        output[i] = alpha * (prev_output + input[i] - prev_input);
        prev_input = input[i];
        prev_output = output[i];
    }
    
    return true;
}

bool adaptive_sampling_rate_optimization(
    const float *signal,
    uint32_t current_rate,
    uint32_t *optimized_rate
)
{
    if (!optimized_filters_initialized || !signal || !optimized_rate) {
        return false;
    }
    
    // محاسبه variance سیگنال
    float mean = 0.0f;
    for (uint32_t i = 0; i < FILTER_BUFFER_SIZE; i++) {
        mean += signal[i];
    }
    mean /= FILTER_BUFFER_SIZE;
    
    float variance = 0.0f;
    for (uint32_t i = 0; i < FILTER_BUFFER_SIZE; i++) {
        float diff = signal[i] - mean;
        variance += diff * diff;
    }
    variance /= FILTER_BUFFER_SIZE;
    
    // بهینه‌سازی sampling rate
    *optimized_rate = optimize_sampling_rate(current_rate, variance);
    
    // تنظیم DVFS بر اساس rate جدید
    uint8_t workload = calculate_workload(*optimized_rate);
    power_optimize_for_workload(workload);
    
    return true;
}

void optimized_filters_deinit(void)
{
    if (!optimized_filters_initialized) {
        return;
    }
    
    hw_accelerator_disable(HW_ACCEL_FFT);
    
    optimized_filters_initialized = false;
}

