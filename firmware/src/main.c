/**
 * @file main.c
 * @brief نقطه ورود اصلی سیستم نوروپلتفرم MS
 * @version 1.0.0
 * 
 * این فایل از FreeRTOS برای مدیریت چندوظیفه‌ای استفاده می‌کند.
 */

#include "config.h"
#include <stdint.h>
#include <stdbool.h>

// FreeRTOS includes (بعد از نصب FreeRTOS فعال می‌شود)
#ifdef FREERTOS_AVAILABLE
    #include "FreeRTOS.h"
    #include "task.h"
#else
    // Stub برای کامپایل بدون FreeRTOS
    #define FREERTOS_AVAILABLE 0
#endif

// System includes
#include "system/rtos_tasks.h"
#include "system/hal.h"
#include "system/state_machine.h"
#include "system/event_driver.h"

// Security includes
#include "security/secure_boot.h"
#include "security/anti_tampering.h"

/**
 * @brief مقداردهی اولیه سیستم قبل از شروع RTOS
 */
static bool system_init(void)
{
    // مقداردهی اولیه HAL
    if (!hal_init())
    {
        return false;
    }
    
    // بررسی Secure Boot (اگر فعال باشد)
    #ifdef ENABLE_SECURE_BOOT
    if (!secure_boot_verify_application())
    {
        // Firmware معتبر نیست
        while(1); // Hang
    }
    #endif
    
    // مقداردهی اولیه State Machine
    // TODO: state_machine_init();
    
    // مقداردهی اولیه Event Driver
    // TODO: event_driver_init();
    
    // مقداردهی اولیه Anti-Tampering
    // TODO: anti_tampering_init();
    
    return true;
}

/**
 * @brief تابع اصلی سیستم
 * @return کد خروجی (هرگز نباید برگردد)
 */
int main(void)
{
    // مقداردهی اولیه سیستم
    if (!system_init())
    {
        // خطا در مقداردهی اولیه
        while(1); // Hang
    }
    
    #if FREERTOS_AVAILABLE
    // مقداردهی اولیه RTOS و ایجاد tasks
    if (!rtos_init())
    {
        // خطا در ایجاد RTOS tasks
        while(1); // Hang
    }
    
    // شروع scheduler - این خط هرگز برنمی‌گردد
    rtos_start_scheduler();
    #else
    // حالت fallback: main loop (برای تست بدون FreeRTOS)
    while (true)
    {
        // TODO: اجرای وظایف به صورت sequential
        // این حالت فقط برای تست است و نباید در production استفاده شود
        
        // Delay
        hal_delay_ms(10);
    }
    #endif
    
    // این خط هرگز نباید اجرا شود
    return 0;
}

