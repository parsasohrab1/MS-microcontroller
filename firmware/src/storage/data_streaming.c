/**
 * @file data_streaming.c
 * @brief پیاده‌سازی Streaming داده‌ها
 * @version 1.0.0
 */

#include "data_streaming.h"
#include "../system/hal.h"
#include <string.h>
#include <stdlib.h>

// Static buffer pool برای streams
#define STREAM_BUFFER_POOL_SIZE 4
#define STREAM_BUFFER_SIZE 4096
static uint8_t stream_buffer_pool[STREAM_BUFFER_POOL_SIZE][STREAM_BUFFER_SIZE];
static bool stream_buffer_used[STREAM_BUFFER_POOL_SIZE] = {false};

// ============================================================================
// متغیرهای داخلی
// ============================================================================

#define MAX_STREAMS 4
#define DEFAULT_CHUNK_SIZE 1024

static bool streaming_initialized = false;
static data_stream_t active_streams[MAX_STREAMS];
static uint8_t next_stream_id = 1;

// ============================================================================
// توابع داخلی
// ============================================================================

/**
 * @brief پیدا کردن stream آزاد
 */
static data_stream_t *find_free_stream(void)
{
    for (uint8_t i = 0; i < MAX_STREAMS; i++) {
        if (!active_streams[i].is_active) {
            return &active_streams[i];
        }
    }
    return NULL;
}

/**
 * @brief پیدا کردن stream با ID
 */
static data_stream_t *find_stream(uint8_t stream_id)
{
    for (uint8_t i = 0; i < MAX_STREAMS; i++) {
        if (active_streams[i].is_active && active_streams[i].stream_id == stream_id) {
            return &active_streams[i];
        }
    }
    return NULL;
}

// ============================================================================
// توابع API عمومی
// ============================================================================

bool data_streaming_init(void)
{
    if (streaming_initialized) {
        return true;
    }
    
    memset(active_streams, 0, sizeof(active_streams));
    next_stream_id = 1;
    
    streaming_initialized = true;
    return true;
}

data_stream_t *stream_create_reader(
    uint8_t stream_id,
    uint32_t total_size,
    uint32_t chunk_size,
    stream_read_callback_t read_callback,
    void *user_data
)
{
    if (!streaming_initialized || total_size == 0 || !read_callback) {
        return NULL;
    }
    
    data_stream_t *stream = find_free_stream();
    if (!stream) {
        return NULL;  // همه streams استفاده شده‌اند
    }
    
    // تنظیمات stream
    stream->stream_id = stream_id;
    stream->total_size = total_size;
    stream->chunk_size = (chunk_size > 0) ? chunk_size : DEFAULT_CHUNK_SIZE;
    stream->current_position = 0;
    stream->is_active = true;
    
    // تخصیص بافر از static pool
    stream->buffer_size = (stream->chunk_size <= STREAM_BUFFER_SIZE) ? 
                          stream->chunk_size : STREAM_BUFFER_SIZE;
    
    // پیدا کردن buffer آزاد
    for (uint8_t i = 0; i < STREAM_BUFFER_POOL_SIZE; i++) {
        if (!stream_buffer_used[i]) {
            stream->buffer = stream_buffer_pool[i];
            stream_buffer_used[i] = true;
            break;
        }
    }
    
    if (!stream->buffer) {
        return NULL;  // همه buffers استفاده شده‌اند
    }
    
    return stream;
}

data_stream_t *stream_create_writer(
    uint8_t stream_id,
    uint32_t total_size,
    uint32_t chunk_size,
    stream_write_callback_t write_callback,
    void *user_data
)
{
    if (!streaming_initialized || total_size == 0 || !write_callback) {
        return NULL;
    }
    
    data_stream_t *stream = find_free_stream();
    if (!stream) {
        return NULL;
    }
    
    stream->stream_id = stream_id;
    stream->total_size = total_size;
    stream->chunk_size = (chunk_size > 0) ? chunk_size : DEFAULT_CHUNK_SIZE;
    stream->current_position = 0;
    stream->is_active = true;
    
    stream->buffer_size = (stream->chunk_size <= STREAM_BUFFER_SIZE) ? 
                          stream->chunk_size : STREAM_BUFFER_SIZE;
    
    // پیدا کردن buffer آزاد
    for (uint8_t i = 0; i < STREAM_BUFFER_POOL_SIZE; i++) {
        if (!stream_buffer_used[i]) {
            stream->buffer = stream_buffer_pool[i];
            stream_buffer_used[i] = true;
            break;
        }
    }
    
    if (!stream->buffer) {
        return NULL;
    }
    
    return stream;
}

uint32_t stream_read_chunk(data_stream_t *stream, uint8_t *buffer, uint32_t buffer_size)
{
    if (!stream || !buffer || buffer_size == 0 || !stream->is_active) {
        return 0;
    }
    
    // محاسبه اندازه chunk باقی‌مانده
    uint32_t remaining = stream->total_size - stream->current_position;
    uint32_t chunk_size = (remaining < stream->chunk_size) ? remaining : stream->chunk_size;
    chunk_size = (chunk_size < buffer_size) ? chunk_size : buffer_size;
    
    if (chunk_size == 0) {
        return 0;  // تمام شده
    }
    
    // خواندن از source (از طریق callback)
    // TODO: استفاده از read_callback
    
    // برای حالا، از buffer استفاده می‌کنیم
    if (stream->buffer) {
        memcpy(buffer, stream->buffer, chunk_size);
    }
    
    stream->current_position += chunk_size;
    
    return chunk_size;
}

bool stream_write_chunk(data_stream_t *stream, const uint8_t *buffer, uint32_t size)
{
    if (!stream || !buffer || size == 0 || !stream->is_active) {
        return false;
    }
    
    // بررسی ظرفیت
    if (stream->current_position + size > stream->total_size) {
        return false;  // بیش از حد
    }
    
    // نوشتن به destination (از طریق callback)
    // TODO: استفاده از write_callback
    
    // برای حالا، در buffer ذخیره می‌کنیم
    if (stream->buffer && size <= stream->buffer_size) {
        memcpy(stream->buffer, buffer, size);
    }
    
    stream->current_position += size;
    
    return true;
}

bool stream_process(data_stream_t *stream, stream_chunk_callback_t callback, void *user_data)
{
    if (!stream || !callback || !stream->is_active) {
        return false;
    }
    
    uint8_t chunk_buffer[DEFAULT_CHUNK_SIZE];
    
    while (!stream_is_complete(stream)) {
        uint32_t chunk_size = stream_read_chunk(stream, chunk_buffer, sizeof(chunk_buffer));
        if (chunk_size == 0) {
            break;
        }
        
        // فراخوانی callback
        callback(chunk_buffer, chunk_size, user_data);
    }
    
    return true;
}

void stream_close(data_stream_t *stream)
{
    if (!stream || !stream->is_active) {
        return;
    }
    
    // آزاد کردن بافر از pool
    if (stream->buffer) {
        // پیدا کردن index buffer
        for (uint8_t i = 0; i < STREAM_BUFFER_POOL_SIZE; i++) {
            if (stream_buffer_pool[i] == stream->buffer) {
                stream_buffer_used[i] = false;
                break;
            }
        }
        stream->buffer = NULL;
    }
    
    stream->is_active = false;
    stream->current_position = 0;
}

bool stream_is_complete(const data_stream_t *stream)
{
    if (!stream || !stream->is_active) {
        return true;
    }
    
    return stream->current_position >= stream->total_size;
}

uint8_t stream_get_progress(const data_stream_t *stream)
{
    if (!stream || !stream->is_active || stream->total_size == 0) {
        return 0;
    }
    
    return (uint8_t)((stream->current_position * 100) / stream->total_size);
}

void data_streaming_deinit(void)
{
    if (!streaming_initialized) {
        return;
    }
    
    // بستن همه streams
    for (uint8_t i = 0; i < MAX_STREAMS; i++) {
        if (active_streams[i].is_active) {
            stream_close(&active_streams[i]);
        }
    }
    
    streaming_initialized = false;
}

