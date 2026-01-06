/**
 * @file hsm.h
 * @brief Hardware Security Module (HSM)
 * ماژول امنیتی سخت‌افزاری برای ذخیره کلیدها و محاسبات رمزنگاری
 */

#ifndef HSM_H
#define HSM_H

#include <stdint.h>
#include <stdbool.h>

// ============================================================================
// Constants
// ============================================================================

#define HSM_MAX_KEYS 16
#define HSM_KEY_SIZE 32
#define HSM_SLOT_SIZE 256

// ============================================================================
// Types
// ============================================================================

typedef enum {
    HSM_KEY_TYPE_AES = 0,
    HSM_KEY_TYPE_ECDSA_PRIVATE,
    HSM_KEY_TYPE_ECDSA_PUBLIC,
    HSM_KEY_TYPE_RSA_PRIVATE,
    HSM_KEY_TYPE_RSA_PUBLIC,
    HSM_KEY_TYPE_SYMMETRIC
} hsm_key_type_t;

typedef enum {
    HSM_KEY_USAGE_ENCRYPT = 0x01,
    HSM_KEY_USAGE_DECRYPT = 0x02,
    HSM_KEY_USAGE_SIGN = 0x04,
    HSM_KEY_USAGE_VERIFY = 0x08,
    HSM_KEY_USAGE_DERIVE = 0x10
} hsm_key_usage_t;

typedef struct {
    uint8_t key_id;
    hsm_key_type_t type;
    uint8_t usage;
    bool persistent;
    bool exportable;
} hsm_key_info_t;

// ============================================================================
// Functions
// ============================================================================

/**
 * @brief مقداردهی اولیه HSM
 * @return true در صورت موفقیت
 */
bool hsm_init(void);

/**
 * @brief تولید کلید جدید
 * @param key_id شناسه کلید
 * @param type نوع کلید
 * @param usage کاربرد کلید
 * @param persistent ذخیره دائمی
 * @return true در صورت موفقیت
 */
bool hsm_generate_key(
    uint8_t key_id,
    hsm_key_type_t type,
    uint8_t usage,
    bool persistent
);

/**
 * @brief ذخیره کلید در HSM
 * @param key_id شناسه کلید
 * @param key_data داده کلید
 * @param key_size اندازه کلید
 * @param type نوع کلید
 * @param usage کاربرد کلید
 * @param persistent ذخیره دائمی
 * @return true در صورت موفقیت
 */
bool hsm_store_key(
    uint8_t key_id,
    const uint8_t *key_data,
    uint32_t key_size,
    hsm_key_type_t type,
    uint8_t usage,
    bool persistent
);

/**
 * @brief حذف کلید از HSM
 * @param key_id شناسه کلید
 * @return true در صورت موفقیت
 */
bool hsm_delete_key(uint8_t key_id);

/**
 * @brief بررسی وجود کلید
 * @param key_id شناسه کلید
 * @return true اگر کلید وجود دارد
 */
bool hsm_key_exists(uint8_t key_id);

/**
 * @brief دریافت اطلاعات کلید
 * @param key_id شناسه کلید
 * @param info خروجی اطلاعات
 * @return true در صورت موفقیت
 */
bool hsm_get_key_info(uint8_t key_id, hsm_key_info_t *info);

/**
 * @brief رمزگذاری با کلید HSM
 * @param key_id شناسه کلید
 * @param plaintext داده اصلی
 * @param plaintext_size اندازه داده
 * @param ciphertext خروجی رمزگذاری شده
 * @param ciphertext_size اندازه خروجی
 * @return true در صورت موفقیت
 */
bool hsm_encrypt(
    uint8_t key_id,
    const uint8_t *plaintext,
    uint32_t plaintext_size,
    uint8_t *ciphertext,
    uint32_t *ciphertext_size
);

/**
 * @brief رمزگشایی با کلید HSM
 * @param key_id شناسه کلید
 * @param ciphertext داده رمزگذاری شده
 * @param ciphertext_size اندازه داده
 * @param plaintext خروجی رمزگشایی شده
 * @param plaintext_size اندازه خروجی
 * @return true در صورت موفقیت
 */
bool hsm_decrypt(
    uint8_t key_id,
    const uint8_t *ciphertext,
    uint32_t ciphertext_size,
    uint8_t *plaintext,
    uint32_t *plaintext_size
);

/**
 * @brief امضای دیجیتال با کلید HSM
 * @param key_id شناسه کلید
 * @param data داده برای امضا
 * @param data_size اندازه داده
 * @param signature خروجی امضا
 * @param signature_size اندازه امضا
 * @return true در صورت موفقیت
 */
bool hsm_sign(
    uint8_t key_id,
    const uint8_t *data,
    uint32_t data_size,
    uint8_t *signature,
    uint32_t *signature_size
);

/**
 * @brief بررسی امضای دیجیتال با کلید HSM
 * @param key_id شناسه کلید
 * @param data داده اصلی
 * @param data_size اندازه داده
 * @param signature امضا
 * @param signature_size اندازه امضا
 * @return true اگر امضا معتبر است
 */
bool hsm_verify(
    uint8_t key_id,
    const uint8_t *data,
    uint32_t data_size,
    const uint8_t *signature,
    uint32_t signature_size
);

/**
 * @brief محاسبه hash با hardware accelerator
 * @param algorithm الگوریتم hash (SHA-256, SHA-512, etc.)
 * @param data داده
 * @param data_size اندازه داده
 * @param hash خروجی hash
 * @param hash_size اندازه hash
 * @return true در صورت موفقیت
 */
bool hsm_hash(
    uint8_t algorithm,
    const uint8_t *data,
    uint32_t data_size,
    uint8_t *hash,
    uint32_t *hash_size
);

/**
 * @brief تولید random number
 * @param random_data خروجی random data
 * @param size اندازه مورد نیاز
 * @return true در صورت موفقیت
 */
bool hsm_random(uint8_t *random_data, uint32_t size);

/**
 * @brief Lock کردن HSM (جلوگیری از دسترسی)
 * @return true در صورت موفقیت
 */
bool hsm_lock(void);

/**
 * @brief Unlock کردن HSM
 * @param password رمز عبور
 * @return true در صورت موفقیت
 */
bool hsm_unlock(const uint8_t *password, uint32_t password_size);

/**
 * @brief دریافت وضعیت HSM
 * @return true اگر HSM فعال است
 */
bool hsm_is_available(void);

#endif // HSM_H

