# API Reference Manual

This document provides specifications for the REST API endpoints exposed by the backend services.

---

## 1. Authentication & User Profile

All application endpoints (except registration, login, and health checks) require a JWT bearer token in the HTTP Authorization header:
```http
Authorization: Bearer <your_jwt_access_token>
```

### 1.1 Request Email Verification OTP
Generates a 6-digit OTP code and emails it to the user.
* **URL:** `/api/users/otp/`
* **Method:** `POST`
* **Auth Required:** No
* **Request Body:**
  ```json
  {
    "email": "participant@example.com"
  }
  ```
* **Response (200 OK):**
  ```json
  {
    "detail": "OTP sent successfully."
  }
  ```

### 1.2 Participant Registration
Registers a new user, verifying their OTP and checking age constraints (15 to 80 years old).
* **URL:** `/api/users/register/`
* **Method:** `POST`
* **Auth Required:** No
* **Request Body:**
  ```json
  {
    "username": "participant123",
    "full_name": "John Doe",
    "email": "participant@example.com",
    "password": "SecurePassword123!",
    "confirm_password": "SecurePassword123!",
    "whatsapp_number": "+923001234567",
    "date_of_birth": "1998-05-15",
    "consent_agreed": true,
    "consent_version": "1.0",
    "otp": "654321"
  }
  ```
* **Response (201 Created):**
  ```json
  {
    "user_id": "8f3d61b2-132d-4ef9-813c-83b3337bf87b",
    "username": "participant123",
    "email": "participant@example.com"
  }
  ```

### 1.3 Fetch User Profile Info
Returns current user state, experimental days, and due questionnaire milestones.
* **URL:** `/api/users/profile/`
* **Method:** `GET`
* **Auth Required:** Yes
* **Response (200 OK):**
  ```json
  {
    "user_id": "8f3d61b2-132d-4ef9-813c-83b3337bf87b",
    "username": "participant123",
    "email": "participant@example.com",
    "group": 1,
    "group_name": "Treatment Group A",
    "current_experiment_day": 3,
    "due_milestone": "3_MONTHS",
    "has_completed_sociodemographic": true,
    "has_completed_posttest": true,
    "has_completed_t2": false,
    "is_disqualified": false
  }
  ```

---

## 2. Daily Reflections & Activities

### 2.1 Get Today's Assigned Reflection Prompt
Retrieves the daily reflection prompt assigned to the user's experimental group.
* **URL:** `/api/activities/daily/current/`
* **Method:** `GET`
* **Auth Required:** Yes
* **Response (200 OK):**
  ```json
  {
    "id": 14,
    "title": "Gratitude Mapping",
    "description": "List three things you are grateful for today and explain why.",
    "day_number": 3,
    "activity_type": "three_good_things",
    "submitted_today": false,
    "current_day": 3
  }
  ```

### 2.2 Submit Today's Reflection
Saves the reflection content. Blocks submission if the user has already submitted today.
* **URL:** `/api/activities/daily/submit/`
* **Method:** `POST`
* **Auth Required:** Yes
* **Request Body:**
  ```json
  {
    "content": "I am grateful for my health, my supportive family, and clean drinking water.",
    "entry_1": "Health",
    "entry_2": "Supportive Family",
    "entry_3": "Clean drinking water"
  }
  ```
* **Response (201 Created):**
  ```json
  {
    "id": "e4b2d184-7a31-419b-bf78-ef731db812a1",
    "content": "I am grateful for my health, my supportive family, and clean drinking water.",
    "experiment_day": 3,
    "submission_date": "2026-06-06T15:24:00+05:00"
  }
  ```

---

## 3. Questionnaires & Psychometrics

### 3.1 Fetch Available Due Questionnaire
Retrieves the psychometric battery questions that the participant needs to answer.
* **URL:** `/api/questionnaires/due/`
* **Method:** `GET`
* **Auth Required:** Yes
* **Response (200 OK):**
  ```json
  {
    "due_milestone": "3_MONTHS",
    "questionnaire": {
      "id": "c3e1b782-b13c-423c-a99f-eef41b31278c",
      "title": "3-Month Psychological Assessment",
      "assessment_type": "PSYCHOMETRIC",
      "sections": [
        {
          "id": 5,
          "title": "Overall Well-being",
          "questions": [
            {
              "id": 102,
              "content": "[PERMA] In general, how active and healthy do you feel?",
              "type": "SCALE",
              "options": [
                {"id": 41, "label": "0 - Not at all", "value": 0},
                {"id": 42, "label": "10 - Extremely", "value": 10}
              ]
            }
          ]
        }
      ]
    }
  }
  ```

### 3.2 Submit Questionnaire Response Set
Saves responses for a psychometric milestone.
* **URL:** `/api/questionnaires/submit/`
* **Method:** `POST`
* **Auth Required:** Yes
* **Request Body:**
  ```json
  {
    "milestone": "3_MONTHS",
    "responses": [
      {
        "question": 102,
        "selected_option": 42,
        "text_value": ""
      }
    ]
  }
  ```
* **Response (201 Created):**
  ```json
  {
    "id": "fb2d8471-ef3c-4a12-8cf9-183db12fa6b2",
    "status": "COMPLETED",
    "milestone": "3_MONTHS",
    "suicide_risk_triggered": false,
    "suicide_risk_opt_in": false
  }
  ```

---

## 4. Admin Tools

Admin endpoints require the user to have staff/superuser database privileges.

### 4.1 Trigger CSV Export
Enqueues a Celery background task to generate the CSV dataset.
* **URL:** `/api/admin/tools/export/t2/csv/` *(replace `t2` with `t0`/`t1`/`t3`/`t4`/`longitudinal`)*
* **Method:** `POST`
* **Auth Required:** Yes (Staff Only)
* **Request Body:**
  ```json
  {
    "group": "Treatment Group A"
  }
  ```
* **Response (202 Accepted):**
  ```json
  {
    "task_id": "a84f3d1b-ef23-4c91-912a-ef3db124fa1b",
    "status": "PROCESSING"
  }
  ```

### 4.2 Query Export Task Status
Polls the status of the enqueued CSV generation process.
* **URL:** `/api/admin/tools/export/status/<task_id>/`
* **Method:** `GET`
* **Auth Required:** Yes (Staff Only)
* **Response (200 OK):**
  ```json
  {
    "task_id": "a84f3d1b-ef23-4c91-912a-ef3db124fa1b",
    "status": "SUCCESS",
    "download_url": "/media/exports/t2_export_a84f3d1b.csv",
    "created_at": "2026-06-06T15:28:00+05:00",
    "error_message": null
  }
  ```

### 4.3 Query Suicide Risk Follow Ups
Retrieves flagged clinical suicide risk protocol alerts. Supports page-based pagination (10 items per page).
* **URL:** `/api/questionnaires/admin/suicide-risk-follow-ups/?page=<page_number>`
* **Method:** `GET`
* **Auth Required:** Yes (Staff Only)
* **Response (200 OK):**
  ```json
  {
    "last_refreshed_at": "2026-06-06T15:30:00+05:00",
    "total_flagged": 12,
    "opt_in_count": 4,
    "count": 12,
    "next": true,
    "previous": false,
    "cases": [
      {
        "user_id": "8f3d61b2-132d-4ef9-813c-83b3337bf87b",
        "username": "participant123",
        "full_name": "John Doe",
        "whatsapp_number": "+923001234567",
        "milestone": "SIGNUP",
        "flagged_at": "2026-06-06T15:24:00+05:00",
        "opt_in_check_in": true,
        "responses": [
          {
            "question_id": 105,
            "question_text": "[SIDAS] How often did you have thoughts of suicide?",
            "selected_option": "5 - Very Often"
          }
        ]
      }
    ]
  }
  ```

---

## 5. Group Management

Group management endpoints are used to manage experimental segments. Modification and creation endpoints require staff/superuser permissions, while retrieval endpoints require authentication.

### 5.1 Fetch All Groups
Retrieves all configured experimental segments with aggregated member counts.
* **URL:** `/api/groups/`
* **Method:** `GET`
* **Auth Required:** Yes
* **Response (200 OK):**
  ```json
  [
    {
      "group_id": 1,
      "name": "Treatment Group A",
      "description": "Gratitude intervention segment.",
      "created_at": "2026-06-06T15:20:00+05:00",
      "member_count": 24
    }
  ]
  ```

### 5.2 Create Group
Configures a new experimental segment.
* **URL:** `/api/groups/`
* **Method:** `POST`
* **Auth Required:** Yes (Staff Only)
* **Request Body:**
  ```json
  {
    "name": "Treatment Group C",
    "description": "Positive reflection segment."
  }
  ```
* **Response (201 Created):**
  ```json
  {
    "group_id": 3,
    "name": "Treatment Group C",
    "description": "Positive reflection segment.",
    "created_at": "2026-06-11T21:40:00+05:00",
    "member_count": 0
  }
  ```

### 5.3 Fetch Group Detail (with Participant Roster)
Retrieves the properties of a group and lists the participant details currently assigned to it.
* **URL:** `/api/groups/<id>/`
* **Method:** `GET`
* **Auth Required:** Yes
* **Response (200 OK):**
  ```json
  {
    "group_id": 1,
    "name": "Treatment Group A",
    "description": "Gratitude intervention segment.",
    "created_at": "2026-06-06T15:20:00+05:00",
    "member_count": 2,
    "participants": [
      {
        "user_id": "8f3d61b2-132d-4ef9-813c-83b3337bf87b",
        "full_name": "John Doe",
        "username": "participant123",
        "email": "participant@example.com",
        "submission_count": 7,
        "has_completed_sociodemographic": true,
        "current_experiment_day": 8,
        "is_disqualified": false
      },
      {
        "user_id": "7a31b2d1-419b-bf78-ef73-e4b2d18412a1",
        "full_name": "Jane Smith",
        "username": "participant456",
        "email": "jane@example.com",
        "submission_count": 3,
        "has_completed_sociodemographic": true,
        "current_experiment_day": 4,
        "is_disqualified": false
      }
    ]
  }
  ```

### 5.4 Update Group
Modifies group properties.
* **URL:** `/api/groups/<id>/`
* **Method:** `PUT` / `PATCH`
* **Auth Required:** Yes (Staff Only)
* **Request Body (PATCH example):**
  ```json
  {
    "description": "Updated description for gratitude segment."
  }
  ```
* **Response (200 OK):**
  ```json
  {
    "group_id": 1,
    "name": "Treatment Group A",
    "description": "Updated description for gratitude segment.",
    "created_at": "2026-06-06T15:20:00+05:00",
    "member_count": 2,
    "participants": [ ... ]
  }
  ```

### 5.5 Delete Group
Deletes an experimental segment.
* **URL:** `/api/groups/<id>/`
* **Method:** `DELETE`
* **Auth Required:** Yes (Staff Only)
* **Response (204 No Content):** Empty

---

## 6. Support Ticketing

Provides endpoints for participants to submit support requests and administrators to manage them.

### 6.1 List Support Tickets
Retrieves a paginated list of support tickets (10 items per page). Staff see all tickets; regular participants see only their own.
* **URL:** `/api/support/tickets/?page=<page_number>&page_size=<page_size>`
* **Method:** `GET`
* **Auth Required:** Yes
* **Response (200 OK):**
  ```json
  {
    "count": 45,
    "next": "http://localhost:8000/api/support/tickets/?page=2",
    "previous": null,
    "results": [
      {
        "id": 12,
        "user": "8f3d61b2-132d-4ef9-813c-83b3337bf87b",
        "subject": "App crashes during Reflection submission",
        "description": "I tried submitting my day 3 reflection and the screen went blank.",
        "status": "OPEN",
        "created_at": "2026-06-06T15:10:00+05:00"
      }
    ]
  }
  ```

