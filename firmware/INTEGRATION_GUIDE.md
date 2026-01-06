# راهنمای یکپارچه‌سازی با nRF5 SDK

## مراحل یکپارچه‌سازی

### 1. نصب nRF5 SDK

1. دانلود nRF5 SDK از [Nordic Semiconductor](https://www.nordicsemi.com/Software-and-tools/Software/nRF5-SDK)
2. استخراج SDK در مسیر مناسب (مثلاً `C:\nRF5_SDK_17.1.0`)
3. نصب nRF Command Line Tools

### 2. تنظیم CMakeLists.txt

فایل `CMakeLists.txt` باید به‌روزرسانی شود تا شامل:

```cmake
# مسیر nRF5 SDK
set(NRF5_SDK_PATH "C:/nRF5_SDK_17.1.0")

# اضافه کردن include paths
include_directories(
    ${NRF5_SDK_PATH}/components
    ${NRF5_SDK_PATH}/components/device
    ${NRF5_SDK_PATH}/components/drivers_nrf
    ${NRF5_SDK_PATH}/components/libraries
    # ...
)

# اضافه کردن source files
file(GLOB SDK_SOURCES
    "${NRF5_SDK_PATH}/components/drivers_nrf/*.c"
    # ...
)

target_sources(${PROJECT_NAME}.elf PRIVATE ${SDK_SOURCES})
```

### 3. یکپارچه‌سازی HAL با nRF5 SDK

در فایل `firmware/src/system/hal.c`، بخش‌های TODO باید تکمیل شوند:

#### I2C
```c
#include "nrf_drv_i2c.h"

static nrf_drv_i2c_t i2c_instance = NRF_DRV_I2C_INSTANCE(0);

bool hal_i2c_init(uint8_t sda_pin, uint8_t scl_pin, uint32_t frequency)
{
    nrf_drv_i2c_config_t config = NRF_DRV_I2C_DEFAULT_CONFIG;
    config.sda = sda_pin;
    config.scl = scl_pin;
    config.frequency = (frequency == 400000) ? NRF_I2C_FREQ_400K : NRF_I2C_FREQ_100K;
    
    ret_code_t err_code = nrf_drv_i2c_init(&i2c_instance, &config, NULL);
    return (err_code == NRF_SUCCESS);
}
```

#### ADC
```c
#include "nrf_drv_adc.h"

static nrf_drv_adc_channel_t adc_channels[8];

bool hal_adc_init(uint8_t resolution)
{
    nrf_drv_adc_config_t config = NRF_DRV_ADC_DEFAULT_CONFIG;
    ret_code_t err_code = nrf_drv_adc_init(&config, NULL);
    return (err_code == NRF_SUCCESS);
}
```

#### Timer
```c
#include "nrf_drv_timer.h"

static nrf_drv_timer_t timer_instance = NRF_DRV_TIMER_INSTANCE(0);
static timer_callback_t timer_cb = NULL;

void timer_handler(nrf_timer_event_t event_type, void *p_context)
{
    if (event_type == NRF_TIMER_EVENT_COMPARE0 && timer_cb) {
        timer_cb();
    }
}

bool hal_timer_init(uint32_t frequency, timer_callback_t callback)
{
    nrf_drv_timer_config_t config = NRF_DRV_TIMER_DEFAULT_CONFIG;
    config.frequency = NRF_TIMER_FREQ_1MHz;
    
    ret_code_t err_code = nrf_drv_timer_init(&timer_instance, &config, timer_handler);
    if (err_code != NRF_SUCCESS) {
        return false;
    }
    
    timer_cb = callback;
    uint32_t time_ticks = nrf_drv_timer_ms_to_ticks(&timer_instance, 1000 / frequency);
    nrf_drv_timer_extended_compare(&timer_instance, NRF_TIMER_CC_CHANNEL0, time_ticks, 
                                   NRF_TIMER_SHORT_COMPARE0_CLEAR_MASK, true);
    return true;
}
```

### 4. یکپارچه‌سازی TensorFlow Lite Micro

#### نصب TensorFlow Lite Micro

1. کلون کردن TensorFlow:
```bash
git clone https://github.com/tensorflow/tensorflow.git
cd tensorflow
```

2. کامپایل برای ARM Cortex-M:
```bash
make -f tensorflow/lite/micro/tools/make/Makefile TARGET=cortex_m_generic TARGET_ARCH=cortex-m4
```

3. کپی فایل‌های مورد نیاز به پروژه:
- `tensorflow/lite/micro/` → `firmware/third_party/tflite/`
- فایل‌های header و source

#### تنظیم CMakeLists.txt

```cmake
# TensorFlow Lite Micro
include_directories(
    firmware/third_party/tflite
    firmware/third_party/tflite/kernels
    # ...
)

target_sources(${PROJECT_NAME}.elf PRIVATE
    firmware/third_party/tflite/micro_interpreter.cc
    firmware/third_party/tflite/all_ops_resolver.cc
    # ...
)
```

### 5. تست یکپارچه‌سازی

1. کامپایل پروژه:
```bash
cd firmware
mkdir build
cd build
cmake ..
make
```

2. فلش روی Development Kit:
```bash
nrfjprog --program firmware.hex --chiperase --verify --reset
```

## نکات مهم

### Memory Management
- TensorFlow Lite Micro نیاز به arena memory دارد
- اندازه arena در `tflite_micro.c` تنظیم شده: `TFLITE_MICRO_ARENA_SIZE`
- ممکن است نیاز به تنظیم بر اساس مدل باشد

### Optimization
- استفاده از CMSIS-NN برای بهینه‌سازی عملیات neural network
- استفاده از FPU برای محاسبات float (Cortex-M4 دارای FPU است)

### Debugging
- استفاده از Segger J-Link برای debugging
- استفاده از RTT (Real-Time Transfer) برای logging

## منابع

- [nRF5 SDK Documentation](https://infocenter.nordicsemi.com/)
- [TensorFlow Lite Micro](https://www.tensorflow.org/lite/microcontrollers)
- [nRF52840 Datasheet](https://www.nordicsemi.com/Products/nRF52840)

