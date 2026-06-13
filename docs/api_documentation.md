# REST API Documentation: CareAI Backend

This document details the REST API endpoints exposed by the CareAI backend services.

## Base URL
All API requests must be directed to: `http://localhost:8001` (or `http://localhost:8000` depending on configuration)


---

## Authentication & Headers

All endpoints except `/login` and `/register` require a signed JSON Web Token (JWT) passed in the `Authorization` header.

```http
Authorization: Bearer <your_jwt_token>
```

---

## 1. Authentication Endpoints

### 1.1 User Registration
Creates a new system user with roles: `patient`, `doctor`, or `caregiver`.

* **URL**: `/register`
* **Method**: `POST`
* **Payload**:
```json
{
  "username": "patient1",
  "password": "securepassword123",
  "role": "patient"
}
```
* **Response (200 OK)**:
```json
{
  "id": 1,
  "username": "patient1",
  "role": "patient"
}
```

### 1.2 User Login
Authenticates credentials and issues a JWT token.

* **URL**: `/login`
* **Method**: `POST`
* **Payload**:
```json
{
  "username": "patient1",
  "password": "securepassword123"
}
```
* **Response (200 OK)**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "role": "patient",
  "username": "patient1"
}
```

### 1.3 Profile Lookup (`/me`)
Returns details of the currently authenticated user session.

* **URL**: `/me`
* **Method**: `GET`
* **Response (200 OK)**:
```json
{
  "id": 1,
  "username": "patient1",
  "role": "patient"
}
```

---

## 2. Patient Health Data Endpoints

### 2.1 Retrieve Health Readings
Fetch historical readings. Patients receive only their own data. Doctors receive all records.

* **URL**: `/health-data`
* **Method**: `GET`
* **Parameters**:
  * `limit` (int, default=20): Number of readings to fetch.
* **Response (200 OK)**:
```json
[
  {
    "id": 5,
    "patient_name": "patient1",
    "heart_rate": 78,
    "blood_pressure": "122/81",
    "fasting_blood_sugar": 95.0,
    "postprandial_blood_sugar": 140.0,
    "age": 45,
    "sex": "male",
    "waist_cm": 88.0,
    "activity": "moderate",
    "family_diabetic": "no",
    "idrs_score": 30,
    "idrs_risk_level": "medium"
  }
]
```

### 2.2 Upload Single Vital Record
Upload vital telemetry. Automatically computes IDRS score and evaluates clinical alert thresholds.

* **URL**: `/health-data`
* **Method**: `POST`
* **Query Parameters**:
  * `patient_name` (string, required)
  * `heart_rate` (int, required)
  * `blood_pressure` (string, required)
  * `age` (int, optional)
  * `sex` (string, optional)
  * `waist_cm` (float, optional)
  * `activity` (string, optional)
  * `family_diabetic` (string, optional)
  * `fasting_blood_sugar` (float, optional)
  * `postprandial_blood_sugar` (float, optional)
* **Response (200 OK)**:
```json
{
  "message": "Health data stored",
  "idrs_score": 30,
  "idrs_risk_level": "medium"
}
```

### 2.3 Bulk Dataset Ingestion
Upload large JSON/CSV/XML clinical history datasets. Uses bulk insert optimization.

* **URL**: `/upload-health-data`
* **Method**: `POST`
* **Content-Type**: `multipart/form-data`
* **Form Parameters**:
  * `file`: (Raw File Binary)
  * `patient_name` (string)
  * `question` (string, optional)
  * `report_format` (string, default="json")
* **Response (200 OK)**:
```json
{
  "parsed_rows": 120,
  "anomaly_count": 2,
  "charts": {
    "heart_rate": "/tmp/charts/heart_rate_trends.png"
  },
  "agent_response": "AI report summary text...",
  "predictive_summary": {
    "future_diabetes_risk": "medium",
    "idrs_score": 30
  }
}
```

---

## 3. Medication Tracker Endpoints

### 3.1 Get Medication Schedules
* **URL**: `/medication-schedule`
* **Method**: `GET`
* **Response (200 OK)**:
```json
[
  {
    "id": 1,
    "patient_name": "patient1",
    "drug_name": "Metformin",
    "dosage": "500mg",
    "timing": "Morning",
    "drug_type": "Allopathic",
    "status": "Active"
  }
]
```

### 3.2 Create Medication Schedule
* **URL**: `/medication-schedule`
* **Method**: `POST`
* **Payload**:
```json
{
  "patient_name": "patient1",
  "drug_name": "Metformin",
  "dosage": "500mg",
  "timing": "Morning",
  "drug_type": "Allopathic"
}
```

### 3.3 Log Daily Adherence
* **URL**: `/medication-adherence`
* **Method**: `POST`
* **Payload**:
```json
{
  "patient_name": "patient1",
  "drug_name": "Metformin",
  "date": "2026-06-06",
  "status": "Taken"
}
```

---

## 4. Caching, Analytics & Journeys

### 4.1 Health Analytics Summary
Fetches general risk summary and chart spec (cached on Redis with fallback).

* **URL**: `/health-analytics`
* **Method**: `GET`

### 4.2 Health Journey History
* **URL**: `/health-journey`
* **Method**: `GET`
* **Query Parameters**:
  * `patient_name` (string)

---

## 5. Security & Compliance Endpoints

### 5.1 System Audit Logs
Guarded by role validation. Only doctor accounts can read log history.

* **URL**: `/audit-logs`
* **Method**: `GET`
* **Parameters**:
  * `limit` (int, default=100)
  * `offset` (int, default=0)
* **Response (200 OK)**:
```json
[
  {
    "id": 12,
    "timestamp": "2026-06-06 10:45:00",
    "username": "patient1",
    "role": "patient",
    "action": "READ",
    "resource": "HealthData:patient1",
    "status": "SUCCESS"
  }
]
```
