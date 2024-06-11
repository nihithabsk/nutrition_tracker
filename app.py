from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:root@localhost/nutrify'
app.config['SECRET_KEY'] = '3d6f45a5fc12445dbac2f59c3b6c7cb1'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(150), nullable=False)
    daily_calories = db.Column(db.Float, default=0.0)
    activities = db.relationship('UserActivity', backref='user', lazy=True)

class FoodItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    calories_per_unit = db.Column(db.Float, nullable=False)

class UserActivity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=date.today)
    food_name = db.Column(db.String(150), nullable=False)
    quantity = db.Column(db.Float, nullable=False)

    def calories_consumed(self):
        food_item = FoodItem.query.filter_by(name=self.food_name).first()
        if food_item:
            return food_item.calories_per_unit * self.quantity
        return 0.0


@app.route('/')
def index():
    user_id = session.get('user_id')
    daily_calories = None
    if user_id:
        user = User.query.get(user_id)
        daily_calories = user.daily_calories
    return render_template('index.html', daily_calories=daily_calories)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return render_template('register.html', error='Username already exists.')

        new_user = User(username=username, password=hashed_password)
        try:
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('login'))
        except IntegrityError:
            db.session.rollback()
            return render_template('register.html', error='An error occurred. Please try again.')
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':  
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/add_food', methods=['GET', 'POST'])
def add_food():
    food_calories = None
    user_id = session.get('user_id')
    
    if request.method == 'POST' and user_id:
        food_name = request.form['food_name']
        quantity = float(request.form['quantity'])
        food_item = FoodItem.query.filter_by(name=food_name).first()

        if food_item:
            food_calories = food_item.calories_per_unit * quantity
            user = User.query.get(user_id)
            user.daily_calories += food_calories
            activity = UserActivity(user_id=user_id, food_name=food_name, quantity=quantity)
            db.session.add(activity)
            db.session.commit()
        return render_template('add_food.html', food_calories=food_calories, quantity=quantity, food_name=food_name, activities=UserActivity.query.filter_by(user_id=user_id).all())
    
    if user_id:
        activities = UserActivity.query.filter_by(user_id=user_id).all()
        return render_template('add_food.html', activities=activities)
    
    return redirect(url_for('login'))


@app.route('/history')
def history():
    user_id = session.get('user_id')
    if user_id:
        user = User.query.get(user_id)
        activities = UserActivity.query.filter_by(user_id=user_id).order_by(UserActivity.date.desc()).all()
        
        daily_calories = {}
        for activity in activities:
            if activity.date not in daily_calories:
                daily_calories[activity.date] = 0
            daily_calories[activity.date] += activity.calories_consumed()

        return render_template('history.html', activities=activities, daily_calories=daily_calories)
    return redirect(url_for('index'))


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))
@app.route('/edit_food/<int:food_id>', methods=['GET', 'POST'])
def edit_food(food_id):
    food_item = FoodItem.query.get(food_id)
    if request.method == 'POST':
        food_item.name = request.form['food_name']
        food_item.calories_per_unit = float(request.form['calories_per_unit'])
        db.session.commit()
        return redirect(url_for('add_food'))
    return render_template('edit_food.html', food_item=food_item)

@app.route('/delete_food/<int:food_id>', methods=['POST'])
def delete_food(food_id):
    food_item = FoodItem.query.get(food_id)
    db.session.delete(food_item)
    db.session.commit()
    return redirect(url_for('add_food'))
@app.route('/edit_activity/<int:activity_id>', methods=['GET', 'POST'])
def edit_activity(activity_id):
    activity = UserActivity.query.get(activity_id)
    if request.method == 'POST' and activity.user_id == session.get('user_id'):
        new_quantity = float(request.form['quantity'])
        food_item = FoodItem.query.filter_by(name=activity.food_name).first()
        if food_item:
            calories_difference = food_item.calories_per_unit * (new_quantity - activity.quantity)
            user = User.query.get(activity.user_id)
            user.daily_calories += calories_difference
            activity.quantity = new_quantity
            db.session.commit()
        return redirect(url_for('add_food'))
    return render_template('edit_activity.html', activity=activity)

@app.route('/delete_activity/<int:activity_id>', methods=['POST'])
def delete_activity(activity_id):
    activity = UserActivity.query.get(activity_id)
    if activity.user_id == session.get('user_id'):
        food_item = FoodItem.query.filter_by(name=activity.food_name).first()
        if food_item:
            user = User.query.get(activity.user_id)
            user.daily_calories -= food_item.calories_per_unit * activity.quantity
            db.session.delete(activity)
            db.session.commit()
    return redirect(url_for('add_food'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
