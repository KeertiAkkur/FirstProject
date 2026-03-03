Online Ticket Booking Application

Project Overview
  This project is a simple online ticket booking application designed for beginners. The application allows users to select the tickets or seats they want to buy. The system stores the selected seats and displays a list of seats that have already been purchased.

The goal of this project is to focus on the basic logic of ticket booking without using complex features like online payment gateways or advanced seat maps.

Project Objectives
- Allow users to choose tickets or seats
- Store selected ticket information
- Display booked seats to users
- Build a simple and easy-to-understand booking system
- Practice basic web development concepts

User Roles
User
- View available tickets or seats
- Select one or more seats
- Confirm ticket selection
- View list of purchased seats
 
Application Features
- Display available seats
- Seat selection by users
- Store selected seats in the database
- Prevent booking the same seat twice
- Show list of purchased seats
- Simple and user-friendly interface

Technology Stack
- Frontend: HTML, CSS
- Backend: Python (Flask)
- Database: SQLite
- Version Control: Git & GitHub
- Tools: Pycharm

Project Structure:
online-ticket-booking-app/
├── app.py
├── README.md
├── requirements.txt
├── .gitignore
├── templates/
│ ├── index.html
│ ├── seats.html
│ └── booked.html
├── static/
│ └── style.css
└── database/
└── tickets.db

Input Validation:

This program validates user input when booking tickets:

Event Selection Validation

•	Must be a whole number.

•	Must match an available event (1–3).

•	Handles invalid input using try/except.

Ticket Quantity Validation

•	Must be a whole number.

•	Must be greater than 0.

•	Must not exceed available tickets.

•	Uses a custom exception class (InvalidTicketQuantityError).

Error Handling

•	Prevents program crashes.

•	Displays clear and user-friendly error messages.

•	Allows user to retry input until valid.





