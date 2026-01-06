/**
 * @file dma_manager.c
 * @brief پیاده‌سازی مدیریت DMA
 * @version 1.0.0
 */

#include "dma_manager.h"
#include "hal.h"
#include <string.h>

// ============================================================================
// متغیرهای داخلی
// ============================================================================

#define MAX_DMA_CHANNELS 8

static bool dma_manager_initialized = false;
static bool channels_in_use[MAX_DMA_CHANNELS];
static dma_stats_t dma_stats;
static uint32_t transfer_start_times[MAX_DMA_CHANNELS];

// ============================================================================
// توابع داخلی
// ============================================================================

/**
 * @brief پیدا کردن channel آزاد
 */
static int32_t find_free_channel(void)
{
    for (uint8_t i = 0; i < MAX_DMA_CHANNELS; i++) {
        if (!channels_in_use[i]) {
            return i;
        }
    }
    return -1;
}

/**
 * @brief محاسبه زمان انتقال بر اساس اندازه و priority
 */
static uint32_t estimate_transfer_time(uint32_t size, dma_priority_t priority)
{
    // فرض: DMA با سرعت 32 MHz
    // هر byte = 1 cycle (برای memory to memory)
    uint32_t cycles = size;
    
    // اضافه کردن overhead بر اساس priority
    switch (priority) {
        case DMA_PRIORITY_VERY_HIGH:
            cycles += 10;  // کمترین overhead
            break;
        case DMA_PRIORITY_HIGH:
            cycles += 20;
            break;
        case DMA_PRIORITY_MEDIUM:
            cycles += 50;
            break;
        case DMA_PRIORITY_LOW:
            cycles += 100;
            break;
    }
    
    // تبدیل به microseconds (فرض: 32 MHz = 31.25 ns per cycle)
    return (cycles * 31) / 1000;  // تقریبی
}

// ============================================================================
// توابع API عمومی
// ============================================================================

bool dma_manager_init(void)
{
    if (dma_manager_initialized) {
        return true;
    }
    
    // مقداردهی اولیه
    memset(channels_in_use, 0, sizeof(channels_in_use));
    memset(&dma_stats, 0, sizeof(dma_stats_t));
    memset(transfer_start_times, 0, sizeof(transfer_start_times));
    
    // مقداردهی اولیه HAL
    hal_dma_init();
    
    dma_manager_initialized = true;
    return true;
}

int32_t dma_start_transfer(const dma_config_t *config)
{
    if (!dma_manager_initialized || !config) {
        return -1;
    }
    
    // پیدا کردن channel آزاد
    int32_t channel = find_free_channel();
    if (channel < 0) {
        return -1;  // هیچ channel آزادی وجود ندارد
    }
    
    // ذخیره زمان شروع
    transfer_start_times[channel] = hal_rtc_get_time_ms() * 1000;  // microseconds
    
    // تنظیم DMA در HAL
    hal_dma_configure(
        channel,
        config->source_address,
        config->destination_address,
        config->data_size,
        config->transfer_count,
        config->increment_source,
        config->increment_destination,
        config->data_width,
        config->circular_mode,
        config->priority,
        config->callback
    );
    
    // شروع انتقال
    hal_dma_start(channel);
    
    channels_in_use[channel] = true;
    
    return channel;
}

bool dma_wait_for_completion(int32_t channel_id, uint32_t timeout_ms)
{
    if (!dma_manager_initialized || channel_id < 0 || channel_id >= MAX_DMA_CHANNELS) {
        return false;
    }
    
    if (!channels_in_use[channel_id]) {
        return true;  // قبلاً تمام شده
    }
    
    uint32_t start_time = hal_rtc_get_time_ms();
    
    // انتظار برای اتمام
    while (channels_in_use[channel_id]) {
        if (hal_dma_is_complete(channel_id)) {
            // محاسبه زمان انتقال
            uint32_t end_time = hal_rtc_get_time_ms() * 1000;
            uint32_t transfer_time = end_time - transfer_start_times[channel_id];
            
            // به‌روزرسانی آمار
            dma_stats.total_transfers++;
            dma_stats.total_bytes_transferred += hal_dma_get_transferred_bytes(channel_id);
            
            if (dma_stats.average_transfer_time_us == 0) {
                dma_stats.average_transfer_time_us = transfer_time;
            } else {
                dma_stats.average_transfer_time_us = 
                    (dma_stats.average_transfer_time_us + transfer_time) / 2;
            }
            
            if (transfer_time > dma_stats.max_transfer_time_us) {
                dma_stats.max_transfer_time_us = transfer_time;
            }
            if (dma_stats.min_transfer_time_us == 0 || transfer_time < dma_stats.min_transfer_time_us) {
                dma_stats.min_transfer_time_us = transfer_time;
            }
            
            channels_in_use[channel_id] = false;
            return true;
        }
        
        // بررسی timeout
        if (timeout_ms > 0) {
            uint32_t elapsed = hal_rtc_get_time_ms() - start_time;
            if (elapsed >= timeout_ms) {
                return false;  // Timeout
            }
        }
        
        // Yield to other tasks
        hal_cpu_wait_for_interrupt();
    }
    
    return true;
}

bool dma_stop_transfer(int32_t channel_id)
{
    if (!dma_manager_initialized || channel_id < 0 || channel_id >= MAX_DMA_CHANNELS) {
        return false;
    }
    
    if (!channels_in_use[channel_id]) {
        return true;  // قبلاً متوقف شده
    }
    
    hal_dma_stop(channel_id);
    channels_in_use[channel_id] = false;
    
    return true;
}

bool dma_is_transferring(int32_t channel_id)
{
    if (!dma_manager_initialized || channel_id < 0 || channel_id >= MAX_DMA_CHANNELS) {
        return false;
    }
    
    return channels_in_use[channel_id] && !hal_dma_is_complete(channel_id);
}

bool dma_memcpy(void *dst, const void *src, uint32_t size)
{
    if (!dma_manager_initialized || !dst || !src || size == 0) {
        return false;
    }
    
    dma_config_t config = {
        .type = DMA_TRANSFER_MEMORY_TO_MEMORY,
        .priority = DMA_PRIORITY_HIGH,
        .source_address = (uint32_t)src,
        .destination_address = (uint32_t)dst,
        .data_size = size,
        .transfer_count = 1,
        .increment_source = true,
        .increment_destination = true,
        .data_width = 32,  // 32-bit transfers برای سرعت بیشتر
        .circular_mode = false,
        .callback = NULL
    };
    
    int32_t channel = dma_start_transfer(&config);
    if (channel < 0) {
        return false;
    }
    
    return dma_wait_for_completion(channel, 100);  // 100ms timeout
}

bool dma_adc_to_memory(uint16_t *buffer, uint32_t size)
{
    if (!dma_manager_initialized || !buffer || size == 0) {
        return false;
    }
    
    dma_config_t config = {
        .type = DMA_TRANSFER_PERIPHERAL_TO_MEMORY,
        .priority = DMA_PRIORITY_VERY_HIGH,
        .source_address = hal_adc_get_data_register_address(),
        .destination_address = (uint32_t)buffer,
        .data_size = size * sizeof(uint16_t),
        .transfer_count = size,
        .increment_source = false,
        .increment_destination = true,
        .data_width = 16,  // ADC data is 16-bit
        .circular_mode = false,
        .callback = NULL
    };
    
    int32_t channel = dma_start_transfer(&config);
    if (channel < 0) {
        return false;
    }
    
    return dma_wait_for_completion(channel, 100);
}

bool dma_memory_to_dac(const uint16_t *buffer, uint32_t size)
{
    if (!dma_manager_initialized || !buffer || size == 0) {
        return false;
    }
    
    dma_config_t priority = {
        .type = DMA_TRANSFER_MEMORY_TO_PERIPHERAL,
        .priority = DMA_PRIORITY_VERY_HIGH,
        .source_address = (uint32_t)buffer,
        .destination_address = hal_dac_get_data_register_address(),
        .data_size = size * sizeof(uint16_t),
        .transfer_count = size,
        .increment_source = true,
        .increment_destination = false,
        .data_width = 16,  // DAC data is 16-bit
        .circular_mode = false,
        .callback = NULL
    };
    
    int32_t channel = dma_start_transfer(&config);
    if (channel < 0) {
        return false;
    }
    
    return dma_wait_for_completion(channel, 100);
}

bool dma_get_stats(dma_stats_t *stats)
{
    if (!dma_manager_initialized || !stats) {
        return false;
    }
    
    *stats = dma_stats;
    return true;
}

void dma_manager_deinit(void)
{
    if (!dma_manager_initialized) {
        return;
    }
    
    // توقف همه channels
    for (uint8_t i = 0; i < MAX_DMA_CHANNELS; i++) {
        if (channels_in_use[i]) {
            dma_stop_transfer(i);
        }
    }
    
    hal_dma_deinit();
    
    dma_manager_initialized = false;
}

