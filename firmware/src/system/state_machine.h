/**
 * @file state_machine.h
 * @brief State Machine برای مدیریت حالت‌های سیستم
 * @version 0.1.0
 * 
 * این ماژول یک State Machine ساده و کارآمد برای مدیریت حالت‌های سیستم
 * نوروپلتفرم MS فراهم می‌کند.
 */

#ifndef STATE_MACHINE_H
#define STATE_MACHINE_H

#include <stdint.h>
#include <stdbool.h>
#include "config.h"

// ============================================================================
// تعریف حالت‌های سیستم
// ============================================================================

typedef enum {
    SYSTEM_STATE_INIT = 0,           // حالت مقداردهی اولیه
    SYSTEM_STATE_IDLE,               // حالت آماده به کار
    SYSTEM_STATE_MONITORING,         // حالت نظارت
    SYSTEM_STATE_PROCESSING,         // حالت پردازش داده
    SYSTEM_STATE_PREDICTING,         // حالت پیش‌بینی
    SYSTEM_STATE_STIMULATING,         // حالت تحریک
    SYSTEM_STATE_DRUG_DELIVERY,      // حالت دارورسانی
    SYSTEM_STATE_COMMUNICATING,       // حالت ارتباط
    SYSTEM_STATE_ERROR,              // حالت خطا
    SYSTEM_STATE_SAFE_MODE,          // حالت ایمن (fail-safe)
    SYSTEM_STATE_COUNT               // تعداد کل حالت‌ها
} system_state_t;

// ============================================================================
// تعریف رویدادها
// ============================================================================

typedef enum {
    EVENT_INIT_COMPLETE = 0,         // مقداردهی اولیه کامل شد
    EVENT_START_MONITORING,          // شروع نظارت
    EVENT_DATA_READY,                // داده آماده است
    EVENT_PROCESSING_COMPLETE,        // پردازش کامل شد
    EVENT_PREDICTION_READY,           // پیش‌بینی آماده است
    EVENT_STIMULATION_NEEDED,         // نیاز به تحریک
    EVENT_DRUG_NEEDED,                // نیاز به دارو
    EVENT_COMMUNICATION_READY,        // ارتباط آماده است
    EVENT_ERROR_DETECTED,             // خطا تشخیص داده شد
    EVENT_ERROR_RESOLVED,             // خطا برطرف شد
    EVENT_EMERGENCY_STOP,             // توقف اضطراری
    EVENT_COUNT                       // تعداد کل رویدادها
} system_event_t;

// ============================================================================
// تعریف توابع callback
// ============================================================================

/**
 * @brief تابع callback برای اجرای اقدامات در هر حالت
 * @param state حالت فعلی
 * @param event رویداد دریافتی
 * @return true در صورت موفقیت
 */
typedef bool (*state_action_t)(system_state_t state, system_event_t event);

/**
 * @brief تابع callback برای بررسی امکان انتقال به حالت جدید
 * @param current_state حالت فعلی
 * @param new_state حالت جدید
 * @param event رویداد
 * @return true اگر انتقال مجاز است
 */
typedef bool (*state_transition_check_t)(system_state_t current_state, 
                                         system_state_t new_state, 
                                         system_event_t event);

// ============================================================================
// ساختار State Machine
// ============================================================================

typedef struct {
    system_state_t current_state;     // حالت فعلی
    system_state_t previous_state;    // حالت قبلی
    uint32_t state_entry_time;        // زمان ورود به حالت (ms)
    uint32_t state_duration;          // مدت زمان در حالت فعلی (ms)
    
    // Callback functions
    state_action_t on_enter;          // هنگام ورود به حالت
    state_action_t on_exit;           // هنگام خروج از حالت
    state_action_t on_action;         // اقدامات در حالت
    state_transition_check_t transition_check;  // بررسی انتقال
    
    // Statistics
    uint32_t state_visit_count[SYSTEM_STATE_COUNT];  // تعداد بازدید از هر حالت
    uint32_t transition_count;        // تعداد انتقال‌ها
} state_machine_t;

// ============================================================================
// API عمومی
// ============================================================================

/**
 * @brief مقداردهی اولیه State Machine
 * @param sm اشاره‌گر به State Machine
 * @return true در صورت موفقیت
 */
bool state_machine_init(state_machine_t *sm);

/**
 * @brief پردازش رویداد و انتقال حالت در صورت نیاز
 * @param sm اشاره‌گر به State Machine
 * @param event رویداد دریافتی
 * @return true در صورت موفقیت
 */
bool state_machine_process_event(state_machine_t *sm, system_event_t event);

/**
 * @brief دریافت حالت فعلی
 * @param sm اشاره‌گر به State Machine
 * @return حالت فعلی
 */
system_state_t state_machine_get_current_state(const state_machine_t *sm);

/**
 * @brief دریافت حالت قبلی
 * @param sm اشاره‌گر به State Machine
 * @return حالت قبلی
 */
system_state_t state_machine_get_previous_state(const state_machine_t *sm);

/**
 * @brief دریافت مدت زمان در حالت فعلی
 * @param sm اشاره‌گر به State Machine
 * @return مدت زمان (ms)
 */
uint32_t state_machine_get_state_duration(const state_machine_t *sm);

/**
 * @brief بررسی اینکه آیا در حالت مشخصی هستیم
 * @param sm اشاره‌گر به State Machine
 * @param state حالت مورد بررسی
 * @return true اگر در این حالت هستیم
 */
bool state_machine_is_in_state(const state_machine_t *sm, system_state_t state);

/**
 * @brief انتقال مستقیم به حالت (با احتیاط استفاده شود)
 * @param sm اشاره‌گر به State Machine
 * @param new_state حالت جدید
 * @return true در صورت موفقیت
 */
bool state_machine_force_transition(state_machine_t *sm, system_state_t new_state);

/**
 * @brief تنظیم callback برای ورود به حالت
 * @param sm اشاره‌گر به State Machine
 * @param callback تابع callback
 */
void state_machine_set_on_enter(state_machine_t *sm, state_action_t callback);

/**
 * @brief تنظیم callback برای خروج از حالت
 * @param sm اشاره‌گر به State Machine
 * @param callback تابع callback
 */
void state_machine_set_on_exit(state_machine_t *sm, state_action_t callback);

/**
 * @brief تنظیم callback برای اقدامات در حالت
 * @param sm اشاره‌گر به State Machine
 * @param callback تابع callback
 */
void state_machine_set_on_action(state_machine_t *sm, state_action_t callback);

/**
 * @brief دریافت آمار State Machine
 * @param sm اشاره‌گر به State Machine
 * @param visit_counts آرایه برای ذخیره تعداد بازدیدها (باید حداقل SYSTEM_STATE_COUNT عنصر داشته باشد)
 */
void state_machine_get_statistics(const state_machine_t *sm, uint32_t *visit_counts);

/**
 * @brief دریافت نام حالت به صورت رشته
 * @param state حالت
 * @return نام حالت
 */
const char* state_machine_get_state_name(system_state_t state);

/**
 * @brief دریافت نام رویداد به صورت رشته
 * @param event رویداد
 * @return نام رویداد
 */
const char* state_machine_get_event_name(system_event_t event);

#endif // STATE_MACHINE_H

