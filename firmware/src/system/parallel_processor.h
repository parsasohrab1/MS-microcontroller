/**
 * @file parallel_processor.h
 * @brief پردازش موازی برای بهینه‌سازی زمان پاسخ
 * @version 1.0.0
 */

#ifndef PARALLEL_PROCESSOR_H
#define PARALLEL_PROCESSOR_H

#include <stdint.h>
#include <stdbool.h>

// ============================================================================
// انواع Task
// ============================================================================

typedef enum {
    TASK_TYPE_SIGNAL_PROCESSING = 0,
    TASK_TYPE_ML_INFERENCE,
    TASK_TYPE_FEATURE_EXTRACTION,
    TASK_TYPE_DATA_COMPRESSION,
    TASK_TYPE_ENCRYPTION
} task_type_t;

typedef enum {
    TASK_PRIORITY_LOW = 0,
    TASK_PRIORITY_NORMAL,
    TASK_PRIORITY_HIGH,
    TASK_PRIORITY_CRITICAL
} task_priority_t;

// ============================================================================
// ساختار Task
// ============================================================================

typedef struct {
    uint8_t task_id;
    task_type_t type;
    task_priority_t priority;
    void *input_data;
    void *output_data;
    uint32_t data_size;
    void (*callback)(void *result);
    bool completed;
    uint32_t execution_time_us;
} parallel_task_t;

// ============================================================================
// توابع API
// ============================================================================

/**
 * @brief مقداردهی اولیه Parallel Processor
 * @return true در صورت موفقیت
 */
bool parallel_processor_init(void);

/**
 * @brief اضافه کردن task به queue
 * @param task task برای اجرا
 * @return شناسه task (یا -1 در صورت خطا)
 */
int32_t parallel_processor_add_task(parallel_task_t *task);

/**
 * @brief اجرای parallel tasks
 * @param max_tasks حداکثر تعداد tasks برای اجرا
 * @return تعداد tasks اجرا شده
 */
uint32_t parallel_processor_execute(uint32_t max_tasks);

/**
 * @brief انتظار برای اتمام task
 * @param task_id شناسه task
 * @param timeout_ms timeout (ms)
 * @return true در صورت موفقیت
 */
bool parallel_processor_wait_for_task(int32_t task_id, uint32_t timeout_ms);

/**
 * @brief بررسی وضعیت task
 * @param task_id شناسه task
 * @return true اگر کامل شده
 */
bool parallel_processor_is_task_complete(int32_t task_id);

/**
 * @brief دریافت نتیجه task
 * @param task_id شناسه task
 * @param result اشاره‌گر به نتیجه
 * @return true در صورت موفقیت
 */
bool parallel_processor_get_result(int32_t task_id, void **result);

/**
 * @brief خاموش کردن ماژول
 */
void parallel_processor_deinit(void);

#endif // PARALLEL_PROCESSOR_H

