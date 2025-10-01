# TodoList Web Application

A simple and intuitive web-based todo list application built with Flask. Manage your tasks and events with a clean, user-friendly interface.

## Features

- **User Authentication**: Secure login and registration system
- **Task Management**: Add, edit, complete, and delete tasks with priority levels
- **Calendar Views**: 
  - Daily task view
  - Weekly schedule view
  - Agenda view for upcoming events
- **Event Scheduling**: Create and manage timed events with recurring options
- **Responsive Design**: Works on desktop and mobile devices
- **Priority System**: Organize tasks by priority levels
- **Recurring Tasks/Events**: Set up daily, weekly, or custom recurring items

## Tech Stack

- **Backend**: Flask (Python)
- **Database**: SQLite with SQLAlchemy ORM
- **Frontend**: HTML, CSS, JavaScript
- **Authentication**: Flask-Login
- **Email**: Flask-Mail for notifications

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Tamanna-2100/todolist.git
   cd todolist
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Initialize the database:
   ```bash
   python init_db.py
   ```

5. Run the application:
   ```bash
   python app.py
   ```

6. Open your browser and go to `http://127.0.0.1:5001`

## Usage

1. Register a new account or login
2. Add tasks from the daily view
3. Schedule events using the weekly view
4. View upcoming items in the agenda
5. Mark tasks as complete when done

## Configuration

Update `config.py` with your email settings for notifications (optional).

---

*Built with ❤️ using Flask*
