from calendar import month_name
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, SelectField, RadioField
from wtforms.validators import DataRequired
from datetime import datetime

timestamp = datetime.now()


class HomeForm(FlaskForm):
    email = StringField("Enter user email:", validators=[DataRequired()])
    submit = SubmitField("Go to ToDo")


class LoginForm(FlaskForm):
    email = StringField("Email:", validators=[DataRequired()])
    password = PasswordField("Password:", validators=[DataRequired()])
    submit = SubmitField("Login")


class SignupForm(FlaskForm):
    email = StringField("Email:", validators=[DataRequired()])
    password = PasswordField("Password:", validators=[DataRequired()])
    submit = SubmitField("Sign up")


class TodoForm(FlaskForm):
    title = StringField("Title:", validators=[DataRequired()])
    category = SelectField("Category:", choices=["Work", "Personal", "Social", "Finance", "Other"])
    type_list = SelectField("Type:", choices=["Daily", "Weekly", "Other"])
    submit = SubmitField("Add")


class TodayForm(FlaskForm):
    action = StringField("Action:", validators=[DataRequired()])
    note = StringField("Notes:")
    hours = [("", "Hour")] + [(str(i), str(i)) for i in range(24)]
    hour = SelectField("Time:", choices=hours, default="23")
    minutes = [("", "Minute")] + [(str(i), str(i)) for i in range(60)]
    minute = SelectField("Minute:", choices=minutes, default="59")
    submit = SubmitField("Add")


class ActionForm(FlaskForm):
    action = StringField("Action:", validators=[DataRequired()])
    note = StringField("Notes:")
    days = [("", "Day")] + [(str(i), str(i)) for i in range(1, 32)]
    day = SelectField("Day", choices=days, render_kw={'class': 'my-class'}, default=timestamp.strftime('%d'))
    months = [("", "Month")] + [(month_name[i], month_name[i]) for i in range(1, 13)]
    month = SelectField("Month", choices=months, render_kw={'class': 'my-class'}, default=timestamp.strftime('%B'))
    hours = [("", "Hour")] + [(str(i), str(i)) for i in range(24)]
    hour = SelectField("Hour", choices=hours, render_kw={'class': 'my-class'}, default=timestamp.strftime('%H'))
    minutes = [("", "Minute")] + [(str(i), str(i)) for i in range(60)]
    minute = SelectField("Minute", choices=minutes, render_kw={'class': 'my-class'}, default=timestamp.strftime('%M'))
    submit = SubmitField("Add")
