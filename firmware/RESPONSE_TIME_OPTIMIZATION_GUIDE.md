# راهنمای بهینه‌سازی زمان پاسخ

## مقدمه

این راهنما نحوه استفاده از قابلیت‌های بهینه‌سازی زمان پاسخ را توضیح می‌دهد.

**هدف:** کاهش زمان پاسخ از 100ms به <50ms

---

## 1. استفاده از DMA برای انتقال داده

### استفاده پایه

```c
#include "system/dma_manager.h"

// مقداردهی اولیه
dma_manager_init();

// انتقال سریع Memory to Memory
float src[256];
float dst[256];
dma_memcpy(dst, src, sizeof(src));
```

### انتقال از ADC

```c
// انتقال سریع از ADC به Memory
uint16_t adc_buffer[128];
dma_adc_to_memory(adc_buffer, 128);
```

### انتقال به DAC

```c
// انتقال سریع از Memory به DAC
uint16_t dac_data[128];
dma_memory_to_dac(dac_data, 128);
```

### انتقال سفارشی

```c
dma_config_t config = {
    .type = DMA_TRANSFER_MEMORY_TO_MEMORY,
    .priority = DMA_PRIORITY_HIGH,
    .source_address = (uint32_t)src,
    .destination_address = (uint32_t)dst,
    .data_size = 1024,
    .transfer_count = 1,
    .increment_source = true,
    .increment_destination = true,
    .data_width = 32,  // 32-bit برای سرعت بیشتر
    .circular_mode = false,
    .callback = NULL
};

int32_t channel = dma_start_transfer(&config);
dma_wait_for_completion(channel, 100);  // 100ms timeout
```

---

## 2. بهینه‌سازی الگوریتم‌های ML

### استفاده از Optimized Prediction

```c
#include "ml/optimized_prediction.h"

// مقداردهی اولیه
optimized_prediction_init();

// اجرای پیش‌بینی بهینه
model_input_t input;
prediction_t output;
optimized_prediction_run(&input, &output);

// بررسی زمان inference
uint32_t time = optimized_prediction_get_last_inference_time();
if (time < 50) {
    // موفق - کمتر از 50ms
}
```

### فعال کردن Parallel Processing

```c
// فعال کردن parallel processing برای ML
optimized_prediction_enable_parallel_processing(true);
```

---

## 3. استفاده از Hardware Floating Point

### بهینه‌سازی محاسبات

```c
// استفاده از FPU hardware (خودکار)
float a = 1.5f;
float b = 2.5f;
float result = a * b;  // استفاده از FPU

// برای بهینه‌سازی بیشتر، از inline functions استفاده کنید
static inline float fast_multiply(float a, float b) {
    return a * b;  // کامپایلر از FPU استفاده می‌کند
}
```

### تنظیمات کامپایلر

```cmake
# در CMakeLists.txt
target_compile_options(${PROJECT_NAME}.elf PRIVATE
    -mfloat-abi=hard  # استفاده از FPU hardware
    -mfpu=fpv4-sp-d16
)
```

---

## 4. Parallel Processing

### استفاده از Parallel Processor

```c
#include "system/parallel_processor.h"

// مقداردهی اولیه
parallel_processor_init();

// ایجاد task
parallel_task_t task = {
    .type = TASK_TYPE_ML_INFERENCE,
    .priority = TASK_PRIORITY_HIGH,
    .input_data = input_buffer,
    .output_data = output_buffer,
    .data_size = sizeof(input_buffer),
    .callback = NULL
};

// اضافه کردن task
int32_t task_id = parallel_processor_add_task(&task);

// اجرای tasks
parallel_processor_execute(4);  // اجرای 4 task

// انتظار برای اتمام
parallel_processor_wait_for_task(task_id, 100);
```

### اجرای چند Task به صورت موازی

```c
// ایجاد چند task
parallel_task_t tasks[4];
for (int i = 0; i < 4; i++) {
    tasks[i].type = TASK_TYPE_FEATURE_EXTRACTION;
    tasks[i].priority = TASK_PRIORITY_HIGH;
    // ... تنظیمات
    parallel_processor_add_task(&tasks[i]);
}

// اجرای همه tasks
parallel_processor_execute(4);
```

---

## 5. ترکیب بهینه‌سازی‌ها

### مثال کامل

```c
#include "system/dma_manager.h"
#include "system/hardware_accelerators.h"
#include "ml/optimized_prediction.h"
#include "system/parallel_processor.h"

void optimized_processing_pipeline(void)
{
    // 1. مقداردهی اولیه
    dma_manager_init();
    hw_accelerators_init();
    optimized_prediction_init();
    parallel_processor_init();
    
    // 2. فعال کردن accelerators
    hw_accelerator_enable(HW_ACCEL_FFT);
    hw_accelerator_enable(HW_ACCEL_ML);
    
    // 3. انتقال داده با DMA
    float input[256];
    float output[256];
    dma_memcpy(output, input, sizeof(input));
    
    // 4. پردازش موازی
    parallel_task_t task1 = {
        .type = TASK_TYPE_FEATURE_EXTRACTION,
        .input_data = input,
        .output_data = output,
        .data_size = sizeof(input)
    };
    parallel_processor_add_task(&task1);
    parallel_processor_execute(1);
    
    // 5. ML inference بهینه
    model_input_t ml_input;
    prediction_t ml_output;
    optimized_prediction_run(&ml_input, &ml_output);
    
    // بررسی زمان کل
    // باید < 50ms باشد
}
```

---

## بهترین روش‌ها

### 1. استفاده از DMA
- برای انتقال داده‌های بزرگ (>100 bytes) از DMA استفاده کنید
- از 32-bit transfers برای سرعت بیشتر استفاده کنید
- از DMA_PRIORITY_HIGH برای tasks بحرانی استفاده کنید

### 2. بهینه‌سازی ML
- از hardware accelerators استفاده کنید
- از parallel processing برای batch inference استفاده کنید
- از DMA برای انتقال داده‌های ورودی/خروجی استفاده کنید

### 3. Hardware Floating Point
- مطمئن شوید که FPU فعال است
- از inline functions برای محاسبات مکرر استفاده کنید
- از SIMD instructions در صورت امکان استفاده کنید

### 4. Parallel Processing
- Tasks مستقل را به صورت موازی اجرا کنید
- از hardware accelerators برای parallel execution استفاده کنید
- از priority برای scheduling استفاده کنید

---

## نتایج مورد انتظار

با استفاده از این بهینه‌سازی‌ها:

- **زمان انتقال داده:** 10ms → 1ms (90% کاهش)
- **زمان ML Inference:** 80ms → 30ms (62% کاهش)
- **زمان کل پاسخ:** 100ms → <50ms (50%+ کاهش)

---

## اندازه‌گیری عملکرد

```c
// اندازه‌گیری زمان
uint32_t start = hal_rtc_get_time_ms();

// انجام کار
optimized_prediction_run(&input, &output);

uint32_t end = hal_rtc_get_time_ms();
uint32_t elapsed = end - start;

if (elapsed < 50) {
    // موفق - کمتر از 50ms
}
```

---

**آخرین به‌روزرسانی:** 2024

