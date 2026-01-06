/**
 * @file parallel_processor.c
 * @brief پیاده‌سازی پردازش موازی
 * @version 1.0.0
 */

#include "parallel_processor.h"
#include "hal.h"
#include "dma_manager.h"
#include "hardware_accelerators.h"
#include <string.h>

// ============================================================================
// متغیرهای داخلی
// ============================================================================

#define MAX_PARALLEL_TASKS 8
#define TASK_QUEUE_SIZE 16

static bool parallel_processor_initialized = false;
static parallel_task_t task_queue[TASK_QUEUE_SIZE];
static uint8_t queue_head = 0;
static uint8_t queue_tail = 0;
static uint8_t queue_count = 0;
static parallel_task_t active_tasks[MAX_PARALLEL_TASKS];
static uint8_t next_task_id = 0;

// ============================================================================
// توابع داخلی
// ============================================================================

/**
 * @brief پیدا کردن task در queue
 */
static parallel_task_t *find_task_in_queue(int32_t task_id)
{
    for (uint8_t i = 0; i < TASK_QUEUE_SIZE; i++) {
        if (task_queue[i].task_id == task_id) {
            return &task_queue[i];
        }
    }
    return NULL;
}

/**
 * @brief پیدا کردن task فعال
 */
static parallel_task_t *find_active_task(int32_t task_id)
{
    for (uint8_t i = 0; i < MAX_PARALLEL_TASKS; i++) {
        if (active_tasks[i].task_id == task_id) {
            return &active_tasks[i];
        }
    }
    return NULL;
}

/**
 * @brief پیدا کردن slot خالی در active tasks
 */
static int8_t find_free_slot(void)
{
    for (uint8_t i = 0; i < MAX_PARALLEL_TASKS; i++) {
        if (active_tasks[i].task_id == 0 || active_tasks[i].completed) {
            return i;
        }
    }
    return -1;
}

/**
 * @brief اجرای task
 */
static bool execute_task(parallel_task_t *task)
{
    if (!task) {
        return false;
    }
    
    uint32_t start_time = hal_rtc_get_time_ms() * 1000;  // microseconds
    
    bool success = false;
    
    switch (task->type) {
        case TASK_TYPE_SIGNAL_PROCESSING:
            // استفاده از DMA و hardware accelerators
            // TODO: پیاده‌سازی signal processing
            success = true;
            break;
            
        case TASK_TYPE_ML_INFERENCE:
            // استفاده از ML hardware accelerator
            if (hw_accelerator_is_enabled(HW_ACCEL_ML)) {
                success = hw_accel_ml_inference(
                    NULL,
                    (float *)task->input_data,
                    (float *)task->output_data
                );
            } else {
                success = false;
            }
            break;
            
        case TASK_TYPE_FEATURE_EXTRACTION:
            // استفاده از FFT accelerator
            if (hw_accelerator_is_enabled(HW_ACCEL_FFT)) {
                success = hw_accel_fft_execute(
                    (float *)task->input_data,
                    (float *)task->output_data,
                    task->data_size / sizeof(float)
                );
            } else {
                success = false;
            }
            break;
            
        case TASK_TYPE_DATA_COMPRESSION:
            // استفاده از DMA برای انتقال سریع
            success = dma_memcpy(task->output_data, task->input_data, task->data_size);
            break;
            
        case TASK_TYPE_ENCRYPTION:
            // استفاده از Crypto accelerator
            if (hw_accelerator_is_enabled(HW_ACCEL_CRYPTO)) {
                // TODO: استفاده از encryption accelerator
                success = true;
            } else {
                success = false;
            }
            break;
            
        default:
            success = false;
            break;
    }
    
    uint32_t end_time = hal_rtc_get_time_ms() * 1000;
    task->execution_time_us = end_time - start_time;
    task->completed = true;
    
    // فراخوانی callback
    if (task->callback && success) {
        task->callback(task->output_data);
    }
    
    return success;
}

// ============================================================================
// توابع API عمومی
// ============================================================================

bool parallel_processor_init(void)
{
    if (parallel_processor_initialized) {
        return true;
    }
    
    // مقداردهی اولیه
    memset(task_queue, 0, sizeof(task_queue));
    memset(active_tasks, 0, sizeof(active_tasks));
    queue_head = 0;
    queue_tail = 0;
    queue_count = 0;
    next_task_id = 1;
    
    parallel_processor_initialized = true;
    return true;
}

int32_t parallel_processor_add_task(parallel_task_t *task)
{
    if (!parallel_processor_initialized || !task) {
        return -1;
    }
    
    // بررسی ظرفیت queue
    if (queue_count >= TASK_QUEUE_SIZE) {
        return -1;  // Queue full
    }
    
    // اختصاص شناسه
    task->task_id = next_task_id++;
    if (next_task_id == 0) {
        next_task_id = 1;  // Skip 0
    }
    
    // اضافه کردن به queue
    task_queue[queue_tail] = *task;
    queue_tail = (queue_tail + 1) % TASK_QUEUE_SIZE;
    queue_count++;
    
    return task->task_id;
}

uint32_t parallel_processor_execute(uint32_t max_tasks)
{
    if (!parallel_processor_initialized) {
        return 0;
    }
    
    uint32_t executed = 0;
    
    // اجرای tasks موجود در queue
    while (queue_count > 0 && executed < max_tasks) {
        // پیدا کردن slot خالی
        int8_t slot = find_free_slot();
        if (slot < 0) {
            break;  // همه slots پر هستند
        }
        
        // گرفتن task از queue
        parallel_task_t *task = &task_queue[queue_head];
        queue_head = (queue_head + 1) % TASK_QUEUE_SIZE;
        queue_count--;
        
        // اضافه کردن به active tasks
        active_tasks[slot] = *task;
        active_tasks[slot].completed = false;
        
        // اجرای task (در صورت امکان به صورت موازی)
        // در این پیاده‌سازی، tasks به صورت sequential اجرا می‌شوند
        // اما می‌توانند با hardware accelerators به صورت موازی اجرا شوند
        execute_task(&active_tasks[slot]);
        
        executed++;
    }
    
    return executed;
}

bool parallel_processor_wait_for_task(int32_t task_id, uint32_t timeout_ms)
{
    if (!parallel_processor_initialized || task_id < 0) {
        return false;
    }
    
    uint32_t start_time = hal_rtc_get_time_ms();
    
    while (true) {
        parallel_task_t *task = find_active_task(task_id);
        if (task && task->completed) {
            return true;
        }
        
        // بررسی timeout
        if (timeout_ms > 0) {
            uint32_t elapsed = hal_rtc_get_time_ms() - start_time;
            if (elapsed >= timeout_ms) {
                return false;  // Timeout
            }
        }
        
        // Yield
        hal_cpu_wait_for_interrupt();
    }
}

bool parallel_processor_is_task_complete(int32_t task_id)
{
    if (!parallel_processor_initialized || task_id < 0) {
        return false;
    }
    
    parallel_task_t *task = find_active_task(task_id);
    return task && task->completed;
}

bool parallel_processor_get_result(int32_t task_id, void **result)
{
    if (!parallel_processor_initialized || task_id < 0 || !result) {
        return false;
    }
    
    parallel_task_t *task = find_active_task(task_id);
    if (!task || !task->completed) {
        return false;
    }
    
    *result = task->output_data;
    return true;
}

void parallel_processor_deinit(void)
{
    if (!parallel_processor_initialized) {
        return;
    }
    
    // پاک کردن queue و active tasks
    memset(task_queue, 0, sizeof(task_queue));
    memset(active_tasks, 0, sizeof(active_tasks));
    queue_head = 0;
    queue_tail = 0;
    queue_count = 0;
    
    parallel_processor_initialized = false;
}

