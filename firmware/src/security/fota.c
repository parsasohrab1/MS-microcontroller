/**
 * @file fota.c
 * @brief Firmware Over-The-Air Implementation
 */

#include "fota.h"
#include "../system/hal.h"
#include <string.h>
#include <stddef.h>

// ============================================================================
// Private Variables
// ============================================================================

static fota_info_t fota_info = {
    .status = FOTA_STATUS_IDLE,
    .error = FOTA_ERROR_NONE,
    .downloaded_bytes = 0,
    .total_bytes = 0,
    .current_version = 1,
    .target_version = 0,
    .progress_percent = 0
};

static fota_metadata_t current_metadata;
static fota_progress_callback_t progress_callback = NULL;
static fota_status_callback_t status_callback = NULL;
static uint32_t current_slot = FOTA_SLOT_B_ADDR;
static bool encryption_enabled = true;

// ============================================================================
// Private Functions
// ============================================================================

/**
 * @brief محاسبه CRC32
 */
static uint32_t calculate_crc32(const uint8_t *data, uint32_t size)
{
    // TODO: پیاده‌سازی CRC32
    // می‌توان از hardware CRC استفاده کرد
    return 0;  // Placeholder
}

/**
 * @brief رمزگشایی firmware
 */
static bool decrypt_firmware_chunk(
    const uint8_t *encrypted,
    uint32_t size,
    uint8_t *decrypted,
    uint8_t key_id
)
{
    if (!encryption_enabled) {
        memcpy(decrypted, encrypted, size);
        return true;
    }
    
    // TODO: استفاده از HSM یا hardware crypto
    // در حال حاضر placeholder
    return false;
}

/**
 * @brief بررسی صحت chunk
 */
static bool verify_chunk(
    const uint8_t *chunk_data,
    uint32_t chunk_size,
    uint32_t chunk_index
)
{
    // بررسی CRC32 chunk
    uint32_t calculated_crc = calculate_crc32(chunk_data, chunk_size);
    // TODO: مقایسه با CRC ذخیره شده
    
    return true;  // Placeholder
}

// ============================================================================
// Public Functions
// ============================================================================

bool fota_init(void)
{
    // بررسی Secure Boot
    if (!secure_boot_is_enabled()) {
        return false;
    }
    
    // دریافت نسخه فعلی
    fota_info.current_version = fota_get_current_version();
    
    fota_info.status = FOTA_STATUS_IDLE;
    fota_info.error = FOTA_ERROR_NONE;
    
    return true;
}

bool fota_start_download(const fota_metadata_t *metadata)
{
    if (fota_info.status != FOTA_STATUS_IDLE) {
        return false;  // FOTA در حال انجام است
    }
    
    // بررسی نسخه
    if (!fota_is_newer_version(metadata->version)) {
        return false;  // نسخه جدیدتر نیست
    }
    
    // بررسی فضای کافی
    if (metadata->size > FOTA_MAX_FIRMWARE_SIZE) {
        fota_info.error = FOTA_ERROR_INSUFFICIENT_SPACE;
        return false;
    }
    
    // کپی metadata
    memcpy(&current_metadata, metadata, sizeof(fota_metadata_t));
    
    // پاک کردن slot
    if (!hal_flash_erase(current_slot, metadata->size)) {
        fota_info.error = FOTA_ERROR_INSUFFICIENT_SPACE;
        return false;
    }
    
    // شروع دانلود
    fota_info.status = FOTA_STATUS_DOWNLOADING;
    fota_info.downloaded_bytes = 0;
    fota_info.total_bytes = metadata->size;
    fota_info.target_version = metadata->version;
    fota_info.progress_percent = 0;
    fota_info.error = FOTA_ERROR_NONE;
    
    if (status_callback) {
        status_callback(fota_info.status, fota_info.error);
    }
    
    return true;
}

bool fota_write_chunk(
    const uint8_t *chunk_data,
    uint32_t chunk_size,
    uint32_t chunk_index
)
{
    if (fota_info.status != FOTA_STATUS_DOWNLOADING) {
        return false;
    }
    
    // بررسی اندازه
    if (fota_info.downloaded_bytes + chunk_size > fota_info.total_bytes) {
        fota_info.status = FOTA_STATUS_FAILED;
        fota_info.error = FOTA_ERROR_DOWNLOAD_FAILED;
        if (status_callback) {
            status_callback(fota_info.status, fota_info.error);
        }
        return false;
    }
    
    // رمزگشایی (در صورت نیاز)
    uint8_t decrypted_chunk[FOTA_CHUNK_SIZE];
    if (current_metadata.encrypted) {
        if (!decrypt_firmware_chunk(
            chunk_data,
            chunk_size,
            decrypted_chunk,
            current_metadata.encryption_key_id
        )) {
            fota_info.status = FOTA_STATUS_FAILED;
            fota_info.error = FOTA_ERROR_DOWNLOAD_FAILED;
            return false;
        }
        chunk_data = decrypted_chunk;
    }
    
    // نوشتن به flash
    uint32_t write_addr = current_slot + (chunk_index * FOTA_CHUNK_SIZE);
    if (!hal_flash_write(write_addr, chunk_data, chunk_size)) {
        fota_info.status = FOTA_STATUS_FAILED;
        fota_info.error = FOTA_ERROR_DOWNLOAD_FAILED;
        if (status_callback) {
            status_callback(fota_info.status, fota_info.error);
        }
        return false;
    }
    
    // به‌روزرسانی progress
    fota_info.downloaded_bytes += chunk_size;
    fota_info.progress_percent = (fota_info.downloaded_bytes * 100) / fota_info.total_bytes;
    
    if (progress_callback) {
        progress_callback(fota_info.downloaded_bytes, fota_info.total_bytes);
    }
    
    // بررسی اتمام دانلود
    if (fota_info.downloaded_bytes >= fota_info.total_bytes) {
        fota_info.status = FOTA_STATUS_VERIFYING;
        if (status_callback) {
            status_callback(fota_info.status, fota_info.error);
        }
    }
    
    return true;
}

bool fota_verify_firmware(void)
{
    if (fota_info.status != FOTA_STATUS_VERIFYING) {
        return false;
    }
    
    // بررسی hash
    uint8_t calculated_hash[32];
    if (!secure_boot_calculate_hash(
        (uint8_t *)current_slot,
        current_metadata.size,
        calculated_hash
    )) {
        fota_info.status = FOTA_STATUS_FAILED;
        fota_info.error = FOTA_ERROR_INVALID_HASH;
        if (status_callback) {
            status_callback(fota_info.status, fota_info.error);
        }
        return false;
    }
    
    if (memcmp(calculated_hash, current_metadata.hash, 32) != 0) {
        fota_info.status = FOTA_STATUS_FAILED;
        fota_info.error = FOTA_ERROR_INVALID_HASH;
        if (status_callback) {
            status_callback(fota_info.status, fota_info.error);
        }
        return false;
    }
    
    // بررسی signature
    secure_boot_status_t sb_status = secure_boot_verify_signature(
        (uint8_t *)current_slot,
        current_metadata.size,
        current_metadata.signature
    );
    
    if (sb_status != SECURE_BOOT_OK) {
        fota_info.status = FOTA_STATUS_FAILED;
        fota_info.error = FOTA_ERROR_INVALID_SIGNATURE;
        if (status_callback) {
            status_callback(fota_info.status, fota_info.error);
        }
        return false;
    }
    
    // بررسی CRC32
    uint32_t calculated_crc = calculate_crc32(
        (uint8_t *)current_slot,
        current_metadata.size
    );
    
    if (calculated_crc != current_metadata.crc32) {
        fota_info.status = FOTA_STATUS_FAILED;
        fota_info.error = FOTA_ERROR_VERIFICATION_FAILED;
        if (status_callback) {
            status_callback(fota_info.status, fota_info.error);
        }
        return false;
    }
    
    fota_info.status = FOTA_STATUS_INSTALLING;
    if (status_callback) {
        status_callback(fota_info.status, fota_info.error);
    }
    
    return true;
}

bool fota_install_firmware(void)
{
    if (fota_info.status != FOTA_STATUS_INSTALLING) {
        return false;
    }
    
    // TODO: نصب firmware
    // 1. پاک کردن slot فعلی
    // 2. کپی firmware جدید به slot فعلی
    // 3. به‌روزرسانی boot configuration
    // 4. Reboot
    
    fota_info.status = FOTA_STATUS_SUCCESS;
    fota_info.current_version = fota_info.target_version;
    
    if (status_callback) {
        status_callback(fota_info.status, fota_info.error);
    }
    
    return true;
}

bool fota_rollback(void)
{
    // TODO: Rollback به نسخه قبلی
    fota_info.status = FOTA_STATUS_ROLLBACK;
    
    if (status_callback) {
        status_callback(fota_info.status, fota_info.error);
    }
    
    return true;
}

bool fota_get_info(fota_info_t *info)
{
    if (!info) {
        return false;
    }
    
    memcpy(info, &fota_info, sizeof(fota_info_t));
    return true;
}

void fota_set_progress_callback(fota_progress_callback_t callback)
{
    progress_callback = callback;
}

void fota_set_status_callback(fota_status_callback_t callback)
{
    status_callback = callback;
}

uint32_t fota_get_current_version(void)
{
    // TODO: خواندن از flash یا OTP
    return fota_info.current_version;
}

bool fota_is_newer_version(uint32_t version)
{
    return version > fota_info.current_version;
}

bool fota_cancel_download(void)
{
    if (fota_info.status != FOTA_STATUS_DOWNLOADING) {
        return false;
    }
    
    fota_info.status = FOTA_STATUS_IDLE;
    fota_info.downloaded_bytes = 0;
    fota_info.total_bytes = 0;
    
    if (status_callback) {
        status_callback(fota_info.status, fota_info.error);
    }
    
    return true;
}

bool fota_clear_downloaded_firmware(void)
{
    if (!hal_flash_erase(current_slot, FOTA_MAX_FIRMWARE_SIZE)) {
        return false;
    }
    
    fota_info.status = FOTA_STATUS_IDLE;
    fota_info.downloaded_bytes = 0;
    fota_info.total_bytes = 0;
    
    return true;
}

bool fota_set_encryption_enabled(bool enable)
{
    encryption_enabled = enable;
    return true;
}

bool fota_decrypt_firmware(
    const uint8_t *encrypted_data,
    uint32_t size,
    uint8_t *decrypted_data,
    uint8_t key_id
)
{
    return decrypt_firmware_chunk(encrypted_data, size, decrypted_data, key_id);
}

