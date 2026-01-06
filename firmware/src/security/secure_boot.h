/**
 * @file secure_boot.h
 * @brief Secure Boot Implementation
 * پیاده‌سازی Secure Boot برای جلوگیری از اجرای firmware غیرمجاز
 */

#ifndef SECURE_BOOT_H
#define SECURE_BOOT_H

#include <stdint.h>
#include <stdbool.h>

// ============================================================================
// Constants
// ============================================================================

#define SECURE_BOOT_KEY_SIZE 32
#define SECURE_BOOT_SIGNATURE_SIZE 64
#define SECURE_BOOT_BOOTLOADER_ADDR 0x08000000
#define SECURE_BOOT_APP_ADDR 0x08020000

// ============================================================================
// Types
// ============================================================================

typedef enum {
    SECURE_BOOT_OK = 0,
    SECURE_BOOT_INVALID_SIGNATURE,
    SECURE_BOOT_INVALID_HASH,
    SECURE_BOOT_KEY_NOT_FOUND,
    SECURE_BOOT_VERIFICATION_FAILED,
    SECURE_BOOT_FLASH_ERROR
} secure_boot_status_t;

typedef struct {
    uint8_t signature[SECURE_BOOT_SIGNATURE_SIZE];
    uint32_t version;
    uint32_t size;
    uint8_t hash[32];  // SHA-256
    uint32_t crc32;
} secure_boot_header_t;

// ============================================================================
// Functions
// ============================================================================

/**
 * @brief مقداردهی اولیه Secure Boot
 * @return true در صورت موفقیت
 */
bool secure_boot_init(void);

/**
 * @brief بررسی صحت bootloader
 * @return secure_boot_status_t
 */
secure_boot_status_t secure_boot_verify_bootloader(void);

/**
 * @brief بررسی صحت application firmware
 * @param app_addr آدرس application
 * @param app_size اندازه application
 * @return secure_boot_status_t
 */
secure_boot_status_t secure_boot_verify_application(
    uint32_t app_addr,
    uint32_t app_size
);

/**
 * @brief بررسی signature firmware
 * @param data داده firmware
 * @param size اندازه داده
 * @param signature signature برای بررسی
 * @return secure_boot_status_t
 */
secure_boot_status_t secure_boot_verify_signature(
    const uint8_t *data,
    uint32_t size,
    const uint8_t *signature
);

/**
 * @brief محاسبه hash firmware
 * @param data داده firmware
 * @param size اندازه داده
 * @param hash خروجی hash (32 bytes)
 * @return true در صورت موفقیت
 */
bool secure_boot_calculate_hash(
    const uint8_t *data,
    uint32_t size,
    uint8_t *hash
);

/**
 * @brief دریافت public key برای verification
 * @param key_id شناسه کلید
 * @param public_key خروجی public key
 * @return true در صورت موفقیت
 */
bool secure_boot_get_public_key(uint8_t key_id, uint8_t *public_key);

/**
 * @brief ذخیره public key در secure storage
 * @param key_id شناسه کلید
 * @param public_key public key
 * @return true در صورت موفقیت
 */
bool secure_boot_store_public_key(uint8_t key_id, const uint8_t *public_key);

/**
 * @brief فعال/غیرفعال کردن Secure Boot
 * @param enable فعال/غیرفعال
 * @return true در صورت موفقیت
 */
bool secure_boot_set_enabled(bool enable);

/**
 * @brief بررسی وضعیت Secure Boot
 * @return true اگر فعال است
 */
bool secure_boot_is_enabled(void);

/**
 * @brief دریافت وضعیت آخرین verification
 * @return secure_boot_status_t
 */
secure_boot_status_t secure_boot_get_last_status(void);

/**
 * @brief Log رویداد Secure Boot
 * @param event رویداد
 * @param status وضعیت
 */
void secure_boot_log_event(const char *event, secure_boot_status_t status);

#endif // SECURE_BOOT_H

