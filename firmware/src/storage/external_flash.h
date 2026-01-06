/**
 * @file external_flash.h
 * @brief مدیریت External Flash برای داده‌های غیرفعال
 * @version 1.0.0
 */

#ifndef EXTERNAL_FLASH_H
#define EXTERNAL_FLASH_H

#include <stdint.h>
#include <stdbool.h>

// ============================================================================
// ساختار Metadata
// ============================================================================

typedef struct {
    uint32_t address;
    uint32_t size;
    uint32_t timestamp;
    uint8_t data_type;
    bool is_valid;
    uint8_t checksum;
} flash_metadata_t;

// ============================================================================
// توابع API
// ============================================================================

/**
 * @brief مقداردهی اولیه External Flash
 * @return true در صورت موفقیت
 */
bool external_flash_init(void);

/**
 * @brief نوشتن داده در flash
 * @param data داده برای نوشتن
 * @param size اندازه داده (bytes)
 * @param metadata metadata داده
 * @return آدرس نوشته شده (یا 0 در صورت خطا)
 */
uint32_t external_flash_write(const uint8_t *data, uint32_t size, flash_metadata_t *metadata);

/**
 * @brief خواندن داده از flash
 * @param address آدرس شروع
 * @param data بافر خروجی
 * @param size اندازه داده (bytes)
 * @return true در صورت موفقیت
 */
bool external_flash_read(uint32_t address, uint8_t *data, uint32_t size);

/**
 * @brief حذف داده از flash
 * @param address آدرس شروع
 * @param size اندازه داده
 * @return true در صورت موفقیت
 */
bool external_flash_erase(uint32_t address, uint32_t size);

/**
 * @brief پیدا کردن فضای خالی
 * @param required_size اندازه مورد نیاز
 * @return آدرس شروع (یا 0 در صورت خطا)
 */
uint32_t external_flash_find_free_space(uint32_t required_size);

/**
 * @brief دریافت اطلاعات flash
 * @param total_size اشاره‌گر به اندازه کل
 * @param free_size اشاره‌گر به فضای خالی
 * @param used_size اشاره‌گر به فضای استفاده شده
 * @return true در صورت موفقیت
 */
bool external_flash_get_info(uint32_t *total_size, uint32_t *free_size, uint32_t *used_size);

/**
 * @brief defragmentation flash
 * @return true در صورت موفقیت
 */
bool external_flash_defragment(void);

/**
 * @brief خاموش کردن ماژول
 */
void external_flash_deinit(void);

#endif // EXTERNAL_FLASH_H

