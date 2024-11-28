import random
from datetime import datetime
import smtplib
import mysql.connector
import re
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from flask import Flask, render_template, url_for, request, current_app as app, redirect, session, jsonify, flash
from DBConnection import Db

app = Flask(__name__)
app.secret_key="123"

app.config['DB_HOST'] = 'localhost'  # Database Host
app.config['DB_USER'] = 'werego_user'  # Your MySQL username
app.config['DB_PASSWORD'] = 'password123'  # Your MySQL password
app.config['DB_NAME'] = 'ev_db'

class Db:
    def __init__(self):
        self.conn = mysql.connector.connect(
            host=app.config['DB_HOST'],
            user=app.config['DB_USER'],
            password=app.config['DB_PASSWORD'],
            database=app.config['DB_NAME']
        )
        self.cursor = self.conn.cursor(dictionary=True)

    def select(self, query, params=None):
        self.cursor.execute(query, params or ())
        return self.cursor.fetchall()

    def selectOne(self, query, params=None):
        self.cursor.execute(query, params or ())
        return self.cursor.fetchone()

    def insert(self, query, params=None):
        self.cursor.execute(query, params or ())
        self.conn.commit()
        return self.cursor.lastrowid

    def delete(self, query, params=None):
        self.cursor.execute(query, params or ())
        self.conn.commit()

    def update(self, query, params=None):
        self.cursor.execute(query, params or ())
        self.conn.commit()

    def close(self):
        self.cursor.close()
        self.conn.close()


#//////////////////////////////////////////////////////////////COMMON/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/find_your_charger')
def find_your_charger():
    return render_template('find_your_charger.html')

@app.route('/about')
def about():
    return render_template('about.html')




@app.route('/contact_us', methods=['GET', 'POST'])
def contact_us():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        feedback = request.form['message']
        db = Db()
        sql = db.insert("INSERT INTO contact_us (Name, Email, feedback_date, feedback) VALUES (%s, %s, NOW(), %s)", (name, email, feedback))
        return render_template('contact_us.html', message='Thank you for your feedback!')
    else:
        return render_template('contact_us.html')





@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == "POST":
        # Validate email input
        email = request.form.get('email', '').strip()
        if not email:
            return "Email is required", 400
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            return "Invalid email format", 400

        # Check if email exists in database
        db = Db()
        user = db.selectOne("SELECT * FROM login WHERE email=%s", (email,))
        if not user:
            return "Sorry, we couldn't find an account associated with that email address.", 400

        # Send email with password reset instructions or link
        password = user['password']
        sender_email = "26ansel@gmail.com"
        sender_password = "robo99501"
        recipient_email = email
        subject = "Password Reset for EV STATION BOOKING WEBSITE"
        content = "Your password for EV STATION BOOKING WEBSITE has been reset. Please login with your new password."
        host = "smtp.gmail.com"
        port = 465
        message = MIMEMultipart()
        message['From'] = sender_email
        message['To'] = recipient_email
        message['Subject'] = subject
        message.attach(MIMEText(content, 'plain', 'utf-8'))
        
        try:
            with smtplib.SMTP_SSL(host, port) as server:            
                server.login(sender_email, sender_password)
                server.sendmail(sender_email, recipient_email, message.as_string())
                return "An email has been sent to your email address with instructions on how to reset your password."
        except smtplib.SMTPAuthenticationError:
            return "Failed to authenticate with the email server. Please check your email credentials.", 500
        except smtplib.SMTPException as e:
            return f"An error occurred while sending the email: {str(e)}", 500

    return render_template("forgot_password.html")








@app.route('/login',methods=['GET', 'POST'])
def login():
    if  'user_type' in session and session['user_type'] == "admin":
        return redirect('/admin-home')

    if request.method == "POST":
        print('form ', request.form)
        username = request.form['username']
        password = request.form['password']
        db = Db()
        ss = db.selectOne("select * from login where username='" + username + "'and password='" + password + "'")
        if ss is not None:
            session['head'] = ""
            session['username'] = username # set the username key in the session
            if ss['usertype'] == 'admin':
                session['user_type'] = 'admin'
                return redirect('/admin-home')

            elif ss['usertype'] == 'user':
                session['user_type'] = 'user'
                session['uid'] = ss['login_id']
                return redirect('/user-dashboard')
            else:
                return '''<script>alert('user not found');window.location="/login"</script>'''
        else:
            return '''<script>alert('user not found');window.location="/login"</script>'''
    return render_template("login.html")


@app.route('/logout')
def logout():
    session.pop('username',None)
    session.pop('user_type',None)
    session.pop('log',None)
    session.pop('usertype',None)

    return redirect('/login')



    # =========================

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == "POST":
        username = request.form['signupUsername']
        email = request.form['email']
        password = request.form['password']
        confirmPassword = request.form['confirmPassword']

        # Perform form validation
        if username.strip() == '':
            return redirect(url_for('register', error='Please enter a username', form_id='createAccount'))

        if email.strip() == '':
            return redirect(url_for('register', error='Please enter an email address', form_id='createAccount'))

        if password.strip() == '':
            return redirect(url_for('register', error='Please enter a password', form_id='createAccount'))

        if confirmPassword.strip() == '':
            return redirect(url_for('register', error='Please confirm the password', form_id='createAccount'))

        if password != confirmPassword:
            return redirect(url_for('register', error='Passwords do not match', form_id='createAccount'))

        db = Db()
        qry = db.insert("INSERT INTO login (username,  password, usertype) VALUES (%s, %s, 'user')", (username,  password))

        return '<script>alert("User registered"); window.location.href="/login";</script>'
    else:
        error = request.args.get('error')  # Get the error message from the URL parameters
        return render_template("login.html", error=error , form_id='createAccount')






#////////////////////////////////////////////////////////////ADMIN///////////////////////////////////////////////////////////////////////////////////////////////////////////////////



@app.route('/admin-home')
def admin_home():
    print('session ', session)
    if session['user_type'] == 'admin':
        username = session['username'] # get the username from the session
        return render_template('admin/admin-login-dashboard.html', username=username)
    else:
        return redirect('/')



@app.route('/Manage_station')
def Manage_station():
    print('session ', session)
    if session['user_type'] == 'admin':
        db=Db()
        qry=db.select("select station_id, station_name, address, city, charger_type, available_ports, status from admin_charging_station_list")
        return render_template("admin/Manage_station.html",data=qry)
    else:
        return redirect('/')

# =============================contact_us
@app.route('/view_feedback')
def view_feedback():
    print('session ', session)
    if session['user_type'] == 'admin':
        db=Db()
        ss=db.select("select * from contact_us")
        return render_template("admin/view_feedback.html",data=ss)
    else:
        return redirect('/')

# 


# ==================delete station=======
@app.route("/adm_delete_station/<station_name>")
def adm_delete_station(station_name):
    print('session ', session)
    if session['user_type'] == 'admin':
        db = Db()
        qry = db.delete("DELETE FROM admin_charging_station_list WHERE Station_name = %s", (station_name,))
        return '''<script>alert('station deleted');window.location="/Manage_station"</script>'''
    else:
        return redirect('/')
# =======================================





@app.route("/adm_delete_feedback/<feedback>")
def adm_delete_feedback(feedback):
    print('session ', session)
    if session['user_type'] == 'admin':
        db = Db()
        qry = db.delete("delete from contact_us where Sl_no='"+feedback+"'")
        return '''<script>alert('feedback deleted');window.location="/view_feedback"</script>'''
    else:
        return redirect('/')



@app.route('/user-list')
def user_list():
    print('session ', session)
    if session['user_type'] == 'admin':
        db=Db()
        qry = db.select("SELECT * FROM user")
        return render_template("admin/user-list.html",data=qry)
    else:
        return redirect('/')


# ==================delete user===========
@app.route("/adm_delete_user/<user_id>")
def adm_delete_user(user_id):
    print('session ', session)
    if session['user_type'] == 'admin':
        db = Db()
        qry = db.delete("delete from user where user_id='"+user_id+"'")
        return '''<script>alert('user deleted');window.location="/user-list"</script>'''
    else:
        return redirect('/')
# ==============view booking=========================

@app.route('/view_booking')
def view_booking():
    if 'user_type' in session and session['user_type'] == 'admin':
        db = Db()

        # SQL query to fetch bookings and related station info
        bookings_query = """
            SELECT b.id AS Booking_id, b.booking_start_time AS Booking_date, 
                   b.booking_start_time AS Time_from, b.booking_end_time AS Time_to, 
                   cs.city AS City, cs.station_name AS Station_name, 
                   cs.available_ports AS Available_ports, b.user_id AS login_id
            FROM charging_station_booking b
            JOIN charging_station_list cs ON b.charging_station_id = cs.id
            ORDER BY b.booking_start_time DESC
        """
        bookings = db.select(bookings_query)

        # Return the bookings to the view template
        return render_template('admin/view_booking.html', bookings=bookings)
    else:
        return redirect('/')


# ===========delete booking

@app.route("/adm_delete_booking/<Booking_id>")
def adm_delete_booking(Booking_id):
    if 'user_type' in session and session['user_type'] == 'admin':
        db = Db()
        
        # SQL query to delete the booking by Booking_id (which is 'id' in charging_station_booking table)
        qry = db.delete("DELETE FROM charging_station_booking WHERE id = %s", (Booking_id,))
        
        # Return an alert message after deletion
        return '''<script>alert('Booking deleted'); window.location="/view_booking"</script>'''
    else:
        return redirect('/')




#//////////////////////////////////////////////////////////////USER//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

# -----------

@app.route('/user-dashboard')
def user_dashboard():
    if 'user_type' in session and session['user_type'] == "user":
        username = session['username']  # Get the username from the session
        db = Db()
        
        # Query to get the user's booking details
        bookings = db.select("""
            SELECT csb.id AS booking_id, 
                   csb.booking_start_time AS Booking_date, 
                   csb.booking_start_time AS Time_from, 
                   csb.booking_end_time AS Time_to, 
                   csl.city AS City,
                   csl.station_name AS Station_name, 
                   csl.available_ports AS Available_ports
            FROM charging_station_booking csb
            JOIN charging_station_list csl ON csb.charging_station_id = csl.id
            WHERE csb.user_id = %s
            ORDER BY csb.booking_start_time DESC;
        """, (session['uid'],))
        
        return render_template("user/user-login-dashboard.html", bookings=bookings, username=username)
    else:
        return redirect('/')





@app.route('/usr_delete_booking/<int:booking_id>')
def usr_delete_booking(booking_id):
    if 'user_type' in session and session['user_type'] == "user":
        db = Db()
        
        # Use the correct column name 'id' for booking ID
        db.delete("DELETE FROM charging_station_booking WHERE id = %s AND user_id = %s", (booking_id, session['uid']))
        
        return '''<script>alert('Booking deleted');window.location="/user-dashboard"</script>'''
    else:
        return redirect('/user-dashboard')




# TODO: Fix the DB (FK, table etc) and frontend field and backend Field

# @app.route('/user-profile', methods=['GET', 'POST'])
# def user_profile():
#     if request.method == 'POST':
#         name = request.form['name']
#         email = request.form['email']
#         password = request.form['password']
#         confirm_password = request.form['confirm-password']
        
#         if password != confirm_password:
#             return redirect(url_for('user_profile', error='Passwords do not match'))
        
#         db = Db()
#         qry = db.update("UPDATE login SET name = %s, email = %s, password = %s WHERE username = %s", (name, email, password, session['username']))  # Assuming you have stored the logged-in user's username in the session
#         return '<script>alert("Account details updated"); window.location.href="/user-profile";</script>'

#     error = request.args.get('error')
#     return render_template('user/user-profile.html', error=error)




@app.route('/user_find_your_charger', methods=['GET', 'POST'])
def user_find_your_charger():
    if 'user_type' in session and session['user_type'] == 'user':
        if request.method == 'POST':
            city = request.form.get('City')
            charger_type = request.form.get('Charger_type')
            db = Db()
            qry = db.select("select Station_name, Address, Charger_type, Available_ports from admin_charging_station_list where City = %s and Charger_type = %s", (city, charger_type))
            return render_template('user/station_search.html', data=qry)       
        else:
            return render_template('user/user_find_your_charger.html')
    else:
        return redirect('/')




@app.route('/search_stations', methods=['POST'])
def search_stations():
    # Get the form data
    City = request.form.get('City')
    Charger_type = request.form.get('Charger_type')

    # Redirect to the station_list page with the city and charger_type as URL parameters
    return redirect(url_for('station_search', City=City, Charger_type=Charger_type))


@app.route('/station_search', methods=['GET'])
def station_search():
    if 'user_type' in session and session['user_type'] == 'user':
        City = request.args.get('City')
        Charger_type = request.args.get('Charger_type')
        # Query your MySQL database using the city and charge_type variables
        db = Db()
        sql = "select * from admin_charging_station_list where City = %s and Charger_type = %s"
        ss = db.select(sql, (City, Charger_type))

        # Return the results to the user in a new template
        return render_template('user/station_search.html', data=ss, City=City, Charger_type=Charger_type)
    else:
        return redirect('/')

# ==============from station_search to booking page====================
@app.route('/booking', methods=['GET', 'POST'])
def booking():
    if request.method == 'POST':
        Station_name = request.form['Station_name']
        City = request.form['City']
        Available_ports = request.form['Available_ports']
        return redirect(url_for('booking_form',  Station_name=Station_name, City=City, Available_ports=Available_ports))
    else:
        # handle GET request to display the form
        Station_name = request.args.get('Station_name')
        City = request.args.get('City')
        Available_ports = request.args.get('Available_ports')
        return redirect(url_for('booking_form', Station_name=Station_name, City=City, Available_ports=Available_ports))

@app.route('/booking-form', methods=['GET'])
def booking_form():
    city = request.args.get('City')
    available_ports = request.args.get('Available_ports')
    station_name = request.args.get('Station_name')
    db = Db()
    station_data = db.select("select * from admin_charging_station_list where Station_name = %s", (station_name,))
    session['station_data'] = station_data[0] if station_data else None
    if 'station_data' in session and session['station_data']:
        return render_template('/user/booking_form.html', city=city, available_ports=available_ports)
    else:
        return redirect(url_for('station_search'))



# ====================from booking to dashboard

@app.route('/book', methods=['POST'])
def book():
    if 'user_type' in session and session['user_type'] == 'user':
        # Get the form data submitted by the user
        station_name = request.form['Station_name']
        city = request.form['City']
        booking_date = request.form['Booking_date']  # This should be in 'YYYY-MM-DD' format
        time_from = request.form['Time_from']  # This should be in 'HH:MM' format
        time_to = request.form['Time_to']  # This should be in 'HH:MM' format
        login_id = session['uid']

        db = Db()

        # Get the current timestamp for when the booking was made
        created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Fetch the charging_station_id and available_ports based on station_name and city
        station_query = "SELECT id, available_ports FROM charging_station_list WHERE station_name = %s AND city = %s"
        station_result = db.select(station_query, (station_name, city))

        if not station_result:
            return "Station not found!"

        charging_station_id = station_result[0]['id']  # Get the station ID
        available_ports = station_result[0]['available_ports']  # Get available ports

        # Combine the booking date with the time to create a full DATETIME format for start and end times
        booking_start_time = f"{booking_date} {time_from}:00"  # Add seconds for proper DATETIME format
        booking_end_time = f"{booking_date} {time_to}:00"  # Add seconds for proper DATETIME format

        # Set booking status to 'Active' by default
        status = 'Active'

        # Insert the booking data into the charging_station_booking table
        sql = """
            INSERT INTO charging_station_booking (charging_station_id, user_id, booking_start_time, booking_end_time, status)
            VALUES (%s, %s, %s, %s, %s)
        """
        booking_id = db.insert(sql, (charging_station_id, login_id, booking_start_time, booking_end_time, status))

        # Return the booking confirmation page
        return render_template("user/user-login-dashboard.html", data={
            'Station_name': station_name,
            'City': city,
            'Available_ports': available_ports,
            'Booking_date': booking_date,
            'Time_from': time_from,
            'Time_to': time_to,
            'Created_at': created_at,
            'Booking_id': booking_id
        })
    else:
        return redirect('/booking-form')





if __name__ == '__main__':        
    app.run(host='127.0.0.1', port=5000, debug=True)
