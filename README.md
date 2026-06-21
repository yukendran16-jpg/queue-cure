# 🏥 Queue Cure '26

## Smart Clinic Queue Management System

Queue Cure is a real-time clinic queue management system built for the **Queue Cure '26 Hackathon**.

Many clinics still use paper token slips and manual calling. Patients wait without knowing when they will be called. Receptionists manage queues manually, and doctors do not have a clear dashboard.

Queue Cure solves this problem using a digital, live, priority-based queue system.

---

## Problem Statement

* Patients wait for long hours without queue visibility.
* Clinics use paper token slips.
* Receptionists manually manage patient queues.
* Emergency patients may not be prioritized properly.
* Doctors do not have a live queue dashboard.

---

## Solution

Queue Cure provides:

* Digital patient token generation
* Priority-based patient triage
* Live receptionist dashboard
* Patient waiting room screen
* Estimated waiting time
* Doctor dashboard
* Reports page with patient history
* Voice announcement when a token is called
* Live queue updates using SocketIO

---

## Features

### Receptionist Dashboard

* Add patient name and symptom
* Automatically generate token number
* Automatically assign priority
* Set average consultation time
* Call next patient
* View current token
* View waiting patient count
* View completed patient count

### Priority-Based Queue

Patients are called in this order:

1. High Priority
2. Medium Priority
3. Low Priority

Patients with the same priority are called based on token number.

| Symptom              | Priority |
| -------------------- | -------- |
| Chest Pain           | High     |
| Heart Attack         | High     |
| Breathing Difficulty | High     |
| Fever                | Medium   |
| Vomiting             | Medium   |
| Severe Headache      | Medium   |
| General Checkup      | Low      |

### Patient Waiting Room

Patients can open their token page using:

```text
/waiting/<token_number>
```

Example:

```text
http://127.0.0.1:5000/waiting/5
```

The waiting room shows:

* Patient token number
* Current token being served
* Tokens ahead based on priority
* Estimated waiting time
* Live updates when receptionist calls the next patient
* Voice announcement for called token

### Doctor Dashboard

Doctor can view:

* Current patient token
* Total waiting patients
* Total completed patients
* Average consultation time

### Reports Page

Reports page shows:

* Token number
* Patient name
* Priority
* Status
* Added date
* Added time
* Completed time

---

## Tech Stack

* Python
* Flask
* Flask-SocketIO
* SQLite Database
* HTML
* CSS
* Bootstrap 5
* JavaScript
* Web Speech API

---

## Project Structure

```text
queue-cure/
│
├── app.py
├── database.py
├── clinic.db
│
└── templates/
    ├── receptionist.html
    ├── waiting_room.html
    ├── doctor.html
    └── reports.html
```

---

## How to Run

### 1. Install required packages

```bash
pip install flask flask-socketio
```

### 2. Run the project

```bash
python app.py
```

### 3. Open in browser

```text
http://127.0.0.1:5000/
```

---

## Pages

| Page                   | URL                |
| ---------------------- | ------------------ |
| Receptionist Dashboard | `/`                |
| Doctor Dashboard       | `/doctor`          |
| Reports                | `/reports`         |
| Patient Waiting Room   | `/waiting/<token>` |

---

## Priority Queue Logic

The system calls patients using this order:

```sql
ORDER BY
CASE
    WHEN priority='High' THEN 1
    WHEN priority='Medium' THEN 2
    ELSE 3
END,
token
```

This ensures critical patients are handled before normal patients.

---

## Live Sync

When the receptionist clicks **Call Next Token**:

1. The highest-priority waiting patient is selected.
2. The patient status becomes `completed`.
3. Completed time is stored in SQLite.
4. All waiting-room screens update automatically.
5. The system announces:

```text
Token X, please proceed to the doctor.
```

---

## Future Improvements

* Login for receptionist and doctor
* QR code for patient waiting room
* SMS or WhatsApp notification
* Multiple doctor rooms
* Appointment booking
* AI symptom analysis
* Daily analytics charts
* CSV and PDF report download

---

## Hackathon Pitch

**Queue Cure is a real-time, priority-based clinic queue management system that replaces paper tokens with live queue visibility, emergency triage, estimated waiting time, doctor dashboards, and digital reports.**

It helps clinics serve critical patients first while giving every patient a clear view of their waiting status.

---

## Team

Built for **Queue Cure '26 Hackathon**.
