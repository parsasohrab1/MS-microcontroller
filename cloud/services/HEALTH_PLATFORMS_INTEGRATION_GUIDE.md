# راهنمای یکپارچه‌سازی با پلتفرم‌های سلامت

## مقدمه

این راهنما نحوه یکپارچه‌سازی با Apple Health, Google Fit, Smartwatch و سیستم‌های بیمارستانی (HL7/FHIR) را توضیح می‌دهد.

---

## 1. Apple Health Integration

### iOS App (Swift)

```swift
import HealthKit

class HealthKitManager {
    let healthStore = HKHealthStore()
    
    func requestAuthorization() {
        let typesToRead: Set<HKObjectType> = [
            HKObjectType.quantityType(forIdentifier: .heartRate)!,
            HKObjectType.quantityType(forIdentifier: .stepCount)!,
            HKObjectType.categoryType(forIdentifier: .sleepAnalysis)!
        ]
        
        healthStore.requestAuthorization(toShare: nil, read: typesToRead) { success, error in
            if success {
                print("HealthKit authorized")
            }
        }
    }
    
    func readHeartRate(completion: @escaping ([Double]) -> Void) {
        let heartRateType = HKQuantityType.quantityType(forIdentifier: .heartRate)!
        let query = HKSampleQuery(
            sampleType: heartRateType,
            predicate: nil,
            limit: 100,
            sortDescriptors: [NSSortDescriptor(key: HKSampleSortIdentifierEndDate, ascending: false)]
        ) { query, results, error in
            let heartRates = results?.compactMap { sample -> Double? in
                guard let quantitySample = sample as? HKQuantitySample else { return nil }
                return quantitySample.quantity.doubleValue(for: HKUnit.count().unitDivided(by: HKUnit.minute()))
            } ?? []
            completion(heartRates)
        }
        healthStore.execute(query)
    }
}
```

### Backend Integration

```python
from cloud.services.integration_service.app.health_platforms import HealthPlatformsIntegration

integration = HealthPlatformsIntegration()

# دریافت داده از Apple Health (از طریق webhook یا API)
# در iOS app، داده‌ها به Backend ارسال می‌شوند
```

---

## 2. Google Fit Integration

### Android App (Kotlin)

```kotlin
import com.google.android.gms.fitness.Fitness
import com.google.android.gms.fitness.data.DataType
import com.google.android.gms.fitness.request.DataReadRequest

class GoogleFitManager(private val context: Context) {
    fun readHeartRate(callback: (List<Float>) -> Unit) {
        val endTime = System.currentTimeMillis()
        val startTime = endTime - (24 * 60 * 60 * 1000) // 24 hours ago
        
        val readRequest = DataReadRequest.Builder()
            .read(DataType.TYPE_HEART_RATE_BPM)
            .setTimeRange(startTime, endTime, TimeUnit.MILLISECONDS)
            .build()
        
        Fitness.getHistoryClient(context, GoogleSignIn.getLastSignedInAccount(context)!!)
            .readData(readRequest)
            .addOnSuccessListener { response ->
                val heartRates = response.dataPoints.map { it.getValue(Field.FIELD_BPM).asFloat() }
                callback(heartRates)
            }
    }
}
```

### Backend Integration

```python
# احراز هویت
await integration.authorize_google_fit(user_id, access_token)

# خواندن داده
heart_rate_data = await integration.read_google_fit_data(
    user_id=user_id,
    data_type="heart_rate",
    start_date=datetime.now() - timedelta(days=7),
    end_date=datetime.now()
)
```

---

## 3. Smartwatch Integration

### Apple Watch

```swift
// در iOS app
func syncWatchData() {
    // استفاده از HealthKit برای sync خودکار
    // یا استفاده از WatchConnectivity framework
}
```

### Samsung Watch / Wear OS

```python
# در Backend
await integration.sync_smartwatch_data(
    user_id="user_123",
    watch_type="samsung_watch",
    data=[
        {
            "type": "heart_rate",
            "value": 72,
            "unit": "bpm",
            "timestamp": "2024-01-01T12:00:00",
            "device_id": "watch_123"
        }
    ]
)
```

---

## 4. HL7/FHIR Integration

### Export به FHIR

```python
from cloud.services.integration_service.app.health_platforms import HealthPlatformsIntegration

integration = HealthPlatformsIntegration()

# Export داده MS به FHIR
fhir_resource = await integration.export_to_fhir(
    user_id="patient_123",
    data={
        "value": 0.75,
        "unit": "risk_score",
        "unit_code": "1",
        "loinc_code": "85354-9",
        "display_name": "MS Risk Score"
    }
)

# ارسال به سیستم بیمارستانی
success = await integration.send_to_hospital_system(
    user_id="patient_123",
    hospital_endpoint="https://hospital.example.com/fhir/Observation",
    fhir_data=fhir_resource
)
```

### Import از FHIR

```python
# دریافت داده از سیستم بیمارستانی
fhir_data = {
    "resourceType": "Observation",
    "valueQuantity": {
        "value": 120,
        "unit": "mmHg"
    }
}

ms_data = await integration.import_from_fhir(fhir_data)
```

---

## 5. استفاده در Mobile App

### React Native

```typescript
// نصب کتابخانه‌ها
// npm install react-native-health
// npm install @react-native-google-fit/google-fit

import { HealthKit } from 'react-native-health';
import GoogleFit from '@react-native-google-fit/google-fit';

// Apple Health
const readHeartRate = async () => {
  const heartRate = await HealthKit.getHeartRateSamples({
    startDate: new Date(Date.now() - 24 * 60 * 60 * 1000),
    endDate: new Date(),
  });
  return heartRate;
};

// Google Fit
const readSteps = async () => {
  const steps = await GoogleFit.getDailyStepCountSamples({
    startDate: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000),
    endDate: new Date(),
  });
  return steps;
};
```

---

## 6. API Endpoints

### احراز هویت

```bash
POST /integration/health/authorize?user_id=user_123
{
  "platform": "google_fit",
  "auth_token": "ya29.a0AfH6..."
}
```

### دریافت داده

```bash
GET /integration/health/data?user_id=user_123&platform=google_fit&data_type=heart_rate&start_date=2024-01-01&end_date=2024-01-08
```

### همگام‌سازی Smartwatch

```bash
POST /integration/smartwatch/sync?user_id=user_123
{
  "watch_type": "apple_watch",
  "data": [
    {
      "type": "heart_rate",
      "value": 72,
      "unit": "bpm",
      "timestamp": "2024-01-01T12:00:00"
    }
  ]
}
```

### Export به FHIR

```bash
POST /integration/fhir/export
{
  "patient_id": "patient_123",
  "data": {
    "value": 0.75,
    "unit": "risk_score"
  }
}
```

---

## بهترین روش‌ها

### 1. Privacy
- درخواست فقط دسترسی‌های لازم
- ذخیره‌سازی امن توکن‌ها
- رعایت GDPR/HIPAA

### 2. Error Handling
- Retry mechanism
- Fallback strategies
- Logging خطاها

### 3. Data Synchronization
- Sync دوره‌ای
- Conflict resolution
- Data validation

---

## منابع

- [Apple HealthKit](https://developer.apple.com/healthkit/)
- [Google Fit API](https://developers.google.com/fit)
- [HL7 FHIR](https://www.hl7.org/fhir/)
- [FHIR REST API](https://www.hl7.org/fhir/http.html)

---

**آخرین به‌روزرسانی:** 2024

