/**
 * @file tinyml_optimization.c
 * @brief پیاده‌سازی TinyML Optimization
 */

#include "tinyml_optimization.h"
#include "../system/hal.h"
#include "../storage/memory_pool.h"
#include <string.h>
#include <math.h>

// ============================================================================
// متغیرهای داخلی
// ============================================================================

static bool tinyml_initialized = false;
static tinyml_model_t registered_models[TINYML_MAX_MODELS];
static uint32_t model_count = 0;

// ============================================================================
// توابع داخلی
// ============================================================================

static int32_t find_model_index(const char *name)
{
    for (uint32_t i = 0; i < model_count; i++) {
        if (strcmp(registered_models[i].name, name) == 0) {
            return i;
        }
    }
    return -1;
}

static void quantize_float_to_int8(const float *input, int8_t *output, uint32_t size, float scale)
{
    for (uint32_t i = 0; i < size; i++) {
        int32_t quantized = (int32_t)round(input[i] / scale);
        if (quantized > 127) quantized = 127;
        if (quantized < -128) quantized = -128;
        output[i] = (int8_t)quantized;
    }
}

static void quantize_float_to_int16(const float *input, int16_t *output, uint32_t size, float scale)
{
    for (uint32_t i = 0; i < size; i++) {
        int32_t quantized = (int32_t)round(input[i] / scale);
        if (quantized > 32767) quantized = 32767;
        if (quantized < -32768) quantized = -32768;
        output[i] = (int16_t)quantized;
    }
}

// ============================================================================
// توابع API
// ============================================================================

bool tinyml_optimization_init(void)
{
    if (tinyml_initialized) {
        return true;
    }
    
    memset(registered_models, 0, sizeof(registered_models));
    model_count = 0;
    
    tinyml_initialized = true;
    return true;
}

bool tinyml_quantize_model(
    const uint8_t *input_model,
    uint32_t input_size,
    uint8_t *output_model,
    uint32_t *output_size,
    quantization_type_t type
)
{
    if (!input_model || !output_model || !output_size) {
        return false;
    }
    
    // این یک پیاده‌سازی ساده است
    // در واقعیت باید از TensorFlow Lite quantization استفاده شود
    
    const float *float_data = (const float *)input_model;
    uint32_t float_count = input_size / sizeof(float);
    
    // محاسبه scale
    float max_val = 0.0f;
    for (uint32_t i = 0; i < float_count; i++) {
        float abs_val = fabsf(float_data[i]);
        if (abs_val > max_val) {
            max_val = abs_val;
        }
    }
    
    float scale = max_val / 127.0f;  // برای int8
    
    if (type == QUANTIZATION_INT8) {
        int8_t *quantized = (int8_t *)output_model;
        quantize_float_to_int8(float_data, quantized, float_count, scale);
        *output_size = float_count * sizeof(int8_t);
    } else if (type == QUANTIZATION_INT16) {
        int16_t *quantized = (int16_t *)output_model;
        quantize_float_to_int16(float_data, quantized, float_count, scale);
        *output_size = float_count * sizeof(int16_t);
    } else {
        // Float16 - نیاز به پشتیبانی hardware
        memcpy(output_model, input_model, input_size);
        *output_size = input_size;
    }
    
    return true;
}

bool tinyml_prune_model(
    const uint8_t *input_model,
    uint32_t input_size,
    uint8_t *output_model,
    uint32_t *output_size,
    pruning_type_t type,
    float sparsity
)
{
    if (!input_model || !output_model || !output_size || sparsity < 0.0f || sparsity > 1.0f) {
        return false;
    }
    
    // این یک پیاده‌سازی ساده است
    // در واقعیت باید از TensorFlow Lite pruning استفاده شود
    
    const float *float_data = (const float *)input_model;
    float *pruned_data = (float *)output_model;
    uint32_t float_count = input_size / sizeof(float);
    
    // محاسبه threshold بر اساس sparsity
    float *abs_values = (float *)memory_pool_alloc(float_count * sizeof(float));
    if (!abs_values) {
        return false;
    }
    
    for (uint32_t i = 0; i < float_count; i++) {
        abs_values[i] = fabsf(float_data[i]);
    }
    
    // Sort (ساده - در واقعیت باید از quicksort استفاده شود)
    for (uint32_t i = 0; i < float_count - 1; i++) {
        for (uint32_t j = i + 1; j < float_count; j++) {
            if (abs_values[i] > abs_values[j]) {
                float temp = abs_values[i];
                abs_values[i] = abs_values[j];
                abs_values[j] = temp;
            }
        }
    }
    
    uint32_t threshold_index = (uint32_t)(float_count * sparsity);
    float threshold = abs_values[threshold_index];
    
    // Prune
    uint32_t pruned_count = 0;
    for (uint32_t i = 0; i < float_count; i++) {
        if (fabsf(float_data[i]) < threshold) {
            pruned_data[i] = 0.0f;
        } else {
            pruned_data[i] = float_data[i];
            pruned_count++;
        }
    }
    
    memory_pool_free(abs_values);
    
    *output_size = input_size;  // اندازه یکسان (اما با صفرهای بیشتر)
    
    return true;
}

bool tinyml_knowledge_distill(
    const uint8_t *teacher_model,
    uint32_t teacher_size,
    uint8_t *student_model,
    uint32_t *student_size,
    float temperature
)
{
    // این یک placeholder است
    // در واقعیت باید از TensorFlow Lite knowledge distillation استفاده شود
    
    if (!teacher_model || !student_model || !student_size) {
        return false;
    }
    
    // TODO: پیاده‌سازی knowledge distillation
    // این نیاز به آموزش دارد و نمی‌تواند در runtime انجام شود
    
    return false;
}

bool tinyml_compress_model(
    const uint8_t *input_model,
    uint32_t input_size,
    uint8_t *output_model,
    uint32_t *output_size,
    float compression_ratio
)
{
    if (!input_model || !output_model || !output_size || compression_ratio <= 0.0f) {
        return false;
    }
    
    // این یک placeholder است
    // در واقعیت باید از compression algorithms استفاده شود
    
    // ساده: فقط کپی می‌کنیم
    // در واقعیت باید از LZ4 یا zlib استفاده شود
    
    memcpy(output_model, input_model, input_size);
    *output_size = input_size;
    
    return true;
}

bool tinyml_register_model(
    const char *name,
    const uint8_t *model_data,
    uint32_t model_size
)
{
    if (!tinyml_initialized || !name || !model_data || model_size == 0) {
        return false;
    }
    
    if (model_count >= TINYML_MAX_MODELS) {
        return false;
    }
    
    // بررسی وجود مدل با همین نام
    if (find_model_index(name) >= 0) {
        return false;
    }
    
    // ثبت مدل
    tinyml_model_t *model = &registered_models[model_count];
    strncpy(model->name, name, TINYML_MODEL_NAME_MAX_LEN - 1);
    model->name[TINYML_MODEL_NAME_MAX_LEN - 1] = '\0';
    
    // تخصیص حافظه برای مدل
    model->model_data = (uint8_t *)memory_pool_alloc(model_size);
    if (!model->model_data) {
        return false;
    }
    
    memcpy(model->model_data, model_data, model_size);
    model->model_size = model_size;
    model->is_active = true;
    model->inference_count = 0;
    model->avg_inference_time_ms = 0.0f;
    
    model_count++;
    
    return true;
}

const char *tinyml_select_model(
    const float *input_features,
    uint32_t feature_count
)
{
    if (!tinyml_initialized || !input_features || feature_count == 0) {
        return NULL;
    }
    
    // انتخاب ساده: اولین مدل فعال
    // در واقعیت باید از heuristics یا ML-based selection استفاده شود
    
    for (uint32_t i = 0; i < model_count; i++) {
        if (registered_models[i].is_active) {
            return registered_models[i].name;
        }
    }
    
    return NULL;
}

bool tinyml_inference(
    const char *model_name,
    const float *input,
    uint32_t input_size,
    float *output,
    uint32_t *output_size
)
{
    if (!tinyml_initialized || !model_name || !input || !output || !output_size) {
        return false;
    }
    
    int32_t index = find_model_index(model_name);
    if (index < 0) {
        return false;
    }
    
    tinyml_model_t *model = &registered_models[index];
    if (!model->is_active) {
        return false;
    }
    
    // TODO: اجرای inference با مدل
    // این نیاز به TensorFlow Lite Micro دارد
    
    // به‌روزرسانی آمار
    model->inference_count++;
    
    return true;
}

bool tinyml_ensemble_inference(
    const char **model_names,
    uint32_t model_count,
    const float *input,
    uint32_t input_size,
    float *output,
    uint32_t *output_size
)
{
    if (!tinyml_initialized || !model_names || !input || !output || !output_size) {
        return false;
    }
    
    // TODO: اجرای ensemble inference
    // ترکیب نتایج چند مدل
    
    return false;
}

bool tinyml_get_model_stats(
    const char *model_name,
    tinyml_model_t *stats
)
{
    if (!tinyml_initialized || !model_name || !stats) {
        return false;
    }
    
    int32_t index = find_model_index(model_name);
    if (index < 0) {
        return false;
    }
    
    *stats = registered_models[index];
    
    return true;
}

bool tinyml_set_model_active(const char *model_name, bool active)
{
    if (!tinyml_initialized || !model_name) {
        return false;
    }
    
    int32_t index = find_model_index(model_name);
    if (index < 0) {
        return false;
    }
    
    registered_models[index].is_active = active;
    
    return true;
}

