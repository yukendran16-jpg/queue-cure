from flask import Flask, render_template, request, redirect

import sqlite3

from datetime import datetime

from database import create_database

from flask_socketio import SocketIO


app = Flask(__name__)

socketio = SocketIO(app)

create_database()


# ---------------------------------------------------------------
# Helper: today's date in the same format used everywhere else
# (dd-mm-yyyy). Every query that should "reset" daily uses this.
# ---------------------------------------------------------------
def today_str():
    return datetime.now().strftime("%d-%m-%Y")


@app.route("/")
def receptionist():

    conn = sqlite3.connect("clinic.db")
    cursor = conn.cursor()

    today = today_str()

    # Only today's waiting patients
    cursor.execute("""
        SELECT *
        FROM patients
        WHERE status='waiting'
        AND created_date=?
        ORDER BY token
        """, (today,))

    patients = cursor.fetchall()

    # Only today's completed count
    cursor.execute("""
        SELECT COUNT(*)
        FROM patients
        WHERE status='completed'
        AND created_date=?
        """, (today,))

    completed_count = cursor.fetchone()[0]

    # Only today's waiting count
    cursor.execute("""
        SELECT COUNT(*)
        FROM patients
        WHERE status='waiting'
        AND created_date=?
        """, (today,))

    waiting_count = cursor.fetchone()[0]

    cursor.execute(
        "SELECT avg_time FROM settings WHERE id=1"
    )

    avg_time = cursor.fetchone()[0]

    # Patient currently being seen RIGHT NOW (not yet completed)
    cursor.execute("""
        SELECT token, name
        FROM patients
        WHERE status='serving'
        AND created_date=?
        ORDER BY token DESC
        LIMIT 1
        """, (today,))

    current_patient = cursor.fetchone()

    conn.close()

    return render_template(
        "receptionist.html",
        patients=patients,
        current_patient=current_patient,
        avg_time=avg_time,
        waiting_count=waiting_count,
        completed_count=completed_count
    )


@app.route("/add_patient", methods=["POST"])
def add_patient():

    name = request.form["name"]
    symptom = request.form["symptom"]

    if symptom in ["Chest Pain", "Heart Attack", "Breathing Difficulty"]:
        priority = "High"

    elif symptom in ["Fever", "Vomiting", "Severe Headache"]:
        priority = "Medium"

    else:
        priority = "Low"

    now = datetime.now()

    created_date = now.strftime("%d-%m-%Y")
    created_time = now.strftime("%H:%M:%S")

    conn = sqlite3.connect("clinic.db")
    cursor = conn.cursor()

    # ---- Token resets every day ----
    # Count only TODAY's patients, not all-time, so token starts
    # back at 1 whenever the date changes.
    cursor.execute(
        "SELECT COUNT(*) FROM patients WHERE created_date=?",
        (created_date,)
    )
    count = cursor.fetchone()[0]

    token = count + 1

    cursor.execute("""
        INSERT INTO patients
        (
            name,
            token,
            priority,
            created_date,
            created_time
        )
        VALUES
        (
            ?,
            ?,
            ?,
            ?,
            ?
        )
        """,
        (
            name,
            token,
            priority,
            created_date,
            created_time
        ))

    conn.commit()
    conn.close()

    return redirect("/")


@app.route("/call_next")
def call_next():

    conn = sqlite3.connect("clinic.db")
    cursor = conn.cursor()

    today = today_str()
    completed_time = datetime.now().strftime("%H:%M:%S")

    # Step 1: whoever is currently being served is now DONE.
    # (On the very first click of the day, this updates 0 rows —
    # nobody has been served yet, which is fine.)
    cursor.execute("""
        UPDATE patients
        SET status='completed',
            completed_time=?
        WHERE status='serving'
        AND created_date=?
        """, (completed_time, today))

    # Step 2: pull the next waiting patient (priority first, then
    # token order) and put THEM into "serving" — not "completed".
    cursor.execute("""
        SELECT id, token
        FROM patients
        WHERE status='waiting'
        AND created_date=?
        ORDER BY
            CASE
                WHEN priority='High' THEN 1
                WHEN priority='Medium' THEN 2
                ELSE 3
            END,
            token
        LIMIT 1
        """, (today,))

    patient = cursor.fetchone()

    if patient:

        cursor.execute("""
            UPDATE patients
            SET status='serving'
            WHERE id=?
            """, (patient[0],))

        socketio.emit("queue_updated")

        socketio.emit(
            "announce_token",
            {"token": patient[1]}
        )

    conn.commit()
    conn.close()

    return redirect("/")


@app.route("/set_time", methods=["POST"])
def set_time():

    avg_time = request.form["avg_time"]

    conn = sqlite3.connect("clinic.db")
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE settings SET avg_time=? WHERE id=1",
        (avg_time,)
    )

    conn.commit()
    conn.close()

    return redirect("/")


@app.route("/waiting/<int:token>")
def waiting(token):

    conn = sqlite3.connect("clinic.db")
    cursor = conn.cursor()

    today = today_str()

    # Current patient = whoever is being served RIGHT NOW today
    cursor.execute("""
        SELECT token, name
        FROM patients
        WHERE status='serving'
        AND created_date=?
        ORDER BY token DESC
        LIMIT 1
        """, (today,))

    current = cursor.fetchone()

    current_token = current[0] if current else 0

    # This patient's priority — match token AND today's date,
    # because tokens repeat every day (1,2,3...) so token alone
    # is not unique across days.
    cursor.execute("""
        SELECT priority
        FROM patients
        WHERE token=?
        AND created_date=?
        """, (token, today))

    patient_data = cursor.fetchone()

    if not patient_data:
        conn.close()
        return "Invalid Token Number"

    patient_priority = patient_data[0]

    # Priority rank:
    # High = 1
    # Medium = 2
    # Low = 3
    priority_rank = {
        "High": 1,
        "Medium": 2,
        "Low": 3
    }

    my_rank = priority_rank.get(patient_priority, 3)

    # Priority-wise tokens ahead, scoped to today only
    cursor.execute("""
        SELECT COUNT(*)
        FROM patients
        WHERE status='waiting'
        AND created_date=?
        AND (
            CASE
                WHEN priority='High' THEN 1
                WHEN priority='Medium' THEN 2
                ELSE 3
            END < ?

            OR (
                CASE
                    WHEN priority='High' THEN 1
                    WHEN priority='Medium' THEN 2
                    ELSE 3
                END = ?

                AND token < ?
            )
        )
        """, (today, my_rank, my_rank, token))

    tokens_ahead = cursor.fetchone()[0]

    # Average consultation time
    cursor.execute("""
        SELECT avg_time
        FROM settings
        WHERE id=1
        """)

    avg_time = cursor.fetchone()[0]

    wait_time = tokens_ahead * avg_time

    conn.close()

    return render_template(
        "waiting_room.html",
        token=token,
        current_token=current_token,
        tokens_ahead=tokens_ahead,
        wait_time=wait_time
    )


@app.route("/doctor")
def doctor():

    conn = sqlite3.connect("clinic.db")
    cursor = conn.cursor()

    today = today_str()

    cursor.execute("""
        SELECT COUNT(*)
        FROM patients
        WHERE status='completed'
        AND created_date=?
        """, (today,))

    completed = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM patients
        WHERE status='waiting'
        AND created_date=?
        """, (today,))

    waiting = cursor.fetchone()[0]

    cursor.execute("""
        SELECT token, name
        FROM patients
        WHERE status='serving'
        AND created_date=?
        ORDER BY token DESC
        LIMIT 1
        """, (today,))

    current_patient = cursor.fetchone()

    cursor.execute(
        "SELECT avg_time FROM settings WHERE id=1"
    )

    avg_time = cursor.fetchone()[0]

    conn.close()

    return render_template(
        "doctor.html",
        completed=completed,
        waiting=waiting,
        current_patient=current_patient,
        avg_time=avg_time
    )


@app.route("/reports")
def reports():

    conn = sqlite3.connect("clinic.db")
    cursor = conn.cursor()

    # Full patient history (kept as-is — nothing deleted)
    cursor.execute("""
        SELECT *
        FROM patients
        ORDER BY created_date DESC, token DESC
        """)

    patients = cursor.fetchall()

    # Per-day patient count, so you can see how many people
    # came on each individual day.
    cursor.execute("""
        SELECT
            created_date,
            COUNT(*) AS total_patients,
            SUM(CASE WHEN status='completed' THEN 1 ELSE 0 END) AS completed,
            SUM(CASE WHEN status='waiting' THEN 1 ELSE 0 END) AS waiting
        FROM patients
        GROUP BY created_date
        ORDER BY created_date DESC
        """)

    daily_summary = cursor.fetchall()

    conn.close()

    return render_template(
        "reports.html",
        patients=patients,
        daily_summary=daily_summary
    )


if __name__ == "__main__":
    socketio.run(app, debug=True)
