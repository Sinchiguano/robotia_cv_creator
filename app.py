from flask import Flask, render_template, request, redirect, url_for, flash, session,send_file
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os

from fpdf import FPDF

# Setup for Flask app and database
basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # 2MB max file size

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)



app.secret_key = "saori_2021"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database', 'data.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)



# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

# Initialize the database
with app.app_context():
    db.create_all()



@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]


        user = User.query.filter_by(username=username).first()

        if user:
            session["user_id"] = user.id
            return redirect(url_for("home"))
        else:
            flash("Invalid credentials", "danger")  # This should show a flash message

    return render_template("login.html")

@app.route("/home")
def home():
    return render_template("home.html")


@app.route("/logout")
def logout():
    session.pop("user_id", None)
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


# ###########################################



@app.route("/cvcreator", methods=['GET','POST'])
def cvcreator():
    return render_template('form.html')




@app.route('/generate', methods=['POST'])
def generate():
    if 'photo' not in request.files:
        return "No file part", 400

    file = request.files['photo']
    if file.filename == '':
        return "No selected file", 400

    if file:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)

    data = {
        'personal_data': {
            'name': request.form['name'],
            'surname': request.form['surname'],
            'id_card': request.form['id_card'],
            'birthday': request.form['birthday'],
            'marital_status': request.form['marital_status'],
            'email': request.form['email'],
            'mobile_phone': request.form['mobile_phone'],
            'address': request.form['address'],
        },
        'education': request.form.getlist('education[]'),
        'work_experience': request.form.getlist('work_experience[]'),
        'personal_references': [
            {'name': request.form['personal_ref1_name'], 'phone': request.form['personal_ref1_phone']},
            {'name': request.form['personal_ref2_name'], 'phone': request.form['personal_ref2_phone']}
        ],
        'working_references': [
            {'name': request.form['working_ref1_name'], 'phone': request.form['working_ref1_phone']},
            {'name': request.form['working_ref2_name'], 'phone': request.form['working_ref2_phone']}
        ],
        'courses': request.form.getlist('courses[]'),
        'skills': request.form.getlist('skills[]'),
    }

    pdf = FPDF()
    pdf.add_page()

    # Add title with background color
    pdf.set_fill_color(30, 144, 255)  # Light blue background for title
    pdf.rect(0, 0, 210, 40, 'F')  # Background for title
    pdf.set_font('Arial', 'B', 28)
    pdf.set_text_color(255, 255, 255)  # White text for title
    pdf.cell(200, 20, 'Curriculum Vitae', ln=True, align='C')

    # Add photo in the top-right corner
    if os.path.exists(file_path):
        pdf.image(file_path, x=150, y=45, w=30, h=40)

    # Start below the title and photo
    pdf.ln(10)

    # Personal Information Section
    pdf.set_font('Arial', 'B', 16)
    pdf.set_text_color(0, 51, 102)  # Dark blue for headings
    pdf.cell(0, 10, 'Personal Information', ln=True, align='L')
    pdf.set_font('Arial', '', 12)
    pdf.set_text_color(0, 0, 0)  # Black text

    # Add personal information with borders for separation
    for key, value in data['personal_data'].items():
        pdf.cell(100, 5, f"{key.capitalize()}: {value}", ln=True, border='L')

    pdf.ln(1)

    # Add Education, Work Experience, Courses, and Skills Sections
    sections = ['Education Background', 'Work Experience', 'Courses', 'Skills']
    section_colors = [(173, 216, 230), (240, 248, 255), (224, 255, 255), (240, 255, 240)]  # Different background colors
    for section, items, color in zip(sections, [data['education'], data['work_experience'], data['courses'], data['skills']], section_colors):
        pdf.set_font('Arial', 'B', 16)
        pdf.set_fill_color(*color)
        pdf.cell(200, 10, section, ln=True, align='L', fill=True)
        pdf.set_font('Arial', '', 12)
        for item in items:
            pdf.cell(200, 5, item, ln=True,border='L')

        pdf.ln(2)

    # Add References Section with background color and borders
    pdf.set_font('Arial', 'B', 16)
    pdf.set_fill_color(173, 216, 230)  # Light blue background for references
    pdf.cell(200, 5, 'References', ln=True, align='L', fill=True)
    # pdf.set_font('Arial', 'B', 12)

    # Personal References and Working References with borders
    for ref_section, refs in [('Personal References', data['personal_references']),
                              ('Working References', data['working_references'])]:
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(200, 7, ref_section, ln=True, align='L', fill=False)
        for ref in refs:
            pdf.set_font('Arial', '', 12)
            pdf.cell(200, 5, f"{ref['name']} - {ref['phone']}", ln=True, border='L')

    # Save PDF
    pdf_file = 'cv.pdf'
    pdf.output(pdf_file)
    return redirect(url_for('download', filename=pdf_file))

@app.route('/download/<filename>')
def download(filename):
    return send_file(filename, as_attachment=True)





if __name__ == "__main__":
    app.run(debug=True)
