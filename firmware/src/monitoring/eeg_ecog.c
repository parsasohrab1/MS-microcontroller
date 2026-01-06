/**
 * @file eeg_ecog.c
 * @brief پیاده‌سازی ماژول ثبت سیگنال‌های عصبی
 * @version 0.2.0
 */

#include "eeg_ecog.h"
#include "../system/hal.h"
#include <string.h>

// ============================================================================
// متغیرهای داخلی
// ============================================================================

static bool eeg_initialized = false;
static bool recording_active = false;
static signal_type_t current_signal_type;
static uint16_t current_sampling_rate = 0;
static uint32_t frame_counter = 0;
static uint16_t channel_gains[EEG_CHANNELS];

// ============================================================================
// توابع داخلی
// ============================================================================

/**
 * @brief مقداردهی اولیه ADC و کانال‌ها
 */
static bool adc_init_internal(void)
{
    // مقداردهی اولیه ADC با وضوح 12 بیت
    if (!hal_adc_init(12)) {
        return false;
    }
    
    // مقداردهی اولیه gain برای تمام کانال‌ها
    for (uint16_t i = 0; i < EEG_CHANNELS; i++) {
        channel_gains[i] = 1000; // پیش‌فرض: gain = 1000
    }
    
    return true;
}

/**
 * @brief خواندن نمونه از ADC
 */
static bool adc_read_sample(uint16_t channel_id, int16_t *value)
{
    if (channel_id >= EEG_CHANNELS || !value) {
        return false;
    }
    
    // خواندن از ADC (کانال‌های 0-7 برای nRF52840)
    // برای 32 کانال، نیاز به multiplexer یا چند ADC
    uint8_t adc_channel = channel_id % 8; // استفاده از 8 کانال ADC موجود
    
    uint16_t raw_value;
    if (!hal_adc_read(adc_channel, &raw_value)) {
        return false;
    }
    
    // تبدیل به signed 16-bit
    // ADC 12-bit: 0-4095 -> تبدیل به -2048 تا +2047
    *value = (int16_t)((int32_t)raw_value - 2048);
    
    // اعمال gain
    *value = (int16_t)((int32_t)(*value) * channel_gains[channel_id] / 1000);
    
    return true;
}

// ============================================================================
// Callback تایمر برای نمونه‌برداری
// ============================================================================

static void sampling_timer_callback(void)
{
    // این تابع توسط تایمر فراخوانی می‌شود
    // در اینجا می‌توانیم نمونه‌برداری را انجام دهیم
    // یا یک flag را set کنیم
}

// ============================================================================
// توابع API عمومی
// ============================================================================

bool eeg_ecog_init(signal_type_t type)
{
    if (eeg_initialized) {
        return true;
    }
    
    current_signal_type = type;
    
    // مقداردهی اولیه ADC
    if (!adc_init_internal()) {
        return false;
    }
    
    eeg_initialized = true;
    return true;
}

bool eeg_ecog_start_recording(uint16_t sampling_rate)
{
    if (!eeg_initialized) {
        return false;
    }
    
    if (sampling_rate == 0 || sampling_rate > 1000) {
        return false;  // محدودیت نرخ نمونه‌برداری
    }
    
    current_sampling_rate = sampling_rate;
    recording_active = true;
    frame_counter = 0;
    
    // راه‌اندازی تایمر برای نمونه‌برداری
    uint32_t timer_freq = sampling_rate; // Hz
    if (!hal_timer_init(timer_freq, sampling_timer_callback)) {
        return false;
    }
    
    hal_timer_start();
    
    return true;
}

void eeg_ecog_stop_recording(void)
{
    recording_active = false;
    hal_timer_stop();
}

bool eeg_ecog_read_frame(eeg_frame_t *frame)
{
    if (!eeg_initialized || !frame || !recording_active) {
        return false;
    }
    
    // خواندن تمام کانال‌ها
    for (uint16_t i = 0; i < EEG_CHANNELS; i++) {
        channel_sample_t *sample = &frame->channels[i];
        
        sample->channel_id = i;
        sample->valid = false;
        
        // خواندن از ADC
        int16_t raw_value;
        if (adc_read_sample(i, &raw_value)) {
            sample->sample_value = raw_value;
            sample->timestamp = hal_rtc_get_time_ms();
            sample->valid = true;
        }
    }
    
    frame->frame_timestamp = hal_rtc_get_time_ms();
    frame->frame_number = frame_counter++;
    
    return true;
}

bool eeg_ecog_read_channel(uint16_t channel_id, channel_sample_t *sample)
{
    if (!eeg_initialized || !sample || channel_id >= EEG_CHANNELS) {
        return false;
    }
    
    sample->channel_id = channel_id;
    sample->valid = false;
    
    // خواندن از ADC
    int16_t raw_value;
    if (adc_read_sample(channel_id, &raw_value)) {
        sample->sample_value = raw_value;
        sample->timestamp = hal_rtc_get_time_ms();
        sample->valid = true;
        return true;
    }
    
    return false;
}

bool eeg_ecog_channel_health_check(uint16_t channel_id)
{
    if (!eeg_initialized || channel_id >= EEG_CHANNELS) {
        return false;
    }
    
    // خواندن چند نمونه و بررسی
    int16_t samples[10];
    bool all_valid = true;
    
    for (int i = 0; i < 10; i++) {
        if (!adc_read_sample(channel_id, &samples[i])) {
            all_valid = false;
            break;
        }
    }
    
    if (!all_valid) {
        return false;
    }
    
    // بررسی محدوده سیگنال (نباید در حالت saturation باشد)
    for (int i = 0; i < 10; i++) {
        if (samples[i] > 3000 || samples[i] < -3000) {
            return false; // احتمال saturation
        }
    }
    
    // بررسی نویز (انحراف معیار نباید خیلی زیاد باشد)
    // TODO: محاسبه انحراف معیار
    
    return true;
}

bool eeg_ecog_set_gain(uint16_t channel_id, uint16_t gain)
{
    if (!eeg_initialized || channel_id >= EEG_CHANNELS) {
        return false;
    }
    
    if (gain < 1 || gain > 1000) {
        return false;  // محدودیت تقویت
    }
    
    channel_gains[channel_id] = gain;
    
    // TODO: تنظیم PGA (Programmable Gain Amplifier) در سخت‌افزار
    // این نیاز به کنترل سخت‌افزاری دارد
    
    return true;
}

void eeg_ecog_deinit(void)
{
    if (!eeg_initialized) {
        return;
    }
    
    eeg_ecog_stop_recording();
    
    eeg_initialized = false;
}
