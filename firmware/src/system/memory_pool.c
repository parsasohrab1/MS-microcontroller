/**
 * @file memory_pool.c
 * @brief پیاده‌سازی Memory Pool Allocator
 * @version 0.1.0
 */

#include "memory_pool.h"
#include <string.h>
#include <stdlib.h>
#include <stdalign.h>

// ============================================================================
// ساختار Memory Pool
// ============================================================================

struct memory_pool {
    void *memory;              // حافظه تخصیص یافته
    size_t block_size;        // اندازه هر بلوک
    uint32_t block_count;      // تعداد بلوک‌ها
    size_t alignment;          // تراز حافظه
    uint32_t *free_list;       // لیست بلوک‌های آزاد (indices)
    uint32_t free_count;       // تعداد بلوک‌های آزاد
    uint32_t used_count;       // تعداد بلوک‌های استفاده شده
    bool *used_flags;          // پرچم‌های استفاده
};

// ============================================================================
// توابع داخلی
// ============================================================================

/**
 * @brief محاسبه اندازه کل حافظه مورد نیاز
 */
static size_t calculate_total_size(size_t block_size, uint32_t block_count, size_t alignment)
{
    // اندازه هر بلوک با تراز
    size_t aligned_block_size = ((block_size + alignment - 1) / alignment) * alignment;
    
    // اندازه کل
    return aligned_block_size * block_count;
}

/**
 * @brief پیدا کردن اولین بلوک آزاد
 */
static uint32_t find_free_block(memory_pool_t *pool)
{
    if (!pool) {
        return UINT32_MAX;
    }
    
    for (uint32_t i = 0; i < pool->block_count; i++) {
        if (!pool->used_flags[i]) {
            return i;
        }
    }
    
    return UINT32_MAX;  // هیچ بلوک آزادی نیست
}

// ============================================================================
// API عمومی
// ============================================================================

memory_pool_t* memory_pool_create(size_t block_size, uint32_t block_count, size_t alignment)
{
    if (block_size == 0 || block_count == 0 || alignment == 0) {
        return NULL;
    }
    
    // تخصیص ساختار pool
    memory_pool_t *pool = (memory_pool_t*)malloc(sizeof(memory_pool_t));
    if (!pool) {
        return NULL;
    }
    
    memset(pool, 0, sizeof(memory_pool_t));
    
    pool->block_size = block_size;
    pool->block_count = block_count;
    pool->alignment = alignment;
    pool->free_count = block_count;
    pool->used_count = 0;
    
    // محاسبه اندازه کل
    size_t total_size = calculate_total_size(block_size, block_count, alignment);
    
    // تخصیص حافظه با تراز
    // استفاده از aligned_alloc یا manual alignment
    #ifdef __STDC_VERSION__
    #if __STDC_VERSION__ >= 201112L
    pool->memory = aligned_alloc(alignment, total_size);
    #else
    // Fallback برای کامپایلرهای قدیمی
    pool->memory = malloc(total_size + alignment);
    if (pool->memory) {
        uintptr_t addr = (uintptr_t)pool->memory;
        uintptr_t aligned_addr = (addr + alignment - 1) & ~(alignment - 1);
        pool->memory = (void*)aligned_addr;
    }
    #endif
    #else
    pool->memory = malloc(total_size + alignment);
    if (pool->memory) {
        uintptr_t addr = (uintptr_t)pool->memory;
        uintptr_t aligned_addr = (addr + alignment - 1) & ~(alignment - 1);
        pool->memory = (void*)aligned_addr;
    }
    #endif
    
    if (!pool->memory) {
        free(pool);
        return NULL;
    }
    
    // تخصیص آرایه پرچم‌ها
    pool->used_flags = (bool*)malloc(block_count * sizeof(bool));
    if (!pool->used_flags) {
        free(pool->memory);
        free(pool);
        return NULL;
    }
    
    // مقداردهی اولیه: همه بلوک‌ها آزاد هستند
    memset(pool->used_flags, 0, block_count * sizeof(bool));
    
    // تخصیص لیست آزاد (اختیاری - برای بهینه‌سازی)
    pool->free_list = NULL;  // در این پیاده‌سازی ساده استفاده نمی‌شود
    
    return pool;
}

void memory_pool_destroy(memory_pool_t *pool)
{
    if (!pool) {
        return;
    }
    
    if (pool->memory) {
        free(pool->memory);
    }
    
    if (pool->used_flags) {
        free(pool->used_flags);
    }
    
    if (pool->free_list) {
        free(pool->free_list);
    }
    
    free(pool);
}

void* memory_pool_alloc(memory_pool_t *pool)
{
    if (!pool || pool->free_count == 0) {
        return NULL;
    }
    
    // پیدا کردن اولین بلوک آزاد
    uint32_t block_index = find_free_block(pool);
    if (block_index == UINT32_MAX) {
        return NULL;
    }
    
    // محاسبه آدرس بلوک
    size_t aligned_block_size = ((pool->block_size + pool->alignment - 1) / pool->alignment) * pool->alignment;
    void *block = (uint8_t*)pool->memory + (block_index * aligned_block_size);
    
    // علامت‌گذاری به عنوان استفاده شده
    pool->used_flags[block_index] = true;
    pool->free_count--;
    pool->used_count++;
    
    return block;
}

bool memory_pool_free(memory_pool_t *pool, void *ptr)
{
    if (!pool || !ptr) {
        return false;
    }
    
    // بررسی اینکه آیا اشاره‌گر در محدوده pool است
    if (!memory_pool_contains(pool, ptr)) {
        return false;
    }
    
    // محاسبه index بلوک
    size_t aligned_block_size = ((pool->block_size + pool->alignment - 1) / pool->alignment) * pool->alignment;
    uintptr_t base_addr = (uintptr_t)pool->memory;
    uintptr_t block_addr = (uintptr_t)ptr;
    
    if ((block_addr - base_addr) % aligned_block_size != 0) {
        return false;  // آدرس تراز نیست
    }
    
    uint32_t block_index = (uint32_t)((block_addr - base_addr) / aligned_block_size);
    
    if (block_index >= pool->block_count) {
        return false;
    }
    
    // بررسی اینکه آیا واقعاً استفاده شده است
    if (!pool->used_flags[block_index]) {
        return false;  // double free
    }
    
    // آزاد کردن
    pool->used_flags[block_index] = false;
    pool->free_count++;
    pool->used_count--;
    
    // پاک کردن حافظه (اختیاری - برای امنیت)
    memset(ptr, 0, pool->block_size);
    
    return true;
}

bool memory_pool_contains(memory_pool_t *pool, const void *ptr)
{
    if (!pool || !ptr) {
        return false;
    }
    
    uintptr_t base_addr = (uintptr_t)pool->memory;
    size_t aligned_block_size = ((pool->block_size + pool->alignment - 1) / pool->alignment) * pool->alignment;
    size_t total_size = aligned_block_size * pool->block_count;
    uintptr_t ptr_addr = (uintptr_t)ptr;
    
    return (ptr_addr >= base_addr && ptr_addr < (base_addr + total_size));
}

uint32_t memory_pool_get_free_count(const memory_pool_t *pool)
{
    if (!pool) {
        return 0;
    }
    return pool->free_count;
}

uint32_t memory_pool_get_used_count(const memory_pool_t *pool)
{
    if (!pool) {
        return 0;
    }
    return pool->used_count;
}

size_t memory_pool_get_block_size(const memory_pool_t *pool)
{
    if (!pool) {
        return 0;
    }
    return pool->block_size;
}

bool memory_pool_is_full(const memory_pool_t *pool)
{
    if (!pool) {
        return true;
    }
    return (pool->free_count == 0);
}

bool memory_pool_is_empty(const memory_pool_t *pool)
{
    if (!pool) {
        return true;
    }
    return (pool->used_count == 0);
}

void memory_pool_get_statistics(const memory_pool_t *pool,
                               uint32_t *total_blocks,
                               uint32_t *free_blocks,
                               uint32_t *used_blocks,
                               uint8_t *fragmentation)
{
    if (!pool) {
        return;
    }
    
    if (total_blocks) {
        *total_blocks = pool->block_count;
    }
    
    if (free_blocks) {
        *free_blocks = pool->free_count;
    }
    
    if (used_blocks) {
        *used_blocks = pool->used_count;
    }
    
    // محاسبه fragmentation (در این پیاده‌سازی ساده، fragmentation = 0)
    if (fragmentation) {
        *fragmentation = 0;  // Memory pool fragmentation-free است
    }
}

