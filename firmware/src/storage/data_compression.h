/**
 * @file data_compression.h
 * @brief فشرده‌سازی داده‌ها برای بهینه‌سازی حافظه
 * @version 1.0.0
 */

#ifndef DATA_COMPRESSION_H
#define DATA_COMPRESSION_H

#include <stdint.h>
#include <stdbool.h>

// ============================================================================
// انواع الگوریتم فشرده‌سازی
// ============================================================================

typedef enum {
    COMPRESSION_NONE = 0,
    COMPRESSION_LZ4,        // سریع، مصرف CPU کم
    COMPRESSION_ZLIB,       // تعادل بین سرعت و نسبت فشرده‌سازی
    COMPRESSION_GZIP,       // نسبت فشرده‌سازی بالا
    COMPRESSION_RLE,        // برای داده‌های تکراری
    COMPRESSION_DELTA        // برای داده‌های سری زمانی
} compression_algorithm_t;

// ============================================================================
// ساختار نتیجه فشرده‌سازی
// ============================================================================

typedef struct {
    uint32_t original_size;
    uint32_t compressed_size;
    float compression_ratio;  // compressed/original
    compression_algorithm_t algorithm;
    bool success;
} compression_result_t;

// ============================================================================
// توابع API
// ============================================================================

/**
 * @brief مقداردهی اولیه فشرده‌سازی
 * @return true در صورت موفقیت
 */
bool data_compression_init(void);

/**
 * @brief فشرده‌سازی داده
 * @param input داده ورودی
 * @param input_size اندازه ورودی (bytes)
 * @param output بافر خروجی
 * @param output_size اندازه بافر خروجی (bytes) - خروجی: اندازه واقعی
 * @param algorithm الگوریتم فشرده‌سازی
 * @return true در صورت موفقیت
 */
bool data_compress(
    const uint8_t *input,
    uint32_t input_size,
    uint8_t *output,
    uint32_t *output_size,
    compression_algorithm_t algorithm
);

/**
 * @brief باز کردن فشرده‌سازی
 * @param input داده فشرده
 * @param input_size اندازه داده فشرده (bytes)
 * @param output بافر خروجی
 * @param output_size اندازه بافر خروجی (bytes) - خروجی: اندازه واقعی
 * @param algorithm الگوریتم فشرده‌سازی
 * @return true در صورت موفقیت
 */
bool data_decompress(
    const uint8_t *input,
    uint32_t input_size,
    uint8_t *output,
    uint32_t *output_size,
    compression_algorithm_t algorithm
);

/**
 * @brief انتخاب بهترین الگوریتم بر اساس نوع داده
 * @param data_type نوع داده (0=EEG, 1=biomarker, 2=general)
 * @return الگوریتم پیشنهادی
 */
compression_algorithm_t data_compression_select_algorithm(uint8_t data_type);

/**
 * @brief فشرده‌سازی با نتیجه
 * @param input داده ورودی
 * @param input_size اندازه ورودی
 * @param output بافر خروجی
 * @param output_size اندازه بافر خروجی
 * @param algorithm الگوریتم
 * @param result نتیجه فشرده‌سازی
 * @return true در صورت موفقیت
 */
bool data_compress_with_result(
    const uint8_t *input,
    uint32_t input_size,
    uint8_t *output,
    uint32_t *output_size,
    compression_algorithm_t algorithm,
    compression_result_t *result
);

/**
 * @brief خاموش کردن ماژول
 */
void data_compression_deinit(void);

#endif // DATA_COMPRESSION_H

