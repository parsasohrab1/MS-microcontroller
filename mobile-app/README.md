# اپلیکیشن موبایل - سیستم نوروپلتفرم MS

## معماری

### تکنولوژی پیشنهادی: React Native

**مزایا:**
- یک کد برای iOS و Android
- Performance خوب
- جامعه بزرگ
- کتابخانه‌های فراوان

**جایگزین:** Flutter (اگر ترجیح می‌دهید)

---

## ساختار پروژه

```
mobile-app/
├── src/
│   ├── screens/          # صفحات اپلیکیشن
│   │   ├── Dashboard/
│   │   ├── Reports/
│   │   ├── Medications/
│   │   ├── Symptoms/
│   │   ├── DoctorChat/
│   │   └── Education/
│   ├── components/       # کامپوننت‌های قابل استفاده مجدد
│   │   ├── Charts/
│   │   ├── Cards/
│   │   └── Forms/
│   ├── services/         # سرویس‌های API
│   │   ├── api.ts
│   │   ├── auth.ts
│   │   └── notifications.ts
│   ├── navigation/       # Navigation
│   ├── store/            # State management (Redux/Zustand)
│   ├── utils/            # توابع کمکی
│   └── types/            # TypeScript types
├── assets/                # تصاویر، فونت‌ها
├── App.tsx
└── package.json
```

---

## قابلیت‌های پیاده‌سازی

### 1. داشبورد تعاملی

- نمودارهای real-time
- نمایش آخرین داده‌ها
- وضعیت سیستم
- هشدارها

### 2. گزارش‌های خودکار

- گزارش روزانه
- گزارش هفتگی
- گزارش ماهانه
- export به PDF

### 3. یادآوری مصرف دارو

- اعلان‌های زمان‌بندی شده
- ثبت مصرف
- تاریخچه مصرف

### 4. ثبت علائم دستی

- فرم ثبت علائم
- عکس/ویدیو
- تاریخچه علائم

### 5. ارتباط با پزشک

- Chat
- Video call
- ارسال گزارش

### 6. آموزش و منابع

- ویدیوهای آموزشی
- مقالات
- FAQ

---

## راه‌اندازی

```bash
# نصب dependencies
npm install

# iOS
cd ios && pod install && cd ..
npm run ios

# Android
npm run android
```

---

## وابستگی‌های اصلی

- React Native
- React Navigation
- Redux Toolkit / Zustand
- React Native Charts
- React Native Paper / NativeBase
- React Native Push Notifications
- Socket.io (برای real-time)

