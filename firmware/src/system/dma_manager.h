/**
 * @file dma_manager.h
 * @brief مدیریت DMA برای انتقال داده‌های سریع
 * @version 1.0.0
 */

#ifndef DMA_MANAGER_H
#define DMA_MANAGER_H

#include <stdint.h>
#include <stdbool.h>

// ============================================================================
// انواع انتقال DMA
// ============================================================================

typedef enum {
    DMA_TRANSFER_MEMORY_TO_MEMORY = 0,  // Memory to Memory
    DMA_TRANSFER_PERIPHERAL_TO_MEMORY,  // Peripheral to Memory
    DMA_TRANSFER_MEMORY_TO_PERIPHERAL,  // Memory to Peripheral
    DMA_TRANSFER_PERIPHERAL_TO_PERIPHERAL  // Peripheral to Peripheral
} dma_transfer_type_t;

typedef enum {
    DMA_PRIORITY_LOW = 0,
    DMA_PRIORITY_MEDIUM,
    DMA_PRIORITY_HIGH,
    DMA_PRIORITY_VERY_HIGH
} dma_priority_t;

// ============================================================================
// ساختار تنظیمات DMA
// ============================================================================

typedef struct {
    dma_transfer_type_t type;
    dma_priority_t priority;
    uint32_t source_address;
    uint32_t destination_address;
    uint32_t data_size;  // bytes
    uint32_t transfer_count;
    bool increment_source;
    bool increment_destination;
    uint8_t data_width;  // 8, 16, 32 bit
    bool circular_mode;
    void (*callback)(void);  // Callback بعد از اتمام
} dma_config_t;

// ============================================================================
// آمار DMA
// ============================================================================

typedef struct {
    uint32_t total_transfers;
    uint32_t total_bytes_transferred;
    uint32_t average_transfer_time_us;
    uint32_t max_transfer_time_us;
    uint32_t min_transfer_time_us;
} dma_stats_t;

// ============================================================================
// توابع API
// ============================================================================

/**
 * @brief مقداردهی اولیه DMA Manager
 * @return true در صورت موفقیت
 */
bool dma_manager_init(void);

/**
 * @brief ایجاد و شروع انتقال DMA
 * @param config تنظیمات DMA
 * @return شناسه DMA channel (یا -1 در صورت خطا)
 */
int32_t dma_start_transfer(const dma_config_t *config);

/**
 * @brief انتظار برای اتمام انتقال
 * @param channel_id شناسه channel
 * @param timeout_ms timeout (ms) - 0 برای نامحدود
 * @return true در صورت موفقیت
 */
bool dma_wait_for_completion(int32_t channel_id, uint32_t timeout_ms);

/**
 * @brief توقف انتقال DMA
 * @param channel_id شناسه channel
 * @return true در صورت موفقیت
 */
bool dma_stop_transfer(int32_t channel_id);

/**
 * @brief بررسی وضعیت انتقال
 * @param channel_id شناسه channel
 * @return true اگر در حال انتقال است
 */
bool dma_is_transferring(int32_t channel_id);

/**
 * @brief انتقال سریع Memory to Memory
 * @param src آدرس مبدأ
 * @param dst آدرس مقصد
 * @param size اندازه (bytes)
 * @return true در صورت موفقیت
 */
bool dma_memcpy(void *dst, const void *src, uint32_t size);

/**
 * @brief انتقال سریع از ADC به Memory
 * @param buffer بافر مقصد
 * @param size اندازه (samples)
 * @return true در صورت موفقیت
 */
bool dma_adc_to_memory(uint16_t *buffer, uint32_t size);

/**
 * @brief انتقال سریع از Memory به DAC
 * @param buffer بافر مبدأ
 * @param size اندازه (samples)
 * @return true در صورت موفقیت
 */
bool dma_memory_to_dac(const uint16_t *buffer, uint32_t size);

/**
 * @brief دریافت آمار DMA
 * @param stats اشاره‌گر به ساختار آمار
 * @return true در صورت موفقیت
 */
bool dma_get_stats(dma_stats_t *stats);

/**
 * @brief خاموش کردن ماژول
 */
void dma_manager_deinit(void);

#endif // DMA_MANAGER_H

