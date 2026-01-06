/**
 * @file memory_pool.h
 * @brief Memory Pool Allocator برای مدیریت حافظه
 * @version 0.1.0
 * 
 * این ماژول یک memory pool allocator برای مدیریت کارآمد حافظه
 * در سیستم embedded فراهم می‌کند.
 */

#ifndef MEMORY_POOL_H
#define MEMORY_POOL_H

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>
#include "config.h"

// ============================================================================
// تعریف Memory Pool
// ============================================================================

typedef struct memory_pool memory_pool_t;

// ============================================================================
// API عمومی
// ============================================================================

/**
 * @brief ایجاد یک memory pool
 * @param block_size اندازه هر بلوک (bytes)
 * @param block_count تعداد بلوک‌ها
 * @param alignment تراز حافظه (مثلاً 4 برای 32-bit)
 * @return اشاره‌گر به memory pool یا NULL در صورت خطا
 */
memory_pool_t* memory_pool_create(size_t block_size, uint32_t block_count, size_t alignment);

/**
 * @brief حذف memory pool
 * @param pool اشاره‌گر به memory pool
 */
void memory_pool_destroy(memory_pool_t *pool);

/**
 * @brief تخصیص یک بلوک از pool
 * @param pool اشاره‌گر به memory pool
 * @return اشاره‌گر به بلوک تخصیص یافته یا NULL
 */
void* memory_pool_alloc(memory_pool_t *pool);

/**
 * @brief آزاد کردن یک بلوک
 * @param pool اشاره‌گر به memory pool
 * @param ptr اشاره‌گر به بلوک
 * @return true در صورت موفقیت
 */
bool memory_pool_free(memory_pool_t *pool, void *ptr);

/**
 * @brief بررسی اینکه آیا اشاره‌گر متعلق به این pool است
 * @param pool اشاره‌گر به memory pool
 * @param ptr اشاره‌گر مورد بررسی
 * @return true اگر متعلق است
 */
bool memory_pool_contains(memory_pool_t *pool, const void *ptr);

/**
 * @brief دریافت تعداد بلوک‌های آزاد
 * @param pool اشاره‌گر به memory pool
 * @return تعداد بلوک‌های آزاد
 */
uint32_t memory_pool_get_free_count(const memory_pool_t *pool);

/**
 * @brief دریافت تعداد بلوک‌های استفاده شده
 * @param pool اشاره‌گر به memory pool
 * @return تعداد بلوک‌های استفاده شده
 */
uint32_t memory_pool_get_used_count(const memory_pool_t *pool);

/**
 * @brief دریافت اندازه هر بلوک
 * @param pool اشاره‌گر به memory pool
 * @return اندازه بلوک (bytes)
 */
size_t memory_pool_get_block_size(const memory_pool_t *pool);

/**
 * @brief بررسی اینکه آیا pool پر است
 * @param pool اشاره‌گر به memory pool
 * @return true اگر پر است
 */
bool memory_pool_is_full(const memory_pool_t *pool);

/**
 * @brief بررسی اینکه آیا pool خالی است
 * @param pool اشاره‌گر به memory pool
 * @return true اگر خالی است
 */
bool memory_pool_is_empty(const memory_pool_t *pool);

/**
 * @brief دریافت آمار pool
 * @param pool اشاره‌گر به memory pool
 * @param total_blocks تعداد کل بلوک‌ها
 * @param free_blocks تعداد بلوک‌های آزاد
 * @param used_blocks تعداد بلوک‌های استفاده شده
 * @param fragmentation درصد fragmentation (0-100)
 */
void memory_pool_get_statistics(const memory_pool_t *pool,
                               uint32_t *total_blocks,
                               uint32_t *free_blocks,
                               uint32_t *used_blocks,
                               uint8_t *fragmentation);

#endif // MEMORY_POOL_H

