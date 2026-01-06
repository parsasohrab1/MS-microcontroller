# راهنمای بهینه‌سازی حافظه

## مقدمه

این راهنما نحوه استفاده از قابلیت‌های بهینه‌سازی حافظه را توضیح می‌دهد.

---

## 1. فشرده‌سازی داده‌ها

### استفاده پایه

```c
#include "storage/data_compression.h"

// مقداردهی اولیه
data_compression_init();

// فشرده‌سازی
uint8_t input[1024];
uint8_t output[512];
uint32_t output_size = sizeof(output);

compression_algorithm_t algorithm = COMPRESSION_LZ4;
bool success = data_compress(input, sizeof(input), output, &output_size, algorithm);
```

### انتخاب الگوریتم مناسب

```c
// برای داده‌های سری زمانی (EEG)
compression_algorithm_t algo = data_compression_select_algorithm(0);  // DELTA

// برای داده‌های biomarker
algo = data_compression_select_algorithm(1);  // RLE

// برای داده‌های عمومی
algo = data_compression_select_algorithm(2);  // LZ4
```

### فشرده‌سازی با نتیجه

```c
compression_result_t result;
data_compress_with_result(input, sizeof(input), output, &output_size, 
                         COMPRESSION_LZ4, &result);

printf("Compression ratio: %.2f\n", result.compression_ratio);
printf("Original: %u bytes, Compressed: %u bytes\n", 
       result.original_size, result.compressed_size);
```

### باز کردن فشرده‌سازی

```c
uint8_t compressed[512];
uint8_t decompressed[1024];
uint32_t decompressed_size = sizeof(decompressed);

data_decompress(compressed, compressed_size, decompressed, 
                &decompressed_size, COMPRESSION_LZ4);
```

---

## 2. Streaming برای داده‌های بزرگ

### ایجاد Stream Reader

```c
#include "storage/data_streaming.h"

// Callback برای خواندن
bool read_callback(uint8_t *buffer, uint32_t size, void *user_data)
{
    // خواندن از source (مثلاً flash)
    return hal_flash_read(current_address, buffer, size);
}

// ایجاد stream
data_stream_t *stream = stream_create_reader(
    1,                    // stream_id
    1024 * 1024,          // total_size (1 MB)
    4096,                 // chunk_size (4 KB)
    read_callback,        // callback
    NULL                  // user_data
);
```

### پردازش Stream

```c
// Callback برای پردازش هر chunk
void process_chunk(const uint8_t *chunk, uint32_t chunk_size, void *user_data)
{
    // پردازش chunk
    process_data(chunk, chunk_size);
}

// پردازش stream
stream_process(stream, process_chunk, NULL);
```

### ایجاد Stream Writer

```c
// Callback برای نوشتن
bool write_callback(const uint8_t *buffer, uint32_t size, void *user_data)
{
    // نوشتن به destination
    return hal_flash_write(current_address, buffer, size);
}

// ایجاد stream
data_stream_t *writer = stream_create_writer(
    2,                    // stream_id
    1024 * 1024,          // total_size
    4096,                 // chunk_size
    write_callback,       // callback
    NULL                  // user_data
);

// نوشتن chunk
stream_write_chunk(writer, data, data_size);
```

### بررسی پیشرفت

```c
uint8_t progress = stream_get_progress(stream);
printf("Progress: %u%%\n", progress);

if (stream_is_complete(stream)) {
    printf("Stream complete!\n");
}
```

---

## 3. بهینه‌سازی ساختار داده‌ها

### استفاده از ساختارهای بهینه

```c
#include "storage/optimized_data_structures.h"

// به جای float (4 bytes)
float eeg_value = 1.5f;

// استفاده از int16_t (2 bytes)
int16_t optimized_value = float_to_int16(eeg_value, 1000.0f);  // scale = 1000

// بازگشت به float
float restored = int16_to_float(optimized_value, 1000.0f);
```

### ساختار EEG بهینه

```c
// به جای:
typedef struct {
    float value;      // 4 bytes
    uint32_t timestamp; // 4 bytes
} eeg_sample_t;  // 8 bytes

// استفاده از:
optimized_eeg_sample_t sample;
sample.value = float_to_int16(eeg_value, 1000.0f);
sample.timestamp = relative_timestamp;  // 2 bytes

// صرفه‌جویی: 8 bytes → 4 bytes (50% کاهش)
```

### ساختار Prediction بهینه

```c
// به جای:
typedef struct {
    float confidence;  // 4 bytes
    float risk_score;  // 4 bytes
} prediction_t;  // 8 bytes

// استفاده از:
optimized_prediction_result_t result;
result.confidence = float_to_uint8(confidence);  // 1 byte
result.risk_score = (uint16_t)(risk_score * 65535.0f);  // 2 bytes

// صرفه‌جویی: 8 bytes → 3 bytes (62% کاهش)
```

---

## 4. استفاده از External Flash

### مقداردهی اولیه

```c
#include "storage/external_flash.h"

external_flash_init();
```

### نوشتن داده

```c
uint8_t data[1024];
flash_metadata_t metadata = {
    .data_type = 0,  // EEG data
    .timestamp = hal_rtc_get_time_s()
};

uint32_t address = external_flash_write(data, sizeof(data), &metadata);
```

### خواندن داده

```c
uint8_t buffer[1024];
bool success = external_flash_read(address, buffer, sizeof(buffer));
```

### حذف داده

```c
external_flash_erase(address, size);
```

### دریافت اطلاعات

```c
uint32_t total, free, used;
external_flash_get_info(&total, &free, &used);

printf("Total: %u KB, Free: %u KB, Used: %u KB\n", 
       total/1024, free/1024, used/1024);
```

### Defragmentation

```c
// برای بهینه‌سازی فضای flash
external_flash_defragment();
```

---

## بهترین روش‌ها

### 1. فشرده‌سازی
- برای داده‌های سری زمانی از DELTA استفاده کنید
- برای داده‌های تکراری از RLE استفاده کنید
- برای داده‌های عمومی از LZ4 استفاده کنید

### 2. Streaming
- برای داده‌های بزرگ (>10 KB) از streaming استفاده کنید
- از chunk size مناسب استفاده کنید (4 KB پیشنهاد می‌شود)
- از callback برای I/O استفاده کنید

### 3. ساختارهای بهینه
- از int16_t به جای float برای داده‌های با دقت محدود
- از uint8_t برای مقادیر 0-1
- از packed structures برای کاهش padding

### 4. External Flash
- داده‌های غیرفعال را به external flash منتقل کنید
- از defragmentation دوره‌ای استفاده کنید
- از metadata برای مدیریت استفاده کنید

---

## نتایج مورد انتظار

با استفاده از این بهینه‌سازی‌ها:

- **فشرده‌سازی:** کاهش 50-70% در اندازه داده
- **Streaming:** کاهش استفاده از RAM تا 90%
- **ساختارهای بهینه:** کاهش 40-60% در اندازه ساختارها
- **External Flash:** آزادسازی RAM برای داده‌های فعال

---

**آخرین به‌روزرسانی:** 2024

