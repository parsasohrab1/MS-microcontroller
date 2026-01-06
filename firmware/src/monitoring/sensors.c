/**
 * @file sensors.c
 * @brief پیاده‌سازی ماژول سنسورها
 * @version 0.2.0
 */

#include "sensors.h"
#include "../system/hal.h"
#include <string.h>

// ============================================================================
// آدرس‌های I2C سنسورها (مثال)
// ============================================================================

#define SENSOR_TEMP_ADDR       0x48
#define SENSOR_PRESSURE_ADDR   0x76
#define SENSOR_IL6_ADDR        0x50
#define SENSOR_TNF_ALPHA_ADDR  0x51
#define SENSOR_CRP_ADDR        0x52

// ============================================================================
// رجیسترهای سنسور (مثال - باید بر اساس دیتاشیت واقعی تنظیم شود)
// ============================================================================

#define REG_TEMP_VALUE         0x00
#define REG_PRESSURE_VALUE     0x00
#define REG_BIOMARKER_VALUE    0x00
#define REG_STATUS             0x01
#define REG_CONFIG             0x02

// ============================================================================
// متغیرهای داخلی
// ============================================================================

static bool sensors_initialized = false;

// ============================================================================
// توابع داخلی
// ============================================================================

/**
 * @brief خواندن مقدار از سنسور I2C
 */
static bool sensor_i2c_read_value(uint8_t address, uint8_t reg, float *value, float scale)
{
    uint8_t data[2];
    
    // خواندن 2 بایت از رجیستر
    if (!hal_i2c_read_register(address, reg, &data[0])) {
        return false;
    }
    if (!hal_i2c_read_register(address, reg + 1, &data[1])) {
        return false;
    }
    
    // تبدیل به مقدار (16-bit signed)
    int16_t raw = (int16_t)((data[0] << 8) | data[1]);
    *value = (float)raw * scale;
    
    return true;
}

/**
 * @brief مقداردهی اولیه یک سنسور خاص
 */
static bool sensor_init_internal(sensor_type_t type)
{
    uint8_t address;
    uint8_t config_reg;
    uint8_t config_value;
    
    // تعیین آدرس و تنظیمات بر اساس نوع سنسور
    switch (type) {
        case SENSOR_TYPE_TEMPERATURE:
            address = SENSOR_TEMP_ADDR;
            config_value = 0x01; // Continuous mode
            break;
        case SENSOR_TYPE_PRESSURE:
            address = SENSOR_PRESSURE_ADDR;
            config_value = 0x01;
            break;
        case SENSOR_TYPE_IL6:
        case SENSOR_TYPE_TNF_ALPHA:
        case SENSOR_TYPE_CRP:
            // سنسورهای بیومارکر
            address = (type == SENSOR_TYPE_IL6) ? SENSOR_IL6_ADDR :
                     (type == SENSOR_TYPE_TNF_ALPHA) ? SENSOR_TNF_ALPHA_ADDR :
                     SENSOR_CRP_ADDR;
            config_value = 0x02; // High sensitivity mode
            break;
        default:
            return false;
    }
    
    // بررسی وجود سنسور (خواندن رجیستر شناسه)
    uint8_t id_reg = 0x0F; // معمولاً رجیستر شناسه
    uint8_t id_value;
    if (!hal_i2c_read_register(address, id_reg, &id_value)) {
        return false; // سنسور پاسخ نمی‌دهد
    }
    
    // تنظیم پیکربندی
    if (!hal_i2c_write_register(address, REG_CONFIG, config_value)) {
        return false;
    }
    
    // تاخیر برای تثبیت
    hal_delay_ms(10);
    
    return true;
}

/**
 * @brief خواندن مقدار خام از سنسور
 */
static bool sensor_read_raw(sensor_type_t type, float *value)
{
    uint8_t address;
    uint8_t reg;
    float scale;
    
    // تعیین پارامترها بر اساس نوع سنسور
    switch (type) {
        case SENSOR_TYPE_TEMPERATURE:
            address = SENSOR_TEMP_ADDR;
            reg = REG_TEMP_VALUE;
            scale = 0.0625f; // مثال: 0.0625 درجه سانتی‌گراد per LSB
            break;
        case SENSOR_TYPE_PRESSURE:
            address = SENSOR_PRESSURE_ADDR;
            reg = REG_PRESSURE_VALUE;
            scale = 0.01f; // مثال: 0.01 mmHg per LSB
            break;
        case SENSOR_TYPE_IL6:
            address = SENSOR_IL6_ADDR;
            reg = REG_BIOMARKER_VALUE;
            scale = 0.1f; // pg/mL per LSB
            break;
        case SENSOR_TYPE_TNF_ALPHA:
            address = SENSOR_TNF_ALPHA_ADDR;
            reg = REG_BIOMARKER_VALUE;
            scale = 0.1f; // pg/mL per LSB
            break;
        case SENSOR_TYPE_CRP:
            address = SENSOR_CRP_ADDR;
            reg = REG_BIOMARKER_VALUE;
            scale = 0.01f; // mg/L per LSB
            break;
        default:
            return false;
    }
    
    return sensor_i2c_read_value(address, reg, value, scale);
}

// ============================================================================
// توابع API عمومی
// ============================================================================

bool sensors_init(void)
{
    if (sensors_initialized) {
        return true;
    }
    
    // مقداردهی اولیه I2C
    // پین‌های I2C باید بر اساس سخت‌افزار تنظیم شوند
    if (!hal_i2c_init(26, 27, 100000)) { // SDA=26, SCL=27, 100kHz
        return false;
    }
    
    // مقداردهی اولیه تمام سنسورها
    for (sensor_type_t i = 0; i < SENSOR_TYPE_COUNT; i++) {
        if (!sensor_init_internal(i)) {
            // در صورت خطا، مقداردهی اولیه را برگردان
            sensors_deinit();
            return false;
        }
    }
    
    sensors_initialized = true;
    return true;
}

bool sensor_read(sensor_type_t type, sensor_data_t *data)
{
    if (!sensors_initialized || !data) {
        return false;
    }
    
    if (type >= SENSOR_TYPE_COUNT) {
        return false;
    }
    
    // خواندن مقدار خام
    float raw_value;
    if (!sensor_read_raw(type, &raw_value)) {
        data->valid = false;
        return false;
    }
    
    // پر کردن ساختار داده
    data->type = type;
    data->value = raw_value;
    data->timestamp = hal_rtc_get_time_ms();
    data->valid = true;
    
    return true;
}

uint8_t sensors_read_all_biomarkers(sensor_data_t *data)
{
    if (!sensors_initialized || !data) {
        return 0;
    }
    
    uint8_t success_count = 0;
    
    // خواندن سنسورهای بیومارکر (از IL6 شروع می‌شود)
    for (sensor_type_t i = SENSOR_TYPE_IL6; 
         i < SENSOR_TYPE_COUNT && success_count < BIOMARKER_COUNT; 
         i++) {
        if (sensor_read(i, &data[success_count])) {
            success_count++;
        }
    }
    
    return success_count;
}

bool sensor_health_check(sensor_type_t type)
{
    if (!sensors_initialized || type >= SENSOR_TYPE_COUNT) {
        return false;
    }
    
    uint8_t address;
    switch (type) {
        case SENSOR_TYPE_TEMPERATURE:
            address = SENSOR_TEMP_ADDR;
            break;
        case SENSOR_TYPE_PRESSURE:
            address = SENSOR_PRESSURE_ADDR;
            break;
        case SENSOR_TYPE_IL6:
            address = SENSOR_IL6_ADDR;
            break;
        case SENSOR_TYPE_TNF_ALPHA:
            address = SENSOR_TNF_ALPHA_ADDR;
            break;
        case SENSOR_TYPE_CRP:
            address = SENSOR_CRP_ADDR;
            break;
        default:
            return false;
    }
    
    // خواندن رجیستر وضعیت
    uint8_t status;
    if (!hal_i2c_read_register(address, REG_STATUS, &status)) {
        return false; // سنسور پاسخ نمی‌دهد
    }
    
    // بررسی بیت‌های وضعیت (مثال: بیت 0 = Ready, بیت 1 = Error)
    if ((status & 0x01) == 0) {
        return false; // سنسور آماده نیست
    }
    if ((status & 0x02) != 0) {
        return false; // خطا در سنسور
    }
    
    return true;
}

void sensors_deinit(void)
{
    if (!sensors_initialized) {
        return;
    }
    
    // TODO: خاموش کردن سنسورها
    // - ارسال دستور sleep به هر سنسور
    // - غیرفعال کردن منبع تغذیه
    
    sensors_initialized = false;
}
