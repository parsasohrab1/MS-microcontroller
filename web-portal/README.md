# پورتال وب پزشک - سیستم نوروپلتفرم MS

## معماری

### تکنولوژی پیشنهادی: React + TypeScript

**Stack:**
- **Frontend:** React 18 + TypeScript
- **UI Framework:** Material-UI (MUI) یا Ant Design
- **State Management:** Redux Toolkit
- **Charts:** Chart.js یا Recharts
- **Forms:** React Hook Form
- **Routing:** React Router v6

---

## ساختار پروژه

```
web-portal/
├── src/
│   ├── pages/            # صفحات اصلی
│   │   ├── Dashboard/
│   │   ├── Patients/
│   │   ├── Analytics/
│   │   ├── Reports/
│   │   └── Settings/
│   ├── components/       # کامپوننت‌های قابل استفاده مجدد
│   │   ├── Charts/
│   │   ├── Tables/
│   │   ├── Forms/
│   │   └── Layout/
│   ├── services/         # API services
│   │   ├── api.ts
│   │   ├── patients.ts
│   │   └── analytics.ts
│   ├── store/            # Redux store
│   ├── hooks/            # Custom hooks
│   ├── utils/            # Utilities
│   └── types/            # TypeScript types
├── public/
└── package.json
```

---

## قابلیت‌های پیاده‌سازی

### 1. داشبورد مدیریت چند بیمار

- لیست بیماران
- فیلتر و جستجو
- وضعیت هر بیمار
- هشدارها

### 2. تحلیل‌های پیشرفته

- نمودارهای تعاملی
- تحلیل روند
- مقایسه بیماران
- پیش‌بینی‌ها

### 3. تنظیم از راه دور

- تنظیم پارامترهای درمان
- فعال/غیرفعال کردن درمان
- مشاهده وضعیت real-time

### 4. مقایسه بیماران

- مقایسه الگوها
- گروه‌بندی
- آمار کلی

### 5. Export داده‌ها

- Export به Excel
- Export به PDF
- Export برای پژوهش

---

## راه‌اندازی

```bash
# نصب dependencies
npm install

# Development
npm run dev

# Build
npm run build

# Production
npm run start
```

---

## وابستگی‌های اصلی

- React 18
- TypeScript
- Material-UI / Ant Design
- Redux Toolkit
- React Router
- Chart.js / Recharts
- React Hook Form
- Axios

