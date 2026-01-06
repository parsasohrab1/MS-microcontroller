/**
 * @file hsm.c
 * @brief Hardware Security Module Implementation
 */

#include "hsm.h"
#include "../system/hal.h"
#include <string.h>
#include <stddef.h>

// ============================================================================
// Private Variables
// ============================================================================

static bool hsm_initialized = false;
static bool hsm_locked = false;
static hsm_key_info_t key_slots[HSM_MAX_KEYS];
static bool key_slot_used[HSM_MAX_KEYS];

// ============================================================================
// Private Functions
// ============================================================================

/**
 * @brief بررسی دسترسی به HSM
 */
static bool check_access(void)
{
    if (!hsm_initialized || hsm_locked) {
        return false;
    }
    return true;
}

/**
 * @brief پیدا کردن slot خالی
 */
static int find_free_slot(void)
{
    for (int i = 0; i < HSM_MAX_KEYS; i++) {
        if (!key_slot_used[i]) {
            return i;
        }
    }
    return -1;
}

// ============================================================================
// Public Functions
// ============================================================================

bool hsm_init(void)
{
    if (hsm_initialized) {
        return true;
    }
    
    // بررسی وجود HSM hardware
    if (!hal_hsm_is_available()) {
        return false;
    }
    
    // مقداردهی اولیه HSM hardware
    if (!hal_hsm_init()) {
        return false;
    }
    
    // پاک کردن key slots
    memset(key_slots, 0, sizeof(key_slots));
    memset(key_slot_used, 0, sizeof(key_slot_used));
    
    hsm_initialized = true;
    hsm_locked = false;
    
    return true;
}

bool hsm_generate_key(
    uint8_t key_id,
    hsm_key_type_t type,
    uint8_t usage,
    bool persistent
)
{
    if (!check_access()) {
        return false;
    }
    
    if (key_id >= HSM_MAX_KEYS) {
        return false;
    }
    
    // بررسی وجود کلید
    if (key_slot_used[key_id]) {
        return false;  // کلید قبلاً وجود دارد
    }
    
    // تولید کلید با hardware
    uint8_t key_data[HSM_KEY_SIZE];
    if (!hal_hsm_generate_key(type, key_data, HSM_KEY_SIZE)) {
        return false;
    }
    
    // ذخیره در HSM hardware
    if (!hal_hsm_store_key(key_id, key_data, HSM_KEY_SIZE, persistent)) {
        return false;
    }
    
    // ذخیره metadata
    key_slots[key_id].key_id = key_id;
    key_slots[key_id].type = type;
    key_slots[key_id].usage = usage;
    key_slots[key_id].persistent = persistent;
    key_slots[key_id].exportable = false;
    key_slot_used[key_id] = true;
    
    return true;
}

bool hsm_store_key(
    uint8_t key_id,
    const uint8_t *key_data,
    uint32_t key_size,
    hsm_key_type_t type,
    uint8_t usage,
    bool persistent
)
{
    if (!check_access()) {
        return false;
    }
    
    if (key_id >= HSM_MAX_KEYS || !key_data || key_size == 0) {
        return false;
    }
    
    // بررسی اندازه کلید
    if (key_size > HSM_KEY_SIZE) {
        return false;
    }
    
    // ذخیره در HSM hardware
    if (!hal_hsm_store_key(key_id, key_data, key_size, persistent)) {
        return false;
    }
    
    // ذخیره metadata
    key_slots[key_id].key_id = key_id;
    key_slots[key_id].type = type;
    key_slots[key_id].usage = usage;
    key_slots[key_id].persistent = persistent;
    key_slots[key_id].exportable = false;
    key_slot_used[key_id] = true;
    
    return true;
}

bool hsm_delete_key(uint8_t key_id)
{
    if (!check_access()) {
        return false;
    }
    
    if (key_id >= HSM_MAX_KEYS) {
        return false;
    }
    
    if (!key_slot_used[key_id]) {
        return false;  // کلید وجود ندارد
    }
    
    // حذف از HSM hardware
    if (!hal_hsm_delete_key(key_id)) {
        return false;
    }
    
    // پاک کردن metadata
    memset(&key_slots[key_id], 0, sizeof(hsm_key_info_t));
    key_slot_used[key_id] = false;
    
    return true;
}

bool hsm_key_exists(uint8_t key_id)
{
    if (key_id >= HSM_MAX_KEYS) {
        return false;
    }
    
    return key_slot_used[key_id];
}

bool hsm_get_key_info(uint8_t key_id, hsm_key_info_t *info)
{
    if (!info || key_id >= HSM_MAX_KEYS) {
        return false;
    }
    
    if (!key_slot_used[key_id]) {
        return false;
    }
    
    memcpy(info, &key_slots[key_id], sizeof(hsm_key_info_t));
    return true;
}

bool hsm_encrypt(
    uint8_t key_id,
    const uint8_t *plaintext,
    uint32_t plaintext_size,
    uint8_t *ciphertext,
    uint32_t *ciphertext_size
)
{
    if (!check_access()) {
        return false;
    }
    
    if (!key_slot_used[key_id]) {
        return false;
    }
    
    // بررسی usage
    if (!(key_slots[key_id].usage & HSM_KEY_USAGE_ENCRYPT)) {
        return false;
    }
    
    // استفاده از hardware crypto
    return hal_hsm_encrypt(
        key_id,
        plaintext,
        plaintext_size,
        ciphertext,
        ciphertext_size
    );
}

bool hsm_decrypt(
    uint8_t key_id,
    const uint8_t *ciphertext,
    uint32_t ciphertext_size,
    uint8_t *plaintext,
    uint32_t *plaintext_size
)
{
    if (!check_access()) {
        return false;
    }
    
    if (!key_slot_used[key_id]) {
        return false;
    }
    
    // بررسی usage
    if (!(key_slots[key_id].usage & HSM_KEY_USAGE_DECRYPT)) {
        return false;
    }
    
    // استفاده از hardware crypto
    return hal_hsm_decrypt(
        key_id,
        ciphertext,
        ciphertext_size,
        plaintext,
        plaintext_size
    );
}

bool hsm_sign(
    uint8_t key_id,
    const uint8_t *data,
    uint32_t data_size,
    uint8_t *signature,
    uint32_t *signature_size
)
{
    if (!check_access()) {
        return false;
    }
    
    if (!key_slot_used[key_id]) {
        return false;
    }
    
    // بررسی usage
    if (!(key_slots[key_id].usage & HSM_KEY_USAGE_SIGN)) {
        return false;
    }
    
    // استفاده از hardware crypto
    return hal_hsm_sign(
        key_id,
        data,
        data_size,
        signature,
        signature_size
    );
}

bool hsm_verify(
    uint8_t key_id,
    const uint8_t *data,
    uint32_t data_size,
    const uint8_t *signature,
    uint32_t signature_size
)
{
    if (!check_access()) {
        return false;
    }
    
    if (!key_slot_used[key_id]) {
        return false;
    }
    
    // بررسی usage
    if (!(key_slots[key_id].usage & HSM_KEY_USAGE_VERIFY)) {
        return false;
    }
    
    // استفاده از hardware crypto
    return hal_hsm_verify(
        key_id,
        data,
        data_size,
        signature,
        signature_size
    );
}

bool hsm_hash(
    uint8_t algorithm,
    const uint8_t *data,
    uint32_t data_size,
    uint8_t *hash,
    uint32_t *hash_size
)
{
    if (!check_access()) {
        return false;
    }
    
    // استفاده از hardware accelerator
    return hal_hsm_hash(algorithm, data, data_size, hash, hash_size);
}

bool hsm_random(uint8_t *random_data, uint32_t size)
{
    if (!check_access()) {
        return false;
    }
    
    // استفاده از hardware RNG
    return hal_hsm_random(random_data, size);
}

bool hsm_lock(void)
{
    hsm_locked = true;
    return true;
}

bool hsm_unlock(const uint8_t *password, uint32_t password_size)
{
    // TODO: بررسی password
    // در حال حاضر placeholder
    hsm_locked = false;
    return true;
}

bool hsm_is_available(void)
{
    return hsm_initialized && !hsm_locked;
}

