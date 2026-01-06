/**
 * @file optimized_prediction.c
 * @brief پیش‌بینی بهینه‌سازی شده با hardware accelerators
 * @version 1.0.0
 */

#include "optimized_prediction.h"
#include "prediction.h"
#include "../system/hardware_accelerators.h"
#include "../system/dma_manager.h"
#include "../system/power_management.h"
#include "../system/hal.h"
#include <string.h>

// ============================================================================
// متغیرهای داخلی
// ============================================================================

static bool optimized_prediction_initialized = false;
static float input_buffer[ML_INPUT_SIZE];
static float output_buffer[ML_OUTPUT_SIZE];
static bool use_hardware_accelerator = false;

// ============================================================================
// توابع داخلی
// ============================================================================

/**
 * @brief بهینه‌سازی ورودی با استفاده از DMA
 */
static bool optimize_input_transfer(const model_input_t *input)
{
    // استفاده از DMA برای کپی سریع
    return dma_memcpy(input_buffer, input->eeg_features, 
                     sizeof(input->eeg_features));
}

/**
 * @brief پیش‌پردازش با hardware accelerator
 */
static bool preprocess_with_accelerator(const float *input, float *output, uint32_t size)
{
    // استفاده از FFT accelerator برای feature extraction
    if (hw_accelerator_is_enabled(HW_ACCEL_FFT)) {
        return hw_accel_fft_execute(input, output, size);
    }
    return false;
}

/**
 * @brief استفاده از hardware floating point
 */
static inline float fast_multiply(float a, float b)
{
    // استفاده از FPU hardware
    // کامپایلر به صورت خودکار از FPU استفاده می‌کند
    // اما می‌توانیم با inline assembly بهینه‌تر کنیم
    return a * b;
}

static inline float fast_add(float a, float b)
{
    return a + b;
}

// ============================================================================
// توابع API عمومی
// ============================================================================

bool optimized_prediction_init(void)
{
    if (optimized_prediction_initialized) {
        return true;
    }
    
    // مقداردهی اولیه DMA
    if (!dma_manager_init()) {
        return false;
    }
    
    // فعال کردن ML accelerator
    if (hw_accelerator_is_enabled(HW_ACCEL_ML)) {
        use_hardware_accelerator = true;
    } else {
        // فعال کردن ML accelerator
        if (hw_accelerator_enable(HW_ACCEL_ML)) {
            use_hardware_accelerator = true;
        }
    }
    
    // بهینه‌سازی power برای ML workload
    power_optimize_for_workload(80);  // ML نیاز به عملکرد بالا دارد
    
    optimized_prediction_initialized = true;
    return true;
}

bool optimized_prediction_run(const model_input_t *input, prediction_t *output)
{
    if (!optimized_prediction_initialized || !input || !output) {
        return false;
    }
    
    uint32_t start_time = hal_rtc_get_time_ms();
    
    // 1. انتقال ورودی با DMA (سریع‌تر از memcpy)
    if (!optimize_input_transfer(input)) {
        // Fallback به memcpy معمولی
        memcpy(input_buffer, input->eeg_features, sizeof(input->eeg_features));
    }
    
    // 2. پیش‌پردازش با hardware accelerator (اگر ممکن باشد)
    float preprocessed[ML_INPUT_SIZE];
    if (!preprocess_with_accelerator(input_buffer, preprocessed, ML_INPUT_SIZE)) {
        // Fallback به software preprocessing
        memcpy(preprocessed, input_buffer, sizeof(input_buffer));
    }
    
    // 3. اجرای ML inference
    bool success = false;
    
    if (use_hardware_accelerator) {
        // استفاده از ML hardware accelerator
        success = hw_accel_ml_inference(
            NULL,  // model_data (در accelerator ذخیره شده)
            preprocessed,
            output_buffer
        );
    }
    
    if (!success) {
        // Fallback به software inference
        // استفاده از prediction_run معمولی
        model_input_t optimized_input = *input;
        memcpy(optimized_input.eeg_features, preprocessed, 
               sizeof(optimized_input.eeg_features));
        
        success = prediction_run(&optimized_input, output);
    } else {
        // تبدیل output_buffer به prediction_t
        output->result = PREDICTION_RESULT_NORMAL;
        output->confidence = output_buffer[0];
        output->risk_score = output_buffer[1];
        output->timestamp = hal_rtc_get_time_ms();
        output->valid = true;
    }
    
    uint32_t end_time = hal_rtc_get_time_ms();
    uint32_t inference_time = end_time - start_time;
    
    // بررسی محدودیت زمان (<50ms)
    if (inference_time > 50) {
        output->valid = false;
        return false;
    }
    
    return success;
}

bool optimized_prediction_enable_parallel_processing(bool enable)
{
    if (!optimized_prediction_initialized) {
        return false;
    }
    
    // فعال/غیرفعال کردن parallel processing
    // در صورت امکان، از چند core یا pipeline استفاده می‌کنیم
    // TODO: پیاده‌سازی parallel processing واقعی
    
    return true;
}

uint32_t optimized_prediction_get_last_inference_time(void)
{
    // این تابع باید آخرین زمان inference را برگرداند
    // TODO: ذخیره زمان در متغیر static
    return 0;
}

void optimized_prediction_deinit(void)
{
    if (!optimized_prediction_initialized) {
        return;
    }
    
    if (use_hardware_accelerator) {
        hw_accelerator_disable(HW_ACCEL_ML);
    }
    
    optimized_prediction_initialized = false;
}

