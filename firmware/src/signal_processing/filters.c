/**
 * @file filters.c
 * @brief پیاده‌سازی فیلترهای دیجیتال
 * @version 0.1.0
 */

#include "filters.h"
#include <stdlib.h>
#include <string.h>
#include <math.h>

// ============================================================================
// توابع داخلی
// ============================================================================

/**
 * @brief محاسبه ضرایب فیلتر Low-Pass Butterworth (مرتبه 2)
 * استفاده از تبدیل bilinear برای تبدیل از s-domain به z-domain
 */
static bool calculate_butterworth_lp_coeffs(filter_t *filter)
{
    if (filter->order != 2) {
        // برای سادگی، فقط مرتبه 2 را پیاده‌سازی می‌کنیم
        // برای مرتبه‌های بالاتر نیاز به محاسبات پیچیده‌تر است
        return false;
    }
    
    float fc = filter->cutoff_freq;
    float fs = filter->sampling_freq;
    
    // محاسبه فرکانس نرمال‌شده
    float wc = 2.0f * 3.14159265359f * fc / fs;
    
    // ضرایب Butterworth مرتبه 2 در s-domain: 1/(s^2 + sqrt(2)*s + 1)
    // تبدیل bilinear: s = 2*fs*(z-1)/(z+1)
    
    // محاسبه ضرایب IIR (Direct Form II)
    // H(z) = (b0 + b1*z^-1 + b2*z^-2) / (1 + a1*z^-1 + a2*z^-2)
    
    float k = tanf(wc / 2.0f);
    float k2 = k * k;
    float sqrt2 = 1.41421356237f;
    
    float a0 = 1.0f + sqrt2 * k + k2;
    
    // ضرایب مخرج (a)
    filter->coefficients[0] = 1.0f;  // a0 (همیشه 1)
    filter->coefficients[1] = 2.0f * (k2 - 1.0f) / a0;  // a1
    filter->coefficients[2] = (1.0f - sqrt2 * k + k2) / a0;  // a2
    
    // ضرایب صورت (b)
    filter->coefficients[3] = k2 / a0;  // b0
    filter->coefficients[4] = 2.0f * k2 / a0;  // b1
    filter->coefficients[5] = k2 / a0;  // b2
    
    return true;
}

/**
 * @brief محاسبه ضرایب فیلتر Notch (مرتبه 2)
 * فیلتر Notch برای حذف فرکانس خاص (50/60Hz)
 */
static bool calculate_notch_coeffs(filter_t *filter, float notch_freq)
{
    if (filter->order != 2) {
        return false;
    }
    
    float fn = notch_freq;
    float fs = filter->sampling_freq;
    
    // محاسبه فرکانس نرمال‌شده
    float w = 2.0f * 3.14159265359f * fn / fs;
    
    // Q factor (عرض باند) - برای Notch باریک، Q بالا
    float Q = 30.0f;  // Q factor بالا برای حذف دقیق
    
    // محاسبه ضرایب
    float r = 1.0f - (3.14159265359f * fn) / (Q * fs);
    float cos_w = cosf(w);
    
    // ضرایب مخرج (a)
    filter->coefficients[0] = 1.0f;  // a0
    filter->coefficients[1] = -2.0f * r * cos_w;  // a1
    filter->coefficients[2] = r * r;  // a2
    
    // ضرایب صورت (b) - برای Notch، b0=1, b1=-2*cos(w), b2=1
    filter->coefficients[3] = 1.0f;  // b0
    filter->coefficients[4] = -2.0f * cos_w;  // b1
    filter->coefficients[5] = 1.0f;  // b2
    
    // نرمال‌سازی (تقسیم بر a0)
    float a0 = filter->coefficients[0];
    for (int i = 1; i < 6; i++) {
        filter->coefficients[i] /= a0;
    }
    
    return true;
}

// ============================================================================
// توابع API عمومی
// ============================================================================

bool filter_init(filter_t *filter, filter_type_t type, 
                 float cutoff_freq, float sampling_freq, uint16_t order)
{
    if (!filter || cutoff_freq <= 0 || sampling_freq <= 0 || order == 0) {
        return false;
    }
    
    // بررسی محدودیت‌ها
    if (cutoff_freq >= sampling_freq / 2) {
        return false;  // فرکانس قطع باید کمتر از Nyquist باشد
    }
    
    memset(filter, 0, sizeof(filter_t));
    
    filter->type = type;
    filter->cutoff_freq = cutoff_freq;
    filter->sampling_freq = sampling_freq;
    filter->order = order;
    
    // تخصیص حافظه برای ضرایب و حالت
    // برای فیلتر IIR مرتبه N، نیاز به N+1 ضریب و N حالت
    size_t coeff_size = (order + 1) * sizeof(float);
    size_t state_size = order * sizeof(float);
    
    filter->coefficients = (float*)malloc(coeff_size);
    filter->state_buffer = (float*)malloc(state_size);
    
    if (!filter->coefficients || !filter->state_buffer) {
        filter_deinit(filter);
        return false;
    }
    
    memset(filter->coefficients, 0, coeff_size);
    memset(filter->state_buffer, 0, state_size);
    
    // محاسبه ضرایب بر اساس نوع فیلتر
    bool success = false;
    switch (type) {
        case FILTER_TYPE_LOW_PASS:
            success = calculate_butterworth_lp_coeffs(filter);
            break;
        case FILTER_TYPE_NOTCH:
            success = calculate_notch_coeffs(filter, cutoff_freq);
            break;
        default:
            // TODO: پیاده‌سازی سایر انواع فیلتر
            success = false;
            break;
    }
    
    if (!success) {
        filter_deinit(filter);
        return false;
    }
    
    filter->initialized = true;
    return true;
}

bool filter_process(filter_t *filter, float input, float *output)
{
    if (!filter || !filter->initialized || !output) {
        return false;
    }
    
    // پیاده‌سازی فیلتر IIR مرتبه 2 (Direct Form II)
    // H(z) = (b0 + b1*z^-1 + b2*z^-2) / (1 + a1*z^-1 + a2*z^-2)
    
    // ضرایب: [a0, a1, a2, b0, b1, b2]
    float *a = filter->coefficients;      // a0, a1, a2
    float *b = &filter->coefficients[3];  // b0, b1, b2
    
    // حالت‌ها: [w[n-1], w[n-2]]
    float *w = filter->state_buffer;  // w[n-1], w[n-2]
    
    // محاسبه w[n] = x[n] - a1*w[n-1] - a2*w[n-2]
    float wn = input - a[1] * w[0] - a[2] * w[1];
    
    // محاسبه y[n] = b0*w[n] + b1*w[n-1] + b2*w[n-2]
    *output = b[0] * wn + b[1] * w[0] + b[2] * w[1];
    
    // به‌روزرسانی حالت‌ها
    w[1] = w[0];  // w[n-2] = w[n-1]
    w[0] = wn;    // w[n-1] = w[n]
    
    return true;
}

uint16_t filter_process_array(filter_t *filter, const float *input, 
                              float *output, uint16_t length)
{
    if (!filter || !filter->initialized || !input || !output || length == 0) {
        return 0;
    }
    
    uint16_t processed = 0;
    for (uint16_t i = 0; i < length; i++) {
        if (filter_process(filter, input[i], &output[i])) {
            processed++;
        } else {
            break;
        }
    }
    
    return processed;
}

bool filter_create_notch(filter_t *filter, float notch_freq, float sampling_freq)
{
    if (!filter) {
        return false;
    }
    
    // ایجاد فیلتر Notch با Q factor مناسب
    // برای حذف نویز 50/60Hz با پهنای باند باریک
    return filter_init(filter, FILTER_TYPE_NOTCH, notch_freq, sampling_freq, 2);
}

void filter_deinit(filter_t *filter)
{
    if (!filter) {
        return;
    }
    
    if (filter->coefficients) {
        free(filter->coefficients);
        filter->coefficients = NULL;
    }
    
    if (filter->state_buffer) {
        free(filter->state_buffer);
        filter->state_buffer = NULL;
    }
    
    memset(filter, 0, sizeof(filter_t));
}

