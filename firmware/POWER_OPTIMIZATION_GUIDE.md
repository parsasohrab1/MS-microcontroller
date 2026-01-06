# راهنمای بهینه‌سازی مصرف انرژی

## مقدمه

این راهنما نحوه استفاده از قابلیت‌های بهینه‌سازی مصرف انرژی را توضیح می‌دهد.

**هدف:** افزایش عمر باتری از 5 به 7+ سال

---

## 1. Sleep Modes پیشرفته

### استفاده پایه

```c
#include "system/power_management.h"

// مقداردهی اولیه
power_management_init();

// ورود به sleep mode
power_enter_sleep(1000);  // Sleep برای 1 ثانیه

// بیدار شدن خودکار با timer یا interrupt
```

### انواع Sleep Modes

```c
// Active mode (تمام ماژول‌ها روشن)
power_set_mode(POWER_MODE_ACTIVE);

// Idle mode (CPU در wait)
power_set_mode(POWER_MODE_IDLE);

// Sleep mode (CPU خاموش، RAM روشن)
power_set_mode(POWER_MODE_SLEEP);

// Deep sleep (CPU و RAM خاموش)
power_set_mode(POWER_MODE_DEEP_SLEEP);

// Ultra low power (حداقل مصرف)
power_set_mode(POWER_MODE_ULTRA_LOW_POWER);
```

---

## 2. Dynamic Voltage and Frequency Scaling (DVFS)

### تنظیم فرکانس CPU

```c
// تنظیم فرکانس CPU
power_set_cpu_frequency(CPU_FREQ_16MHZ);  // کاهش مصرف

// فرکانس‌های موجود:
// - CPU_FREQ_64MHZ  (حداکثر عملکرد)
// - CPU_FREQ_32MHZ
// - CPU_FREQ_16MHZ  (پیش‌فرض)
// - CPU_FREQ_8MHZ
// - CPU_FREQ_4MHZ   (حداقل مصرف)
```

### تنظیم ولتاژ CPU

```c
// تنظیم ولتاژ CPU
power_set_cpu_voltage(CPU_VOLTAGE_2V5);  // کاهش مصرف

// ولتاژهای موجود:
// - CPU_VOLTAGE_3V3  (حداکثر عملکرد)
// - CPU_VOLTAGE_3V0  (پیش‌فرض)
// - CPU_VOLTAGE_2V5
// - CPU_VOLTAGE_2V0
// - CPU_VOLTAGE_1V8  (حداقل مصرف)
```

### بهینه‌سازی خودکار بر اساس Workload

```c
// بهینه‌سازی خودکار DVFS
power_optimize_for_workload(50);  // 50% workload

// سیستم به صورت خودکار:
// - فرکانس و ولتاژ را تنظیم می‌کند
// - حالت power را تغییر می‌دهد
```

---

## 3. Hardware Accelerators

### فعال کردن Accelerators

```c
#include "system/hardware_accelerators.h"

// مقداردهی اولیه
hw_accelerators_init();

// فعال کردن FFT accelerator
hw_accelerator_enable(HW_ACCEL_FFT);

// استفاده از FFT accelerator
float input[256];
float output[256];
hw_accel_fft_execute(input, output, 256);
```

### انواع Accelerators

```c
// FFT Accelerator
hw_accelerator_enable(HW_ACCEL_FFT);

// Cryptographic Accelerator
hw_accelerator_enable(HW_ACCEL_CRYPTO);

// ML Accelerator
hw_accelerator_enable(HW_ACCEL_ML);

// DMA Controller
hw_accelerator_enable(HW_ACCEL_DMA);
```

---

## 4. بهینه‌سازی الگوریتم‌های پردازش

### استفاده از فیلترهای بهینه

```c
#include "signal_processing/optimized_filters.h"

// مقداردهی اولیه
optimized_filters_init();

// فیلتر lowpass بهینه
float input[256];
float output[256];
optimized_lowpass_filter(
    input, output, 256,
    100.0f,  // cutoff frequency
    1000     // sampling rate
);
```

### Adaptive Sampling Rate

```c
// بهینه‌سازی sampling rate بر اساس variance سیگنال
uint32_t current_rate = 1000;
uint32_t optimized_rate;
adaptive_sampling_rate_optimization(signal, current_rate, &optimized_rate);

// استفاده از rate بهینه شده
```

---

## 5. مدیریت Peripherals

### غیرفعال کردن Peripherals غیرضروری

```c
// غیرفعال کردن peripheral
power_set_peripheral_enabled(2, false);  // Peripheral ID 2

// فعال کردن مجدد
power_set_peripheral_enabled(2, true);
```

---

## 6. آمار و مانیتورینگ

### دریافت آمار مصرف انرژی

```c
power_stats_t stats;
power_get_stats(&stats);

printf("Current consumption: %u uA\n", stats.current_power_consumption_uA);
printf("Average consumption: %u uA\n", stats.average_power_consumption_uA);
printf("Battery level: %u%%\n", stats.battery_level_percent);
printf("Days remaining: %u\n", stats.estimated_days_remaining);
```

### تخمین عمر باتری

```c
uint32_t days = power_estimate_battery_life_days();
printf("Estimated battery life: %u days\n", days);
```

---

## بهترین روش‌ها

### 1. استفاده از Sleep Modes
- در صورت عدم نیاز به پردازش، از Deep Sleep استفاده کنید
- از Timer برای بیدار شدن دوره‌ای استفاده کنید

### 2. DVFS
- برای workload پایین، فرکانس و ولتاژ را کاهش دهید
- از `power_optimize_for_workload()` برای بهینه‌سازی خودکار استفاده کنید

### 3. Hardware Accelerators
- برای FFT، Crypto، ML از hardware accelerators استفاده کنید
- این کار مصرف انرژی را تا 90% کاهش می‌دهد

### 4. Adaptive Algorithms
- از adaptive sampling rate استفاده کنید
- در صورت عدم تغییر سیگنال، sampling rate را کاهش دهید

### 5. Peripheral Management
- فقط peripherals مورد نیاز را فعال کنید
- بعد از استفاده، آنها را غیرفعال کنید

---

## مثال کامل

```c
#include "system/power_management.h"
#include "system/hardware_accelerators.h"
#include "signal_processing/optimized_filters.h"

void main_loop(void)
{
    // مقداردهی اولیه
    power_management_init();
    hw_accelerators_init();
    optimized_filters_init();
    
    while (1) {
        // فعال کردن accelerators
        hw_accelerator_enable(HW_ACCEL_FFT);
        
        // پردازش داده
        float input[256];
        float output[256];
        optimized_lowpass_filter(input, output, 256, 100.0f, 1000);
        
        // غیرفعال کردن accelerators
        hw_accelerator_disable(HW_ACCEL_FFT);
        
        // بهینه‌سازی برای workload پایین
        power_optimize_for_workload(10);
        
        // ورود به sleep
        power_enter_sleep(100);  // 100ms sleep
    }
}
```

---

## نتایج مورد انتظار

با استفاده از این بهینه‌سازی‌ها:

- **مصرف در Active Mode:** 5 mA → 2 mA (60% کاهش)
- **مصرف در Sleep Mode:** 100 uA → 10 uA (90% کاهش)
- **عمر باتری:** 5 سال → 7+ سال (40% افزایش)

---

**آخرین به‌روزرسانی:** 2024

