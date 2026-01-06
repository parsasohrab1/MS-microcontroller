/**
 * @file hardware_accelerators.h
 * @brief مدیریت Hardware Accelerators برای بهینه‌سازی مصرف انرژی
 * @version 1.0.0
 */

#ifndef HARDWARE_ACCELERATORS_H
#define HARDWARE_ACCELERATORS_H

#include <stdint.h>
#include <stdbool.h>

// ============================================================================
// انواع Hardware Accelerators
// ============================================================================

typedef enum {
    HW_ACCEL_FFT = 0,          // FFT accelerator
    HW_ACCEL_CRYPTO,           // Cryptographic accelerator
    HW_ACCEL_ML,               // Machine Learning accelerator
    HW_ACCEL_DMA,              // DMA controller
    HW_ACCEL_ADC,              // ADC accelerator
    HW_ACCEL_COUNT
} hw_accelerator_t;

// ============================================================================
// آمار استفاده از Accelerators
// ============================================================================

typedef struct {
    uint32_t usage_count;
    uint32_t total_cycles_saved;
    uint32_t power_saved_uA;
    bool is_active;
} hw_accel_stats_t;

// ============================================================================
// توابع API
// ============================================================================

/**
 * @brief مقداردهی اولیه Hardware Accelerators
 * @return true در صورت موفقیت
 */
bool hw_accelerators_init(void);

/**
 * @brief فعال کردن accelerator
 * @param accel نوع accelerator
 * @return true در صورت موفقیت
 */
bool hw_accelerator_enable(hw_accelerator_t accel);

/**
 * @brief غیرفعال کردن accelerator
 * @param accel نوع accelerator
 * @return true در صورت موفقیت
 */
bool hw_accelerator_disable(hw_accelerator_t accel);

/**
 * @brief بررسی فعال بودن accelerator
 * @param accel نوع accelerator
 * @return true اگر فعال است
 */
bool hw_accelerator_is_enabled(hw_accelerator_t accel);

/**
 * @brief اجرای FFT با استفاده از hardware accelerator
 * @param input داده ورودی
 * @param output داده خروجی
 * @param size اندازه FFT
 * @return true در صورت موفقیت
 */
bool hw_accel_fft_execute(const float *input, float *output, uint32_t size);

/**
 * @brief اجرای encryption با استفاده از hardware accelerator
 * @param data داده برای encryption
 * @param key کلید encryption
 * @param output داده خروجی
 * @param size اندازه داده
 * @return true در صورت موفقیت
 */
bool hw_accel_crypto_encrypt(
    const uint8_t *data,
    const uint8_t *key,
    uint8_t *output,
    uint32_t size
);

/**
 * @brief اجرای ML inference با استفاده از hardware accelerator
 * @param model_data داده مدل
 * @param input داده ورودی
 * @param output داده خروجی
 * @return true در صورت موفقیت
 */
bool hw_accel_ml_inference(
    const uint8_t *model_data,
    const float *input,
    float *output
);

/**
 * @brief دریافت آمار accelerator
 * @param accel نوع accelerator
 * @param stats اشاره‌گر به ساختار آمار
 * @return true در صورت موفقیت
 */
bool hw_accelerator_get_stats(hw_accelerator_t accel, hw_accel_stats_t *stats);

/**
 * @brief خاموش کردن ماژول
 */
void hw_accelerators_deinit(void);

#endif // HARDWARE_ACCELERATORS_H

