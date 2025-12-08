from flask import Blueprint, render_template, session, redirect, url_for, flash

mood_calendar_bp = Blueprint('mood_calendar', __name__)

@mood_calendar_bp.route("/mood_calendar")
def mood_calendar():
    now = datetime.now()
    year = now.year
    month = now.month
    month_name = now.strftime("%B")
    
    cal_data = calendar.monthcalendar(year, month)
    return render_template("mood_calendar.html",
                            year=year,
                            month_name=month_name,
                            calendar=cal_data,
                            mood_data=mock_mood_data
    )