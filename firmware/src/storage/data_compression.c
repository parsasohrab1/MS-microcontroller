/**
 * @file data_compression.c
 * @brief پیاده‌سازی فشرده‌سازی داده‌ها
 * @version 1.0.0
 */

#include "data_compression.h"
#include "../system/hal.h"
#include <string.h>

// ============================================================================
// متغیرهای داخلی
// ============================================================================

static bool compression_initialized = false;

// ============================================================================
// توابع داخلی - RLE Compression
// ============================================================================

/**
 * @brief فشرده‌سازی RLE (Run-Length Encoding)
 */
static bool compress_rle(
    const uint8_t *input,
    uint32_t input_size,
    uint8_t *output,
    uint32_t *output_size
)
{
    uint32_t out_idx = 0;
    uint32_t in_idx = 0;
    
    while (in_idx < input_size && out_idx < *output_size - 2) {
        uint8_t value = input[in_idx];
        uint8_t count = 1;
        
        // شمارش تکرارها
        while (in_idx + count < input_size && 
               input[in_idx + count] == value && 
               count < 255) {
            count++;
        }
        
        // نوشتن به خروجی
        if (count > 3 || value == 0xFF) {
            // استفاده از RLE
            output[out_idx++] = 0xFF;  // Marker
            output[out_idx++] = value;
            output[out_idx++] = count;
        } else {
            // نوشتن مستقیم
            for (uint8_t i = 0; i < count; i++) {
                output[out_idx++] = value;
            }
        }
        
        in_idx += count;
    }
    
    *output_size = out_idx;
    return (in_idx == input_size);
}

/**
 * @brief باز کردن فشرده‌سازی RLE
 */
static bool decompress_rle(
    const uint8_t *input,
    uint32_t input_size,
    uint8_t *output,
    uint32_t *output_size
)
{
    uint32_t out_idx = 0;
    uint32_t in_idx = 0;
    
    while (in_idx < input_size && out_idx < *output_size) {
        if (input[in_idx] == 0xFF && in_idx + 2 < input_size) {
            // RLE sequence
            uint8_t value = input[in_idx + 1];
            uint8_t count = input[in_idx + 2];
            
            for (uint8_t i = 0; i < count && out_idx < *output_size; i++) {
                output[out_idx++] = value;
            }
            
            in_idx += 3;
        } else {
            // Direct value
            output[out_idx++] = input[in_idx++];
        }
    }
    
    *output_size = out_idx;
    return (in_idx == input_size);
}

// ============================================================================
// توابع داخلی - Delta Compression
// ============================================================================

/**
 * @brief فشرده‌سازی Delta (برای داده‌های سری زمانی)
 */
static bool compress_delta(
    const int16_t *input,
    uint32_t input_size,
    int16_t *output,
    uint32_t *output_size
)
{
    if (input_size == 0) {
        *output_size = 0;
        return true;
    }
    
    // اولین مقدار بدون تغییر
    output[0] = input[0];
    uint32_t out_idx = 1;
    
    // محاسبه delta
    for (uint32_t i = 1; i < input_size && out_idx < *output_size; i++) {
        int16_t delta = input[i] - input[i-1];
        output[out_idx++] = delta;
    }
    
    *output_size = out_idx;
    return true;
}

/**
 * @brief باز کردن فشرده‌سازی Delta
 */
static bool decompress_delta(
    const int16_t *input,
    uint32_t input_size,
    int16_t *output,
    uint32_t *output_size
)
{
    if (input_size == 0) {
        *output_size = 0;
        return true;
    }
    
    // اولین مقدار بدون تغییر
    output[0] = input[0];
    uint32_t out_idx = 1;
    
    // بازسازی از delta
    for (uint32_t i = 1; i < input_size && out_idx < *output_size; i++) {
        output[out_idx] = output[out_idx - 1] + input[i];
        out_idx++;
    }
    
    *output_size = out_idx;
    return true;
}

// ============================================================================
// توابع داخلی - LZ4-like Compression (ساده شده)
// ============================================================================

/**
 * @brief فشرده‌سازی LZ4 ساده شده
 */
static bool compress_lz4_simple(
    const uint8_t *input,
    uint32_t input_size,
    uint8_t *output,
    uint32_t *output_size
)
{
    // پیاده‌سازی ساده LZ4
    // جستجوی توالی‌های تکراری
    uint32_t out_idx = 0;
    uint32_t in_idx = 0;
    
    while (in_idx < input_size && out_idx < *output_size - 4) {
        // جستجوی match (حداکثر 4 بایت)
        bool found_match = false;
        uint8_t match_len = 0;
        uint16_t match_offset = 0;
        
        // جستجو در 256 بایت قبلی
        uint32_t search_start = (in_idx > 256) ? in_idx - 256 : 0;
        for (uint32_t i = search_start; i < in_idx && !found_match; i++) {
            uint8_t len = 0;
            while (in_idx + len < input_size && 
                   i + len < in_idx && 
                   input[i + len] == input[in_idx + len] && 
                   len < 15) {
                len++;
            }
            
            if (len >= 4) {
                found_match = true;
                match_len = len;
                match_offset = in_idx - i;
            }
        }
        
        if (found_match) {
            // Literal + Match
            output[out_idx++] = (match_len << 4) | (match_offset >> 8);
            output[out_idx++] = match_offset & 0xFF;
            in_idx += match_len;
        } else {
            // Literal
            output[out_idx++] = input[in_idx++];
        }
    }
    
    *output_size = out_idx;
    return (in_idx == input_size);
}

// ============================================================================
// توابع API عمومی
// ============================================================================

bool data_compression_init(void)
{
    if (compression_initialized) {
        return true;
    }
    
    compression_initialized = true;
    return true;
}

bool data_compress(
    const uint8_t *input,
    uint32_t input_size,
    uint8_t *output,
    uint32_t *output_size,
    compression_algorithm_t algorithm
)
{
    if (!compression_initialized || !input || !output || input_size == 0) {
        return false;
    }
    
    uint32_t max_output_size = *output_size;
    
    switch (algorithm) {
        case COMPRESSION_RLE:
            return compress_rle(input, input_size, output, output_size);
            
        case COMPRESSION_DELTA:
            // تبدیل به int16_t
            return compress_delta(
                (const int16_t *)input,
                input_size / sizeof(int16_t),
                (int16_t *)output,
                output_size
            );
            
        case COMPRESSION_LZ4:
            return compress_lz4_simple(input, input_size, output, output_size);
            
        case COMPRESSION_NONE:
            // بدون فشرده‌سازی
            if (max_output_size >= input_size) {
                memcpy(output, input, input_size);
                *output_size = input_size;
                return true;
            }
            return false;
            
        case COMPRESSION_ZLIB:
        case COMPRESSION_GZIP:
            // TODO: پیاده‌سازی ZLIB/GZIP (نیاز به کتابخانه)
            // برای حالا از LZ4 استفاده می‌کنیم
            return compress_lz4_simple(input, input_size, output, output_size);
            
        default:
            return false;
    }
}

bool data_decompress(
    const uint8_t *input,
    uint32_t input_size,
    uint8_t *output,
    uint32_t *output_size,
    compression_algorithm_t algorithm
)
{
    if (!compression_initialized || !input || !output || input_size == 0) {
        return false;
    }
    
    uint32_t max_output_size = *output_size;
    
    switch (algorithm) {
        case COMPRESSION_RLE:
            return decompress_rle(input, input_size, output, output_size);
            
        case COMPRESSION_DELTA:
            return decompress_delta(
                (const int16_t *)input,
                input_size / sizeof(int16_t),
                (int16_t *)output,
                output_size
            );
            
        case COMPRESSION_LZ4:
            // TODO: پیاده‌سازی decompress LZ4
            // برای حالا، بدون decompress
            return false;
            
        case COMPRESSION_NONE:
            if (max_output_size >= input_size) {
                memcpy(output, input, input_size);
                *output_size = input_size;
                return true;
            }
            return false;
            
        default:
            return false;
    }
}

compression_algorithm_t data_compression_select_algorithm(uint8_t data_type)
{
    switch (data_type) {
        case 0:  // EEG data (سری زمانی)
            return COMPRESSION_DELTA;
            
        case 1:  // Biomarker data (مقادیر کم)
            return COMPRESSION_RLE;
            
        case 2:  // General data
            return COMPRESSION_LZ4;
            
        default:
            return COMPRESSION_NONE;
    }
}

bool data_compress_with_result(
    const uint8_t *input,
    uint32_t input_size,
    uint8_t *output,
    uint32_t *output_size,
    compression_algorithm_t algorithm,
    compression_result_t *result
)
{
    if (!result) {
        return false;
    }
    
    result->original_size = input_size;
    result->algorithm = algorithm;
    
    bool success = data_compress(input, input_size, output, output_size, algorithm);
    
    if (success) {
        result->compressed_size = *output_size;
        result->compression_ratio = (float)result->compressed_size / (float)result->original_size;
        result->success = true;
    } else {
        result->success = false;
        result->compressed_size = 0;
        result->compression_ratio = 1.0f;
    }
    
    return success;
}

void data_compression_deinit(void)
{
    compression_initialized = false;
}

