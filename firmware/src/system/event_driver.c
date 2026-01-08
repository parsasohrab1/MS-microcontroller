/**
 * @file event_driver.c
 * @brief پیاده‌سازی Event-Driven Architecture
 * @version 0.1.0
 */

#include "event_driver.h"
#include "system/memory_pool.h"
#include "system/hal.h"
#include <string.h>
#include <stdlib.h>

// ============================================================================
// تعریف صف رویدادها (Circular Buffer با Priority Queue)
// ============================================================================

#define DEFAULT_QUEUE_SIZE 32
#define MAX_PRIORITY_LEVELS 8

typedef struct {
    event_t *events;
    uint32_t size;
    uint32_t head;
    uint32_t tail;
    uint32_t count;
    bool full;
} event_queue_t;

// Priority queue برای رویدادهای با اولویت بالا
typedef struct {
    event_t *events;
    uint32_t size;
    uint32_t count;
} priority_queue_t;

// ============================================================================
// متغیرهای داخلی
// ============================================================================

static event_queue_t g_event_queue;
static priority_queue_t g_priority_queue;
static event_listener_t *g_listeners[EVENT_COUNT] = {NULL};
static bool g_initialized = false;
static memory_pool_t *g_event_pool = NULL;  // Memory pool برای event data

// آمار
static uint32_t g_total_events = 0;
static uint32_t g_processed_events = 0;
static uint32_t g_dropped_events = 0;
static uint32_t g_high_priority_events = 0;

// Thread-safety (برای RTOS)
#ifdef FREERTOS_AVAILABLE
    #include "FreeRTOS.h"
    #include "semphr.h"
    static SemaphoreHandle_t g_event_mutex = NULL;
#else
    static void* g_event_mutex = NULL;
    #define xSemaphoreTake(mutex, timeout) 1
    #define xSemaphoreGive(mutex) 1
#endif

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
    
    // ایجاد memory pool برای event data (اختیاری - برای داده‌های بزرگ)
    g_event_pool = memory_pool_create(64, 16, 4);  // 64 bytes, 16 blocks
    
    // تخصیص حافظه برای صف اصلی
    g_event_queue.events = (event_t*)malloc(DEFAULT_QUEUE_SIZE * sizeof(event_t));
    if (!g_event_queue.events) {
        return false;
    }
    
    g_event_queue.size = DEFAULT_QUEUE_SIZE;
    g_event_queue.head = 0;
    g_event_queue.tail = 0;
    g_event_queue.count = 0;
    g_event_queue.full = false;
    
    // تخصیص حافظه برای priority queue
    g_priority_queue.events = (event_t*)malloc(8 * sizeof(event_t));  // 8 events با اولویت بالا
    if (!g_priority_queue.events) {
        free(g_event_queue.events);
        return false;
    }
    
    g_priority_queue.size = 8;
    g_priority_queue.count = 0;
    
    // ایجاد mutex برای thread-safety (اگر RTOS موجود باشد)
    #ifdef FREERTOS_AVAILABLE
    g_event_mutex = xSemaphoreCreateMutex();
    if (!g_event_mutex) {
        free(g_event_queue.events);
        free(g_priority_queue.events);
        return false;
    }
    #endif
    
    // پاک کردن listeners
    for (int i = 0; i < EVENT_COUNT; i++) {
        g_listeners[i] = NULL;
    }
    
    // Reset statistics
    g_total_events = 0;
    g_processed_events = 0;
    g_dropped_events = 0;
    g_high_priority_events = 0;
    
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
    
    // Thread-safety
    #ifdef FREERTOS_AVAILABLE
    if (g_event_mutex && xSemaphoreTake(g_event_mutex, portMAX_DELAY) != pdTRUE) {
        return false;
    }
    #endif
    
    g_total_events++;
    
    // اگر اولویت بالا است، به priority queue اضافه کن
    bool success = false;
    if (event->priority >= 200) {  // اولویت بالا
        // اضافه به priority queue (اگر جا دارد)
        if (g_priority_queue.count < g_priority_queue.size) {
            // پیدا کردن جای مناسب (مرتب بر اساس اولویت)
            int insert_pos = g_priority_queue.count;
            for (int i = 0; i < g_priority_queue.count; i++) {
                if (g_priority_queue.events[i].priority < event->priority) {
                    insert_pos = i;
                    break;
                }
            }
            
            // جابجایی events
            for (int i = g_priority_queue.count; i > insert_pos; i--) {
                g_priority_queue.events[i] = g_priority_queue.events[i - 1];
            }
            
            // اضافه کردن event جدید
            memcpy(&g_priority_queue.events[insert_pos], event, sizeof(event_t));
            g_priority_queue.count++;
            g_high_priority_events++;
            success = true;
        } else {
            // Priority queue پر است - به صف عادی اضافه کن
            success = queue_enqueue(&g_event_queue, event);
        }
    } else {
        // اولویت عادی - به صف عادی اضافه کن
        success = queue_enqueue(&g_event_queue, event);
    }
    
    if (!success) {
        g_dropped_events++;
    }
    
    #ifdef FREERTOS_AVAILABLE
    if (g_event_mutex) {
        xSemaphoreGive(g_event_mutex);
    }
    #endif
    return success;
}

bool event_driver_post_simple_event(event_type_t type, uint16_t source_id, uint32_t priority)
{
    event_t event = {
        .type = type,
        .timestamp = hal_get_timestamp(),  // استفاده از HAL timer
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
    
    // Thread-safety
    #ifdef FREERTOS_AVAILABLE
    if (g_event_mutex && xSemaphoreTake(g_event_mutex, 0) != pdTRUE) {
        // Mutex گرفته شده - skip این بار
        return 0;
    }
    #endif
    
    // اول پردازش رویدادهای با اولویت بالا
    while (g_priority_queue.count > 0) {
        // گرفتن اولین رویداد (با بالاترین اولویت)
        event = g_priority_queue.events[0];
        
        // جابجایی بقیه
        for (int i = 0; i < g_priority_queue.count - 1; i++) {
            g_priority_queue.events[i] = g_priority_queue.events[i + 1];
        }
        g_priority_queue.count--;
        
        #ifdef FREERTOS_AVAILABLE
        if (g_event_mutex) {
            xSemaphoreGive(g_event_mutex);
        }
        #endif
        
        // پردازش رویداد
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
        
        // آزاد کردن event data اگر از memory pool استفاده شده
        if (event.data && g_event_pool) {
            memory_pool_free(g_event_pool, event.data);
        }
        
        // گرفتن mutex برای iteration بعدی
        #ifdef FREERTOS_AVAILABLE
        if (g_event_mutex && xSemaphoreTake(g_event_mutex, 0) != pdTRUE) {
            break;
        }
        #endif
    }
    
    // سپس پردازش رویدادهای عادی
    while (queue_dequeue(&g_event_queue, &event)) {
        #ifdef FREERTOS_AVAILABLE
        if (g_event_mutex) {
            xSemaphoreGive(g_event_mutex);
        }
        #endif
        
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
        
        // آزاد کردن event data اگر از memory pool استفاده شده
        if (event.data && g_event_pool) {
            memory_pool_free(g_event_pool, event.data);
        }
        
        // گرفتن mutex برای iteration بعدی
        #ifdef FREERTOS_AVAILABLE
        if (g_event_mutex && xSemaphoreTake(g_event_mutex, 0) != pdTRUE) {
            break;
        }
        #endif
    }
    
    #ifdef FREERTOS_AVAILABLE
    if (g_event_mutex) {
        xSemaphoreGive(g_event_mutex);
    }
    #endif
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
                                uint32_t *dropped_events,
                                uint32_t *high_priority_events)
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
    if (high_priority_events) {
        *high_priority_events = g_high_priority_events;
    }
}

bool event_driver_post_event_with_data(event_type_t type,
                                      uint16_t source_id,
                                      uint32_t priority,
                                      const void *data,
                                      uint16_t data_size)
{
    if (!g_initialized || type >= EVENT_COUNT || !data || data_size == 0) {
        return false;
    }
    
    event_t event = {
        .type = type,
        .timestamp = hal_get_timestamp(),
        .source_id = source_id,
        .data_size = data_size,
        .data = NULL,
        .priority = priority
    };
    
    // تخصیص حافظه از memory pool یا malloc
    if (g_event_pool && data_size <= 64) {
        event.data = memory_pool_alloc(g_event_pool);
    } else {
        event.data = malloc(data_size);
    }
    
    if (!event.data) {
        return false;
    }
    
    // کپی داده
    memcpy(event.data, data, data_size);
    
    return event_driver_post_event(&event);
}

bool event_driver_post_event_from_isr(event_type_t type,
                                      uint16_t source_id,
                                      uint32_t priority)
{
    if (!g_initialized || type >= EVENT_COUNT) {
        return false;
    }
    
    event_t event = {
        .type = type,
        .timestamp = hal_get_timestamp(),
        .source_id = source_id,
        .data_size = 0,
        .data = NULL,
        .priority = priority
    };
    
    // ISR-safe: بدون mutex
    g_total_events++;
    
    // فقط به priority queue اضافه کن (سریع‌تر)
    if (priority >= 200 && g_priority_queue.count < g_priority_queue.size) {
        int insert_pos = g_priority_queue.count;
        for (int i = 0; i < g_priority_queue.count; i++) {
            if (g_priority_queue.events[i].priority < priority) {
                insert_pos = i;
                break;
            }
        }
        
        for (int i = g_priority_queue.count; i > insert_pos; i--) {
            g_priority_queue.events[i] = g_priority_queue.events[i - 1];
        }
        
        memcpy(&g_priority_queue.events[insert_pos], &event, sizeof(event_t));
        g_priority_queue.count++;
        g_high_priority_events++;
        return true;
    }
    
    // Fallback: به صف عادی (اگر جا دارد)
    if (g_event_queue.count < g_event_queue.size) {
        return queue_enqueue(&g_event_queue, &event);
    }
    
    g_dropped_events++;
    return false;
}

