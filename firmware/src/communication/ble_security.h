/**
 * @file ble_security.h
 * @brief BLE Security - رمزنگاری پیشرفته BLE
 * بهبود رمزنگاری BLE با pairing پیشرفته، key rotation و mutual authentication
 */

#ifndef BLE_SECURITY_H
#define BLE_SECURITY_H

#include <stdint.h>
#include <stdbool.h>

// ============================================================================
// Constants
// ============================================================================

#define BLE_SECURITY_MAX_PAIRED_DEVICES 8
#define BLE_SECURITY_KEY_SIZE 16
#define BLE_SECURITY_IRK_SIZE 16  // Identity Resolving Key
#define BLE_SECURITY_CSRK_SIZE 16  // Connection Signature Resolving Key
#define BLE_SECURITY_LTK_SIZE 16  // Long Term Key
#define BLE_SECURITY_KEY_ROTATION_INTERVAL 3600  // seconds (1 hour)

// ============================================================================
// Types
// ============================================================================

typedef enum {
    BLE_PAIRING_METHOD_JUST_WORKS = 0,
    BLE_PAIRING_METHOD_PASSKEY,
    BLE_PAIRING_METHOD_OOB,  // Out-of-Band
    BLE_PAIRING_METHOD_NUMERIC_COMPARISON
} ble_pairing_method_t;

typedef enum {
    BLE_SECURITY_LEVEL_NONE = 0,
    BLE_SECURITY_LEVEL_LOW,
    BLE_SECURITY_LEVEL_MEDIUM,
    BLE_SECURITY_LEVEL_HIGH
} ble_security_level_t;

typedef struct {
    uint8_t device_address[6];
    uint8_t irk[BLE_SECURITY_IRK_SIZE];
    uint8_t ltk[BLE_SECURITY_LTK_SIZE];
    uint8_t csrk[BLE_SECURITY_CSRK_SIZE];
    uint32_t pairing_timestamp;
    uint32_t last_key_rotation;
    ble_security_level_t security_level;
    bool authenticated;
    bool bonded;
} ble_paired_device_t;

typedef struct {
    uint8_t public_key[64];  // ECDH public key
    uint8_t private_key[32];  // ECDH private key
    bool key_exchange_complete;
} ble_key_exchange_t;

// ============================================================================
// Functions
// ============================================================================

/**
 * @brief مقداردهی اولیه BLE Security
 * @return true در صورت موفقیت
 */
bool ble_security_init(void);

/**
 * @brief شروع pairing پیشرفته
 * @param method روش pairing
 * @param device_address آدرس دستگاه
 * @return true در صورت موفقیت
 */
bool ble_security_start_pairing(
    ble_pairing_method_t method,
    const uint8_t *device_address
);

/**
 * @brief تکمیل pairing
 * @param device_address آدرس دستگاه
 * @param passkey Passkey (در صورت نیاز)
 * @return true در صورت موفقیت
 */
bool ble_security_complete_pairing(
    const uint8_t *device_address,
    uint32_t passkey
);

/**
 * @brief Mutual authentication
 * @param device_address آدرس دستگاه
 * @return true در صورت موفقیت
 */
bool ble_security_mutual_authenticate(const uint8_t *device_address);

/**
 * @brief Key rotation
 * @param device_address آدرس دستگاه
 * @return true در صورت موفقیت
 */
bool ble_security_rotate_keys(const uint8_t *device_address);

/**
 * @brief بررسی نیاز به key rotation
 * @param device_address آدرس دستگاه
 * @return true اگر نیاز به rotation است
 */
bool ble_security_needs_key_rotation(const uint8_t *device_address);

/**
 * @brief دریافت LTK برای دستگاه
 * @param device_address آدرس دستگاه
 * @param ltk خروجی LTK
 * @return true در صورت موفقیت
 */
bool ble_security_get_ltk(const uint8_t *device_address, uint8_t *ltk);

/**
 * @brief دریافت IRK برای دستگاه
 * @param device_address آدرس دستگاه
 * @param irk خروجی IRK
 * @return true در صورت موفقیت
 */
bool ble_security_get_irk(const uint8_t *device_address, uint8_t *irk);

/**
 * @brief دریافت CSRK برای دستگاه
 * @param device_address آدرس دستگاه
 * @param csrk خروجی CSRK
 * @return true در صورت موفقیت
 */
bool ble_security_get_csrk(const uint8_t *device_address, uint8_t *csrk);

/**
 * @brief حذف paired device
 * @param device_address آدرس دستگاه
 * @return true در صورت موفقیت
 */
bool ble_security_remove_device(const uint8_t *device_address);

/**
 * @brief بررسی اینکه آیا دستگاه paired است
 * @param device_address آدرس دستگاه
 * @return true اگر paired است
 */
bool ble_security_is_paired(const uint8_t *device_address);

/**
 * @brief دریافت اطلاعات paired device
 * @param device_address آدرس دستگاه
 * @param device_info خروجی اطلاعات
 * @return true در صورت موفقیت
 */
bool ble_security_get_device_info(
    const uint8_t *device_address,
    ble_paired_device_t *device_info
);

/**
 * @brief تنظیم security level
 * @param level سطح امنیتی
 * @return true در صورت موفقیت
 */
bool ble_security_set_level(ble_security_level_t level);

/**
 * @brief دریافت security level
 * @return سطح امنیتی فعلی
 */
ble_security_level_t ble_security_get_level(void);

/**
 * @brief Key exchange (ECDH)
 * @param device_address آدرس دستگاه
 * @param peer_public_key public key طرف مقابل
 * @param shared_secret خروجی shared secret
 * @return true در صورت موفقیت
 */
bool ble_security_key_exchange(
    const uint8_t *device_address,
    const uint8_t *peer_public_key,
    uint8_t *shared_secret
);

/**
 * @brief تولید passkey برای pairing
 * @return passkey (6 digits)
 */
uint32_t ble_security_generate_passkey(void);

/**
 * @brief بررسی passkey
 * @param device_address آدرس دستگاه
 * @param passkey passkey برای بررسی
 * @return true اگر صحیح است
 */
bool ble_security_verify_passkey(
    const uint8_t *device_address,
    uint32_t passkey
);

#endif // BLE_SECURITY_H

