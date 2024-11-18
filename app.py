from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import date,datetime
import segno 
import os
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_LINK")

db = SQLAlchemy(app)

# migrate = Migrate(app,db)
# flask db init ---> in terminal
# flask db migrate -m "Initial Migration"
# flask db upgrade

class details(db.Model):
    entryId = db.Column(db.String(10),nullable=False,primary_key=True)
    name = db.Column(db.String(25),nullable=False)
    fatherName = db.Column(db.String(25),nullable=False)
    surname = db.Column(db.String(25),nullable=False)
    dob = db.Column(db.Date,nullable=False)
    vatan = db.Column(db.String(25),nullable=False)
    contact = db.Column(db.String(10),nullable=False)
    address= db.Column(db.String(100),nullable=False)
    def __repr__(self):
        return '<Id %r>' % self.id
    
class Login(db.Model):
    userName = db.Column(db.String(25),nullable=False,primary_key=True)
    passWord = db.Column(db.String(25),nullable=False)

# with app.app_context():
#     db.create_all()
#     print(1)

@app.route('/',methods=['GET','POST'])
def login():
    if request.method == 'POST':
        if request.form['username'] == os.getenv("USERNAME"):
            if request.form['password'] == os.getenv("PASSWORD"):
                return redirect(url_for('index'))
            else:
                return 'WRONG PASSWORD'
        else:
            return 'WRONG USERNAME'
    else:
        return render_template('login.html')

@app.route('/home', methods=['GET', 'POST'])
def index():
    results = db.session.query(details.entryId, details.contact).all()
    data = [{"entryId": result.entryId, "contact": result.contact} for result in results]
    print(data[:10])
    for i in data:
        # print(i['contact'])
        qrcode = segno.make_qr("https://wa.me/+91"+i['contact'])
        qrcode.save("static/QR Code/"+i['entryId'][3:]+".png",scale=6)
    if request.method == 'POST':
        print(request.form)
        name = request.form['name']
        entryId = request.form['entryId']
        father_name = request.form['father_name']
        surname = request.form['surname']
        dob_str = request.form['dob']
        dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
        vatan = request.form['vatan']
        contact = request.form['contact']
        qrcode = segno.make_qr("https://wa.me/+91"+contact)
        qrcode.save("static/QR Code/"+entryId[3:]+".png",scale=6)
        address = request.form["address"]
        # age = request.form['age']
        image_file = request.files['image']
        image_file.save('static/Image/' + entryId[3:] + ".jpg")

        # print(name,entryId,father_name,surname,dob,vatan,contact)
        new_todo = details(entryId=entryId,name=name,fatherName=father_name,
                            surname=surname,dob=dob,vatan=vatan,contact=contact,address=address)
        try:
            db.session.add(new_todo)
            db.session.commit()
            return redirect(url_for('index'))
        except Exception as e:
            print(e)
            return str(e)
    else:
        tasks = details.query.order_by(details.entryId).all()
        return render_template('index.html',tasks=tasks)

@app.route('/delete/<string:id>')
def delete(id):
    task_to_delete = details.query.get_or_404(id)
    try:
        image_base_path = 'static/Image/'
        file_number = id[3:]
        image_file_path = f"{image_base_path}{file_number}.jpg"
        qr_base_path = 'static/QR Code/'
        qr_file_path = f"{image_base_path}{file_number}.jpg"
        db.session.delete(task_to_delete)
        db.session.commit()
        if os.path.exists(image_file_path):
            os.remove(image_file_path)
            print(f"{image_file_path} has been deleted successfully.")
            return redirect(url_for('index'))
        elif os.path.exists(qr_file_path):
            os.remove(qr_file_path)
            print(f"{qr_file_path} has been deleted successfully.")
            return redirect(url_for('index'))
        else:
            print('file error')
    except:
        return 'There was a problem deleting that task'

@app.route('/update/<string:id>', methods=['GET', 'POST'])
def update(id):
    task = details.query.get_or_404(id)
    if request.method == 'POST':
        task.entryId = request.form['entryId']
        task.name = request.form['name']
        task.fatherName = request.form['father_name']
        task.surname = request.form['surname']
        dob_str = request.form['dob']
        task.dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
        task.address=request.form["address"]
        task.vatan = request.form['vatan']
        image_file = request.files['image']
        if image_file.filename != '':
            image_file.save('static/Image/' + task.entryId[3:] + ".jpg")
        if request.form['contact'] != task.contact:
            print('qr change')
            qrcode = segno.make_qr("https://wa.me/+91"+request.form['contact'])
            qrcode.save("static/QR Code/"+task.entryId[3:]+".png",scale=6)
        
        task.contact = request.form['contact']
        try:
            db.session.commit()
            return redirect(url_for('index'))
        except:
            return 'There was an issue updating your task'
    else:
        return render_template('update.html', task=task)
    
@app.route('/print/<string:id>')
def printCard(id):
    task_to_print = details.query.get_or_404(id)
    return render_template('card.html',task=task_to_print)

if __name__ == "__main__":
    app.run(debug=True)