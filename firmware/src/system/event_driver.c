/**
 * @file event_driver.c
 * @brief پیاده‌سازی Event-Driven Architecture
 * @version 0.1.0
 */

#include "event_driver.h"
#include <string.h>
#include <stdlib.h>

// ============================================================================
// تعریف صف رویدادها (Circular Buffer)
// ============================================================================

#define DEFAULT_QUEUE_SIZE 32

typedef struct {
    event_t *events;
    uint32_t size;
    uint32_t head;
    uint32_t tail;
    uint32_t count;
    bool full;
} event_queue_t;

// ============================================================================
// متغیرهای داخلی
// ============================================================================

static event_queue_t g_event_queue;
static event_listener_t *g_listeners[EVENT_COUNT] = {NULL};
static bool g_initialized = false;

// آمار
static uint32_t g_total_events = 0;
static uint32_t g_processed_events = 0;
static uint32_t g_dropped_events = 0;

// ============================================================================
// توابع داخلی
// ============================================================================

/**
 * @brief اضافه کردن رویداد به صف
 */
static bool queue_enqueue(event_queue_t *queue, const event_t *event)
{
    if (!queue || !event || queue->count >= queue->size) {
        return false;
    }
    
    // کپی رویداد
    memcpy(&queue->events[queue->tail], event, sizeof(event_t));
    
    // به‌روزرسانی tail
    queue->tail = (queue->tail + 1) % queue->size;
    queue->count++;
    
    if (queue->count == queue->size) {
        queue->full = true;
    }
    
    return true;
}

/**
 * @brief خارج کردن رویداد از صف
 */
static bool queue_dequeue(event_queue_t *queue, event_t *event)
{
    if (!queue || !event || queue->count == 0) {
        return false;
    }
    
    // کپی رویداد
    memcpy(event, &queue->events[queue->head], sizeof(event_t));
    
    // به‌روزرسانی head
    queue->head = (queue->head + 1) % queue->size;
    queue->count--;
    queue->full = false;
    
    return true;
}

/**
 * @brief مرتب‌سازی listeners بر اساس اولویت
 */
static void sort_listeners_by_priority(event_listener_t **listeners)
{
    // Bubble sort ساده (برای تعداد کم listener کافی است)
    event_listener_t *temp;
    bool swapped;
    
    do {
        swapped = false;
        for (int i = 0; listeners[i] != NULL && listeners[i + 1] != NULL; i++) {
            if (listeners[i]->priority < listeners[i + 1]->priority) {
                temp = listeners[i];
                listeners[i] = listeners[i + 1];
                listeners[i + 1] = temp;
                swapped = true;
            }
        }
    } while (swapped);
}

// ============================================================================
// API عمومی
// ============================================================================

bool event_driver_init(void)
{
    if (g_initialized) {
        return true;
    }
    
    // تخصیص حافظه برای صف
    g_event_queue.events = (event_t*)malloc(DEFAULT_QUEUE_SIZE * sizeof(event_t));
    if (!g_event_queue.events) {
        return false;
    }
    
    g_event_queue.size = DEFAULT_QUEUE_SIZE;
    g_event_queue.head = 0;
    g_event_queue.tail = 0;
    g_event_queue.count = 0;
    g_event_queue.full = false;
    
    // پاک کردن listeners
    for (int i = 0; i < EVENT_COUNT; i++) {
        g_listeners[i] = NULL;
    }
    
    // Reset statistics
    g_total_events = 0;
    g_processed_events = 0;
    g_dropped_events = 0;
    
    g_initialized = true;
    return true;
}

bool event_driver_register_listener(event_listener_t *listener,
                                   event_type_t event_type,
                                   event_handler_t handler,
                                   uint32_t priority)
{
    if (!g_initialized || !listener || event_type >= EVENT_COUNT || !handler) {
        return false;
    }
    
    listener->event_type = event_type;
    listener->handler = handler;
    listener->priority = priority;
    listener->enabled = true;
    listener->next = NULL;
    
    // اضافه کردن به لیست listeners برای این نوع رویداد
    if (g_listeners[event_type] == NULL) {
        g_listeners[event_type] = listener;
    } else {
        // اضافه کردن به انتهای لیست
        event_listener_t *current = g_listeners[event_type];
        while (current->next != NULL) {
            current = current->next;
        }
        current->next = listener;
    }
    
    return true;
}

bool event_driver_unregister_listener(event_listener_t *listener)
{
    if (!g_initialized || !listener) {
        return false;
    }
    
    event_type_t type = listener->event_type;
    if (type >= EVENT_COUNT) {
        return false;
    }
    
    // حذف از لیست
    if (g_listeners[type] == listener) {
        g_listeners[type] = listener->next;
    } else {
        event_listener_t *current = g_listeners[type];
        while (current && current->next != listener) {
            current = current->next;
        }
        if (current) {
            current->next = listener->next;
        }
    }
    
    listener->next = NULL;
    return true;
}

void event_driver_set_listener_enabled(event_listener_t *listener, bool enabled)
{
    if (listener) {
        listener->enabled = enabled;
    }
}

bool event_driver_post_event(const event_t *event)
{
    if (!g_initialized || !event || event->type >= EVENT_COUNT) {
        return false;
    }
    
    g_total_events++;
    
    // اضافه کردن به صف
    if (!queue_enqueue(&g_event_queue, event)) {
        g_dropped_events++;
        return false;
    }
    
    return true;
}

bool event_driver_post_simple_event(event_type_t type, uint16_t source_id, uint32_t priority)
{
    event_t event = {
        .type = type,
        .timestamp = 0,  // TODO: استفاده از timer واقعی
        .source_id = source_id,
        .data_size = 0,
        .data = NULL,
        .priority = priority
    };
    
    return event_driver_post_event(&event);
}

uint32_t event_driver_process_events(void)
{
    if (!g_initialized) {
        return 0;
    }
    
    uint32_t processed = 0;
    event_t event;
    
    // پردازش تمام رویدادهای در صف
    while (queue_dequeue(&g_event_queue, &event)) {
        processed++;
        g_processed_events++;
        
        // پیدا کردن listeners برای این نوع رویداد
        event_listener_t *listener = g_listeners[event.type];
        
        // اجرای listeners (به ترتیب اولویت)
        while (listener) {
            if (listener->enabled && listener->handler) {
                // اجرای handler
                listener->handler(&event);
            }
            listener = listener->next;
        }
    }
    
    return processed;
}

bool event_driver_has_pending_events(void)
{
    if (!g_initialized) {
        return false;
    }
    return (g_event_queue.count > 0);
}

uint32_t event_driver_get_pending_count(void)
{
    if (!g_initialized) {
        return 0;
    }
    return g_event_queue.count;
}

void event_driver_clear_queue(void)
{
    if (!g_initialized) {
        return;
    }
    
    g_event_queue.head = 0;
    g_event_queue.tail = 0;
    g_event_queue.count = 0;
    g_event_queue.full = false;
}

bool event_driver_set_queue_size(uint32_t size)
{
    if (!g_initialized || size == 0) {
        return false;
    }
    
    // اگر صف خالی نیست، نمی‌توان اندازه را تغییر داد
    if (g_event_queue.count > 0) {
        return false;
    }
    
    // آزاد کردن حافظه قدیمی
    if (g_event_queue.events) {
        free(g_event_queue.events);
    }
    
    // تخصیص حافظه جدید
    g_event_queue.events = (event_t*)malloc(size * sizeof(event_t));
    if (!g_event_queue.events) {
        return false;
    }
    
    g_event_queue.size = size;
    g_event_queue.head = 0;
    g_event_queue.tail = 0;
    g_event_queue.count = 0;
    g_event_queue.full = false;
    
    return true;
}

void event_driver_get_statistics(uint32_t *total_events,
                                uint32_t *processed_events,
                                uint32_t *dropped_events)
{
    if (total_events) {
        *total_events = g_total_events;
    }
    if (processed_events) {
        *processed_events = g_processed_events;
    }
    if (dropped_events) {
        *dropped_events = g_dropped_events;
    }
}

