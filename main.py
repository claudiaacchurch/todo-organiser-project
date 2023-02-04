from flask import Flask, render_template, flash, redirect, url_for, request, session, abort
from forms import LoginForm, HomeForm, SignupForm, TodoForm, TodayForm, ActionForm
from flask_bootstrap import Bootstrap
import os
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user
from datetime import datetime, time, date
from apscheduler.schedulers.background import BackgroundScheduler
from dateutil.relativedelta import relativedelta
from sqlalchemy.orm import relationship
from flask_moment import Moment
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash

basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
scheduler = BackgroundScheduler()
scheduler.start()
app.config['SQLALCHEMY_DATABASE_URI'] =\
        'sqlite:///' + os.path.join(basedir, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = "hellopythonusers"

db = SQLAlchemy(app)
moment = Moment(app)
Bootstrap(app)

today = datetime.now()

# Login Manager:
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    # NewList / ActionItem / TodayItem objects attached to each User
    user_lists = relationship("NewList", back_populates="list_author")
    user_actions = relationship("ActionItem", back_populates="action_author")
    user_today = relationship("TodayItem", back_populates="today_author")

    def __repr__(self):
        return f'<User {self.email}>'


class NewList(db.Model):
    __tablename__ = "lists"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    category = db.Column(db.String(200), default="other")
    type_list = db.Column(db.String(200), default=None)
    creation_time = db.Column(db.DateTime, nullable=False)
    # connection to ActionItems:
    actions = relationship("ActionItem", back_populates="list")
    # Create Foreign Key, "users.id"
    list_author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    # Create reference to the User object, the "user_lists" refers to the user_lists property in the User class
    list_author = relationship("User", back_populates="user_lists")

    def __init__(self, title, category, type_list, creation_time):
        self.title = title
        self.category = category
        self.type_list = type_list
        self.creation_time = creation_time


class ActionItem(db.Model):
    __tablename__ = "action_items"
    id = db.Column(db.Integer, primary_key=True)
    # create foreign key to NewList:
    list_id = db.Column(db.Integer, db.ForeignKey("lists.id"))
    action = db.Column(db.String(250), nullable=False)
    note = db.Column(db.String(250), default=None)
    reminder = db.Column(db.DateTime, default=None)
    complete = db.Column(db.Boolean, default=False)
    # connection to NewList:
    list = relationship("NewList", back_populates="actions")
    # Create Foreign Key, "users.id"
    action_author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    # Create reference to the User object, the "user_lists" refers to the user_lists property in the User class
    action_author = relationship("User", back_populates="user_actions")


class TodayItem(db.Model):
    __tablename__ = "today_items"
    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(250), nullable=False)
    note = db.Column(db.String(250), default=None)
    reminder = db.Column(db.DateTime)
    complete = db.Column(db.Boolean, default=False)
    # Create Foreign Key, "users.id"
    today_author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    # Create reference to the User object, the "user_lists" refers to the user_lists property in the User class
    today_author = relationship("User", back_populates="user_today")


db.create_all()
# db.drop_all()


def user_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            user_id = current_user.id
        except:
            user_id = 0

        if user_id:
            return f(*args, **kwargs)
        else:
            return abort(403)

    return decorated_function


@app.route("/", methods=["GET", "POST"])
def home():
    today_year = today.strftime("%Y")
    form = HomeForm()
    if form.validate_on_submit():
        email = form.email.data
        user = User.query.filter_by(email=email).first()
        if user:
            session['email'] = form.email.data
            return redirect(url_for("login", email=form.email.data))
        else:
            session['email'] = form.email.data
            return redirect(url_for("signup",  email=form.email.data))
    return render_template("index.html", form=form, year=today_year)


@app.route("/signup", methods=["GET", "POST"])
def signup():
    today_year = today.strftime("%Y")
    form = SignupForm()
    email = request.args.get("email")
    if email:
        form.email.data = email
    if form.validate_on_submit():
        hash_and_salted_password = generate_password_hash(
            form.password.data,
            method='pbkdf2:sha256',
            salt_length=8
        )
        new_user = User(
            email=form.email.data,
            password=hash_and_salted_password,
        )
        user = User.query.filter_by(email=new_user.email).first()
        if user:
            session['email'] = form.email.data
            flash('Email already registered, please login')
            return redirect(url_for('login', email=form.email.data))
        else:
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return redirect(url_for("todo"))
    return render_template("signup.html", form=form, year=today_year)


@app.route("/login", methods=["GET", "POST"])
def login():
    today_year = today.strftime("%Y")
    form = LoginForm()
    email = request.args.get("email")
    if email:
        form.email.data = email
    if request.method == "POST":
        email = form.email.data
        password = form.password.data
        user = User.query.filter_by(email=email).first()
        if not user:
            flash("Email isn't registered, sign up for a new account")
            return redirect(url_for("signup", email=form.email.data))
        elif not check_password_hash(user.password, password):
            flash("Password incorrect")
            return redirect(url_for("login", email=form.email.data))
        else:
            login_user(user)
            return redirect(url_for("todo"))
    return render_template("login.html", form=form, year=today_year)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route("/todo", methods=["GET", "POST"])
@user_only
def todo():
    user_lists = NewList.query.filter_by(list_author=current_user).all()
    user_actions = ActionItem.query.filter_by(action_author=current_user).order_by(ActionItem.reminder).all()
    user_today = TodayItem.query.filter_by(today_author=current_user).order_by(TodayItem.reminder).all()
    timestamp = datetime.now()
    one_week = timestamp + relativedelta(weeks=1)
    return render_template("todo.html", all_lists=user_lists, timestamp=timestamp,
                           today_item=user_today, one_week=one_week, actions=user_actions)


@app.route("/new_list", methods=["GET", "POST"])
@user_only
def new_list():
    form = TodoForm()
    today_item = datetime.now()
    if form.validate_on_submit():
        create_list = NewList(
            title=form.title.data,
            category=form.category.data,
            type_list=form.type_list.data,
            creation_time=today_item,
        )
        create_list.list_author_id = current_user.id
        db.session.add(create_list)
        db.session.commit()
        return redirect(url_for("todo"))
    return render_template("new_list.html", form=form)


@app.route("/new_today", methods=["GET", "POST"])
@user_only
def new_today():
    form = TodayForm()
    if form.validate_on_submit():
        hour = int(form.hour.data)
        minute = int(form.minute.data)
        now = datetime.now()
        today_list = TodayItem(
            action=form.action.data,
            note=form.note.data,
            reminder=datetime.combine(date.today(), time(hour, minute))
        )
        today_list.today_author_id = current_user.id
        db.session.add(today_list)
        db.session.commit()
        return redirect(url_for("todo"))
    return render_template("new_today.html", form=form)


@app.route("/new_action/<choice_id>", methods=["GET", "POST"])
@user_only
def new_action(choice_id):
    form = ActionForm()
    lists = NewList.query.all()
    selected_list = NewList.query.filter_by(id=choice_id).first()
    if form.validate_on_submit():
        day = int(form.day.data)
        month_name = "January"
        month_number = datetime.strptime(month_name, '%B').strftime('%m')
        month = int(month_number)
        hour = int(form.hour.data)
        minute = int(form.minute.data)
        time_object = time(hour, minute)
        date_object = date(date.today().year, month, day)
        new_action_item = ActionItem(
            list_id=selected_list.id,
            action=form.action.data,
            note=form.note.data,
            reminder=datetime.combine(date_object, time_object),
        )
        new_action_item.action_author_id = current_user.id
        db.session.add(new_action_item)
        db.session.commit()
        return redirect(url_for("todo"))
    return render_template("new_action.html", form=form, selected_list=selected_list, all_lists=lists)


@app.route("/delete/<int:list_id>")
@user_only
def delete_list(list_id):
    list_to_delete = NewList.query.get(list_id)
    db.session.delete(list_to_delete)
    db.session.commit()
    return redirect(url_for('todo'))


@app.route("/delete_action_item/<int:action_id>")
@user_only
def delete_action_item(action_id):
    action_to_delete = ActionItem.query.get(action_id)
    db.session.delete(action_to_delete)
    db.session.commit()
    return redirect(url_for('todo'))


@app.route("/delete_today/<int:item_id>")
@user_only
def delete_today(item_id):
    item_to_delete = TodayItem.query.get(item_id)
    db.session.delete(item_to_delete)
    db.session.commit()
    return redirect(url_for('todo'))


@app.route("/edit_action/<int:action_id>", methods=["GET", "POST"])
@user_only
def edit_action(action_id):
    action_item = ActionItem.query.filter_by(id=action_id).first()
    form = ActionForm(request.form, action=action_item.action, note=action_item.note, reminder=action_item.reminder)
    if form.validate_on_submit():
        day = int(form.day.data)
        month_name = "January"
        month_number = datetime.strptime(month_name, '%B').strftime('%m')
        month = int(month_number)
        hour = int(form.hour.data)
        minute = int(form.minute.data)
        time_object = time(hour, minute)
        date_object = date(date.today().year, month, day)
        action_item.action = form.action.data
        action_item.note = form.note.data
        action_item.reminder = datetime.combine(date_object, time_object)
        db.session.commit()
        return redirect(url_for('todo'))
    return render_template('edit_post.html', action_item=action_item, form=form)


@app.route("/edit_today/<item_id>", methods=["GET", "POST"])
@user_only
def edit_today(item_id):
    today_item = TodayItem.query.filter_by(id=item_id).first()
    form = TodayForm(request.form, action=today_item.action, note=today_item.note, reminder=today_item.reminder)
    if form.validate_on_submit():
        hour = int(form.hour.data)
        minute = int(form.minute.data)
        reminder_obj = datetime.combine(date.today(), time(hour, minute))
        today_item.action = form.action.data
        today_item.note = form.note.data
        today_item.reminder = reminder_obj
        db.session.commit()
        return redirect(url_for("todo"))
    return render_template("new_today.html", form=form, today_item=today_item)


@app.route("/complete_action/<int:action_id>")
@user_only
def complete_action(action_id):
    completed_action = ActionItem.query.filter_by(id=action_id).first()
    completed_action.complete = True
    db.session.commit()
    return redirect(url_for('todo'))


@app.route("/complete_item/<int:item_id>")
@user_only
def complete_item(item_id):
    completed_item = TodayItem.query.filter_by(id=item_id).first()
    completed_item.complete = True
    db.session.commit()
    return redirect(url_for('todo'))


if __name__ == '__main__':
    app.run(debug=True, port=5001)