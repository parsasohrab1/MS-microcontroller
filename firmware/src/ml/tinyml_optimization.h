/**
 * @file tinyml_optimization.h
 * @brief TinyML Optimization
 * بهینه‌سازی بیشتر مدل‌ها: Quantization, Pruning, Knowledge Distillation, Model Compression
 */

#ifndef TINYML_OPTIMIZATION_H
#define TINYML_OPTIMIZATION_H

#include <stdint.h>
#include <stdbool.h>

// ============================================================================
// Constants
// ============================================================================

#define TINYML_MAX_MODELS 4
#define TINYML_MODEL_NAME_MAX_LEN 32

// ============================================================================
// Types
// ============================================================================

typedef enum {
    QUANTIZATION_INT8 = 0,
    QUANTIZATION_INT16,
    QUANTIZATION_FLOAT16
} quantization_type_t;

typedef enum {
    PRUNING_MAGNITUDE = 0,
    PRUNING_GRADIENT,
    PRUNING_STRUCTURED
} pruning_type_t;

typedef struct {
    char name[TINYML_MODEL_NAME_MAX_LEN];
    uint8_t *model_data;
    uint32_t model_size;
    quantization_type_t quantization;
    float sparsity;  // 0.0 = no pruning, 1.0 = fully pruned
    bool is_active;
    uint32_t inference_count;
    float avg_inference_time_ms;
} tinyml_model_t;

// ============================================================================
// Functions
// ============================================================================

/**
 * @brief مقداردهی اولیه TinyML Optimization
 * @return true در صورت موفقیت
 */
bool tinyml_optimization_init(void);

/**
 * @brief Quantization مدل
 * @param input_model مدل ورودی
 * @param input_size اندازه مدل
 * @param output_model خروجی مدل quantized
 * @param output_size اندازه خروجی
 * @param type نوع quantization
 * @return true در صورت موفقیت
 */
bool tinyml_quantize_model(
    const uint8_t *input_model,
    uint32_t input_size,
    uint8_t *output_model,
    uint32_t *output_size,
    quantization_type_t type
);

/**
 * @brief Pruning مدل
 * @param input_model مدل ورودی
 * @param input_size اندازه مدل
 * @param output_model خروجی مدل pruned
 * @param output_size اندازه خروجی
 * @param type نوع pruning
 * @param sparsity میزان sparsity (0.0 - 1.0)
 * @return true در صورت موفقیت
 */
bool tinyml_prune_model(
    const uint8_t *input_model,
    uint32_t input_size,
    uint8_t *output_model,
    uint32_t *output_size,
    pruning_type_t type,
    float sparsity
);

/**
 * @brief Knowledge Distillation
 * @param teacher_model مدل teacher
 * @param teacher_size اندازه teacher
 * @param student_model خروجی student model
 * @param student_size اندازه student
 * @param temperature temperature برای distillation
 * @return true در صورت موفقیت
 */
bool tinyml_knowledge_distill(
    const uint8_t *teacher_model,
    uint32_t teacher_size,
    uint8_t *student_model,
    uint32_t *student_size,
    float temperature
);

/**
 * @brief Model Compression
 * @param input_model مدل ورودی
 * @param input_size اندازه مدل
 * @param output_model خروجی مدل compressed
 * @param output_size اندازه خروجی
 * @param compression_ratio نسبت فشرده‌سازی مورد نظر
 * @return true در صورت موفقیت
 */
bool tinyml_compress_model(
    const uint8_t *input_model,
    uint32_t input_size,
    uint8_t *output_model,
    uint32_t *output_size,
    float compression_ratio
);

/**
 * @brief ثبت مدل
 * @param name نام مدل
 * @param model_data داده مدل
 * @param model_size اندازه مدل
 * @return true در صورت موفقیت
 */
bool tinyml_register_model(
    const char *name,
    const uint8_t *model_data,
    uint32_t model_size
);

/**
 * @brief انتخاب خودکار مدل مناسب
 * @param input_features ویژگی‌های ورودی
 * @param feature_count تعداد ویژگی‌ها
 * @return نام مدل انتخاب شده یا NULL
 */
const char *tinyml_select_model(
    const float *input_features,
    uint32_t feature_count
);

/**
 * @brief اجرای inference با مدل
 * @param model_name نام مدل
 * @param input داده ورودی
 * @param input_size اندازه ورودی
 * @param output خروجی
 * @param output_size اندازه خروجی
 * @return true در صورت موفقیت
 */
bool tinyml_inference(
    const char *model_name,
    const float *input,
    uint32_t input_size,
    float *output,
    uint32_t *output_size
);

/**
 * @brief Ensemble inference (ترکیب چند مدل)
 * @param model_names نام مدل‌ها
 * @param model_count تعداد مدل‌ها
 * @param input داده ورودی
 * @param input_size اندازه ورودی
 * @param output خروجی
 * @param output_size اندازه خروجی
 * @return true در صورت موفقیت
 */
bool tinyml_ensemble_inference(
    const char **model_names,
    uint32_t model_count,
    const float *input,
    uint32_t input_size,
    float *output,
    uint32_t *output_size
);

/**
 * @brief دریافت آمار مدل
 * @param model_name نام مدل
 * @param stats خروجی آمار
 * @return true در صورت موفقیت
 */
bool tinyml_get_model_stats(
    const char *model_name,
    tinyml_model_t *stats
);

/**
 * @brief فعال/غیرفعال کردن مدل
 * @param model_name نام مدل
 * @param active فعال/غیرفعال
 * @return true در صورت موفقیت
 */
bool tinyml_set_model_active(const char *model_name, bool active);

#endif // TINYML_OPTIMIZATION_H

