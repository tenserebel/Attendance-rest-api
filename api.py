# Importing required library 
from flask import Flask, request, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy,BaseQuery
from flask_cors import CORS, cross_origin
import uuid
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
from functools import wraps
import json
from datetime import date
from sqlalchemy import inspect
import ast

# Setting up the flask app and sqlite database
app=Flask(__name__)
cors=CORS(app, supports_credentials=True)
app.config['CORS_HEADERS'] = 'Content-Type'
app.config["SECRET_KEY"]='prem'
app.config["SQLALCHEMY_DATABASE_URI"]="sqlite:///user.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JSON_SORT_KEYS'] = False

db=SQLAlchemy(app)

# Creating required tables of user and students
class User(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    public_id=db.Column(db.String(50),unique=True)
    name=db.Column(db.String(50))
    password = db.Column(db.String(80))
    admin = db.Column(db.Boolean) 

class student(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    name=db.Column(db.String(50))
    div=db.Column(db.String)
    month=db.Column(db.Integer)
    present=db.Column(db.Integer)
    absent=db.Column(db.Integer)
    record=db.Column(db.String)


# Decorator for Token requirement 
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']

        if not token:
            return jsonify({'message' : 'Token is missing!'}), 401

        try: 
            data = jwt.decode(token, app.config['SECRET_KEY'])
            current_user = User.query.filter_by(public_id=data['public_id']).first()
        except:
            return jsonify({'message' : 'Token is invalid!'}), 401

        return f(current_user, *args, **kwargs)

    return decorated

# Route for all user information 
@app.route('/user', methods=['GET'])
@token_required
def get_all_users(current_user):

    if not current_user.admin:
        return jsonify({'message' : 'Cannot perform that function!'})

    users = User.query.all()

    output = []

    for user in users:
        user_data = {}
        user_data['public_id'] = user.public_id
        user_data['name'] = user.name
        user_data['password'] = user.password
        user_data['admin'] = user.admin
        output.append(user_data)

    return jsonify({'users' : output})

# Route for specific user information
@app.route('/user/<public_id>', methods=['GET'])
@token_required
def get_one_user(current_user, public_id):

    if not current_user.admin:
        return jsonify({'message' : 'Cannot perform that function!'})

    user = User.query.filter_by(public_id=public_id).first()

    if not user:
        return jsonify({'message' : 'No user found!'})

    user_data = {}
    user_data['public_id'] = user.public_id
    user_data['name'] = user.name
    user_data['password'] = user.password
    user_data['admin'] = user.admin

    return jsonify({'user' : user_data})

# Route for posting new user information
@app.route('/user', methods=['POST'])
@token_required
def create_user(current_user):
    if not current_user.admin:
        return jsonify({'message' : 'Cannot perform that function!'})

    data = request.get_json()

    hashed_password = generate_password_hash(data['password'], method='sha256')

    new_user = User(public_id=str(uuid.uuid4()), name=data['name'], password=hashed_password, admin=False)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message' : 'New user created!'})

# Route for promoting user status 
@app.route('/user/<public_id>', methods=['PUT'])
@token_required
def promote_user(current_user, public_id):
    if not current_user.admin:
        return jsonify({'message' : 'Cannot perform that function!'})

    user = User.query.filter_by(public_id=public_id).first()

    if not user:
        return jsonify({'message' : 'No user found!'})

    user.admin = True
    db.session.commit()

    return jsonify({'message' : 'The user has been promoted!'})

# Route for deleting user from database
@app.route('/user/<public_id>', methods=['DELETE'])
@token_required
def delete_user(current_user, public_id):
    if not current_user.admin:
        return jsonify({'message' : 'Cannot perform that function!'})

    user = User.query.filter_by(public_id=public_id).first()

    if not user:
        return jsonify({'message' : 'No user found!'})

    db.session.delete(user)
    db.session.commit()

    return jsonify({'message' : 'The user has been deleted!'})

# Route for login
@app.route('/login')
def login():
    auth = request.authorization

    if not auth or not auth.username or not auth.password:
        return make_response('Could not verify', 401, {'WWW-Authenticate' : 'Basic realm="Login required!"'})

    user = User.query.filter_by(name=auth.username).first()

    if not user:
        return make_response('Could not verify', 401, {'WWW-Authenticate' : 'Basic realm="Login required!"'})

    if check_password_hash(user.password, auth.password):
        token = jwt.encode({'public_id' : user.public_id, 'exp' : datetime.datetime.utcnow() + datetime.timedelta(minutes=200)}, app.config['SECRET_KEY'])

        return jsonify({'token' : token.decode('UTF-8')})

    return make_response('Could not verify', 401, {'WWW-Authenticate' : 'Basic realm="Login required!"'})

# Route for home page
@app.route("/")
@cross_origin()
def homepage():
    return "Api for attendance management system."

# Route for adding student information
@app.route("/student",methods=['POST'])
@token_required
def add_student(current_user):
    
    data = request.get_json()

    check_student = student.query.filter_by(name=data['name']).first()

    if check_student:
        return jsonify({'message' : 'Student already exist'})

    att=str(data['record'])
    test=att.split(",")
    for i in test:
        if i=="p":
            data['present']+=1
        elif i=="a":
            data['absent']+=1
    student_data = student(name=data['name'], div=data['div'], month=data['month'],present=data['present'],absent=data['absent'],record=data['record'])
    db.session.add(student_data)
    db.session.commit()

    return jsonify({'message' : 'New user created!'})

# Route for getting all students information
@app.route('/student',methods=['GET'])
@token_required
def get_all_students(current_user):
    students = student.query.all()
    
    student_output = []

    for stud in students:
        student_data = {}
        student_data['name'] = stud.name
        student_data['div'] = stud.div
        student_data['month'] = stud.month
        student_data['present'] = stud.present
        student_data['absent'] = stud.absent
        student_data['record']=stud.record
        student_output.append(student_data)

    return jsonify({'students' : student_output})

# Route for getting one student information
@app.route('/student/<string:student_name>', methods=['GET'])
@token_required
def get_one_student(current_user,student_name):

    studs = student.query.filter_by(name=student_name).all()

    if not studs:
        return jsonify({'message' : 'No Student found!'})

    student_output = []
    for stud in studs:
        stud_data = {}
        stud_data['name'] = stud.name
        stud_data['div'] = stud.div
        stud_data['month'] = stud.month
        stud_data['present'] = stud.present
        stud_data['absent'] = stud.absent
        stud_data['record']=stud.record
        student_output.append(stud_data)

    return jsonify({'student' : student_output})

# Route for getting the whole month attendance
@app.route('/student/<int:month>')
@token_required
def stud_by_month(current_user,month):
    mon=student.query.filter_by(month=month).all()
    print(mon)
    if not mon: 
        return jsonify({'message':'attendance for that month is not available'})

    new_div={}
    for i in range(0,len(mon)):
        new_div[mon[i].name]={"present":mon[i].present,"absent":mon[i].absent}

    return jsonify(new_div)

# Route for deleting student from the database
@app.route('/student/delete/<name>', methods=['DELETE'])
@token_required
def delete_stud(current_user,name):
    stud = student.query.filter_by(name=name).first()

    if not stud:
        return jsonify({'message' : 'No student found!'})

    student.query.filter_by(name=name).delete()
    db.session.commit()

    return jsonify({'message' : 'The student has been deleted!'})

# Route for getting students in one Divison 
@app.route('/<string:divison>', methods=['GET'])
@token_required
def get_divison(current_user,divison):
    div_data= student.query.with_entities(student.name).filter_by(div=divison).all()
    
    new_div={}
    for i in range(0,len(div_data)):
        new_div[i]=div_data[i].name

    return jsonify(new_div)

# Routing for marking the attendance 
@app.route('/student/attendance/<student_name>/<int:month>/<atte>',methods=['GET'])
@token_required
def attendance(current_user,student_name,month,atte):

    stud = student.query.filter_by(name=student_name,month=month).first()
    
    if stud!=None and month == stud.month:
        
        stud.name = stud.name
        stud.div = stud.div
        stud.month = stud.month
        for i in str(atte):
            if i=="p":
                stud.present=stud.present+1
                stud.absent=stud.absent
            elif i=="a":
                stud.absent=stud.absent+1
                stud.present=stud.present
        stud.record= f"{stud.record},{str(atte)}"
        db.session.commit()
    else:
        stud_data = {}
        stud = student.query.filter_by(name=student_name).first()
        stud_data['month'] =month
    
        stud_data['name'] = stud.name
        stud_data['div'] = stud.div
     
        for i in str(atte):
            if i=="p":
                stud_data['present']=stud.present+1
                stud_data['absent']=stud.absent
            elif i=="a":
                stud_data['absent']=stud.absent+1
                stud_data['present']=stud.present
        stud_data['record']= atte
        student_data = student(name=stud_data['name'], div=stud_data['div'], month=stud_data['month'],present=stud_data['present'],absent=stud_data['absent'],record=stud_data['record'])
        db.session.add(student_data)
        db.session.commit()

    return jsonify({'message' : 'updated'})

# For running the app and creating the database
if __name__=='__main__':
    db.create_all()
    app.run()

