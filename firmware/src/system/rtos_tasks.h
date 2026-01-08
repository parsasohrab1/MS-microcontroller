/**
 * @file rtos_tasks.h
 * @brief تعریف وظایف (Tasks) برای FreeRTOS
 * @version 1.0.0
 */

#ifndef RTOS_TASKS_H
#define RTOS_TASKS_H

#include <stdint.h>
#include <stdbool.h>
#include "config.h"

// ============================================================================
// اولویت‌های Task
// ============================================================================

#define TASK_PRIORITY_IDLE                0           // پایین‌ترین اولویت
#define TASK_PRIORITY_LOW                 1           // اولویت پایین
#define TASK_PRIORITY_NORMAL              2           // اولویت عادی
#define TASK_PRIORITY_HIGH                3           // اولویت بالا
#define TASK_PRIORITY_CRITICAL            4           // بالاترین اولویت

// ============================================================================
// اندازه Stack برای هر Task
// ============================================================================

#define TASK_STACK_MONITORING             512         // Monitoring task
#define TASK_STACK_PROCESSING             1024        // Signal processing task
#define TASK_STACK_ML                     2048        // ML inference task
#define TASK_STACK_STIMULATION            512         // Stimulation task
#define TASK_STACK_COMMUNICATION          512         // Communication task
#define TASK_STACK_POWER_MANAGEMENT       256         // Power management task
#define TASK_STACK_WATCHDOG               256         // Watchdog task

// ============================================================================
// تعریف ساختارهای داده برای Queue
// ============================================================================

/**
 * @brief داده‌های سنسور
 */
typedef struct {
    float eeg_data[EEG_CHANNELS];          // داده‌های EEG
    float biomarkers[BIOMARKER_COUNT];     // بیومارکرها
    uint32_t timestamp;                    // زمان نمونه‌برداری
    bool valid;                            // اعتبار داده
} sensor_data_t;

/**
 * @brief داده‌های پردازش شده
 */
typedef struct {
    float filtered_eeg[EEG_CHANNELS];     // داده‌های فیلتر شده
    float features[64];                     // ویژگی‌های استخراج شده
    uint32_t timestamp;
    bool valid;
} processed_data_t;

/**
 * @brief نتیجه پیش‌بینی ML
 */
typedef struct {
    float attack_probability;               // احتمال حمله (0-1)
    float severity;                         // شدت (0-1)
    float confidence;                       // اطمینان (0-1)
    uint32_t timestamp;
    bool valid;
} ml_prediction_t;

/**
 * @brief دستور تحریک
 */
typedef struct {
    float current;                          // جریان (mA)
    float frequency;                        // فرکانس (Hz)
    float pulse_width;                      // عرض پالس (ms)
    uint32_t duration;                      // مدت زمان (ms)
    bool enable;                            // فعال/غیرفعال
} stimulation_command_t;

// ============================================================================
// Prototypes برای Tasks
// ============================================================================

/**
 * @brief Task مانیتورینگ سنسورها
 * @param pvParameters پارامترهای task (QueueHandle_t برای ارسال داده)
 */
void vMonitoringTask(void *pvParameters);

/**
 * @brief Task پردازش سیگنال
 * @param pvParameters پارامترهای task (QueueHandle_t برای دریافت/ارسال)
 */
void vProcessingTask(void *pvParameters);

/**
 * @brief Task اجرای مدل ML
 * @param pvParameters پارامترهای task (QueueHandle_t برای دریافت/ارسال)
 */
void vMLTask(void *pvParameters);

/**
 * @brief Task کنترل تحریک
 * @param pvParameters پارامترهای task (QueueHandle_t برای دریافت دستورات)
 */
void vStimulationTask(void *pvParameters);

/**
 * @brief Task ارتباطات (BLE)
 * @param pvParameters پارامترهای task
 */
void vCommunicationTask(void *pvParameters);

/**
 * @brief Task مدیریت انرژی
 * @param pvParameters پارامترهای task
 */
void vPowerManagementTask(void *pvParameters);

/**
 * @brief Task Watchdog
 * @param pvParameters پارامترهای task
 */
void vWatchdogTask(void *pvParameters);

// ============================================================================
// Prototypes برای Initialization
// ============================================================================

/**
 * @brief مقداردهی اولیه RTOS و ایجاد تمام tasks
 * @return true در صورت موفقیت
 */
bool rtos_init(void);

/**
 * @brief شروع scheduler
 */
void rtos_start_scheduler(void);

// ============================================================================
// Global Queue Handles (تعریف در rtos_tasks.c)
// ============================================================================

extern void* g_sensor_queue;                // Queue برای داده‌های سنسور
extern void* g_processed_queue;            // Queue برای داده‌های پردازش شده
extern void* g_ml_queue;                    // Queue برای نتایج ML
extern void* g_stimulation_queue;           // Queue برای دستورات تحریک

// ============================================================================
// Global Semaphore Handles
// ============================================================================

extern void* g_ml_mutex;                    // Mutex برای ML inference
extern void* g_stimulation_mutex;           // Mutex برای تحریک
extern void* g_communication_mutex;          // Mutex برای ارتباطات

#endif // RTOS_TASKS_H

