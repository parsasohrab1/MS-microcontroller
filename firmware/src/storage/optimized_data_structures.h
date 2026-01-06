/**
 * @file optimized_data_structures.h
 * @brief ساختارهای داده بهینه‌سازی شده
 * @version 1.0.0
 */

#ifndef OPTIMIZED_DATA_STRUCTURES_H
#define OPTIMIZED_DATA_STRUCTURES_H

#include <stdint.h>
#include <stdbool.h>

// ============================================================================
// ساختارهای داده بهینه
// ============================================================================

/**
 * @brief ساختار EEG sample بهینه (کاهش از 4 bytes به 2 bytes)
 */
typedef struct {
    int16_t value;      // 2 bytes (کاهش از float)
    uint16_t timestamp; // 2 bytes (relative timestamp)
} __attribute__((packed)) optimized_eeg_sample_t;

/**
 * @brief ساختار Biomarker بهینه
 */
typedef struct {
    uint8_t type;       // 1 byte
    uint16_t value;     // 2 bytes (کاهش از float)
    uint8_t quality;    // 1 byte (quality indicator)
} __attribute__((packed)) optimized_biomarker_t;

/**
 * @brief ساختار Prediction result بهینه
 */
typedef struct {
    uint8_t result;     // 1 byte (enum)
    uint8_t confidence; // 1 byte (0-255 = 0.0-1.0)
    uint16_t risk_score; // 2 bytes (0-65535 = 0.0-1.0)
} __attribute__((packed)) optimized_prediction_result_t;

// ============================================================================
// توابع تبدیل
// ============================================================================

/**
 * @brief تبدیل float به int16_t (با scaling)
 */
static inline int16_t float_to_int16(float value, float scale)
{
    return (int16_t)(value * scale);
}

/**
 * @brief تبدیل int16_t به float
 */
static inline float int16_to_float(int16_t value, float scale)
{
    return (float)value / scale;
}

/**
 * @brief تبدیل float به uint8_t (0-255 = 0.0-1.0)
 */
static inline uint8_t float_to_uint8(float value)
{
    if (value < 0.0f) return 0;
    if (value > 1.0f) return 255;
    return (uint8_t)(value * 255.0f);
}

/**
 * @brief تبدیل uint8_t به float
 */
static inline float uint8_to_float(uint8_t value)
{
    return (float)value / 255.0f;
}

#endif // OPTIMIZED_DATA_STRUCTURES_H

