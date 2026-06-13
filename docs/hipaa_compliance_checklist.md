# HIPAA Compliance & Security Assessment Checklist

This document details how the CareAI system satisfies the Technical Safeguards required under the **Health Insurance Portability and Accountability Act (HIPAA)** Security Rule.

---

## 1. Access Control (§ 164.312(a))

### 1.1 Unique User Identification
* **Implementation**: Every user (Patient, Clinician, Caregiver) must create a unique account. Hashed passwords are required.
* **Mechanism**: Users are assigned unique IDs, usernames, and roles. Password validation requires a minimum of 6 characters. Passwords are hashed using `bcrypt` in the auth database.

### 1.2 Role-Based Access Control (RBAC)
* **Implementation**: APIs enforce user context validation.
* **Rules**:
  * **Patients**: Can only read, write, or export their own medical history, chat with AI about their own vitals, and configure their own goals. Attempting to pass another patient's username returns a `403 Forbidden` response.
  * **Doctors**: Have clinical search privileges. They can access the multi-patient registry list, view historical trend graphs for any selected patient, and inspect system audit logs.
  * **Caregivers**: Can monitor linked patient adherence logs, vital summaries, and wellness progress indicators.

---

## 2. Audit Controls (§ 164.312(b))

### 2.1 Access Log Ingestion
* **Implementation**: Any access to Protected Health Information (PHI) or administrative dashboards triggers an automatic entry in the `AuditLog` table.
* **Mechanism**: The backend calls the `log_audit_event()` function to save details:
  * Timestamp of access.
  * Username and user role.
  * Action performed (`READ`, `WRITE`, `EXPORT`, `LOGIN`).
  * Resource identifier (e.g., `HealthData:patient1`).
  * Access status (`SUCCESS`, `DENIED`).

### 2.2 Log Protection
* **Implementation**: Audit logs are indexed on the database, read-only via standard API endpoints, and accessible solely by the `doctor` role.

---

## 3. Transmission Security (§ 164.312(e))

### 3.1 Data Transit Encryption
* **Recommendation**: In a production deployment, the FastAPI server and React frontend must be configured behind an SSL/TLS termination proxy (e.g., Nginx, AWS ALBs) enforcing HTTPS (TLS 1.2 or 1.3).
* **Local Dev**: Handled over local loopback ports with simulated headers.

---

## 4. Encryption at Rest (§ 164.312(a)(2)(iv))

### 4.1 Column-Level PHI Encryption
* **Implementation**: Transparent Column-Level Encryption (TCE) is configured inside `backend/models.py`.
* **Mechanism**: SQLAlchemy custom `TypeDecorator` instances (`EncryptedString`, `EncryptedInteger`, `EncryptedFloat`) automatically intercept write/read queries.
  * **Writes**: Cleartext values are encrypted using **Fernet Symmetric Key Encryption** (built on AES-128 in CBC mode with HMAC-SHA256 authentication).
  * **Reads**: Ciphertext is decrypted back to cleartext using the environment `ENCRYPTION_KEY`.
* **Columns Covered**:
  * `PatientProfile`: age, gender, height, weight, dietary_preference, state, pincode, waist_cm, physical_activity, family_history.
  * `HealthInsurance`: provider_name, policy_number, coverage_limit, emergency_contact.
  * `HealthData`: age, sex, waist_cm, activity, family_diabetic, idrs_score, idrs_risk_level.

### 4.2 Key Management
* **Mechanism**: The backend automatically generates a 32-byte cryptographically secure URL-safe base64-encoded key and appends it as `ENCRYPTION_KEY` in `.env` if missing during startup, preventing hardcoded keys.
