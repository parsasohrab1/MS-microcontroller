# ساختار پروژه سیستم نوروپلتفرم MS

```
MS-microcontroller/
├── README.md                          # سند اصلی SRS و SDP
├── project-structure.md               # این فایل - توضیح ساختار پروژه
│
├── firmware/                          # کد میکروکنترلر (Embedded)
│   ├── src/
│   │   ├── main.c                     # نقطه ورود اصلی
│   │   ├── config.h                   # تنظیمات سیستم
│   │   ├── monitoring/                 # ماژول مانیتورینگ
│   │   │   ├── sensors.c/h            # درایورهای سنسور
│   │   │   ├── eeg_ecog.c/h           # ثبت سیگنال‌های عصبی
│   │   │   └── biomarkers.c/h         # اندازه‌گیری بیومارکرها
│   │   ├── signal_processing/         # پردازش سیگنال
│   │   │   ├── filters.c/h            # فیلترهای دیجیتال
│   │   │   ├── feature_extraction.c/h # استخراج ویژگی
│   │   │   └── noise_reduction.c/h    # کاهش نویز
│   │   ├── ml/                        # مدل‌های TinyML
│   │   │   ├── model_inference.c/h    # اجرای مدل
│   │   │   ├── prediction.c/h         # پیش‌بینی حملات
│   │   │   └── models/                 # مدل‌های کامپایل شده
│   │   ├── stimulation/               # سیستم تحریک
│   │   │   ├── adbs_controller.c/h    # کنترلر aDBS
│   │   │   ├── pid_control.c/h        # کنترل PID
│   │   │   └── safety_limits.c/h      # محدودیت‌های ایمنی
│   │   ├── drug_delivery/             # دارورسانی
│   │   │   ├── micropump.c/h          # کنترل میکروپمپ
│   │   │   └── dosage_control.c/h     # کنترل دوز
│   │   ├── communication/             # ارتباطات
│   │   │   ├── ble.c/h                # بلوتوث کم‌مصرف
│   │   │   ├── data_sync.c/h          # همگام‌سازی داده
│   │   │   └── encryption.c/h         # رمزنگاری
│   │   ├── storage/                    # ذخیره‌سازی
│   │   │   ├── flash.c/h              # حافظه فلش
│   │   │   └── data_buffer.c/h        # بافر داده
│   │   └── system/                     # سیستم
│   │       ├── power_management.c/h   # مدیریت انرژی
│   │       ├── watchdog.c/h           # Watchdog timer
│   │       └── error_handler.c/h      # مدیریت خطا
│   ├── include/                       # هدرهای مشترک
│   ├── tests/                         # تست‌های واحد
│   └── CMakeLists.txt                 # فایل ساخت CMake
│
├── gateway/                            # گیت‌وی موبایل/گوشی
│   ├── mobile-app/                     # اپلیکیشن موبایل
│   │   ├── android/                    # نسخه Android
│   │   │   ├── app/
│   │   │   │   ├── src/
│   │   │   │   │   ├── main/
│   │   │   │   │   │   ├── java/.../
│   │   │   │   │   │   └── res/
│   │   │   │   │   └── test/
│   │   │   │   └── build.gradle
│   │   │   └── gradle/
│   │   └── ios/                        # نسخه iOS
│   │       ├── MSPlatform/
│   │       │   ├── MSPlatform.xcodeproj
│   │       │   └── MSPlatform/
│   │       └── Podfile
│   └── gateway-service/                # سرویس گیت‌وی
│       ├── src/
│       │   ├── data_collection.py      # جمع‌آوری داده
│       │   ├── preprocessing.py        # پیش‌پردازش
│       │   ├── cloud_sync.py           # همگام‌سازی ابری
│       │   └── ble_handler.py          # مدیریت BLE
│       └── requirements.txt
│
├── cloud/                              # لایه ابری/سرور
│   ├── backend/                        # بک‌اند
│   │   ├── api/                        # REST API
│   │   │   ├── routes/
│   │   │   │   ├── patients.py
│   │   │   │   ├── doctors.py
│   │   │   │   └── data.py
│   │   │   ├── models/                 # مدل‌های داده
│   │   │   ├── auth/                   # احراز هویت
│   │   │   └── middleware/             # میدل‌ورها
│   │   ├── ml_services/                # سرویس‌های ML
│   │   │   ├── model_training.py       # آموزش مدل
│   │   │   ├── advanced_analytics.py   # تحلیل‌های پیشرفته
│   │   │   └── model_optimization.py   # بهینه‌سازی مدل
│   │   ├── database/                   # پایگاه داده
│   │   │   ├── models.py               # مدل‌های ORM
│   │   │   ├── migrations/             # مایگریشن‌ها
│   │   │   └── seeds.py                # داده‌های اولیه
│   │   └── config/                     # تنظیمات
│   ├── frontend/                       # پورتال وب پزشک
│   │   ├── src/
│   │   │   ├── components/             # کامپوننت‌های React
│   │   │   ├── pages/                  # صفحات
│   │   │   ├── services/               # سرویس‌های API
│   │   │   └── utils/                  # ابزارها
│   │   ├── public/
│   │   └── package.json
│   └── infrastructure/                 # زیرساخت
│       ├── docker/                     # فایل‌های Docker
│       ├── kubernetes/                 # تنظیمات K8s
│       └── terraform/                  # Infrastructure as Code
│
├── ml/                                 # مدل‌های یادگیری ماشین
│   ├── training/                       # آموزش مدل‌ها
│   │   ├── data_preprocessing.py       # پیش‌پردازش داده
│   │   ├── model_training.py           # آموزش مدل
│   │   ├── evaluation.py              # ارزیابی
│   │   └── notebooks/                  # Jupyter notebooks
│   ├── optimization/                   # بهینه‌سازی برای TinyML
│   │   ├── quantization.py             # کوانتیزاسیون
│   │   ├── pruning.py                  # Pruning
│   │   └── conversion.py               # تبدیل به فرمت میکروکنترلر
│   └── models/                         # مدل‌های ذخیره شده
│
├── tests/                              # تست‌های یکپارچه
│   ├── unit/                           # تست واحد
│   ├── integration/                    # تست یکپارچه‌سازی
│   ├── system/                         # تست سیستم
│   └── clinical/                       # تست‌های بالینی
│
├── docs/                               # مستندات
│   ├── architecture/                   # مستندات معماری
│   ├── api/                            # مستندات API
│   ├── hardware/                       # مستندات سخت‌افزاری
│   └── deployment/                     # راهنماهای استقرار
│
├── scripts/                            # اسکریپت‌های کمکی
│   ├── build.sh                        # اسکریپت ساخت
│   ├── flash.sh                        # فلش میکروکنترلر
│   ├── test.sh                         # اجرای تست‌ها
│   └── deploy.sh                       # استقرار
│
└── tools/                              # ابزارهای توسعه
    ├── simulators/                     # شبیه‌سازها
    └── analyzers/                      # آنالایزرها
```

## توضیحات ساختار

### firmware/
کد میکروکنترلر که روی nRF52840 اجرا می‌شود. شامل تمام ماژول‌های اصلی سیستم.

### gateway/
گیت‌وی موبایل که بین ایمپلنت و سرور ارتباط برقرار می‌کند.

### cloud/
لایه ابری شامل بک‌اند، فرانت‌اند و زیرساخت.

### ml/
مدل‌های یادگیری ماشین و ابزارهای بهینه‌سازی برای TinyML.

### tests/
تمام تست‌ها در یک مکان مرکزی.

### docs/
مستندات فنی و راهنماها.

