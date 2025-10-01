from flask import Flask, render_template, request, redirect, url_for, flash, abort, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime, date, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import random
from flask_mail import Mail, Message
from sqlalchemy import or_

app = Flask(__name__)
app.config.from_pyfile('config.py')

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Initialize Flask-Mail
mail = Mail(app)

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    tasks = db.relationship('Task', backref='user', lazy=True)
    events = db.relationship('Event', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    date = db.Column(db.Date, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_recurring = db.Column(db.Boolean, default=False)
    recurrence = db.Column(db.String(20))
    priority = db.Column(db.Integer, default=2)

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    is_all_day = db.Column(db.Boolean, default=False)
    frequency = db.Column(db.String(20))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    original_event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=True)

# user_loader callback
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Context processor to make current_date available to all templates
@app.context_processor
def inject_current_date():
    return {'current_date': date.today()}

# Routes
@app.route('/')
@login_required
def index():
    today = date.today()
    return redirect(url_for('daily_tasks', date_str=today.strftime('%Y-%m-%d')))

@app.route('/tasks/<date_str>')
@login_required
def daily_tasks(date_str):
    try:
        task_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        task_date = date.today()
    
    tasks = Task.query.filter_by(user_id=current_user.id, date=task_date).all()
    return render_template('tasks/daily.html', tasks=tasks, current_date=task_date)

@app.route('/calendar')
@login_required
def calendar():
    current_month = date.today()
    return render_template('tasks/calendar.html', current_month=current_month)

# Schedule views
@app.route('/schedule/<view_type>')
@login_required
def schedule_view(view_type):
    # Get the date from query parameter or use today
    date_str = request.args.get('date')
    if date_str:
        try:
            current_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            current_date = date.today()
    else:
        current_date = date.today()
    
    if view_type == 'schedule':
        # Calculate week start (Sunday)
        start_date = current_date - timedelta(days=(current_date.weekday() + 1) % 7)
        end_date = start_date + timedelta(days=6)
        
        # Prepare days data
        days = []
        for i in range(7):
            day_date = start_date + timedelta(days=i)
            day_events = Event.query.filter(
                Event.user_id == current_user.id,
                Event.date == day_date
            ).all()
            
            # Separate all-day and timed events
            all_day_events = [e for e in day_events if e.is_all_day]
            timed_events = []
            
            for event in day_events:
                if not event.is_all_day:
                    # Calculate position and height for timed events
                    start_minutes = event.start_time.hour * 60 + event.start_time.minute
                    end_minutes = event.end_time.hour * 60 + event.end_time.minute
                    duration_minutes = end_minutes - start_minutes
                    
                    timed_events.append({
                        'id': event.id,
                        'title': event.title,
                        'start_time': event.start_time.strftime('%I:%M %p').lstrip('0'),
                        'end_time': event.end_time.strftime('%I:%M %p').lstrip('0'),
                        'start_position': (start_minutes / 60) * 60,
                        'duration': (duration_minutes / 60) * 60
                    })
            
            days.append({
                'name': day_date.strftime('%a'),
                'date': day_date,
                'all_day_events': all_day_events,
                'timed_events': timed_events
            })
        
        return render_template('tasks/schedule.html', 
                             view_type=view_type,
                             start_date=start_date,
                             end_date=end_date,
                             days=days)
    
    elif view_type == 'agenda':
        events = Event.query.filter(
            Event.user_id == current_user.id,
            Event.date >= current_date,
            Event.date <= current_date + timedelta(days=30)
        ).order_by(Event.date, Event.start_time).all()
        
        return render_template('tasks/agenda.html', 
                             view_type=view_type,
                             events=events,
                             current_date=current_date)
    
    return redirect(url_for('schedule_view', view_type='schedule'))

@app.route('/add_event', methods=['POST'])
@login_required
def add_event():
    title = request.form.get('title')
    date_str = request.form.get('date')
    start_time_str = request.form.get('start_time')
    end_time_str = request.form.get('end_time')
    frequency = request.form.get('frequency', 'none')
    is_all_day = request.form.get('is_all_day') == 'on'
    
    try:
        event_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        start_time = datetime.strptime(start_time_str, '%H:%M').time()
        end_time = datetime.strptime(end_time_str, '%H:%M').time()
    except ValueError:
        flash('Invalid date or time format', 'error')
        return redirect(request.referrer or url_for('schedule_view', view_type='schedule'))
    
    # Create the main event
    new_event = Event(
        title=title,
        date=event_date,
        start_time=start_time,
        end_time=end_time,
        is_all_day=is_all_day,
        frequency=frequency,
        user_id=current_user.id
    )
    
    db.session.add(new_event)
    db.session.flush()  # Get the ID without committing
    
    # Create recurring events if enabled
    if frequency != 'none':
        recurring_events = create_recurring_events(new_event, frequency)
        for event in recurring_events:
            db.session.add(event)
    
    db.session.commit()
    
    flash('Event added successfully', 'success')
    return redirect(url_for('schedule_view', view_type='schedule'))

def create_recurring_events(original_event, frequency):
    """Create recurring events based on the frequency pattern"""
    events = []
    start_date = original_event.date
    
    if frequency == 'daily':
        # Create events for next 365 days
        for i in range(1, 366):
            event_date = start_date + timedelta(days=i)
            events.append(Event(
                title=original_event.title,
                date=event_date,
                start_time=original_event.start_time,
                end_time=original_event.end_time,
                is_all_day=original_event.is_all_day,
                frequency=frequency,
                user_id=original_event.user_id,
                original_event_id=original_event.id
            ))
    
    elif frequency == 'weekly':
        # Create events for same day of week for next 52 weeks
        for i in range(1, 53):
            event_date = start_date + timedelta(weeks=i)
            events.append(Event(
                title=original_event.title,
                date=event_date,
                start_time=original_event.start_time,
                end_time=original_event.end_time,
                is_all_day=original_event.is_all_day,
                frequency=frequency,
                user_id=original_event.user_id,
                original_event_id=original_event.id
            ))
    
    elif frequency == 'weekday':
        # Create events for every weekday (Mon-Fri) for next 3 months
        for i in range(1, 91):  # 90 days = about 3 months
            event_date = start_date + timedelta(days=i)
            if event_date.weekday() < 5:  # 0-4 = Monday-Friday
                events.append(Event(
                    title=original_event.title,
                    date=event_date,
                    start_time=original_event.start_time,
                    end_time=original_event.end_time,
                    is_all_day=original_event.is_all_day,
                    frequency=frequency,
                    user_id=original_event.user_id,
                    original_event_id=original_event.id
                ))
    
    elif frequency in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']:
        # Map day names to weekday numbers (0=Monday, 6=Sunday)
        day_map = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
            'friday': 4, 'saturday': 5, 'sunday': 6
        }
        target_weekday = day_map[frequency]
        
        # Create events for the specific day of week for next 12 weeks
        for i in range(1, 85):  # 12 weeks * 7 days = 84 days
            event_date = start_date + timedelta(days=i)
            if event_date.weekday() == target_weekday:
                events.append(Event(
                    title=original_event.title,
                    date=event_date,
                    start_time=original_event.start_time,
                    end_time=original_event.end_time,
                    is_all_day=original_event.is_all_day,
                    frequency=frequency,
                    user_id=original_event.user_id,
                    original_event_id=original_event.id
                ))
    
    return events

@app.route('/delete_event_series/<int:event_id>')
@login_required
def delete_event_series(event_id):
    event = Event.query.get_or_404(event_id)
    if event.user_id != current_user.id:
        abort(403)
    
    # If it's part of a recurring series, delete all events in the series
    if event.original_event_id:
        # This is a recurring event - delete all events with this original_event_id
        Event.query.filter(
            Event.user_id == current_user.id,
            Event.original_event_id == event.original_event_id
        ).delete()
    else:
        # This is the original event - delete it and all its recurrences
        Event.query.filter(
            Event.user_id == current_user.id,
            or_(
                Event.id == event.id,
                Event.original_event_id == event.id
            )
        ).delete()
    
    db.session.commit()
    flash('Event series deleted successfully', 'success')
    return redirect(request.referrer or url_for('schedule_view', view_type='schedule'))

@app.route('/delete_event/<int:event_id>')
@login_required
def delete_event(event_id):
    event = Event.query.get_or_404(event_id)
    if event.user_id != current_user.id:
        abort(403)
    
    db.session.delete(event)
    db.session.commit()
    flash('Event deleted successfully', 'success')
    return redirect(request.referrer or url_for('schedule_view', view_type='schedule'))

@app.route('/add_task', methods=['POST'])
@login_required
def add_task():
    content = request.form.get('content')
    date_str = request.form.get('date')
    is_recurring = request.form.get('is_recurring') == 'on'
    recurrence = request.form.get('recurrence')
    priority = request.form.get('priority', 2, type=int)
    
    try:
        task_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else date.today()
    except ValueError:
        task_date = date.today()
    
    # Create the main task
    new_task = Task(
        content=content,
        date=task_date,
        user_id=current_user.id,
        is_recurring=is_recurring,
        recurrence=recurrence if is_recurring else None,
        priority=priority
    )
    
    db.session.add(new_task)
    
    # Create recurring tasks if enabled
    if is_recurring and recurrence:
        recurring_tasks = create_recurring_tasks(content, task_date, recurrence, current_user.id, priority)
        for task in recurring_tasks:
            db.session.add(task)
    
    db.session.commit()
    
    return redirect(request.referrer or url_for('index'))

def create_recurring_tasks(content, start_date, recurrence, user_id, priority):
    """Create recurring tasks based on the recurrence pattern"""
    tasks = []
    
    if recurrence == 'daily':
        for i in range(1, 366):
            task_date = start_date + timedelta(days=i)
            tasks.append(Task(
                content=content,
                date=task_date,
                user_id=user_id,
                is_recurring=True,
                recurrence=recurrence,
                priority=priority
            ))
    
    elif recurrence == 'weekly':
        for i in range(1, 53):
            task_date = start_date + timedelta(weeks=i)
            tasks.append(Task(
                content=content,
                date=task_date,
                user_id=user_id,
                is_recurring=True,
                recurrence=recurrence,
                priority=priority
            ))
    
    elif recurrence == 'monthly':
        for i in range(1, 13):
            next_month = start_date.month + i
            next_year = start_date.year
            if next_month > 12:
                next_month -= 12
                next_year += 1
            
            try:
                task_date = date(next_year, next_month, start_date.day)
            except ValueError:
                task_date = date(next_year, next_month, 1) + timedelta(days=-1)
            
            tasks.append(Task(
                content=content,
                date=task_date,
                user_id=user_id,
                is_recurring=True,
                recurrence=recurrence,
                priority=priority
            ))
    
    elif recurrence == 'yearly':
        for i in range(1, 6):
            task_date = date(start_date.year + i, start_date.month, start_date.day)
            tasks.append(Task(
                content=content,
                date=task_date,
                user_id=user_id,
                is_recurring=True,
                recurrence=recurrence,
                priority=priority
            ))
    
    return tasks

@app.route('/toggle_task/<int:task_id>')
@login_required
def toggle_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.id:
        abort(403)
    
    task.completed = not task.completed
    db.session.commit()
    return jsonify({'success': True, 'completed': task.completed})

@app.route('/update_task_priority/<int:task_id>', methods=['POST'])
@login_required
def update_task_priority(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.id:
        abort(403)
    
    new_priority = request.json.get('priority')
    if new_priority in [1, 2, 3]:
        task.priority = new_priority
        db.session.commit()
        return jsonify({'success': True})
    
    return jsonify({'success': False, 'message': 'Invalid priority'})

@app.route('/move_task_tomorrow/<int:task_id>')
@login_required
def move_task_tomorrow(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.id:
        abort(403)
    
    task.date = date.today() + timedelta(days=1)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/delete_task_completely/<int:task_id>')
@login_required
def delete_task_completely(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.id:
        abort(403)
    
    if task.is_recurring:
        Task.query.filter(
            Task.user_id == current_user.id,
            Task.content == task.content,
            Task.date >= task.date
        ).delete()
    else:
        db.session.delete(task)
    
    db.session.commit()
    return jsonify({'success': True})

# Email verification routes
@app.route('/send_verification_code', methods=['POST'])
@login_required
def send_verification_code():
    data = request.json
    verification_type = data.get('type', 'email_change')
    verification_code = str(random.randint(100000, 999999))
    
    session[f'{verification_type}_code'] = verification_code
    
    try:
        msg = Message('Verification Code',
                      sender=app.config['MAIL_USERNAME'],
                      recipients=[current_user.email])
        msg.body = f'Your verification code for {verification_type.replace("_", " ")} is: {verification_code}\n\nThis code will expire in 10 minutes.'
        mail.send(msg)
        return jsonify({'success': True, 'message': 'Verification code sent!'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Failed to send email: {str(e)}'})

@app.route('/verify_email_change', methods=['POST'])
@login_required
def verify_email_change():
    data = request.json
    code = data.get('code')
    new_email = data.get('new_email')
    
    if code == session.get('email_change_code'):
        if User.query.filter_by(email=new_email).first():
            return jsonify({'success': False, 'message': 'Email already exists'})
        
        current_user.email = new_email
        db.session.commit()
        
        session.pop('email_change_code', None)
        
        return jsonify({'success': True, 'message': 'Email updated successfully!'})
    else:
        return jsonify({'success': False, 'message': 'Invalid verification code'})

@app.route('/verify_password_change', methods=['POST'])
@login_required
def verify_password_change():
    data = request.json
    code = data.get('code')
    new_password = data.get('new_password')
    
    if code == session.get('password_change_code'):
        current_user.set_password(new_password)
        db.session.commit()
        
        session.pop('password_change_code', None)
        
        return jsonify({'success': True, 'message': 'Password updated successfully!'})
    else:
        return jsonify({'success': False, 'message': 'Invalid verification code'})

# Auth routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        
        user = User.query.filter_by(email=email).first()
        
        if not user or not user.check_password(password):
            flash('Invalid email or password', 'error')
            return redirect(url_for('login'))
        
        login_user(user, remember=remember)
        return redirect(url_for('index'))
    
    return render_template('auth/login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'error')
            return redirect(url_for('register'))
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return redirect(url_for('register'))
        
        new_user = User(username=username, email=email)
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Account created successfully! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('auth/register.html')

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        
        if username and username != current_user.username:
            if User.query.filter_by(username=username).first():
                flash('Username already exists', 'error')
            else:
                current_user.username = username
                flash('Username updated successfully', 'success')
        
        if email and email != current_user.email:
            if User.query.filter_by(email=email).first():
                flash('Email already exists', 'error')
            else:
                current_user.email = email
                flash('Email updated successfully', 'success')
        
        db.session.commit()
        return redirect(url_for('profile'))
    
    return render_template('profile.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True, port=5001)