from flask import Flask, render_template, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_mail import Mail
from werkzeug.utils import secure_filename
import os
import json
import math

local_server = False
with open('config.json', 'r') as f:
    parameter = json.load(f)["para"]

app = Flask(__name__)
app.secret_key = 'super-secret-key'
app.config['UPLOAD_FOLDER'] = parameter['upload_location']
app.config.update(
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = '465',
    MAIL_USE_SSL = 'True',
    MAIL_USERNAME = parameter['gmail-user'],
    MAIL_PASSWORD = parameter['gmail-pass']
)
mail = Mail(app)
if local_server:
    app.config['SQLALCHEMY_DATABASE_URI'] = parameter['local_uri']
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = parameter['prod_uri']
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class Contacts(db.Model):
    # serial_no	name	phone_num	msg	date	email
    serial_no = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    phone_num = db.Column(db.String(14), nullable=False)
    msg = db.Column(db.String(200), nullable=False)
    date = db.Column(db.String(12), nullable=True)
    email = db.Column(db.String(50), nullable=False)


class Posts(db.Model):
    # serial_no	title slug content date
    serial_no = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50), nullable=False)
    tagline = db.Column(db.String(50), nullable=False)
    slug = db.Column(db.String(50), nullable=False)
    content = db.Column(db.String(9999), nullable=False)
    date = db.Column(db.String(12), nullable=True)
    img_file = db.Column(db.String(30), nullable=True)





@app.route('/')
def home():
    posts = Posts.query.filter_by().order_by(Posts.serial_no.desc())[0:4]
    return render_template('index.html', par=parameter, posts=posts)


@app.route('/about')
def about():
    return render_template('about.html', par=parameter)


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if (request.method=='POST'):
        # adding entries to database
        name = request.form.get('name')
        emailFor = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')
        entry = Contacts(name=name, phone_num=phone, msg=message, email=emailFor, date=datetime.now())
        db.session.add(entry)
        db.session.commit()
        mail.send_message(
            subject='New message from' + name,
            sender=emailFor,
            recipients=[parameter['gmail-user']],
            body=message + "\n" + phone
        )

    return render_template('contact.html', par=parameter)


@app.route('/post/<string:post_slug>', methods=['GET'])
def post_route(post_slug):
    post = Posts.query.filter_by(slug=post_slug).first()
    return render_template('post.html', par=parameter, post=post)


@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if ('user' in session and session['user'] == parameter['admin_user']):
        posts = Posts.query.all()
        return render_template('dashboard.html', par=parameter, posts=posts)

    if request.method == 'POST':
        username = request.form.get('usrname')
        password = request.form.get('pwd')
        if (username == parameter['admin_user'] and password == parameter['admin_pas']):
            session['user'] = username
            posts = Posts.query.all()
            return render_template('dashboard.html', par=parameter, posts=posts)

    return render_template('login.html', par=parameter)


@app.route("/edit/<string:serial_no>", methods=['GET', 'POST'])
def edit(serial_no):
    if ('user' in session and session['user'] == parameter['admin_user']):
        if request.method == 'POST':
            box_title = request.form.get('title')
            tline = request.form.get('tline')
            slug = request.form.get('slug')
            content = request.form.get('content')
            img_file = request.form.get('img_file')
            date = datetime.now()

            if serial_no == '0':
                post = Posts(date=date, title=box_title, tagline=tline, slug=slug, content=content, img_file=img_file)
                db.session.add(post)
                db.session.commit()
            else:
                post = Posts.query.filter_by(serial_no=serial_no).first()
                post.title = box_title
                post.slug = slug
                post.content = content
                post.tagline = tline
                post.img_file = img_file
                post.date = date
                db.session.commit()
                return redirect('/edit/'+serial_no)
        post = Posts.query.filter_by(serial_no=serial_no).first()
        return render_template('edit.html', par=parameter, post=post, serial_no=serial_no)


@app.route('/uploader', methods=['GET', 'POST'])
def uploader():
    if ('user' in session and session['user'] == parameter['admin_user']):
        if request.method == 'POST':
            fi = request.files['file1']
            fi.save(os.path.join(app.config['UPLOAD_FOLDER'],secure_filename(fi.filename)))
            return "Uploaded Sucessfully"


@app.route('/logout')
def logout():
    session.pop('user')
    return redirect('/')


@app.route('/blogs')
def blogs():
    posts = Posts.query.filter_by().all()[::-1]

    last = math.ceil(len(posts)/int(parameter['no_of_post']))
    page = request.args.get('page')
    if (not str(page).isnumeric()):
        page = 1
    page = int(page)
    posts = posts[(page-1)*int(parameter['no_of_post']):(page-1)*int(parameter['no_of_post'])+int(parameter['no_of_post'] )]
    if page == 1:
        prev = "/blogs"
        next = "/blogs?page=" + str(page+1)

    elif page == last:
        prev = "/blogs?page=" + str(page - 1)
        next = "/blogs"

    else:
        prev = "/blogs?page=" + str(page - 1)
        next = "/blogs?page=" + str(page + 1)

    return render_template('blogs.html', par=parameter, posts=posts, next=next, prev=prev)


@app.route("/delete/<string:serial_no>", methods=['GET', 'POST'])
def delete(serial_no):
    if ('user' in session and session['user'] == parameter['admin_user']):
        post = Posts.query.filter_by(serial_no=serial_no).first()
        db.session.delete(post)
        db.session.commit()
    return redirect('/dashboard')

@app.route('/undercons')
def undercons():
    return render_template('undercons.html', par=parameter)


if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)

