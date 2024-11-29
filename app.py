from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///travelbuddy.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User Model with enhanced profile
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    
    # Basic Info
    name = db.Column(db.String(100))
    age = db.Column(db.Integer)
    gender = db.Column(db.String(20))
    interests = db.Column(db.String(500))
    
    # Travel Preferences
    preferred_destinations = db.Column(db.String(500))
    budget_range = db.Column(db.String(50))
    travel_style = db.Column(db.String(100))  # adventure, leisure, cultural
    current_city = db.Column(db.String(100))
    
    # Safety Features
    is_verified = db.Column(db.Boolean, default=False)
    emergency_contact = db.Column(db.String(200))
    
    # Relationships
    trips = db.relationship('Trip', backref='traveler', lazy=True)
    blocked_users = db.relationship('BlockedUser', 
                                  foreign_keys='BlockedUser.user_id',
                                  backref=db.backref('blocker', lazy=True),
                                  lazy=True)
    blocked_by = db.relationship('BlockedUser',
                               foreign_keys='BlockedUser.blocked_user_id',
                               backref=db.backref('blocked', lazy=True),
                               lazy=True)

# Trip Model with enhanced features
class Trip(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    destination = db.Column(db.String(120), nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Trip Details
    accommodation = db.Column(db.String(500))
    transport_details = db.Column(db.String(500))
    itinerary = db.Column(db.Text)
    total_budget = db.Column(db.Float)
    
    # Relationships
    expenses = db.relationship('Expense', backref='trip', lazy=True)
    participants = db.relationship('TripParticipant', backref='trip', lazy=True)
    activities = db.relationship('TripActivity', backref='trip', lazy=True, order_by='TripActivity.day,TripActivity.time')
    transport = db.relationship('TransportDetail', backref='trip', lazy=True)

# Trip Activity Model
class TripActivity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    trip_id = db.Column(db.Integer, db.ForeignKey('trip.id'), nullable=False)
    day = db.Column(db.Integer, nullable=False)
    time = db.Column(db.String(10))
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    location = db.Column(db.String(200))
    cost = db.Column(db.Float)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))

# Transport Details Model
class TransportDetail(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    trip_id = db.Column(db.Integer, db.ForeignKey('trip.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    mode = db.Column(db.String(50))  # flight, train, bus, car
    cost = db.Column(db.Float)
    details = db.Column(db.String(500))  # ticket numbers, timings, etc.

# Expense Tracking
class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    trip_id = db.Column(db.Integer, db.ForeignKey('trip.id'), nullable=False)
    description = db.Column(db.String(200))
    amount = db.Column(db.Float, nullable=False)
    paid_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    date = db.Column(db.DateTime, default=datetime.utcnow)
    category = db.Column(db.String(50))  # accommodation, transport, food, etc.

# Trip Participants
class TripParticipant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    trip_id = db.Column(db.Integer, db.ForeignKey('trip.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20))  # pending, accepted, rejected

# Blocked Users for Safety
class BlockedUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    blocked_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    reason = db.Column(db.String(200))
    date = db.Column(db.DateTime, default=datetime.utcnow)

# Destination Recommendations
class Destination(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    must_visit_places = db.Column(db.Text)
    local_cuisines = db.Column(db.Text)
    events = db.Column(db.Text)
    activities = db.Column(db.Text)
    best_time_to_visit = db.Column(db.String(200))
    average_cost = db.Column(db.Float)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('register'))
        
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful!')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    trips = Trip.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', trips=trips)

@app.route('/create_trip', methods=['GET', 'POST'])
@login_required
def create_trip():
    if request.method == 'POST':
        # Convert date strings to datetime objects
        start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d')
        end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d')
        
        trip = Trip(
            destination=request.form.get('destination'),
            start_date=start_date,
            end_date=end_date,
            user_id=current_user.id,
            accommodation=request.form.get('accommodation'),
            transport_details=request.form.get('transport_details'),
            itinerary=request.form.get('itinerary'),
            total_budget=request.form.get('total_budget', type=float)
        )
        db.session.add(trip)
        db.session.commit()
        flash('Trip created successfully!')
        return redirect(url_for('dashboard'))
    
    return render_template('create_trip.html')

@app.route('/trip/<int:trip_id>')
@login_required
def trip_details(trip_id):
    trip = Trip.query.get_or_404(trip_id)
    return render_template('trip_details.html', trip=trip)

@app.route('/trip/<int:trip_id>/add_expense', methods=['POST'])
@login_required
def add_expense(trip_id):
    trip = Trip.query.get_or_404(trip_id)
    if request.method == 'POST':
        expense = Expense(
            trip_id=trip.id,
            description=request.form.get('description'),
            amount=float(request.form.get('amount')),
            category=request.form.get('category'),
            paid_by=current_user.id
        )
        db.session.add(expense)
        db.session.commit()
        flash('Expense added successfully!')
    return redirect(url_for('trip_details', trip_id=trip.id))

@app.route('/trip/<int:trip_id>/invite', methods=['POST'])
@login_required
def invite_buddies(trip_id):
    trip = Trip.query.get_or_404(trip_id)
    if trip.user_id != current_user.id:
        flash('You are not authorized to invite users to this trip.')
        return redirect(url_for('trip_details', trip_id=trip.id))
    
    selected_users = request.form.getlist('selected_users[]')
    for user_id in selected_users:
        if not TripParticipant.query.filter_by(trip_id=trip.id, user_id=user_id).first():
            participant = TripParticipant(
                trip_id=trip.id,
                user_id=int(user_id),
                status='pending'
            )
            db.session.add(participant)
    
    db.session.commit()
    flash('Invitations sent successfully!')
    return redirect(url_for('trip_details', trip_id=trip.id))

@app.route('/api/search_users')
@login_required
def search_users():
    query = request.args.get('q', '')
    if len(query) < 2:
        return jsonify([])
    
    users = User.query.filter(
        User.id != current_user.id,
        User.name.ilike(f'%{query}%')
    ).limit(5).all()
    
    return jsonify([{
        'id': user.id,
        'name': user.name,
        'current_city': user.current_city
    } for user in users])

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user)

@app.route('/profile/<int:user_id>')
@login_required
def view_profile(user_id):
    user = User.query.get_or_404(user_id)
    return render_template('profile.html', user=user)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/trip/<int:trip_id>/plan')
@login_required
def plan_trip(trip_id):
    trip = Trip.query.get_or_404(trip_id)
    
    # Calculate expenses by category
    expenses_by_category = {}
    total_expenses = sum(expense.amount for expense in trip.expenses)
    
    for category in ['accommodation', 'transport', 'food', 'activities']:
        category_sum = sum(expense.amount for expense in trip.expenses if expense.category == category)
        expenses_by_category[category] = category_sum
        
    # Calculate expense percentages
    expense_percentages = {
        category: (amount / total_expenses * 100) if total_expenses > 0 else 0
        for category, amount in expenses_by_category.items()
    }
    
    # Organize activities by day
    trip_days = (trip.end_date - trip.start_date).days + 1
    itinerary = []
    
    for day in range(trip_days):
        current_date = trip.start_date + timedelta(days=day)
        day_activities = [
            activity for activity in trip.activities
            if activity.day == day + 1
        ]
        itinerary.append({
            'date': current_date,
            'activities': day_activities
        })
    
    # Get destination information
    destination = Destination.query.filter_by(name=trip.destination).first()
    
    return render_template('plan_trip.html',
                         trip=trip,
                         itinerary=itinerary,
                         destination=destination,
                         expenses_by_category=expenses_by_category,
                         expense_percentages=expense_percentages)

@app.route('/trip/<int:trip_id>/activity', methods=['POST'])
@login_required
def add_activity(trip_id):
    trip = Trip.query.get_or_404(trip_id)
    
    activity = TripActivity(
        trip_id=trip.id,
        day=int(request.form.get('day')),
        time=request.form.get('time'),
        title=request.form.get('title'),
        description=request.form.get('description'),
        location=request.form.get('location'),
        cost=float(request.form.get('cost')) if request.form.get('cost') else None,
        created_by=current_user.id
    )
    
    db.session.add(activity)
    db.session.commit()
    flash('Activity added to itinerary!')
    return redirect(url_for('plan_trip', trip_id=trip.id))

@app.route('/trip/<int:trip_id>/transport', methods=['POST'])
@login_required
def update_transport(trip_id):
    trip = Trip.query.get_or_404(trip_id)
    
    # Update transport details for each participant
    for participant in trip.participants:
        user_id = participant.user.id
        transport = TransportDetail.query.filter_by(
            trip_id=trip.id,
            user_id=user_id
        ).first() or TransportDetail(trip_id=trip.id, user_id=user_id)
        
        transport.mode = request.form.get(f'transport_mode_{user_id}')
        transport.cost = float(request.form.get(f'transport_cost_{user_id}')) if request.form.get(f'transport_cost_{user_id}') else None
        transport.details = request.form.get(f'transport_details_{user_id}')
        
        if not transport.id:
            db.session.add(transport)
    
    db.session.commit()
    flash('Transport details updated!')
    return redirect(url_for('plan_trip', trip_id=trip.id))

if __name__ == '__main__':
    with app.app_context():
        # Drop all tables and recreate them
        db.drop_all()
        db.create_all()
        print("Database tables created successfully!")
    app.run(host='0.0.0.0', port=5000, debug=True)
