/**
 * @file sensors.h
 * @brief هدر ماژول سنسورها - مانیتورینگ بیومارکرها و پارامترهای فیزیولوژیک
 * @version 0.1.0
 */

#ifndef SENSORS_H
#define SENSORS_H

#include <stdint.h>
#include <stdbool.h>
#include "../config.h"

// ============================================================================
// انواع سنسورها
// ============================================================================

typedef enum {
    SENSOR_TYPE_TEMPERATURE = 0,
    SENSOR_TYPE_PRESSURE,
    SENSOR_TYPE_IL6,           // Interleukin-6
    SENSOR_TYPE_TNF_ALPHA,      // Tumor Necrosis Factor-alpha
    SENSOR_TYPE_CRP,            // C-Reactive Protein
    SENSOR_TYPE_COUNT
} sensor_type_t;

// ============================================================================
// ساختار داده سنسور
// ============================================================================

typedef struct {
    sensor_type_t type;
    float value;
    uint32_t timestamp;
    bool valid;
} sensor_data_t;

// ============================================================================
// توابع API
// ============================================================================

/**
 * @brief مقداردهی اولیه ماژول سنسورها
 * @return true در صورت موفقیت، false در غیر این صورت
 */
bool sensors_init(void);

/**
 * @brief خواندن مقدار از یک سنسور
 * @param type نوع سنسور
 * @param data اشاره‌گر به ساختار داده خروجی
 * @return true در صورت موفقیت، false در غیر این صورت
 */
bool sensor_read(sensor_type_t type, sensor_data_t *data);

/**
 * @brief خواندن تمام سنسورهای بیومارکر
 * @param data آرایه خروجی داده‌ها (باید حداقل BIOMARKER_COUNT عنصر داشته باشد)
 * @return تعداد سنسورهای خوانده شده با موفقیت
 */
uint8_t sensors_read_all_biomarkers(sensor_data_t *data);

/**
 * @brief بررسی سلامت سنسور
 * @param type نوع سنسور
 * @return true اگر سنسور سالم است، false در غیر این صورت
 */
bool sensor_health_check(sensor_type_t type);

/**
 * @brief خاموش کردن ماژول سنسورها (صرفه‌جویی انرژی)
 */
void sensors_deinit(void);

#endif // SENSORS_H

