from flask import Flask, render_template, request, redirect, url_for, session, Response
from flask_mail import Mail, Message
import os
from werkzeug.utils import secure_filename 
from functools import wraps
from dotenv import load_dotenv
load_dotenv
from flask_sqlalchemy import SQLAlchemy # pentru salvare skill-uri in baza de date
from urllib.parse import unquote # se importa pentru spatiile dintre cuvinte cand adaug sau sterg un skill
from flask_migrate import Migrate # pentru actualizare baza de date
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart



app = Flask(__name__)
app.secret_key = os.urandom(24) # Genereaza o cheie aleatorie pentru securizarea autentificarii

# Config baza date
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///portfolio.db' # Ori MySql ori PosgresSql
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initializez baza de date
db = SQLAlchemy(app)

# Initializez Flask-Migrate
migrate = Migrate(app, db)

class Skill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    # level = db.Column(db.String(200), nullable=True) # nivelul de cunoasterea al skill-ului # flask db migrate -m "Eliminare level din Skill" apoi flask db upgrade
    image = db.Column(db.String(255), nullable=True)

    with app.app_context():
        db.create_all()  # Crează tabelele


    def __repr__(self):
        return f'<Skill {self.name}>'

# Setare user pentru login la sectiunea admin
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["logged_in"] = True
            return redirect(url_for("admin"))
        
        return "Login failed. Try again"
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("logged_in", None)  # Șterge sesiunea utilizatorului
    return redirect(url_for("login"))  # Redirecționează către pagina de login

# Decorator pentru protejarea paginii login
def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    wrap.__name__ = f.__name__
    return wrap

# Decorator pentru autentificare:
def check_auth(username, password):
    return username == "ADMIN_USERNAME" and password == "ADMIN_PASSWORD"

def authenticate():
    return Response(
        "Autentificare necesara,", 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'}
    )

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

# Setează directorul unde se vor salva imaginile
UPLOAD_FOLDER = 'static/image'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}


@app.route('/')
def home():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/professional-development')
def professional_development():
    professional_development_list = [
        {"title": "Automation Engineer", "date": "2014 -present", "company": "SC SECRET DATA SRL", "location":"Satu Mare, Romania"},
        {"title": "Food Engineer", "date": "2009 -2013", "company": "SC NATURLACT GROUP SRL", "location":"Ooreu, Jud. Satu Mare, Romania"},
        {"title": " Physics Lab. Technician", "date": "2006 -2009", "company": "NATIONAL COLLEGE GHEORGHE SINCAI", "location":"Baia Mare, Jud. Maramures, Romania"}    
    ]    
    return render_template('professional-development.html', professional_development_list=professional_development_list)

@app.route('/certification')
def certification():
    certification_list = [
        {"name": "DevOps", "organization": "IT School", "year": 2024, "link": "https://drive.google.com/file/d/1EMXP1SVsKNKuDielmP891bhUGRenkivo/view?usp=drive_link"},
        {"name": "QA Automation with Python", "organization": "IT Factory", "year": 2023, "link": "https://drive.google.com/file/d/1cLuP9-4Y0HKlcTy5nBtWKb6sm0-zE6Wy/view?usp=drive_link"},
        {"name": "Cyber Security", "organization": "EOS CyberStart", "year": 2023, "link": "https://drive.google.com/file/d/1_8P62WfdNwqoVb4bmfXUpvRtQw1LbBVg/view?usp=drive_link"},
        {"name": "Master's Degree", "organization": "Analysis methods used in environmental and product quality control", "year": 2010,},
        {"name": "Bachelor Degree", "organization": "Food Industry Engineer", "year": 2008,}
    ]
    return render_template('certification.html', certifications=certification_list)

skill_list = [        
        #{"name": "Linux", "level":"Beginner to Intermediate", "image":"image/linux.png"},   # lista nu mai este valabila pentru ca am mutat-o la pagina admin  
        #{"name": "Ansible", "level":"Beginner to Intermediate", "image":"image/python.jpg"},
        #{"name": "Docker", "level":"Beginner to Intermediate", "image":"image/python.jpg"},
        #{"name": "Python", "level":"Beginner to Intermediate", "image":"/image/python.jpg"}

    ]   

@app.route('/skills')
def skills():
    skill_list = Skill.query.all()    
    return render_template('skills.html', skills=skill_list)

# Funcție pentru a verifica tipul fișierului
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


@app.route('/admin-panel-1984')
@login_required
def admin():
    skill_list = Skill.query.all()
    return render_template('admin.html', skills=skill_list)

# @app.route('/admin')   # sectiune de cod pentru pagina admin la vedere
# @login_required
# def admin():
#     skill_list = Skill.query.all()
#     return render_template('admin.html', skills=skill_list)

@app.route('/add_skill', methods=['POST'])
def add_skill():
    name = request.form.get('name')
    #level = request.form.get('level') # decomenteaza pentru skill level in sectiunea de skilluri
    image = request.files.get('image')

    # Salvează fișierul imagine
    image_filename = None
    if image and allowed_file(image.filename):
        filename = secure_filename(image.filename)
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])
        image.save(image_path)
        image_filename = f"image/{filename}"
    else:
        image_filename = "image/default.png"  # Folosește o imagine implicită dacă nu există imagine

    if name:
        skill_list.append({"name": name, "image": image_filename})
    # if name and level:
    #     skill_list.append({"name": name, "level": level, "image": image_filename})  # decomenteaza pentru skill level in sectiunea de skilluri

    new_skill = Skill(name=name, image= image_filename)
    #new_skill = Skill(name=name, level = level, image= image_filename) # linia originala cu skill
    db.session.add(new_skill)
    db.session.commit()

    return redirect(url_for('admin'))

@app.route('/delete_skill/<skill_name>', methods=['POST'])
def delete_skill(skill_name):
    # # Folosesc skill_list global pentru a modifica lista
    # global skill_list
    # # Șterge skillul din listă
    # skill_list = [skill for skill in skill_list if skill["name"] != skill_name]
    skill_name = unquote(skill_name)
    skill = Skill.query.filter_by(name=skill_name).first_or_404()
    db.session.delete(skill)
    db.session.commit()
    return redirect(url_for('admin'))

@app.route('/edit_skill/<int:skill_id>', methods=['GET', 'POST'])
def edit_skill(skill_id):
    skill = Skill.query.get_or_404(skill_id)

    if request.method == 'POST':
        skill.name = request.form['name']
        
        if 'image' in request.files:
            file = request.files['image']
            if file.filename != '':
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                skill.image = filename
        
        db.session.commit()
        return redirect(url_for('admin'))

    return render_template('edit_skill.html', skill=skill)


@app.route('/projects')
def projects():
    project_list = [
        {
            "title": "Python & MySQL Database",
            "description": "Graphical interface with Python for adding or searching for information in a MySQL database and replicating the database on another PC.",
            "image": "/static/project1.jpg",
            "link": "https://github.com/PopFlaviuCiprian/python_mysql_database.git"

        },
        {
            "title": "Terraform, Ansible, AWS and Docker Container Automation",
            "description": "Server configuration management and nodes with Docker containers, using Terraform and Ansible in AWS cloud.",
            "image": "/static/devops.jpg",
            "link": "https://github.com/PopFlaviuCiprian/Terraform_Ansible_AWS.git"
        },
        {
            "title": "Kubernetes cluster",
            "description": "A Frontend Service that serves the web application to users to vote for their favorite pets (cats or dogs). It is Developed using Python & Flask.",
            "image": "/static/kubernetes.jpg",
            "link": "https://github.com/PopFlaviuCiprian/kubernetes-cluster.git"
        },
        {
            "title": "Shopping List Android App",
            "description": "Android application to create a shopping list and check every item after buing it, for forgetful people like me :)).",
            "image": "/static/shoplist.jpg",
            "link": "https://github.com/PopFlaviuCiprian/Android_shopping_list.git"
        },
        {
            "title": " Event Reminder Android App",
            "description": "Simple android app for reminding an planned event, olso for forgetful people like me.",
            "image": "/static/event_reminder.jpg",
            "link": "https://github.com/PopFlaviuCiprian/Android_App_Reminder.git"
        },
        {
            "title": " Backup tool",
            "description": "Backup tool created in Python .",
            "image": "/static/backup.jpg",
            "link": "https://github.com/PopFlaviuCiprian/Back-up_tool_with_GUI.git"
        },
        {
            "title": " Client Reminder",
            "description": "A python application to display the subscription status of a customer from a customer list after a color code.",
            "image": "/static/reminder.jpg",
            "link": "https://github.com/exemplu/todo-app"
        },
        {
            "title": " Web Site Testing",
            "description": "A suite of tests to check the  functionality of an e-commerce platform.",
            "image": "/static/testing.jpg",
            "link": "https://github.com/PopFlaviuCiprian/Testing_site_Emag.ro.git"
        }      
        
    ]
    return render_template('projects.html', projects=project_list)

# Configurare mail pentru sectiunea de contact - Configurare server SMTP
MAIL_SERVER = "smtp.gmail.com"
MAIL_PORT = 587
MAIL_USERNAME = os.getenv("MAIL_USERNAME")  # Adresa de email din env
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")  # Parola de aplicație din env
MAIL_DEFAULT_SENDER = os.getenv("MAIL_USERNAME")  # Expeditorul

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']
        
        # Construiește emailul
        msg = MIMEMultipart()
        msg["From"] = MAIL_DEFAULT_SENDER
        msg["To"] = MAIL_USERNAME  # Emailul adminului unde ajunge mesajul
        msg["Subject"] = f"New Contact Message from {name}"
        
        body = f"Name: {name}\nEmail: {email}\n\nMessage:\n{message}"
        msg.attach(MIMEText(body, "plain"))

        try:
            # Trimite emailul prin SMTP
            server = smtplib.SMTP(MAIL_SERVER, MAIL_PORT)
            server.starttls()  # Activează criptarea
            server.login(MAIL_USERNAME, MAIL_PASSWORD)
            server.sendmail(MAIL_DEFAULT_SENDER, MAIL_USERNAME, msg.as_string())
            server.quit()
            
            return render_template('contact.html', success=True)
        
        except Exception as e:
            print("Error sending email:", e)
            return render_template('contact.html', success=False)

    return render_template('contact.html', success=False)


if __name__ == '__main__':
    with app.app_context():
        db.create_all() # creaza baza de date
    app.run(debug=True)