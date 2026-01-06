/**
 * @file hardware_accelerators.c
 * @brief پیاده‌سازی Hardware Accelerators
 * @version 1.0.0
 */

#include "hardware_accelerators.h"
#include "hal.h"
#include <string.h>

// ============================================================================
// متغیرهای داخلی
// ============================================================================

static bool hw_accelerators_initialized = false;
static bool accelerators_enabled[HW_ACCEL_COUNT];
static hw_accel_stats_t accelerators_stats[HW_ACCEL_COUNT];

// ============================================================================
// توابع داخلی
// ============================================================================

/**
 * @brief محاسبه power saved با استفاده از accelerator
 */
static uint32_t calculate_power_saved(hw_accelerator_t accel, uint32_t cycles_saved)
{
    // فرض: هر cycle در CPU = 1 nJ
    // Hardware accelerator = 0.1 nJ per cycle
    // Power saved = (cycles_saved * 0.9) nJ
    
    uint32_t power_saved_nJ = (cycles_saved * 9) / 10;
    
    // تبدیل به uA (فرض: 1V, 1MHz)
    // Power (W) = Energy (J) / Time (s)
    // Current (A) = Power (W) / Voltage (V)
    // برای سادگی، فرض می‌کنیم 1 cycle = 1 ns در 1 MHz
    uint32_t power_saved_uA = power_saved_nJ / 1000;  // تقریبی
    
    return power_saved_uA;
}

// ============================================================================
// توابع API عمومی
// ============================================================================

bool hw_accelerators_init(void)
{
    if (hw_accelerators_initialized) {
        return true;
    }
    
    // مقداردهی اولیه
    memset(accelerators_enabled, 0, sizeof(accelerators_enabled));
    memset(accelerators_stats, 0, sizeof(accelerators_stats));
    
    // مقداردهی اولیه HAL
    hal_hw_accelerators_init();
    
    hw_accelerators_initialized = true;
    return true;
}

bool hw_accelerator_enable(hw_accelerator_t accel)
{
    if (!hw_accelerators_initialized || accel >= HW_ACCEL_COUNT) {
        return false;
    }
    
    accelerators_enabled[accel] = true;
    accelerators_stats[accel].is_active = true;
    
    // فعال کردن در HAL
    hal_hw_accelerator_enable(accel);
    
    return true;
}

bool hw_accelerator_disable(hw_accelerator_t accel)
{
    if (!hw_accelerators_initialized || accel >= HW_ACCEL_COUNT) {
        return false;
    }
    
    accelerators_enabled[accel] = false;
    accelerators_stats[accel].is_active = false;
    
    // غیرفعال کردن در HAL
    hal_hw_accelerator_disable(accel);
    
    return true;
}

bool hw_accelerator_is_enabled(hw_accelerator_t accel)
{
    if (!hw_accelerators_initialized || accel >= HW_ACCEL_COUNT) {
        return false;
    }
    
    return accelerators_enabled[accel];
}

bool hw_accel_fft_execute(const float *input, float *output, uint32_t size)
{
    if (!hw_accelerators_initialized || !input || !output || size == 0) {
        return false;
    }
    
    // بررسی فعال بودن accelerator
    if (!accelerators_enabled[HW_ACCEL_FFT]) {
        // Fallback به software FFT
        return false;
    }
    
    // اجرای FFT با hardware accelerator
    uint32_t start_cycles = hal_get_cpu_cycles();
    bool success = hal_hw_accel_fft_execute(input, output, size);
    uint32_t end_cycles = hal_get_cpu_cycles();
    
    if (success) {
        // محاسبه cycles saved
        uint32_t cycles_used = end_cycles - start_cycles;
        // فرض: software FFT نیاز به 10x cycles بیشتر دارد
        uint32_t cycles_saved = cycles_used * 9;
        
        accelerators_stats[HW_ACCEL_FFT].usage_count++;
        accelerators_stats[HW_ACCEL_FFT].total_cycles_saved += cycles_saved;
        accelerators_stats[HW_ACCEL_FFT].power_saved_uA += 
            calculate_power_saved(HW_ACCEL_FFT, cycles_saved);
    }
    
    return success;
}

bool hw_accel_crypto_encrypt(
    const uint8_t *data,
    const uint8_t *key,
    uint8_t *output,
    uint32_t size
)
{
    if (!hw_accelerators_initialized || !data || !key || !output || size == 0) {
        return false;
    }
    
    // بررسی فعال بودن accelerator
    if (!accelerators_enabled[HW_ACCEL_CRYPTO]) {
        return false;
    }
    
    // اجرای encryption با hardware accelerator
    uint32_t start_cycles = hal_get_cpu_cycles();
    bool success = hal_hw_accel_crypto_encrypt(data, key, output, size);
    uint32_t end_cycles = hal_get_cpu_cycles();
    
    if (success) {
        // محاسبه cycles saved
        uint32_t cycles_used = end_cycles - start_cycles;
        // فرض: software crypto نیاز به 20x cycles بیشتر دارد
        uint32_t cycles_saved = cycles_used * 19;
        
        accelerators_stats[HW_ACCEL_CRYPTO].usage_count++;
        accelerators_stats[HW_ACCEL_CRYPTO].total_cycles_saved += cycles_saved;
        accelerators_stats[HW_ACCEL_CRYPTO].power_saved_uA += 
            calculate_power_saved(HW_ACCEL_CRYPTO, cycles_saved);
    }
    
    return success;
}

bool hw_accel_ml_inference(
    const uint8_t *model_data,
    const float *input,
    float *output
)
{
    if (!hw_accelerators_initialized || !model_data || !input || !output) {
        return false;
    }
    
    // بررسی فعال بودن accelerator
    if (!accelerators_enabled[HW_ACCEL_ML]) {
        return false;
    }
    
    // اجرای ML inference با hardware accelerator
    uint32_t start_cycles = hal_get_cpu_cycles();
    bool success = hal_hw_accel_ml_inference(model_data, input, output);
    uint32_t end_cycles = hal_get_cpu_cycles();
    
    if (success) {
        // محاسبه cycles saved
        uint32_t cycles_used = end_cycles - start_cycles;
        // فرض: software ML نیاز به 50x cycles بیشتر دارد
        uint32_t cycles_saved = cycles_used * 49;
        
        accelerators_stats[HW_ACCEL_ML].usage_count++;
        accelerators_stats[HW_ACCEL_ML].total_cycles_saved += cycles_saved;
        accelerators_stats[HW_ACCEL_ML].power_saved_uA += 
            calculate_power_saved(HW_ACCEL_ML, cycles_saved);
    }
    
    return success;
}

bool hw_accelerator_get_stats(hw_accelerator_t accel, hw_accel_stats_t *stats)
{
    if (!hw_accelerators_initialized || accel >= HW_ACCEL_COUNT || !stats) {
        return false;
    }
    
    *stats = accelerators_stats[accel];
    return true;
}

void hw_accelerators_deinit(void)
{
    if (!hw_accelerators_initialized) {
        return;
    }
    
    // غیرفعال کردن همه accelerators
    for (uint8_t i = 0; i < HW_ACCEL_COUNT; i++) {
        hw_accelerator_disable((hw_accelerator_t)i);
    }
    
    hal_hw_accelerators_deinit();
    
    hw_accelerators_initialized = false;
}

