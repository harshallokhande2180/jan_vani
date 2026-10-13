# Jan-Vani: Data Protection & Privacy Compliance Policy
**In Compliance with India's Digital Personal Data Protection (DPDP) Act, 2023**

---

## 1. Executive Summary
Jan-Vani is a Vernacular Voice Assistant for Civic Grievance Redressal developed for civic authorities (Nagpur Municipal Corporation). Personal data gathered during grievance filing—specifically voice recordings, GPS coordinates, and phone numbers—are subject to strict data minimization, purpose limitation, and consent protocols under the Digital Personal Data Protection Act, 2023 (DPDP Act).

---

## 2. Categories of Personal Data Collected
| Data Type | Purpose | Minimisation Strategy | Retention Period |
| :--- | :--- | :--- | :--- |
| **Voice Audio Stream** | Regional language transcription (ASR) into text | Recorded at 16 kHz mono; raw audio stream is deleted after transcription is generated and verified. | Max 24 hours (buffer), then permanently purged. |
| **GPS Geolocation (Lat/Lon)** | Assigning grievance to municipal ward polygon & spatial deduplication (50m radius) | Stored only to identify administrative ward polygon. Fuzzed coordinate option for indoor/private residences. | Lifetime of active civic grievance; archived upon resolution. |
| **Phone Number (Optional)** | SMS status notification & ticket tracking reference | Stored only as masked reference (last 4 digits) or salted cryptographic hash (`phone_hash`). No unsolicited marketing. | Masked immediately upon entry. |

---

## 3. Lawful Basis and Explicit Consent (Section 6, DPDP Act 2023)
- **On-Screen and Spoken Consent:**
  Before the microphone begins recording, citizens are presented with a clear consent notice in their selected dialect (Marathi / Hindi / English):
  - *Marathi:* "मी माझा आवाज आणि स्थान महापालिकेस पाठवण्यास संमती देतो/देते (DPDP कायदा २०२३)."
  - *Hindi:* "मैं अपनी आवाज और स्थान नगर निगम को भेजने की सहमति देता/देती हूँ (DPDP एक्ट 2023)।"
- **Unambiguous Opt-in:** The recording trigger is inhibited until the citizen consents.

---

## 4. Role-Based Access Control (RBAC) & Security
- **Bcrypt Password Encryption:** Administrative and Ward Officer logins are protected with bcrypt cryptographic salted hashing.
- **Ward-Level Isolation:** Ward officers are granted access only to grievances originating within their assigned municipal ward polygon. Cross-ward queries are restricted to the Municipal Commissioner role.
- **Environment Isolation:** All secret API keys (Bhashini, LLM tokens) reside exclusively in `.env` and are strictly excluded from repository version control.
