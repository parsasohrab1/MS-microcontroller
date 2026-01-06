/**
 * @file prediction.c
 * @brief پیاده‌سازی ماژول پیش‌بینی
 * @version 0.1.0
 */

#include "prediction.h"
#include "tflite_micro.h"
#include "../system/hal.h"
#include <string.h>

// ============================================================================
// متغیرهای داخلی
// ============================================================================

static bool prediction_initialized = false;
static bool model_loaded = false;
static tflite_interpreter_t interpreter;
static uint32_t last_inference_time = 0;

// ============================================================================
// توابع داخلی
// ============================================================================

/**
 * @brief تبدیل ویژگی‌های ورودی به آرایه float برای مدل
 */
static void prepare_model_input(const model_input_t *input, float *model_input_array)
{
    uint32_t idx = 0;
    
    // ویژگی‌های EEG (32 کانال)
    for (uint32_t i = 0; i < 32; i++) {
        model_input_array[idx++] = input->eeg_features[i];
    }
    
    // مقادیر بیومارکرها
    for (uint32_t i = 0; i < BIOMARKER_COUNT; i++) {
        model_input_array[idx++] = input->biomarker_values[i];
    }
    
    // پارامترهای فیزیولوژیک
    for (uint32_t i = 0; i < 5; i++) {
        model_input_array[idx++] = input->physiological_params[i];
    }
}

/**
 * @brief تبدیل خروجی مدل به نتیجه پیش‌بینی
 */
static void process_model_output(const float *model_output, prediction_t *output)
{
    // فرض می‌کنیم مدل 4 خروجی دارد (برای 4 کلاس)
    // [normal_prob, warning_prob, imminent_prob, active_prob]
    
    float normal_prob = model_output[0];
    float warning_prob = model_output[1];
    float imminent_prob = model_output[2];
    float active_prob = model_output[3];
    
    // پیدا کردن کلاس با بیشترین احتمال
    float max_prob = normal_prob;
    prediction_result_t result = PREDICTION_RESULT_NORMAL;
    
    if (warning_prob > max_prob) {
        max_prob = warning_prob;
        result = PREDICTION_RESULT_WARNING;
    }
    if (imminent_prob > max_prob) {
        max_prob = imminent_prob;
        result = PREDICTION_RESULT_ATTACK_IMMINENT;
    }
    if (active_prob > max_prob) {
        max_prob = active_prob;
        result = PREDICTION_RESULT_ATTACK_ACTIVE;
    }
    
    output->result = result;
    output->confidence = max_prob;
    output->risk_score = (imminent_prob + active_prob); // مجموع احتمال حمله
}

/**
 * @brief اجرای inference مدل TinyML
 */
static bool run_model_inference(const model_input_t *input, prediction_t *output)
{
    if (!model_loaded || !input || !output) {
        return false;
    }
    
    // آماده‌سازی ورودی مدل
    // اندازه ورودی: 32 (EEG) + 10 (biomarkers) + 5 (physiological) = 47
    float model_input[47];
    prepare_model_input(input, model_input);
    
    // تنظیم ورودی
    if (!tflite_micro_set_input(&interpreter, 0, model_input, 47)) {
        return false;
    }
    
    // اجرای inference
    uint32_t start_time = hal_rtc_get_time_ms();
    if (!tflite_micro_invoke(&interpreter)) {
        return false;
    }
    uint32_t end_time = hal_rtc_get_time_ms();
    last_inference_time = end_time - start_time;
    
    // دریافت خروجی
    float model_output[4]; // 4 کلاس
    if (!tflite_micro_get_output(&interpreter, 0, model_output, 4)) {
        return false;
    }
    
    // پردازش خروجی
    process_model_output(model_output, output);
    
    return true;
}

// ============================================================================
// توابع API عمومی
// ============================================================================

bool prediction_init(void)
{
    if (prediction_initialized) {
        return true;
    }
    
    // مقداردهی اولیه TensorFlow Lite Micro
    if (!tflite_micro_init()) {
        return false;
    }
    
    prediction_initialized = true;
    return true;
}

bool prediction_load_model(const uint8_t *model_data, uint32_t model_size)
{
    if (!prediction_initialized || !model_data || model_size == 0) {
        return false;
    }
    
    // اگر مدل قبلی بارگذاری شده، آن را حذف می‌کنیم
    if (model_loaded) {
        tflite_micro_delete_interpreter(&interpreter);
        model_loaded = false;
    }
    
    // ایجاد interpreter از مدل
    if (!tflite_micro_create_interpreter(&interpreter, model_data, model_size)) {
        return false;
    }
    
    model_loaded = true;
    return true;
}

bool prediction_run(const model_input_t *input, prediction_t *output)
{
    if (!prediction_initialized || !model_loaded || !input || !output) {
        return false;
    }
    
    // اجرای inference
    bool success = run_model_inference(input, output);
    
    // بررسی محدودیت زمان
    if (last_inference_time > ML_INFERENCE_MAX_TIME) {
        output->valid = false;
        return false;
    }
    
    if (success) {
        output->timestamp = hal_rtc_get_time_ms();
        output->valid = true;
    }
    
    return success;
}

bool prediction_is_ready(void)
{
    return prediction_initialized && model_loaded;
}

uint32_t prediction_get_last_inference_time(void)
{
    return last_inference_time;
}

void prediction_deinit(void)
{
    if (!prediction_initialized) {
        return;
    }
    
    // حذف interpreter
    if (model_loaded) {
        tflite_micro_delete_interpreter(&interpreter);
        model_loaded = false;
    }
    
    // خاموش کردن TensorFlow Lite Micro
    tflite_micro_deinit();
    
    prediction_initialized = false;
}

