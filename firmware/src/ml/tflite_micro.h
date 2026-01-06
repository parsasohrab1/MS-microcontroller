/**
 * @file tflite_micro.h
 * @brief رابط برای TensorFlow Lite Micro runtime
 * @version 0.1.0
 */

#ifndef TFLITE_MICRO_H
#define TFLITE_MICRO_H

#include <stdint.h>
#include <stdbool.h>

// ============================================================================
// ساختار interpreter
// ============================================================================

typedef struct {
    void *model_data;           // داده مدل
    uint32_t model_size;        // اندازه مدل
    void *interpreter;          // TensorFlow Lite interpreter
    bool initialized;
} tflite_interpreter_t;

// ============================================================================
// توابع API
// ============================================================================

/**
 * @brief مقداردهی اولیه TensorFlow Lite Micro
 * @return true در صورت موفقیت
 */
bool tflite_micro_init(void);

/**
 * @brief ایجاد interpreter از مدل
 * @param interpreter اشاره‌گر به interpreter
 * @param model_data داده مدل
 * @param model_size اندازه مدل
 * @return true در صورت موفقیت
 */
bool tflite_micro_create_interpreter(tflite_interpreter_t *interpreter,
                                     const uint8_t *model_data, uint32_t model_size);

/**
 * @brief تنظیم ورودی مدل
 * @param interpreter اشاره‌گر به interpreter
 * @param input_index ایندکس ورودی
 * @param data داده ورودی
 * @param size اندازه داده
 * @return true در صورت موفقیت
 */
bool tflite_micro_set_input(tflite_interpreter_t *interpreter, uint8_t input_index,
                            const float *data, uint32_t size);

/**
 * @brief اجرای inference
 * @param interpreter اشاره‌گر به interpreter
 * @return true در صورت موفقیت
 */
bool tflite_micro_invoke(tflite_interpreter_t *interpreter);

/**
 * @brief دریافت خروجی مدل
 * @param interpreter اشاره‌گر به interpreter
 * @param output_index ایندکس خروجی
 * @param data بافر خروجی
 * @param size اندازه بافر
 * @return true در صورت موفقیت
 */
bool tflite_micro_get_output(tflite_interpreter_t *interpreter, uint8_t output_index,
                             float *data, uint32_t size);

/**
 * @brief حذف interpreter
 * @param interpreter اشاره‌گر به interpreter
 */
void tflite_micro_delete_interpreter(tflite_interpreter_t *interpreter);

/**
 * @brief خاموش کردن TensorFlow Lite Micro
 */
void tflite_micro_deinit(void);

#endif // TFLITE_MICRO_H

