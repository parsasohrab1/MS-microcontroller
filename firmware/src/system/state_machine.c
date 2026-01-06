/**
 * @file state_machine.c
 * @brief پیاده‌سازی State Machine
 * @version 0.1.0
 */

#include "state_machine.h"
#include <string.h>
#include <stddef.h>

// ============================================================================
// متغیرهای داخلی
// ============================================================================

static state_machine_t g_state_machine;

// ============================================================================
// جدول انتقال حالت‌ها
// ============================================================================

/**
 * جدول انتقال حالت‌ها بر اساس رویدادها
 * [حالت فعلی][رویداد] = حالت جدید
 */
static const system_state_t state_transition_table[SYSTEM_STATE_COUNT][EVENT_COUNT] = {
    // INIT
    [SYSTEM_STATE_INIT] = {
        [EVENT_INIT_COMPLETE] = SYSTEM_STATE_IDLE,
        [EVENT_ERROR_DETECTED] = SYSTEM_STATE_ERROR,
        [EVENT_EMERGENCY_STOP] = SYSTEM_STATE_SAFE_MODE,
    },
    
    // IDLE
    [SYSTEM_STATE_IDLE] = {
        [EVENT_START_MONITORING] = SYSTEM_STATE_MONITORING,
        [EVENT_ERROR_DETECTED] = SYSTEM_STATE_ERROR,
        [EVENT_EMERGENCY_STOP] = SYSTEM_STATE_SAFE_MODE,
    },
    
    // MONITORING
    [SYSTEM_STATE_MONITORING] = {
        [EVENT_DATA_READY] = SYSTEM_STATE_PROCESSING,
        [EVENT_ERROR_DETECTED] = SYSTEM_STATE_ERROR,
        [EVENT_EMERGENCY_STOP] = SYSTEM_STATE_SAFE_MODE,
    },
    
    // PROCESSING
    [SYSTEM_STATE_PROCESSING] = {
        [EVENT_PROCESSING_COMPLETE] = SYSTEM_STATE_PREDICTING,
        [EVENT_ERROR_DETECTED] = SYSTEM_STATE_ERROR,
        [EVENT_EMERGENCY_STOP] = SYSTEM_STATE_SAFE_MODE,
    },
    
    // PREDICTING
    [SYSTEM_STATE_PREDICTING] = {
        [EVENT_PREDICTION_READY] = SYSTEM_STATE_MONITORING,
        [EVENT_STIMULATION_NEEDED] = SYSTEM_STATE_STIMULATING,
        [EVENT_DRUG_NEEDED] = SYSTEM_STATE_DRUG_DELIVERY,
        [EVENT_COMMUNICATION_READY] = SYSTEM_STATE_COMMUNICATING,
        [EVENT_ERROR_DETECTED] = SYSTEM_STATE_ERROR,
        [EVENT_EMERGENCY_STOP] = SYSTEM_STATE_SAFE_MODE,
    },
    
    // STIMULATING
    [SYSTEM_STATE_STIMULATING] = {
        [EVENT_PREDICTION_READY] = SYSTEM_STATE_MONITORING,
        [EVENT_ERROR_DETECTED] = SYSTEM_STATE_ERROR,
        [EVENT_EMERGENCY_STOP] = SYSTEM_STATE_SAFE_MODE,
    },
    
    // DRUG_DELIVERY
    [SYSTEM_STATE_DRUG_DELIVERY] = {
        [EVENT_PREDICTION_READY] = SYSTEM_STATE_MONITORING,
        [EVENT_ERROR_DETECTED] = SYSTEM_STATE_ERROR,
        [EVENT_EMERGENCY_STOP] = SYSTEM_STATE_SAFE_MODE,
    },
    
    // COMMUNICATING
    [SYSTEM_STATE_COMMUNICATING] = {
        [EVENT_PREDICTION_READY] = SYSTEM_STATE_MONITORING,
        [EVENT_ERROR_DETECTED] = SYSTEM_STATE_ERROR,
        [EVENT_EMERGENCY_STOP] = SYSTEM_STATE_SAFE_MODE,
    },
    
    // ERROR
    [SYSTEM_STATE_ERROR] = {
        [EVENT_ERROR_RESOLVED] = SYSTEM_STATE_IDLE,
        [EVENT_EMERGENCY_STOP] = SYSTEM_STATE_SAFE_MODE,
    },
    
    // SAFE_MODE
    [SYSTEM_STATE_SAFE_MODE] = {
        [EVENT_ERROR_RESOLVED] = SYSTEM_STATE_IDLE,
    },
};

// ============================================================================
// نام‌های حالت‌ها و رویدادها
// ============================================================================

static const char* state_names[] = {
    [SYSTEM_STATE_INIT] = "INIT",
    [SYSTEM_STATE_IDLE] = "IDLE",
    [SYSTEM_STATE_MONITORING] = "MONITORING",
    [SYSTEM_STATE_PROCESSING] = "PROCESSING",
    [SYSTEM_STATE_PREDICTING] = "PREDICTING",
    [SYSTEM_STATE_STIMULATING] = "STIMULATING",
    [SYSTEM_STATE_DRUG_DELIVERY] = "DRUG_DELIVERY",
    [SYSTEM_STATE_COMMUNICATING] = "COMMUNICATING",
    [SYSTEM_STATE_ERROR] = "ERROR",
    [SYSTEM_STATE_SAFE_MODE] = "SAFE_MODE",
};

static const char* event_names[] = {
    [EVENT_INIT_COMPLETE] = "INIT_COMPLETE",
    [EVENT_START_MONITORING] = "START_MONITORING",
    [EVENT_DATA_READY] = "DATA_READY",
    [EVENT_PROCESSING_COMPLETE] = "PROCESSING_COMPLETE",
    [EVENT_PREDICTION_READY] = "PREDICTION_READY",
    [EVENT_STIMULATION_NEEDED] = "STIMULATION_NEEDED",
    [EVENT_DRUG_NEEDED] = "DRUG_NEEDED",
    [EVENT_COMMUNICATION_READY] = "COMMUNICATION_READY",
    [EVENT_ERROR_DETECTED] = "ERROR_DETECTED",
    [EVENT_ERROR_RESOLVED] = "ERROR_RESOLVED",
    [EVENT_EMERGENCY_STOP] = "EMERGENCY_STOP",
};

// ============================================================================
// توابع داخلی
// ============================================================================

/**
 * @brief انتقال به حالت جدید
 */
static bool transition_to_state(state_machine_t *sm, system_state_t new_state)
{
    if (!sm || new_state >= SYSTEM_STATE_COUNT) {
        return false;
    }
    
    // اگر در همان حالت هستیم، کاری نکن
    if (sm->current_state == new_state) {
        return true;
    }
    
    // اجرای callback خروج از حالت فعلی
    if (sm->on_exit) {
        if (!sm->on_exit(sm->current_state, EVENT_COUNT)) {
            return false;  // خروج ناموفق
        }
    }
    
    // به‌روزرسانی حالت
    sm->previous_state = sm->current_state;
    sm->current_state = new_state;
    sm->state_entry_time = 0;  // TODO: استفاده از timer واقعی
    sm->state_duration = 0;
    sm->state_visit_count[new_state]++;
    sm->transition_count++;
    
    // اجرای callback ورود به حالت جدید
    if (sm->on_enter) {
        if (!sm->on_enter(new_state, EVENT_COUNT)) {
            return false;  // ورود ناموفق
        }
    }
    
    return true;
}

// ============================================================================
// API عمومی
// ============================================================================

bool state_machine_init(state_machine_t *sm)
{
    if (!sm) {
        return false;
    }
    
    memset(sm, 0, sizeof(state_machine_t));
    sm->current_state = SYSTEM_STATE_INIT;
    sm->previous_state = SYSTEM_STATE_INIT;
    sm->state_entry_time = 0;
    sm->state_duration = 0;
    sm->transition_count = 0;
    
    // Initialize visit counts
    for (int i = 0; i < SYSTEM_STATE_COUNT; i++) {
        sm->state_visit_count[i] = 0;
    }
    
    return true;
}

bool state_machine_process_event(state_machine_t *sm, system_event_t event)
{
    if (!sm || event >= EVENT_COUNT) {
        return false;
    }
    
    system_state_t current = sm->current_state;
    system_state_t new_state = state_transition_table[current][event];
    
    // اگر انتقالی تعریف نشده، در همان حالت بمان
    if (new_state == current || new_state >= SYSTEM_STATE_COUNT) {
        // رویداد در این حالت نادیده گرفته می‌شود
        return false;
    }
    
    // بررسی انتقال (اگر callback تعریف شده باشد)
    if (sm->transition_check) {
        if (!sm->transition_check(current, new_state, event)) {
            return false;  // انتقال مجاز نیست
        }
    }
    
    // انجام انتقال
    return transition_to_state(sm, new_state);
}

system_state_t state_machine_get_current_state(const state_machine_t *sm)
{
    if (!sm) {
        return SYSTEM_STATE_INIT;
    }
    return sm->current_state;
}

system_state_t state_machine_get_previous_state(const state_machine_t *sm)
{
    if (!sm) {
        return SYSTEM_STATE_INIT;
    }
    return sm->previous_state;
}

uint32_t state_machine_get_state_duration(const state_machine_t *sm)
{
    if (!sm) {
        return 0;
    }
    // TODO: محاسبه واقعی بر اساس timer
    return sm->state_duration;
}

bool state_machine_is_in_state(const state_machine_t *sm, system_state_t state)
{
    if (!sm) {
        return false;
    }
    return (sm->current_state == state);
}

bool state_machine_force_transition(state_machine_t *sm, system_state_t new_state)
{
    if (!sm || new_state >= SYSTEM_STATE_COUNT) {
        return false;
    }
    
    return transition_to_state(sm, new_state);
}

void state_machine_set_on_enter(state_machine_t *sm, state_action_t callback)
{
    if (sm) {
        sm->on_enter = callback;
    }
}

void state_machine_set_on_exit(state_machine_t *sm, state_action_t callback)
{
    if (sm) {
        sm->on_exit = callback;
    }
}

void state_machine_set_on_action(state_machine_t *sm, state_action_t callback)
{
    if (sm) {
        sm->on_action = callback;
    }
}

void state_machine_get_statistics(const state_machine_t *sm, uint32_t *visit_counts)
{
    if (!sm || !visit_counts) {
        return;
    }
    
    for (int i = 0; i < SYSTEM_STATE_COUNT; i++) {
        visit_counts[i] = sm->state_visit_count[i];
    }
}

const char* state_machine_get_state_name(system_state_t state)
{
    if (state >= SYSTEM_STATE_COUNT) {
        return "UNKNOWN";
    }
    return state_names[state];
}

const char* state_machine_get_event_name(system_event_t event)
{
    if (event >= EVENT_COUNT) {
        return "UNKNOWN";
    }
    return event_names[event];
}

// تابع دسترسی به State Machine سراسری
state_machine_t* state_machine_get_instance(void)
{
    return &g_state_machine;
}

