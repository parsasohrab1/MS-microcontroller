/**
 * @file data_streaming.h
 * @brief Streaming داده‌های بزرگ برای بهینه‌سازی حافظه
 * @version 1.0.0
 */

#ifndef DATA_STREAMING_H
#define DATA_STREAMING_H

#include <stdint.h>
#include <stdbool.h>

// ============================================================================
// ساختار Stream
// ============================================================================

typedef struct {
    uint8_t stream_id;
    uint32_t total_size;
    uint32_t chunk_size;
    uint32_t current_position;
    bool is_active;
    void *buffer;
    uint32_t buffer_size;
} data_stream_t;

// ============================================================================
// Callback functions
// ============================================================================

typedef void (*stream_chunk_callback_t)(const uint8_t *chunk, uint32_t chunk_size, void *user_data);
typedef bool (*stream_read_callback_t)(uint8_t *buffer, uint32_t size, void *user_data);
typedef bool (*stream_write_callback_t)(const uint8_t *buffer, uint32_t size, void *user_data);

// ============================================================================
// توابع API
// ============================================================================

/**
 * @brief مقداردهی اولیه Streaming
 * @return true در صورت موفقیت
 */
bool data_streaming_init(void);

/**
 * @brief ایجاد stream برای خواندن
 * @param stream_id شناسه stream
 * @param total_size اندازه کل داده
 * @param chunk_size اندازه هر chunk
 * @param read_callback callback برای خواندن
 * @param user_data داده کاربر
 * @return اشاره‌گر به stream (یا NULL در صورت خطا)
 */
data_stream_t *stream_create_reader(
    uint8_t stream_id,
    uint32_t total_size,
    uint32_t chunk_size,
    stream_read_callback_t read_callback,
    void *user_data
);

/**
 * @brief ایجاد stream برای نوشتن
 * @param stream_id شناسه stream
 * @param total_size اندازه کل داده
 * @param chunk_size اندازه هر chunk
 * @param write_callback callback برای نوشتن
 * @param user_data داده کاربر
 * @return اشاره‌گر به stream (یا NULL در صورت خطا)
 */
data_stream_t *stream_create_writer(
    uint8_t stream_id,
    uint32_t total_size,
    uint32_t chunk_size,
    stream_write_callback_t write_callback,
    void *user_data
);

/**
 * @brief خواندن chunk بعدی
 * @param stream اشاره‌گر به stream
 * @param buffer بافر خروجی
 * @param buffer_size اندازه بافر
 * @return تعداد bytes خوانده شده
 */
uint32_t stream_read_chunk(data_stream_t *stream, uint8_t *buffer, uint32_t buffer_size);

/**
 * @brief نوشتن chunk
 * @param stream اشاره‌گر به stream
 * @param buffer بافر داده
 * @param size اندازه داده
 * @return true در صورت موفقیت
 */
bool stream_write_chunk(data_stream_t *stream, const uint8_t *buffer, uint32_t size);

/**
 * @brief پردازش stream با callback
 * @param stream اشاره‌گر به stream
 * @param callback callback برای هر chunk
 * @param user_data داده کاربر
 * @return true در صورت موفقیت
 */
bool stream_process(data_stream_t *stream, stream_chunk_callback_t callback, void *user_data);

/**
 * @brief بستن stream
 * @param stream اشاره‌گر به stream
 */
void stream_close(data_stream_t *stream);

/**
 * @brief بررسی اتمام stream
 * @param stream اشاره‌گر به stream
 * @return true اگر تمام شده
 */
bool stream_is_complete(const data_stream_t *stream);

/**
 * @brief دریافت پیشرفت stream
 * @param stream اشاره‌گر به stream
 * @return درصد پیشرفت (0-100)
 */
uint8_t stream_get_progress(const data_stream_t *stream);

/**
 * @brief خاموش کردن ماژول
 */
void data_streaming_deinit(void);

#endif // DATA_STREAMING_H

