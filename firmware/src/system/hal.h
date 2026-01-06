/**
 * @file hal.h
 * @brief Hardware Abstraction Layer - لایه انتزاع سخت‌افزار
 * @version 0.1.0
 * 
 * این فایل رابط‌های مشترک برای دسترسی به سخت‌افزار را تعریف می‌کند
 * و یکپارچه‌سازی با nRF5 SDK را فراهم می‌کند
 */

#ifndef HAL_H
#define HAL_H

#include <stdint.h>
#include <stdbool.h>

// ============================================================================
// nRF5 SDK Includes
// ============================================================================
// TODO: اضافه کردن include های nRF5 SDK
// #include "nrf_drv_i2c.h"
// #include "nrf_drv_spi.h"
// #include "nrf_drv_adc.h"
// #include "nrf_drv_timer.h"
// #include "nrf_drv_rtc.h"
// #include "nrf_ble_gatt.h"

// ============================================================================
// I2C Interface
// ============================================================================

typedef struct {
    uint8_t address;        // آدرس I2C
    uint8_t reg;           // رجیستر
    uint8_t *data;         // داده
    uint16_t length;       // طول داده
} i2c_transfer_t;

/**
 * @brief مقداردهی اولیه I2C
 * @param sda_pin پین SDA
 * @param scl_pin پین SCL
 * @param frequency فرکانس (100000 یا 400000)
 * @return true در صورت موفقیت
 */
bool hal_i2c_init(uint8_t sda_pin, uint8_t scl_pin, uint32_t frequency);

/**
 * @brief نوشتن داده روی I2C
 * @param address آدرس دستگاه
 * @param data داده
 * @param length طول
 * @return true در صورت موفقیت
 */
bool hal_i2c_write(uint8_t address, const uint8_t *data, uint16_t length);

/**
 * @brief خواندن داده از I2C
 * @param address آدرس دستگاه
 * @param data بافر خروجی
 * @param length طول
 * @return true در صورت موفقیت
 */
bool hal_i2c_read(uint8_t address, uint8_t *data, uint16_t length);

/**
 * @brief نوشتن رجیستر I2C
 * @param address آدرس دستگاه
 * @param reg آدرس رجیستر
 * @param value مقدار
 * @return true در صورت موفقیت
 */
bool hal_i2c_write_register(uint8_t address, uint8_t reg, uint8_t value);

/**
 * @brief خواندن رجیستر I2C
 * @param address آدرس دستگاه
 * @param reg آدرس رجیستر
 * @param value اشاره‌گر به مقدار خروجی
 * @return true در صورت موفقیت
 */
bool hal_i2c_read_register(uint8_t address, uint8_t reg, uint8_t *value);

// ============================================================================
// SPI Interface
// ============================================================================

/**
 * @brief مقداردهی اولیه SPI
 * @param mosi_pin پین MOSI
 * @param miso_pin پین MISO
 * @param sck_pin پین SCK
 * @param cs_pin پین CS
 * @param frequency فرکانس (Hz)
 * @return true در صورت موفقیت
 */
bool hal_spi_init(uint8_t mosi_pin, uint8_t miso_pin, uint8_t sck_pin, 
                  uint8_t cs_pin, uint32_t frequency);

/**
 * @brief انتقال SPI
 * @param tx_data داده ارسالی
 * @param rx_data داده دریافتی
 * @param length طول
 * @return true در صورت موفقیت
 */
bool hal_spi_transfer(const uint8_t *tx_data, uint8_t *rx_data, uint16_t length);

// ============================================================================
// ADC Interface
// ============================================================================

/**
 * @brief مقداردهی اولیه ADC
 * @param resolution وضوح (8, 10, 12, 14 bit)
 * @return true در صورت موفقیت
 */
bool hal_adc_init(uint8_t resolution);

/**
 * @brief خواندن از کانال ADC
 * @param channel کانال (0-7)
 * @param value اشاره‌گر به مقدار خروجی
 * @return true در صورت موفقیت
 */
bool hal_adc_read(uint8_t channel, uint16_t *value);

/**
 * @brief خواندن از چند کانال ADC
 * @param channels آرایه کانال‌ها
 * @param values آرایه مقادیر خروجی
 * @param count تعداد کانال‌ها
 * @return تعداد کانال‌های خوانده شده
 */
uint8_t hal_adc_read_multiple(const uint8_t *channels, uint16_t *values, uint8_t count);

// ============================================================================
// Timer Interface
// ============================================================================

typedef void (*timer_callback_t)(void);

/**
 * @brief مقداردهی اولیه تایمر
 * @param frequency فرکانس (Hz)
 * @param callback تابع callback
 * @return true در صورت موفقیت
 */
bool hal_timer_init(uint32_t frequency, timer_callback_t callback);

/**
 * @brief شروع تایمر
 */
void hal_timer_start(void);

/**
 * @brief توقف تایمر
 */
void hal_timer_stop(void);

// ============================================================================
// RTC Interface
// ============================================================================

/**
 * @brief مقداردهی اولیه RTC
 * @return true در صورت موفقیت
 */
bool hal_rtc_init(void);

/**
 * @brief دریافت زمان فعلی (milliseconds از boot)
 * @return زمان به میلی‌ثانیه
 */
uint32_t hal_rtc_get_time_ms(void);

/**
 * @brief دریافت زمان فعلی (seconds از boot)
 * @return زمان به ثانیه
 */
uint32_t hal_rtc_get_time_s(void);

// ============================================================================
// GPIO Interface
// ============================================================================

typedef enum {
    GPIO_DIR_INPUT = 0,
    GPIO_DIR_OUTPUT
} gpio_direction_t;

typedef enum {
    GPIO_PULL_NONE = 0,
    GPIO_PULL_UP,
    GPIO_PULL_DOWN
} gpio_pull_t;

/**
 * @brief پیکربندی پین GPIO
 * @param pin شماره پین
 * @param direction جهت (ورودی/خروجی)
 * @param pull حالت Pull (None/Up/Down)
 * @return true در صورت موفقیت
 */
bool hal_gpio_config(uint8_t pin, gpio_direction_t direction, gpio_pull_t pull);

/**
 * @brief تنظیم سطح پین
 * @param pin شماره پین
 * @param level سطح (0 یا 1)
 */
void hal_gpio_write(uint8_t pin, uint8_t level);

/**
 * @brief خواندن سطح پین
 * @param pin شماره پین
 * @return سطح پین (0 یا 1)
 */
uint8_t hal_gpio_read(uint8_t pin);

// ============================================================================
// Delay Functions
// ============================================================================

/**
 * @brief تاخیر به میلی‌ثانیه
 * @param ms میلی‌ثانیه
 */
void hal_delay_ms(uint32_t ms);

/**
 * @brief تاخیر به میکروثانیه
 * @param us میکروثانیه
 */
void hal_delay_us(uint32_t us);

// ============================================================================
// Power Management Interface
// ============================================================================

/**
 * @brief تنظیم حالت power
 */
void hal_power_set_mode_active(void);
void hal_power_set_mode_idle(void);
void hal_power_set_mode_sleep(void);
void hal_power_set_mode_deep_sleep(void);
void hal_power_set_mode_ultra_low_power(void);

/**
 * @brief تنظیم فرکانس CPU
 * @param freq_hz فرکانس (Hz)
 */
void hal_clock_set_cpu_frequency(uint32_t freq_hz);

/**
 * @brief تنظیم ولتاژ CPU
 * @param voltage_mv ولتاژ (mV)
 */
void hal_power_set_voltage(uint32_t voltage_mv);

/**
 * @brief فعال/غیرفعال کردن peripheral
 * @param peripheral_id شناسه peripheral
 * @param enabled true برای فعال
 */
void hal_peripheral_set_enabled(uint8_t peripheral_id, bool enabled);

/**
 * @brief تنظیم wake timer
 * @param duration_ms مدت زمان (ms)
 */
void hal_rtc_set_wake_timer(uint32_t duration_ms);

/**
 * @brief انتظار برای interrupt
 */
void hal_cpu_wait_for_interrupt(void);

/**
 * @brief دریافت سطح باتری
 * @return سطح باتری (0-100)
 */
uint8_t hal_battery_get_level(void);

// ============================================================================
// Hardware Accelerators Interface
// ============================================================================

/**
 * @brief مقداردهی اولیه hardware accelerators
 */
void hal_hw_accelerators_init(void);

/**
 * @brief فعال کردن accelerator
 * @param accel نوع accelerator
 */
void hal_hw_accelerator_enable(uint8_t accel);

/**
 * @brief غیرفعال کردن accelerator
 * @param accel نوع accelerator
 */
void hal_hw_accelerator_disable(uint8_t accel);

/**
 * @brief اجرای FFT با accelerator
 */
bool hal_hw_accel_fft_execute(const float *input, float *output, uint32_t size);

/**
 * @brief اجرای encryption با accelerator
 */
bool hal_hw_accel_crypto_encrypt(
    const uint8_t *data,
    const uint8_t *key,
    uint8_t *output,
    uint32_t size
);

/**
 * @brief اجرای ML inference با accelerator
 */
bool hal_hw_accel_ml_inference(
    const uint8_t *model_data,
    const float *input,
    float *output
);

/**
 * @brief دریافت تعداد CPU cycles
 * @return تعداد cycles
 */
uint32_t hal_get_cpu_cycles(void);

/**
 * @brief خاموش کردن accelerators
 */
void hal_hw_accelerators_deinit(void);

// ============================================================================
// DMA Interface
// ============================================================================

/**
 * @brief مقداردهی اولیه DMA
 */
void hal_dma_init(void);

/**
 * @brief پیکربندی DMA channel
 */
void hal_dma_configure(
    uint8_t channel,
    uint32_t src_addr,
    uint32_t dst_addr,
    uint32_t size,
    uint32_t count,
    bool inc_src,
    bool inc_dst,
    uint8_t data_width,
    bool circular,
    uint8_t priority,
    void (*callback)(void)
);

/**
 * @brief شروع انتقال DMA
 */
void hal_dma_start(uint8_t channel);

/**
 * @brief توقف انتقال DMA
 */
void hal_dma_stop(uint8_t channel);

/**
 * @brief بررسی اتمام انتقال
 */
bool hal_dma_is_complete(uint8_t channel);

/**
 * @brief دریافت تعداد bytes منتقل شده
 */
uint32_t hal_dma_get_transferred_bytes(uint8_t channel);

/**
 * @brief خاموش کردن DMA
 */
void hal_dma_deinit(void);

/**
 * @brief دریافت آدرس رجیستر داده ADC
 */
uint32_t hal_adc_get_data_register_address(void);

/**
 * @brief دریافت آدرس رجیستر داده DAC
 */
uint32_t hal_dac_get_data_register_address(void);

// ============================================================================
// Flash Interface
// ============================================================================

/**
 * @brief مقداردهی اولیه Flash
 */
void hal_flash_init(void);

/**
 * @brief نوشتن در Flash
 */
void hal_flash_write(uint32_t address, const uint8_t *data, uint32_t size);

/**
 * @brief خواندن از Flash
 */
void hal_flash_read(uint32_t address, uint8_t *data, uint32_t size);

/**
 * @brief پاک کردن Sector
 */
void hal_flash_erase_sector(uint32_t address);

/**
 * @brief دریافت آدرس نوشتن Flash
 */
uint32_t hal_flash_get_write_address(uint32_t address);

/**
 * @brief خاموش کردن Flash
 */
void hal_flash_deinit(void);

/**
 * @brief پاک کردن Flash (full erase)
 */
bool hal_flash_erase(uint32_t address, uint32_t size);

// ============================================================================
// Security Interface (Crypto, HSM, Tamper)
// ============================================================================

/**
 * @brief محاسبه SHA-256 hash
 */
bool hal_crypto_hash_sha256(const uint8_t *data, uint32_t size, uint8_t *hash);

/**
 * @brief HSM: بررسی وجود HSM
 */
bool hal_hsm_is_available(void);

/**
 * @brief HSM: مقداردهی اولیه
 */
bool hal_hsm_init(void);

/**
 * @brief HSM: تولید کلید
 */
bool hal_hsm_generate_key(uint8_t key_type, uint8_t *key_data, uint32_t key_size);

/**
 * @brief HSM: ذخیره کلید
 */
bool hal_hsm_store_key(uint8_t key_id, const uint8_t *key_data, uint32_t key_size, bool persistent);

/**
 * @brief HSM: حذف کلید
 */
bool hal_hsm_delete_key(uint8_t key_id);

/**
 * @brief HSM: رمزگذاری
 */
bool hal_hsm_encrypt(
    uint8_t key_id,
    const uint8_t *plaintext,
    uint32_t plaintext_size,
    uint8_t *ciphertext,
    uint32_t *ciphertext_size
);

/**
 * @brief HSM: رمزگشایی
 */
bool hal_hsm_decrypt(
    uint8_t key_id,
    const uint8_t *ciphertext,
    uint32_t ciphertext_size,
    uint8_t *plaintext,
    uint32_t *plaintext_size
);

/**
 * @brief HSM: امضا
 */
bool hal_hsm_sign(
    uint8_t key_id,
    const uint8_t *data,
    uint32_t data_size,
    uint8_t *signature,
    uint32_t *signature_size
);

/**
 * @brief HSM: بررسی امضا
 */
bool hal_hsm_verify(
    uint8_t key_id,
    const uint8_t *data,
    uint32_t data_size,
    const uint8_t *signature,
    uint32_t signature_size
);

/**
 * @brief HSM: محاسبه hash
 */
bool hal_hsm_hash(
    uint8_t algorithm,
    const uint8_t *data,
    uint32_t data_size,
    uint8_t *hash,
    uint32_t *hash_size
);

/**
 * @brief HSM: تولید random
 */
bool hal_hsm_random(uint8_t *random_data, uint32_t size);

/**
 * @brief Tamper: مقداردهی اولیه
 */
void hal_tamper_init(void);

/**
 * @brief Tamper: دریافت وضعیت case
 */
bool hal_tamper_get_case_status(void);

/**
 * @brief Tamper: دریافت دما
 */
int16_t hal_tamper_get_temperature(void);

/**
 * @brief Tamper: دریافت ولتاژ
 */
uint16_t hal_tamper_get_voltage(void);

/**
 * @brief Tamper: دریافت وضعیت debug
 */
bool hal_tamper_get_debug_status(void);

/**
 * @brief Tamper: دریافت سطح impact
 */
uint16_t hal_tamper_get_impact_level(void);

/**
 * @brief دریافت timestamp
 */
uint32_t hal_get_timestamp(void);

#endif // HAL_H

