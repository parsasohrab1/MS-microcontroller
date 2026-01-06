/**
 * @file eeg_ecog.h
 * @brief ماژول ثبت سیگنال‌های عصبی EEG/ECoG
 * @version 0.1.0
 */

#ifndef EEG_ECOG_H
#define EEG_ECOG_H

#include <stdint.h>
#include <stdbool.h>
#include "../config.h"

// ============================================================================
// انواع سیگنال
// ============================================================================

typedef enum {
    SIGNAL_TYPE_EEG = 0,
    SIGNAL_TYPE_ECOG
} signal_type_t;

// ============================================================================
// ساختار داده کانال
// ============================================================================

typedef struct {
    uint16_t channel_id;        // شناسه کانال (0-31)
    int16_t sample_value;       // مقدار نمونه (12-16 bit ADC)
    uint32_t timestamp;        // زمان نمونه
    bool valid;                 // اعتبار نمونه
} channel_sample_t;

// ============================================================================
// ساختار داده تمام کانال‌ها
// ============================================================================

typedef struct {
    channel_sample_t channels[EEG_CHANNELS];
    uint32_t frame_timestamp;
    uint16_t frame_number;
} eeg_frame_t;

// ============================================================================
// توابع API
// ============================================================================

/**
 * @brief مقداردهی اولیه ماژول EEG/ECoG
 * @param type نوع سیگنال (EEG یا ECoG)
 * @return true در صورت موفقیت
 */
bool eeg_ecog_init(signal_type_t type);

/**
 * @brief شروع ثبت پیوسته
 * @param sampling_rate نرخ نمونه‌برداری (Hz)
 * @return true در صورت موفقیت
 */
bool eeg_ecog_start_recording(uint16_t sampling_rate);

/**
 * @brief توقف ثبت
 */
void eeg_ecog_stop_recording(void);

/**
 * @brief خواندن یک فریم از تمام کانال‌ها
 * @param frame اشاره‌گر به ساختار فریم خروجی
 * @return true در صورت موفقیت
 */
bool eeg_ecog_read_frame(eeg_frame_t *frame);

/**
 * @brief خواندن نمونه از یک کانال خاص
 * @param channel_id شناسه کانال (0-31)
 * @param sample اشاره‌گر به نمونه خروجی
 * @return true در صورت موفقیت
 */
bool eeg_ecog_read_channel(uint16_t channel_id, channel_sample_t *sample);

/**
 * @brief بررسی سلامت کانال
 * @param channel_id شناسه کانال
 * @return true اگر کانال سالم است
 */
bool eeg_ecog_channel_health_check(uint16_t channel_id);

/**
 * @brief تنظیم تقویت (Gain) کانال
 * @param channel_id شناسه کانال
 * @param gain مقدار تقویت (1-1000)
 * @return true در صورت موفقیت
 */
bool eeg_ecog_set_gain(uint16_t channel_id, uint16_t gain);

/**
 * @brief خاموش کردن ماژول
 */
void eeg_ecog_deinit(void);

#endif // EEG_ECOG_H

