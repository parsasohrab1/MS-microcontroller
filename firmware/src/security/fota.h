/**
 * @file fota.h
 * @brief Firmware Over-The-Air (FOTA) Secure Update
 * به‌روزرسانی امن firmware از طریق OTA
 */

#ifndef FOTA_H
#define FOTA_H

#include <stdint.h>
#include <stdbool.h>
#include "secure_boot.h"

// ============================================================================
// Constants
// ============================================================================

#define FOTA_MAX_FIRMWARE_SIZE (512 * 1024)  // 512 KB
#define FOTA_CHUNK_SIZE 1024
#define FOTA_METADATA_SIZE 256
#define FOTA_SLOT_A_ADDR 0x08020000
#define FOTA_SLOT_B_ADDR 0x08100000

// ============================================================================
// Types
// ============================================================================

typedef enum {
    FOTA_STATUS_IDLE = 0,
    FOTA_STATUS_DOWNLOADING,
    FOTA_STATUS_VERIFYING,
    FOTA_STATUS_INSTALLING,
    FOTA_STATUS_SUCCESS,
    FOTA_STATUS_FAILED,
    FOTA_STATUS_ROLLBACK
} fota_status_t;

typedef enum {
    FOTA_ERROR_NONE = 0,
    FOTA_ERROR_INVALID_SIGNATURE,
    FOTA_ERROR_INVALID_HASH,
    FOTA_ERROR_INSUFFICIENT_SPACE,
    FOTA_ERROR_DOWNLOAD_FAILED,
    FOTA_ERROR_VERIFICATION_FAILED,
    FOTA_ERROR_INSTALL_FAILED,
    FOTA_ERROR_ROLLBACK_FAILED
} fota_error_t;

typedef struct {
    uint32_t version;
    uint32_t size;
    uint8_t hash[32];
    uint8_t signature[SECURE_BOOT_SIGNATURE_SIZE];
    uint32_t crc32;
    bool encrypted;
    uint8_t encryption_key_id;
} fota_metadata_t;

typedef struct {
    fota_status_t status;
    fota_error_t error;
    uint32_t downloaded_bytes;
    uint32_t total_bytes;
    uint32_t current_version;
    uint32_t target_version;
    uint8_t progress_percent;
} fota_info_t;

// ============================================================================
// Callbacks
// ============================================================================

typedef void (*fota_progress_callback_t)(uint32_t downloaded, uint32_t total);
typedef void (*fota_status_callback_t)(fota_status_t status, fota_error_t error);

// ============================================================================
// Functions
// ============================================================================

/**
 * @brief مقداردهی اولیه FOTA
 * @return true در صورت موفقیت
 */
bool fota_init(void);

/**
 * @brief شروع دانلود firmware جدید
 * @param metadata metadata firmware
 * @return true در صورت موفقیت
 */
bool fota_start_download(const fota_metadata_t *metadata);

/**
 * @brief دریافت chunk از firmware
 * @param chunk_data داده chunk
 * @param chunk_size اندازه chunk
 * @param chunk_index شماره chunk
 * @return true در صورت موفقیت
 */
bool fota_write_chunk(
    const uint8_t *chunk_data,
    uint32_t chunk_size,
    uint32_t chunk_index
);

/**
 * @brief بررسی صحت firmware دانلود شده
 * @return true در صورت موفقیت
 */
bool fota_verify_firmware(void);

/**
 * @brief نصب firmware جدید
 * @return true در صورت موفقیت
 */
bool fota_install_firmware(void);

/**
 * @brief Rollback به نسخه قبلی
 * @return true در صورت موفقیت
 */
bool fota_rollback(void);

/**
 * @brief دریافت وضعیت FOTA
 * @param info خروجی اطلاعات
 * @return true در صورت موفقیت
 */
bool fota_get_info(fota_info_t *info);

/**
 * @brief تنظیم callback برای progress
 * @param callback تابع callback
 */
void fota_set_progress_callback(fota_progress_callback_t callback);

/**
 * @brief تنظیم callback برای status
 * @param callback تابع callback
 */
void fota_set_status_callback(fota_status_callback_t callback);

/**
 * @brief دریافت نسخه فعلی firmware
 * @return نسخه firmware
 */
uint32_t fota_get_current_version(void);

/**
 * @brief بررسی وجود firmware جدید
 * @param version نسخه جدید
 * @return true اگر نسخه جدیدتر است
 */
bool fota_is_newer_version(uint32_t version);

/**
 * @brief لغو دانلود
 * @return true در صورت موفقیت
 */
bool fota_cancel_download(void);

/**
 * @brief پاک کردن firmware دانلود شده
 * @return true در صورت موفقیت
 */
bool fota_clear_downloaded_firmware(void);

/**
 * @brief فعال/غیرفعال کردن encryption
 * @param enable فعال/غیرفعال
 * @return true در صورت موفقیت
 */
bool fota_set_encryption_enabled(bool enable);

/**
 * @brief decrypt کردن firmware
 * @param encrypted_data داده رمزگذاری شده
 * @param size اندازه داده
 * @param decrypted_data خروجی داده رمزگشایی شده
 * @param key_id شناسه کلید
 * @return true در صورت موفقیت
 */
bool fota_decrypt_firmware(
    const uint8_t *encrypted_data,
    uint32_t size,
    uint8_t *decrypted_data,
    uint8_t key_id
);

#endif // FOTA_H

