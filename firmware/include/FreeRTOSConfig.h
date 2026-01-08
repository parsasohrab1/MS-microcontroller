/**
 * @file FreeRTOSConfig.h
 * @brief تنظیمات FreeRTOS برای سیستم نوروپلتفرم MS
 * @version 1.0.0
 * 
 * این فایل تنظیمات FreeRTOS را برای میکروکنترلر nRF52840 (Cortex-M4) تعریف می‌کند.
 */

#ifndef FREERTOS_CONFIG_H
#define FREERTOS_CONFIG_H

// ============================================================================
// تنظیمات CPU و Clock
// ============================================================================

#define configCPU_CLOCK_HZ                64000000UL  // 64 MHz برای nRF52840
#define configTICK_RATE_HZ                1000UL      // 1 ms tick rate
#define configUSE_PREEMPTION              1           // Preemptive scheduling
#define configUSE_TIME_SLICING            1           // Time slicing برای tasks با اولویت یکسان

// ============================================================================
// تنظیمات Task
// ============================================================================

#define configMAX_PRIORITIES              5           // 5 سطح اولویت (0-4)
#define configMINIMAL_STACK_SIZE          128         // حداقل stack size (bytes)
#define configMAX_TASK_NAME_LEN          16          // حداکثر طول نام task

// ============================================================================
// تنظیمات Memory
// ============================================================================

#define configTOTAL_HEAP_SIZE             16384      // 16 KB heap (قابل تنظیم)
#define configUSE_MALLOC_FAILED_HOOK      1           // Hook برای malloc failed
#define configUSE_MEMORY_POOL             0           // استفاده از heap استاندارد

// ============================================================================
// تنظیمات Synchronization
// ============================================================================

#define configUSE_MUTEXES                 1           // استفاده از Mutex
#define configUSE_RECURSIVE_MUTEXES       1           // Recursive mutex
#define configUSE_COUNTING_SEMAPHORES     1           // Counting semaphore
#define configUSE_BINARY_SEMAPHORES       1           // Binary semaphore
#define configUSE_QUEUES                  1           // استفاده از Queue

// ============================================================================
// تنظیمات Interrupt
// ============================================================================

#define configKERNEL_INTERRUPT_PRIORITY   0           // بالاترین اولویت برای kernel
#define configMAX_SYSCALL_INTERRUPT_PRIORITY 4        // اولویت برای FreeRTOS API calls
#define configPRIO_BITS                   3           // 3 بیت برای اولویت (8 سطح)
#define configLIBRARY_LOWEST_INTERRUPT_PRIORITY 7      // پایین‌ترین اولویت interrupt

// ============================================================================
// تنظیمات Hooks
// ============================================================================

#define configUSE_IDLE_HOOK               0           // Idle hook (غیرفعال برای صرفه‌جویی)
#define configUSE_TICK_HOOK               0           // Tick hook (غیرفعال)
#define configUSE_TICKLESS_IDLE           1           // Tickless idle برای صرفه‌جویی انرژی
#define configEXPECTED_IDLE_TIME_BEFORE_SLEEP 2       // حداقل idle time قبل از sleep (ticks)

// ============================================================================
// تنظیمات Trace و Debug
// ============================================================================

#define configUSE_TRACE_FACILITY          1           // Trace facility
#define configUSE_STATS_FORMATTING_FUNCTIONS 1        // Stats formatting
#define configGENERATE_RUN_TIME_STATS     0           // Runtime stats (نیاز به timer)

// ============================================================================
// تنظیمات Software Timer
// ============================================================================

#define configUSE_TIMERS                  1           // استفاده از Software timers
#define configTIMER_TASK_PRIORITY         2           // اولویت timer task
#define configTIMER_QUEUE_LENGTH          10          // طول صف timer
#define configTIMER_TASK_STACK_DEPTH      256         // Stack size برای timer task

// ============================================================================
// تنظیمات Application-specific
// ============================================================================

// Hook functions - باید در main.c یا فایل دیگری تعریف شوند
extern void vApplicationStackOverflowHook(TaskHandle_t xTask, char *pcTaskName);
extern void vApplicationMallocFailedHook(void);
extern void vApplicationIdleHook(void);
extern void vApplicationTickHook(void);

// ============================================================================
// تنظیمات Port-specific برای ARM Cortex-M4
// ============================================================================

// این تنظیمات برای nRF52840 (Cortex-M4F) مناسب است
#define configENABLE_FPU                  1           // Floating Point Unit
#define configENABLE_MPU                  0           // Memory Protection Unit (غیرفعال)

// ============================================================================
// تنظیمات Co-routines (غیرفعال)
// ============================================================================

#define configUSE_CO_ROUTINES             0           // Co-routines غیرفعال

// ============================================================================
// تنظیمات Assert
// ============================================================================

#define configASSERT(x)                   if((x) == 0) { taskDISABLE_INTERRUPTS(); for(;;); }

// ============================================================================
// Include FreeRTOS headers
// ============================================================================

#include <stdint.h>

// تعریف نوع داده‌های FreeRTOS
typedef void * TaskHandle_t;
typedef void * QueueHandle_t;
typedef void * SemaphoreHandle_t;
typedef void * TimerHandle_t;

#endif // FREERTOS_CONFIG_H

