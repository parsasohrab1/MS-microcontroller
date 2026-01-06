/**
 * @file external_flash.c
 * @brief پیاده‌سازی مدیریت External Flash
 * @version 1.0.0
 */

#include "external_flash.h"
#include "../system/hal.h"
#include "../system/dma_manager.h"
#include <string.h>

// ============================================================================
// متغیرهای داخلی
// ============================================================================

#define FLASH_TOTAL_SIZE (4 * 1024 * 1024)  // 4 MB
#define FLASH_PAGE_SIZE 4096
#define FLASH_SECTOR_SIZE (64 * 1024)  // 64 KB
#define METADATA_SIZE 16

static bool flash_initialized = false;
static uint32_t flash_base_address = 0x00000000;
static uint32_t flash_current_address = 0;
static flash_metadata_t metadata_table[256];  // جدول metadata
static uint8_t metadata_count = 0;

// ============================================================================
// توابع داخلی
// ============================================================================

/**
 * @brief محاسبه checksum
 */
static uint8_t calculate_checksum(const uint8_t *data, uint32_t size)
{
    uint8_t checksum = 0;
    for (uint32_t i = 0; i < size; i++) {
        checksum ^= data[i];
    }
    return checksum;
}

/**
 * @brief پیدا کردن metadata با address
 */
static flash_metadata_t *find_metadata(uint32_t address)
{
    for (uint8_t i = 0; i < metadata_count; i++) {
        if (metadata_table[i].address == address && metadata_table[i].is_valid) {
            return &metadata_table[i];
        }
    }
    return NULL;
}

/**
 * @brief اضافه کردن metadata
 */
static bool add_metadata(const flash_metadata_t *metadata)
{
    if (metadata_count >= 256) {
        return false;  // جدول پر است
    }
    
    metadata_table[metadata_count] = *metadata;
    metadata_count++;
    
    return true;
}

/**
 * @brief حذف metadata
 */
static void remove_metadata(uint32_t address)
{
    for (uint8_t i = 0; i < metadata_count; i++) {
        if (metadata_table[i].address == address) {
            metadata_table[i].is_valid = false;
            break;
        }
    }
}

// ============================================================================
// توابع API عمومی
// ============================================================================

bool external_flash_init(void)
{
    if (flash_initialized) {
        return true;
    }
    
    // مقداردهی اولیه HAL
    hal_flash_init();
    
    // پاک کردن جدول metadata
    memset(metadata_table, 0, sizeof(metadata_table));
    metadata_count = 0;
    flash_current_address = flash_base_address;
    
    flash_initialized = true;
    return true;
}

uint32_t external_flash_write(const uint8_t *data, uint32_t size, flash_metadata_t *metadata)
{
    if (!flash_initialized || !data || size == 0) {
        return 0;
    }
    
    // پیدا کردن فضای خالی
    uint32_t address = external_flash_find_free_space(size + METADATA_SIZE);
    if (address == 0) {
        return 0;  // فضای کافی نیست
    }
    
    // محاسبه checksum
    uint8_t checksum = calculate_checksum(data, size);
    
    // آماده‌سازی metadata
    flash_metadata_t new_metadata;
    if (metadata) {
        new_metadata = *metadata;
    } else {
        memset(&new_metadata, 0, sizeof(new_metadata));
    }
    
    new_metadata.address = address;
    new_metadata.size = size;
    new_metadata.timestamp = hal_rtc_get_time_s();
    new_metadata.checksum = checksum;
    new_metadata.is_valid = true;
    
    // نوشتن metadata
    hal_flash_write(address, (uint8_t *)&new_metadata, METADATA_SIZE);
    
    // نوشتن داده با DMA (سریع‌تر)
    uint32_t data_address = address + METADATA_SIZE;
    
    // استفاده از DMA برای نوشتن سریع
    dma_config_t dma_config = {
        .type = DMA_TRANSFER_MEMORY_TO_PERIPHERAL,
        .priority = DMA_PRIORITY_HIGH,
        .source_address = (uint32_t)data,
        .destination_address = hal_flash_get_write_address(data_address),
        .data_size = size,
        .transfer_count = 1,
        .increment_source = true,
        .increment_destination = false,
        .data_width = 32,
        .circular_mode = false,
        .callback = NULL
    };
    
    int32_t dma_channel = dma_start_transfer(&dma_config);
    if (dma_channel >= 0) {
        dma_wait_for_completion(dma_channel, 1000);
    } else {
        // Fallback به نوشتن معمولی
        hal_flash_write(data_address, data, size);
    }
    
    // اضافه کردن به جدول metadata
    add_metadata(&new_metadata);
    
    // به‌روزرسانی آدرس فعلی
    flash_current_address = data_address + size;
    
    return address;
}

bool external_flash_read(uint32_t address, uint8_t *data, uint32_t size)
{
    if (!flash_initialized || !data || size == 0) {
        return false;
    }
    
    // خواندن metadata
    flash_metadata_t metadata;
    hal_flash_read(address, (uint8_t *)&metadata, METADATA_SIZE);
    
    if (!metadata.is_valid) {
        return false;  // داده معتبر نیست
    }
    
    // بررسی اندازه
    if (size > metadata.size) {
        size = metadata.size;
    }
    
    // خواندن داده
    uint32_t data_address = address + METADATA_SIZE;
    hal_flash_read(data_address, data, size);
    
    // بررسی checksum
    uint8_t checksum = calculate_checksum(data, size);
    if (checksum != metadata.checksum) {
        return false;  // داده خراب است
    }
    
    return true;
}

bool external_flash_erase(uint32_t address, uint32_t size)
{
    if (!flash_initialized) {
        return false;
    }
    
    // حذف metadata
    remove_metadata(address);
    
    // پاک کردن sector
    uint32_t sector_start = (address / FLASH_SECTOR_SIZE) * FLASH_SECTOR_SIZE;
    hal_flash_erase_sector(sector_start);
    
    return true;
}

uint32_t external_flash_find_free_space(uint32_t required_size)
{
    if (!flash_initialized || required_size == 0) {
        return 0;
    }
    
    // جستجوی خطی برای فضای خالی
    uint32_t current = flash_current_address;
    
    // بررسی اینکه آیا فضای کافی در انتها وجود دارد
    if (current + required_size + METADATA_SIZE <= flash_base_address + FLASH_TOTAL_SIZE) {
        return current;
    }
    
    // جستجوی gaps (فضاهای خالی بین داده‌ها)
    // TODO: پیاده‌سازی جستجوی gaps
    
    return 0;  // فضای کافی پیدا نشد
}

bool external_flash_get_info(uint32_t *total_size, uint32_t *free_size, uint32_t *used_size)
{
    if (!flash_initialized || !total_size || !free_size || !used_size) {
        return false;
    }
    
    *total_size = FLASH_TOTAL_SIZE;
    
    // محاسبه فضای استفاده شده
    uint32_t used = 0;
    for (uint8_t i = 0; i < metadata_count; i++) {
        if (metadata_table[i].is_valid) {
            used += metadata_table[i].size + METADATA_SIZE;
        }
    }
    
    *used_size = used;
    *free_size = FLASH_TOTAL_SIZE - used;
    
    return true;
}

bool external_flash_defragment(void)
{
    if (!flash_initialized) {
        return false;
    }
    
    // TODO: پیاده‌سازی defragmentation
    // 1. خواندن همه داده‌های معتبر
    // 2. نوشتن مجدد به صورت پیوسته
    // 3. به‌روزرسانی metadata
    
    return true;
}

void external_flash_deinit(void)
{
    if (!flash_initialized) {
        return;
    }
    
    hal_flash_deinit();
    
    flash_initialized = false;
}

