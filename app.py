from flask import Flask, render_template_string, request, redirect, url_for, flash
import sqlite3
import uuid
from datetime import datetime, timedelta, timezone

app = Flask(__name__)
app.secret_key = "ticket-booking-secret"

STATUS_AVAILABLE = "AVAILABLE"
STATUS_RESERVED = "RESERVED"
STATUS_BOOKED = "BOOKED"

RESERVATION_TTL_MINUTES = 5
DATABASE_FILE = "ticket_booking.db"


def generate_id():
    return str(uuid.uuid4())


def current_utc_time():
    return datetime.now(timezone.utc)


def to_iso(dt):
    return dt.isoformat()


def from_iso(iso_string):
    return datetime.fromisoformat(iso_string)


def get_connection():
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def initialize_database():
    with get_connection() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS events (
            event_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            event_date TEXT NOT NULL,
            venue TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS seats (
            seat_id TEXT PRIMARY KEY,
            event_id TEXT NOT NULL,
            seat_number TEXT NOT NULL,
            status TEXT CHECK(status IN ('AVAILABLE','RESERVED','BOOKED')) NOT NULL,
            reserved_by TEXT,
            reservation_id TEXT,
            reserved_until TEXT,
            booking_id TEXT,
            UNIQUE(event_id, seat_number)
        );

        CREATE TABLE IF NOT EXISTS bookings (
            booking_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            event_id TEXT NOT NULL,
            seat_list TEXT NOT NULL,
            booked_at TEXT NOT NULL
        );
        """)


def seed_sample_data():
    with get_connection() as conn:
        user_count = conn.execute(
            "SELECT COUNT(*) AS count FROM users"
        ).fetchone()["count"]

        if user_count == 0:
            user_id = "user-1"
            event_id = "event-1"

            conn.execute("""
            INSERT INTO users (user_id, name, email)
            VALUES (?, ?, ?)
            """, (user_id, "John Doe", "john@example.com"))

            conn.execute("""
            INSERT INTO events (event_id, name, event_date, venue)
            VALUES (?, ?, ?, ?)
            """, (event_id, "Music Concert", "2026-05-01", "Main Hall"))

            for seat_number in ["A1", "A2", "A3", "A4", "A5"]:
                conn.execute("""
                INSERT INTO seats (seat_id, event_id, seat_number, status)
                VALUES (?, ?, ?, ?)
                """, (
                    generate_id(),
                    event_id,
                    seat_number,
                    STATUS_AVAILABLE
                ))


def release_expired_reservations(event_id):
    now_iso = to_iso(current_utc_time())

    with get_connection() as conn:
        conn.execute("""
        UPDATE seats
        SET status=?,
            reserved_by=NULL,
            reservation_id=NULL,
            reserved_until=NULL
        WHERE event_id=?
          AND status=?
          AND reserved_until < ?
        """, (
            STATUS_AVAILABLE,
            event_id,
            STATUS_RESERVED,
            now_iso
        ))


def get_event(event_id):
    with get_connection() as conn:
        return conn.execute("""
        SELECT * FROM events WHERE event_id=?
        """, (event_id,)).fetchone()


def get_all_seats(event_id):
    release_expired_reservations(event_id)

    with get_connection() as conn:
        return conn.execute("""
        SELECT seat_number, status, reservation_id, booking_id
        FROM seats
        WHERE event_id=?
        ORDER BY seat_number
        """, (event_id,)).fetchall()


def reserve_seats(user_id, event_id, seat_numbers):
    if not seat_numbers:
        raise Exception("Please select at least one seat.")

    release_expired_reservations(event_id)

    reservation_id = generate_id()
    reserved_until = current_utc_time() + timedelta(minutes=RESERVATION_TTL_MINUTES)

    with get_connection() as conn:
        try:
            conn.execute("BEGIN")

            placeholders = ",".join("?" * len(seat_numbers))

            rows = conn.execute(f"""
            SELECT seat_number, status
            FROM seats
            WHERE event_id=? AND seat_number IN ({placeholders})
            """, [event_id] + seat_numbers).fetchall()

            if len(rows) != len(seat_numbers):
                raise Exception("Invalid seat selection.")

            for row in rows:
                if row["status"] != STATUS_AVAILABLE:
                    raise Exception(f"Seat {row['seat_number']} is already reserved or booked.")

            conn.execute(f"""
            UPDATE seats
            SET status=?,
                reserved_by=?,
                reservation_id=?,
                reserved_until=?
            WHERE event_id=? AND seat_number IN ({placeholders})
            """, [
                STATUS_RESERVED,
                user_id,
                reservation_id,
                to_iso(reserved_until),
                event_id
            ] + seat_numbers)

            conn.execute("COMMIT")
            return reservation_id

        except Exception:
            conn.execute("ROLLBACK")
            raise


def confirm_booking(user_id, reservation_id):
    with get_connection() as conn:
        try:
            conn.execute("BEGIN")

            rows = conn.execute("""
            SELECT event_id, seat_number, reserved_by, reserved_until
            FROM seats
            WHERE reservation_id=?
            """, (reservation_id,)).fetchall()

            if not rows:
                raise Exception("Reservation not found.")

            for row in rows:
                if row["reserved_by"] != user_id:
                    raise Exception("Reservation ownership mismatch.")

                if current_utc_time() > from_iso(row["reserved_until"]):
                    raise Exception("Reservation expired.")

            booking_id = generate_id()
            seat_list = ",".join([row["seat_number"] for row in rows])
            event_id = rows[0]["event_id"]

            conn.execute("""
            UPDATE seats
            SET status=?,
                booking_id=?
            WHERE reservation_id=?
            """, (
                STATUS_BOOKED,
                booking_id,
                reservation_id
            ))

            conn.execute("""
            INSERT INTO bookings (
                booking_id, user_id, event_id, seat_list, booked_at
            )
            VALUES (?, ?, ?, ?, ?)
            """, (
                booking_id,
                user_id,
                event_id,
                seat_list,
                to_iso(current_utc_time())
            ))

            conn.execute("COMMIT")
            return booking_id

        except Exception:
            conn.execute("ROLLBACK")
            raise


def get_bookings():
    with get_connection() as conn:
        return conn.execute("""
        SELECT * FROM bookings ORDER BY booked_at DESC
        """).fetchall()


HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Ticket Booking System</title>
    <style>
        body {
            font-family: Arial;
            background: #f4f6f8;
            padding: 30px;
        }

        .container {
            background: white;
            padding: 25px;
            max-width: 900px;
            margin: auto;
            border-radius: 10px;
            box-shadow: 0 0 10px #ccc;
        }

        h1, h2 {
            color: #333;
        }

        .seat {
            display: inline-block;
            padding: 15px;
            margin: 8px;
            border-radius: 8px;
            border: 1px solid #ccc;
        }

        .AVAILABLE {
            background: #d4edda;
        }

        .RESERVED {
            background: #fff3cd;
        }

        .BOOKED {
            background: #f8d7da;
        }

        button {
            padding: 10px 18px;
            background: #007bff;
            color: white;
            border: none;
            border-radius: 6px;
            cursor: pointer;
        }

        button:hover {
            background: #0056b3;
        }

        .message {
            padding: 10px;
            margin: 10px 0;
            background: #e2e3e5;
            border-radius: 6px;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }

        th, td {
            padding: 10px;
            border: 1px solid #ccc;
        }

        th {
            background: #eee;
        }
    </style>
</head>
<body>
<div class="container">
    <h1>Ticket Booking System</h1>

    <h2>{{ event["name"] }}</h2>
    <p><strong>Date:</strong> {{ event["event_date"] }}</p>
    <p><strong>Venue:</strong> {{ event["venue"] }}</p>

    {% with messages = get_flashed_messages() %}
        {% if messages %}
            {% for message in messages %}
                <div class="message">{{ message }}</div>
            {% endfor %}
        {% endif %}
    {% endwith %}

    <h2>Select Seats</h2>

    <form method="POST" action="/reserve">
        {% for seat in seats %}
            <label class="seat {{ seat['status'] }}">
                {% if seat["status"] == "AVAILABLE" %}
                    <input type="checkbox" name="seats" value="{{ seat['seat_number'] }}">
                {% endif %}
                {{ seat["seat_number"] }} - {{ seat["status"] }}
            </label>
        {% endfor %}

        <br><br>
        <button type="submit">Reserve Selected Seats</button>
    </form>

    {% if reservation_id %}
        <hr>
        <h2>Confirm Reservation</h2>
        <p><strong>Reservation ID:</strong> {{ reservation_id }}</p>

        <form method="POST" action="/confirm">
            <input type="hidden" name="reservation_id" value="{{ reservation_id }}">
            <button type="submit">Confirm Booking</button>
        </form>
    {% endif %}

    <hr>

    <h2>Bookings</h2>

    {% if bookings %}
        <table>
            <tr>
                <th>Booking ID</th>
                <th>User ID</th>
                <th>Event ID</th>
                <th>Seats</th>
                <th>Booked At</th>
            </tr>
            {% for booking in bookings %}
            <tr>
                <td>{{ booking["booking_id"] }}</td>
                <td>{{ booking["user_id"] }}</td>
                <td>{{ booking["event_id"] }}</td>
                <td>{{ booking["seat_list"] }}</td>
                <td>{{ booking["booked_at"] }}</td>
            </tr>
            {% endfor %}
        </table>
    {% else %}
        <p>No bookings found.</p>
    {% endif %}
</div>
</body>
</html>
"""


@app.route("/")
def home():
    event_id = "event-1"
    event = get_event(event_id)
    seats = get_all_seats(event_id)
    bookings = get_bookings()

    return render_template_string(
        HTML,
        event=event,
        seats=seats,
        bookings=bookings,
        reservation_id=None
    )


@app.route("/reserve", methods=["POST"])
def reserve():
    user_id = "user-1"
    event_id = "event-1"
    selected_seats = request.form.getlist("seats")

    try:
        reservation_id = reserve_seats(user_id, event_id, selected_seats)
        flash("Seats reserved successfully. Please confirm booking.")

        event = get_event(event_id)
        seats = get_all_seats(event_id)
        bookings = get_bookings()

        return render_template_string(
            HTML,
            event=event,
            seats=seats,
            bookings=bookings,
            reservation_id=reservation_id
        )

    except Exception as e:
        flash(str(e))
        return redirect(url_for("home"))


@app.route("/confirm", methods=["POST"])
def confirm():
    user_id = "user-1"
    reservation_id = request.form.get("reservation_id")

    try:
        booking_id = confirm_booking(user_id, reservation_id)
        flash(f"Booking confirmed successfully. Booking ID: {booking_id}")

    except Exception as e:
        flash(str(e))

    return redirect(url_for("home"))


if __name__ == "__main__":
    initialize_database()
    seed_sample_data()
    app.run(debug=True)
