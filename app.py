from random import randint
import imghdr
import os
import glob
from flask import Flask, render_template, request, redirect, url_for, abort, send_from_directory, session 
from werkzeug.utils import secure_filename
from email.mime.text import MIMEText
import email
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
import smtplib, ssl, os, boto3, json
import sqlite3
import socket
print('Hostname', socket.gethostbyname(socket.gethostname()))
app = Flask(__name__)
app.secret_key = 'ChidozieNnajiMySQLAdminDbhost2005@gmail.com#codewithcn.com'
app.host=socket.gethostbyname(socket.gethostname())
#app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024
app.config['UPLOAD_EXTENSIONS'] = ['.jpg', '.png', '.gif', '.ai', '.bmp', '.ico', '.jpeg',
'.ps', '.psd', '.svg', '.tif', '.tiff', '.eps', '.indd', '.raw', '.cr2','.crw', '.nef', '.pef']
app.config['UPLOAD_PATH'] = 'static/images/reviews'

def check_type(stuff, types):
    if  type(stuff) == type(types):
        return True
    return False

app.jinja_env.filters['check_type'] = check_type

def check_len(obj):
    return len(obj)

app.jinja_env.filters['check_len'] = check_len
def send_email(subject, message, email, emailer, emailer_pass):
        port = 587  # For starttls
        smtp_server = "smtp.mail.me.com"
        sender_email = emailer
        receiver_email = email
        password = emailer_pass
        messages = MIMEMultipart()
        messages['From'] = sender_email
        messages['To'] = receiver_email
        messages['Subject'] = subject
        messages['Bcc'] = receiver_email
        messages.attach(MIMEText(message, 'plain'))
        context = ssl.create_default_context()
        with smtplib.SMTP(smtp_server, port) as server:
            server.ehlo()  # Can be omitted
            server.starttls(context=context)
            server.ehlo()  # Can be omitted
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, messages.as_string())

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/set/appointments', methods=['GET','POST'])
def contact():
    msg=''
    if request.method=='POST':
        name = request.form["First-Name"]
        date = request.form["Date"]
        email = request.form["Email"]
        number = request.form["Contact-Phone-Number"]
        message = request.form["Message"]
        statement = name + ' wants to set an appointment at '+ date +';\n You can reach them at (Email): '+ email +' or at (Phone): '+ number + '\nThere message was: ' + message
        conn = sqlite3.connect('server.db')
        cursor = conn.cursor()
        query = """select email from users"""
        cursor.execute(query)
        emails =  cursor.fetchall()
        for i in emails:
          send_email('Contact for Barber Appointment', statement, i,'nnajisgai@icloud.com', 'vhow-umlp-oobe-uuls')
        msg = 'Appointment recieved I will try to get to you as soon as possible.' 
    return render_template('appointments.html', msg=msg)

@app.route('/reviews', methods=['GET'])
def reviews():
    conn = sqlite3.connect('server.db')
    cursor = conn.cursor()
    query = """select * from reviews"""
    cursor.execute(query)
    review = cursor.fetchall()
    print(review, type(review))
    return render_template('review.html', review=review[::-1])

@app.route('/add_like', methods=["POST"])
def add_likes():
    data = request.get_json() 
    print(data)
    try:
        conn = sqlite3.connect('server.db')
        cursor = conn.cursor()
        query = """select like_count from reviews where id={}""".format(int(data["content"]))
        cursor.execute(query)
        count = cursor.fetchone()[0]
        query = """update reviews set like_count={} where id={}""".format(count+1, int(data["content"]))
        cursor.execute(query)
        conn.commit()
        conn.close()
        return str(count+1), 200
    except Exception as e:
        print(e)
        return 'Issue'

def split_list_in_two(list, amount):
  n = 0
  new = []
  for i in range(len(list)):
    if len(list[n : n+amount]) != 0:
      new.append(list[n: n+amount])
      n+=amount
  return new

def split_list_in_four_then_two(list):
  final = []
  step_1 = []
  step_1 = split_list_in_two(list, 4)
  for i in step_1:
    if len(i) <= 2:
      final.append(i)
    else:
      final.append(split_list_in_two(i, 2))
  return final

@app.route('/admin', methods=['GET'])
def admin_home():
    try:
        if session['id']:
            conn = sqlite3.connect('server.db')
            cursor = conn.cursor()
            query = """select * from reviews"""
            cursor.execute(query)
            review = cursor.fetchall()[::-1]
            split_four_two = split_list_in_four_then_two(review)
            for split in split_four_two:
                for i in split:
                    print(i)
            conn.close()
            return render_template('admin_home.html', splitted=split_four_two, name=session['name'])

    except KeyError:
        print('Session not created')
        return redirect('/admin/login')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    msg = ''
    if request.method == 'POST':
        name = request.form["First-Name"]
        password = request.form["Last-Name"]
        email = request.form["Email"]
        conn = sqlite3.connect('server.db')
        cursor = conn.cursor()
        query = """select id from users where name='{}' and password='{}' and email='{}' """.format(
            name, password, email
        )
        print(query)
        cursor.execute(query)
        ids = cursor.fetchone()
        print(ids)
        if ids != None:
            session['id'] = ids[0]
            session['name'] = name
            session['email'] = email
            session['password'] = password
            return redirect('/admin')
        msg='Incorrect credentials'

    return render_template('admin_login.html', msg=msg)

@app.route('/change_comment', methods=['POST'])
def change_comment():
    data = request.get_json() 
    print(data)
    try:
        conn = sqlite3.connect('server.db')
        cursor = conn.cursor()
        query = """update reviews set comment="{}" where id={}""".format(
            data['new_comment'], int(data["content"])
        )
        cursor.execute(query)
        conn.commit()
        conn.close()
        return data['new_comment'], 200

    except Exception as e:
        print(e)
        return "Issue"

@app.route('/change_name', methods=['POST'])
def change_name():
    data = request.get_json()
    try:
        conn = sqlite3.connect('server.db')
        cursor = conn.cursor()
        query = """update users set name="{}" where name="{}" """.format(
            data['new_name'], data['content']
        )
        cursor.execute(query)
        conn.commit()
        conn.close() 
        session['name'] = data['new_name']
        return data['new_name'], 200

    except Exception as e:
        print(e)
        return "Issue"

@app.route('/change_password', methods=['POST'])
def change_password():
    data = request.get_json()
    print(data)
    try:
        conn = sqlite3.connect('server.db')
        cursor = conn.cursor()
        query = """update users set password='{}' where name='{}' """.format(
            data['new_password'], data['content']
        )
        cursor.execute(query)
        conn.commit()
        conn.close()
        session['password']= data['new_password']
        return 'OK', 200
    except Exception as e:
        print(e)
        return  'Issue'

@app.route('/change_email', methods=['POST'])
def change_email():
    data = request.get_json()
    print(data)
    try:
        conn = sqlite3.connect('server.db')
        cursor = conn.cursor()
        query = """update users set email='{}' where name='{}' """.format(
            data['new_email'], data['content']
        )
        cursor.execute(query)
        conn.commit()
        conn.close()
        session['email']= data['new_email']
        return 'OK', 200

    except Exception as e:
        print(e)
        return "Issue"

def validate_image(stream):
    header = stream.read(512)
    stream.seek(0)
    format = imghdr.what(None, header)
    if not format:
        return None
    return '.' + (format if format != 'jpeg' else 'jpg')

@app.errorhandler(413)
def too_large(e):
    return "File is too large", 413

@app.route("/add/review", methods=['GET'])
def add_review():
    try:
        if session['id']:
            files = os.listdir(app.config['UPLOAD_PATH'])
            return render_template('add_review.html', files=files)

    except KeyError:
        print('session not created')
        return redirect('/admin/login')

@app.route('/sign_s3', methods=['POST'])
def save_file_image():
    try:
        file_name = request.args.get('file_name')
        while True:
          if file_name not in get_taken_names():
            break
          else:
            file_name = file_name + str(randint(0, 100000))
        file_type= request.args.get('file_type')
        if file_name != '':
            S3_BUCKET = 'drowninbooks' 
            """os.environ['S3_BUCKET_EMAIL']"""
            s3 = boto3.client('s3')
            presigned_post = s3.generate_presigned_post(
                Bucket = S3_BUCKET,
                Key = file_name,
                Fields = {"acl": "public-read", "Content-Type": file_type},
                Conditions = [
                {"acl": "public-read"},
                {"Content-Type": file_type}
                ],
                ExpiresIn = 3600
            )
            return json.dumps({
                'data': presigned_post,
                'url': 'https://%s.s3.amazonaws.com/%s' % (S3_BUCKET, file_name),
            })
        else:
            raise ValueError
    except Exception as e:
        print(e)
        return "Issue", 200

@app.route('/send_review/data',methods=['POST'])
def save_reviews():
  data = request.get_json()
  conn = sqlite3.connect('server.db')
  cursor = conn.cursor()
  f = False
  for i in data:
    if len(data[i]) <=0:
      f= False
      break
    else:
      f = True
  if f:
    query = """insert into reviews (before_file_path, after_file_path, like_count, comment) VALUES ('{}', '{}', 0, '{}')""".format(data['Before'], data['After'], data['Comment'])
    print(query)
    cursor.execute(query)
    conn.commit()
    return {"result":"Good"}, 200
  return {'result':"Issue"}, 200

def get_taken_names():
  s3 = boto3.resource('s3')
  domains=[]
  bucket = s3.Bucket('drowninbooks')
  for obj in bucket.objects.all():
    key = obj.key
    domains.append(key)
  return domains

if __name__ == '__main__':
  app.run(host='0.0.0.0', debug=True)