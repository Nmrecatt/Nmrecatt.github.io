import os,datetime,face_recognition
from PIL import Image
from flask import Flask, flash, request, redirect, url_for,render_template,session
from werkzeug.utils import secure_filename
from flask_pymongo import PyMongo
import shutil
import bcrypt
import extract
import dynamic_fac
import gmail
import json_Extract
import create_excelhtml
import original
import webbrowser
from threading import Timer
app = Flask(__name__, static_url_path='/static')                   #  creating flask app
app.secret_key = '?&Kjhd$^ljm>x21'      # secret key for flash messages

app.config['MONGO_DBNAME'] = 'FacultyLogin'     # creating mongo db or accessing if it exist
app.config['MONGO_URI'] = 'mongodb://127.0.0.1:27017/FacultyLogin'  # mongo server

mongo = PyMongo(app)                            # running pymongo with flask app
# -------------------------------------------------- Home page route starting page -------------------------------------------------------------------------------
@app.route('/', methods=['POST','GET'])
def home():
    if 'username' in session:
        users = mongo.db.users
        login_user = users.find_one({'username' : session['username']})
        name=login_user["firstname"]+" "+login_user["lastname"]
        if login_user['username']=="ADMIN":
            return render_template('/admin/admin.html',username=name)
        return render_template('details.html',username=name)
    return render_template('login.html')

# ------------------------------------------------ Login page validations -------------------------------------------------------------
@app.route('/login', methods=['POST','GET'])
def login():
    if 'username' in session:
        return """<center><h2>Please logout to login as another user...<br><br> Click <a href="/">here</a> to Go back</h2></center>"""
    else:
        alert="alert"
        if request.method == 'POST':
            users = mongo.db.users
            login_user = users.find_one({'username' : request.form['UserName']})
            login_mail=users.find_one({'mailid': request.form['UserName']})
            if login_user:
                if bcrypt.hashpw(request.form['Password'].encode('utf-8'), login_user['password']) == login_user['password']:
                    user = login_user['username']
                    session['username'] = user
                    return redirect(url_for('home'))
            elif login_mail:
                if bcrypt.hashpw(request.form['Password'].encode('utf-8'), login_mail['password']) == login_mail['password']:
                    user = login_mail['username']
                    session['username'] = user
                    return redirect(url_for('home'))
            flash("Username or Password is invalid")
        return render_template("login.html",failed=alert)

# ------------------------------------------------------ Register page validations ---------------------------------------------------------------------------------------------------------------------------------------------------------
@app.route('/register', methods=['POST', 'GET'])
def register():
    if 'username' in session:
        return """<center><h2>Please logout to register as a new user...<br><br> Click <a href="/">here</a> to Go back</h2></center>"""
    else:
        alert="alert"
        if request.method == 'POST':
            users = mongo.db.users
            OTPS = mongo.db.OTPS
            Admin = users.find_one({'username' : 'ADMIN'})
            if(Admin):
                Admin_mailid = Admin['mailid']
                passcode = OTPS.find_one({'mailid': Admin_mailid})
            existing_user = users.find_one({'username' : request.form['UserName']})
            existing_mail= users.find_one({'mailid': request.form['Mailid']})
            if request.form['UserName']== "ADMIN" or (passcode and (bcrypt.hashpw(request.form['passcode'].encode('utf-8'), passcode['OTP'])) == passcode['OTP']):
                if existing_user is None and existing_mail is None:
                    hashpass = bcrypt.hashpw(request.form['Password'].encode('utf-8'), bcrypt.gensalt())
                    users.insert({'username' : request.form['UserName'], 'password' : hashpass , 'firstname' : request.form['First_Name'] , 'lastname' : request.form['Last_Name'], 'mailid': request.form['Mailid']})
                    #OTPS.remove({'mailid': Admin_mailid },True)
                    flash('successfully registered ...')
                    return render_template("login.html",passed=alert)
                flash('Username or Mailid is already exist')
                return render_template('register.html')
            flash('Invalid Passcode')
        return render_template('register.html')
# -------------------------------------------------- Forgot password page mail validation ------------------------------------------------------
@app.route("/forgot",methods=['POST','GET'])
def forgot():
    if 'username' in session:
        return """<center><h2>Unautnorised Access found please logout and try again...<br><br> Click <a href="/">here</a> to Go back</h2></center>"""
    else:
        if request.method == 'POST':
            users = mongo.db.users
            OTPS = mongo.db.OTPS
            mailid = request.form['mailid']
            valid_mailid = users.find_one({'mailid' : request.form['mailid']})
            existing_mail = OTPS.find_one({'mailid' : request.form['mailid']})
            print(existing_mail)
            if valid_mailid:
                OTPO = gmail.mail(mailid,1)
                OTP = bcrypt.hashpw(OTPO.encode('utf-8'), bcrypt.gensalt())
                if existing_mail:
                    OTPS.update_one({'mailid' : request.form['mailid']},{"$set" : {"OTP": OTP}})
                else:
                    OTPS.insert_one({'OTP' : OTP , 'mailid' : request.form['mailid']})
                return render_template("resetpassword.html",mailid = mailid)
            flash('Invalid Mail id')
        return render_template("forgot.html")

#----------------------------------------------------- Password reset page validations ----------------------------------------------------
@app.route("/resetpassword",methods=['POST','GET'])
def reset():
    if 'username' in session:
        return """<center><h2>Unautnorised Access found...<br><br> Click <a href="/">here</a> to Go back</h2></center>"""
    else:
        alert="alert"
        if request.method == 'POST':
            users = mongo.db.users
            OTPS = mongo.db.OTPS
            User_mail = OTPS.find_one({'mailid': request.form['mailid']})
            if User_mail:
                if(bcrypt.hashpw(request.form['OTP'].encode('utf-8'), User_mail['OTP'])) == User_mail['OTP']:
                    newpassword = bcrypt.hashpw(request.form['Password'].encode('utf-8'), bcrypt.gensalt())
                    users.update_one({'mailid':request.form['mailid']},{"$set":{"password":newpassword}})
                    OTPS.remove({'mailid':request.form['mailid']},True)
                    flash('Password reset successfull')
                    return render_template("login.html",passed=alert)
                flash('Invalid OTP')
            return render_template("resetpassword.html",mailid = User_mail['mailid'])
        else:
            return """<center><h2>Unautnorised Access found...<br><br> Click <a href="/">here</a> to Go back</h2></center>"""
# ----------------------------------------------------------------- Logout -----------------------------------------------------------------------------
@app.route("/logout",methods=["POST","GET"])
def logout():
    session.clear()
    return redirect(url_for("login"))

# ----------------------------------------------- method to create required paths --------------------------------------------------------------------
def createpath(dep,year,subj_code,hr):
    dep=dep.upper()
    year=year.upper()
    subj_code=subj_code.upper()
    temp=dep+"/"+year+"/"
    hr=hr.upper()
    # Paths of original images, individual face encoding error images, original images json file path 
    opath=str(default+temp+"original/")
    ojsonpath=str(default+temp+"original.json")
    erpath=str(default+temp+"error/")
    # Subjects folder Inner folders paths
    gpath=str(default+temp+"subjects/"+subj_code+"/group/"+hr+"/")
    epath=str(default+temp+"subjects/"+subj_code+"/extracted/")
    extracted_erpath=str(default+temp+"subjects/"+subj_code+"/error")
    cjsonpath=str(default+temp+"subjects/"+subj_code+"/original.json")
    return opath,ojsonpath,erpath,gpath,epath,extracted_erpath,cjsonpath

# ------------------------------------------------------------------- Required Paths -------------------------------------------------------------------

project=os.getcwd()+"/"             # to get the current path of server file
default=project+"static/images/"    # Adding static image file path to above project folder path
if not os.path.isdir(str(default)):
    os.mkdir(str(default))
# -------------------------------------------- details page given details validation of path -----------------------------------------------------
@app.route('/path', methods=['GET', 'POST'])
def checkpath():
    alert="alert"
    if request.method == "POST":
        dep=request.form["department"]
        year=request.form["year"]
        sub=request.form["subject"]
        hr=request.form["hour"]
        dep=dep.upper()
        sub=sub.upper()
        departments=dep.split(",")
        locations = mongo.db.locations
        location_value = locations.find({})
        for loc in location_value:
            location_list=loc['locations']
        for i in range(len(departments)):
            department=departments[i]
            opath,ojsonpath,erpath,gpath,epath,extracted_erpath,cjsonpath=createpath(department,year,sub,hr)
            flag=0
            if(os.path.isdir(gpath)):
                flag=1
                for filename in os.listdir(epath):
                    ipath=str(epath+filename)
                    os.remove(ipath)
                for filename in os.listdir(extracted_erpath):
                    ipath=str(extracted_erpath+filename)
                    os.remove(ipath)
            else:
                flag=0
        if(flag):
            return render_template('upload.html',dep=dep,year=year,sub=sub,hour=hr,locations=location_list)
        else:
            flash("Ivalid details")
    
            return render_template('details.html',fail=alert)
    else:
        return """<center><h2>Unautnorised Access found...<br><br> Click <a href="/">here</a> to Go back</h2></center>"""

# ----------------------------------------------------------- View attendance in details page  --------------------------------------------------
@app.route('/view_attendance',methods=['GET','POST'])
def view_attendance():
    if 'username' in session:
        users = mongo.db.users
        login_user = users.find_one({'username' : session['username']})
        name=login_user["firstname"]+" "+login_user["lastname"]
        if request.method == "POST":
            alert="alert"
            dep=request.form["department"]
            year=request.form["year"]
            sub=request.form["subject"]
            date=request.form["date"]
            dep=dep.upper()
            year=year.upper()
            sub=sub.upper()
            check_path=str(default+dep+"/"+year+"/subjects/"+sub+"/")
            if(os.path.isdir(check_path)):
                xl_fname=dep+"_"+year+"_"+sub+".html"
                xlhtmlpath=str(project+"templates/excel_html/"+xl_fname)
                excelpath=str(default+dep+"/"+year+"/subjects/"+sub+"/excel/")
                value,dt,msg= create_excelhtml.view_attendance_date(date,excelpath,xlhtmlpath)
                if login_user["username"] == "ADMIN":
                    return render_template("/admin/view_attendance.html",dep=dep,year=year,sub=sub,view_excel=value,date_msg=msg,date=dt,username=name)    
                return render_template("details.html",dep=dep,year=year,sub=sub,view_excel=value,date_msg=msg,date=dt,username=name)
            else:
                flash("Invalid details")
                if login_user["username"] == "ADMIN":
                    return render_template("/admin/view_attendance.html",username=name,fail=alert)
                return render_template("details.html",username=name,fail=alert)
        if login_user["username"] == "ADMIN":
            return render_template("/admin/view_attendance.html",username=name)
        return render_template("details.html",username=name)
    return render_template("login.html")

# ----------------------------------------------------------- uploading image --------------------------------------------------------
@app.route('/upload',methods=['GET','POST'])
def imgupload():
    success="success"
    if request.method == "POST":
        dep=request.form["department"]
        year=request.form["year"]
        sub=request.form["subject"]
        hr=request.form["hour"]
        total=request.form["total"]
        departments=dep.split(",")
        locations = mongo.db.locations
        location_value = locations.find({})
        for loc in location_value:
            location_list=loc['locations']
        filename=str(datetime.date.today())
        if request.files:
            for department in departments:
                opath,ojsonpath,erpath,gpath,epath,extracted_erpath,cjsonpath=createpath(department,year,sub,hr)
                image = request.files["image"]
                i=1
                while(i):
                    fpath1=gpath+filename+"_"+str(i)+".png"
                    fpath2=gpath+filename+"_"+str(i)+".jpg"
                    if(os.path.isfile(fpath1) or os.path.isfile(fpath2)):
                        i+=1
                        continue
                    else:
                        app.config["IMAGE_UPLOADS"]=gpath
                        filename=filename+"_"+str(i)
                        filename1=filename+".jpg"
                        image.save(os.path.join(app.config["IMAGE_UPLOADS"], filename1))
                        for department in departments:
                            if department!=departments[0]:
                                dest_path=str(default+department+"/"+year+"/subjects/"+sub+"/group/"+hr+"/")
                                shutil.copy(fpath2,dest_path)
                        count=extract.extract_count(fpath2,epath,filename)
                        flash("Your image is uploaded successfully")
                        return render_template("upload.html",success=success,dep=dep,year=year,sub=sub,hour=hr,count=count,total=total,locations=location_list)
                        break
    else:
        return """<center><h2>Unautnorised Access found...<br><br> Click <a href="/">here</a> to Go back</h2></center>"""
# ---------------------------------------------------------  To Discard Image previously uploaded ----------------------------------------------
@app.route('/discard',methods=['GET','POST'])
def discard():
    if request.method == "POST":
        dep=request.form["department"]
        year=request.form["year"]
        sub=request.form["subject"]
        hr=request.form["hour"]
        count=request.form["count"]
        total=request.form["total"]
        count=float(count)
        total=float(total)
        locations = mongo.db.locations
        location_value = locations.find({})
        departments=dep.split(",")
        for loc in location_value:
            location_list=loc['locations']
        for department in departments:
            opath,ojsonpath,erpath,gpath,epath,extracted_erpath,cjsonpath=createpath(department,year,sub,hr)
            filename=str(datetime.date.today())
            i=1
            while(i):
                fpath1=gpath+filename+"_"+str(i)+".jpg"
                fpath2=gpath+filename+"_"+str(i+1)+".jpg"
                if(os.path.isfile(fpath2)):
                    i+=1
                    continue
                else:
                    os.remove(fpath1)
                    break;
            if(departments.index(department)==0):
                while(int(count)>=1):
                    fpath=epath+filename+"_"+str(i)+"-"+str(int(count))+".jpg"
                    os.remove(fpath)
                    count=int(count-1)
        total=int(total-count)
        return render_template("upload.html",dep=dep,year=year,sub=sub,hour=hr,total=total,locations=location_list)
    else:
        return """<center><h2>Unautnorised Access found...<br><br> Click <a href="/">here</a> to Go back</h2></center>"""

# -------------------------------------------------- Marking attendance for presenties --------------------------------------------------
@app.route('/mark_attendance',methods=['GET','POST'])
def mark_attendance():
    success="success"
    if request.method == "POST":
        dep=request.form["department"].upper()
        year=request.form["year"].upper()
        sub=request.form["subject"].upper()
        hr=request.form["hour"].upper()
        departments=dep.split(",")
        hr=request.form["hour"]
        opath,ojsonpath,erpath,gpath,epath,extracted_erpath,cjsonpath=createpath(departments[0],year,sub,hr)
        present,l=dynamic_fac.match(opath,epath,extracted_erpath,departments,year,sub,hr)
        present=str(present)
        images=[]
        for filename in os.listdir(epath):
            ipath=str("/static/images/"+dep+"/"+year+"/subjects/"+sub+"/extracted/"+filename)
            images.append(ipath)
        for filename in os.listdir(extracted_erpath):
            ipath=str("/static/images/"+dep+"/"+year+"/subjects/"+sub+"/error/"+filename)
            images.append(ipath)
        flash("Period-"+hr+" Attendance of "+dep+"-"+year+" " +sub+" subject is marked successfully for "+present+" students")
        return render_template("error.html",dep=dep,departments_list=departments,year=year,sub=sub,hour=hr,present=present,success=success,images=images,absent_list=l)
    else:
        return """<center><h2>Unautnorised Access found...<br><br> Click <a href="/">here</a> to Go back</h2></center>"""

# -------------------------------------------------- Retaking image for error images occured in group image --------------------------------------
@app.route('/retake',methods=['GET','POST'])
def retake():
    success="success"
    if request.method == "POST":
        dep=request.form["department"]
        year=request.form["year"]
        sub=request.form["subject"]
        hr=request.form["hour"]
        total=request.form["total"]
        departments=dep.split(",")
        locations = mongo.db.locations
        location_value = locations.find({})
        for loc in location_value:
            location_list=loc['locations']
        opath,ojsonpath,erpath,gpath,epath,extracted_erpath,cjsonpath=createpath(departments[0],year,sub,hr)
        for filename in os.listdir(epath):
            ipath=str(project+"static/images/"+departments[0]+"/"+year+"/subjects/"+sub+"/extracted/"+filename)
            os.remove(ipath)
        for filename in os.listdir(erpath):
            ipath=str(project+"static/images/"+departments[0]+"/"+year+"/subjects/"+sub+"/error/"+filename)
            os.remove(ipath)
        #return render_template("upload.html",dep=dep,year=year,sub=sub,hour=hr,total=total,locations=location_list)
        return render_template("upload.html",dep=dep,year=year,sub=sub,hour=hr,total=total,locations=location_list)
    else:
        return """<center><h2>Unautnorised Access found...<br><br> Click <a href="/">here</a> to Go back</h2></center>"""

# ------------------------------------------------------------ ADMIN Home page ----------------------------------------------------------------------
@app.route('/admin_page',methods=['GET','POST'])
def admin_page():
    if 'username' in session:
        users = mongo.db.users
        login_user = users.find_one({'username' : session['username']})
        name=login_user["firstname"]+" "+login_user["lastname"]
        if login_user["username"] == "ADMIN":
            return render_template('/admin/admin.html',username=name)
        else:
            return """<center><h2>Unautnorised Access found... You are not an admin<br><br> Click <a href="/">here</a> to Go back</h2></center>"""
    else:
        return """<center><h2>Unautnorised Access found... You are not an admin<br><br> Click <a href="/">here</a> to Go back</h2></center>"""

# ------------------------------------------------------------ Hour Home page ----------------------------------------------------------------------
@app.route('/Hours_page',methods=['GET','POST'])
def Hours_page():
    if 'username' in session:
        users = mongo.db.users
        login_user = users.find_one({'username' : session['username']})
        name=login_user["firstname"]+" "+login_user["lastname"]
        if login_user["username"] == "ADMIN":
            return render_template('/admin/hours.html',username=name)
        else:
            return """<center><h2>Unautnorised Access found... You are not an admin<br><br> Click <a href="/">here</a> to Go back</h2></center>"""
    else:
        return """<center><h2>Unautnorised Access found... You are not an admin<br><br> Click <a href="/">here</a> to Go back</h2></center>"""

# -------------------------------------------------------- ADMIN Generate Encodings page -------------------------------------------------------------------
@app.route('/Generate_Encodings_page',methods=['GET','POST'])
def Generate_Encodings_page():
    if 'username' in session:
        users = mongo.db.users
        login_user = users.find_one({'username' : session['username']})
        name=login_user["firstname"]+" "+login_user["lastname"]
        if login_user["username"] == "ADMIN":
            return render_template('/admin/Generate_Encodes.html',username=name)
        else:
            return """<center><h2>Unautnorised Access found... You are not an admin<br><br> Click <a href="/">here</a> to Go back</h2></center>"""
    else:
        return """<center><h2>Unautnorised Access found... You are not an admin<br><br> Click <a href="/">here</a> to Go back</h2></center>"""

# -------------------------------------------------------- ADMIN Seperate Encodings page -------------------------------------------------------------------
@app.route('/Seperate_Encodings_page',methods=['GET','POST'])
def Seperate_Encodings_page():
    if 'username' in session:
        users = mongo.db.users
        login_user = users.find_one({'username' : session['username']})
        name=login_user["firstname"]+" "+login_user["lastname"]
        if login_user["username"] == "ADMIN":
            return render_template('/admin/Seperate_Encodes.html',username=name)
        else:
            return """<center><h2>Unautnorised Access found... You are not an admin<br><br> Click <a href="/">here</a> to Go back</h2></center>"""
    else:
        return """<center><h2>Unautnorised Access found... You are not an admin<br><br> Click <a href="/">here</a> to Go back</h2></center>"""

# ------------------------------------------------------------------- ADMIN Make Folders -------------------------------------------------------------------
@app.route('/registration_control_page',methods=['GET','POST'])
def Registration_Control_page():
    if 'username' in session:
        users = mongo.db.users
        login_user = users.find_one({'username' : session['username']})
        name=login_user["firstname"]+" "+login_user["lastname"]
        if login_user["username"] == "ADMIN":
            return render_template('/admin/Registration_control.html',username=name)
        else:
            return """<center><h2>Unautnorised Access found... You are not an admin<br><br> Click <a href="/">here</a> to Go back</h2></center>"""
    else:
        return """<center><h2>Unautnorised Access found... You are not an admin<br><br> Click <a href="/">here</a> to Go back</h2></center>"""
# -------------------------------------------------------- ADMIN view attendance page-------------------------------------------------------------------
@app.route('/view_attendance_page',methods=['GET','POST'])
def view_attendance_page():
    if 'username' in session:
        users = mongo.db.users
        login_user = users.find_one({'username' : session['username']})
        name=login_user["firstname"]+" "+login_user["lastname"]
        if login_user["username"] == "ADMIN":
            return render_template('/admin/view_attendance.html',username=name)
        else:
            return """<center><h2>Unautnorised Access found... You are not an admin<br><br> Click <a href="/">here</a> to Go back</h2></center>"""
    else:
        return """<center><h2>Unautnorised Access found... You are not an admin<br><br> Click <a href="/">here</a> to Go back</h2></center>"""

# ------------------------------------------------------------------- ADMIN Make Folders -------------------------------------------------------------------

@app.route('/Make_Folders',methods=['GET','POST'])
def Make_Folders():
    alert="alert"
    flag=0
    if request.method == "POST":
        dep=request.form["department"].upper()
        year=request.form["year"]
        subjects=request.form["subject_codes"].upper()
        subject_codes=subjects.split(",")
        hours=mongo.db.hours
        hours_value=hours.find({})
        for hour in hours_value:
            hr=hour["hours"]
        users = mongo.db.users
        login_user = users.find_one({'username' : session['username']})
        name=login_user["firstname"]+" "+login_user["lastname"]
        if login_user["username"] == "ADMIN":
            # Creating Folders path
            dep_path=default+dep+"/"                # ../FRBAA/static/images/Department path
            year_path=dep_path+str(year)+"/"        # ../FRBAA/static/images/Department/year path
            original_path=year_path+"original/"     # ../FRBAA/static/images/Department/year/original path
            encode_err_path=year_path+"error/"      # ../FRBAA/static/images/Department/year/error path
            subjects_path=year_path+"subjects/"     # ../FRBAA/static/images/Department/year/subjects path

            # Checking and creating not existing folders as per admin request.

            if not os.path.isdir(str(dep_path)):    # Checking Department path is not existing
                os.mkdir(str(dep_path))             # Creating Department folder as it is not existing
                flag=1
            if not os.path.isdir(str(year_path)):   # Checking Year path is is not existing
                os.mkdir(str(year_path))            # Creating Year folder inside department folder as it doesn't exist
                flag=1
            if not os.path.isdir(str(original_path)):   # Checking original path is not existing
                os.mkdir(str(original_path))            # Creating original folder inside year folder as it doesn't exist
                flag=1
            if not os.path.isdir(str(encode_err_path)):   # Checking original path is not existing
                os.mkdir(str(encode_err_path))            # Creating original folder inside year folder as it doesn't exist
                flag=1
            if not os.path.isdir(str(subjects_path)):   # Checking error path is not existing
                os.mkdir(str(subjects_path))            # Creating error folder inside year folder as it doesn't exist
                flag=1
            for i in range(len(subject_codes)):        # Iterating subject codes to check they exist or not
                if len(subject_codes[i])!=0:            # Checking given subject value is not a null
                    subject_code_path=str(subjects_path+subject_codes[i]+"/") # Creating individual subject code path
                    if not os.path.isdir(str(subject_code_path)):             #Checking subeject folder exist or not
                        os.mkdir(subject_code_path)                           # Creating subject code folde0r if it doesn't exit
                        flag=1
                    if not os.path.isdir(str(subject_code_path+"error/")):  # Checking for error folder inside subject code folder
                        os.mkdir(str(subject_code_path+"error/"))           # Creating error folder inside subject code folder
                        flag=1
                    if not os.path.isdir(str(subject_code_path+"extracted/")): # Checking for extracted folder inside the subject code folder
                        os.mkdir(str(subject_code_path+"extracted/"))           # Creating extracted folder inside the subject code folder
                        flag=1
                    if not os.path.isdir(str(subject_code_path+"excel/")):      # Checking for excel folder inside the subject code folder
                        os.mkdir(str(subject_code_path+"excel/"))               # Creating excel folder inside the subject code folder
                        flag=1
                    if not os.path.isdir(str(subject_code_path+"group/")):      # Checking for group folder inside the subject code folder
                        os.mkdir(str(subject_code_path+"group/"))               # Creating group folder insidet the subject code folder
                        flag=1
                    for j in range(int(hr)):                                            # Iteration to check each hour folder inside group folder
                        if not os.path.isdir(str(subject_code_path+"group/"+str(j+1))): # Checking individual hour folder inside the group folder
                            os.mkdir(str(subject_code_path+"group/"+str(j+1)))          # Creating the individual hour folder inside the group folder
                            flag=1
            if flag==1:
                flash("Requested folders are ready to use")
                return redirect("/admin_page")
            else:
                flash("Requested folders already exist for "+str(dep)+"-"+year+" year")
                return render_template('/admin/admin.html',username=name,fail=alert)
        else:
            return """<center><h2>Unautnorised Access found... You are not an admin<br><br> Click <a href="/">here</a> to Go back</h2></center>"""
    else:
        return """<center><h2>Unautnorised Access found... You are not an admin<br><br> Click <a href="/admin_page">here</a> to Go back</h2></center>"""

# ----------------------------------------- Save Hours ----------------------------------------
@app.route('/Save_Hour',methods=['GET','POST'])
def Save_Hour():
    alert="alert"
    if 'username' in session:
        users = mongo.db.users
        hours=mongo.db.hours
        login_user = users.find_one({'username' : session['username']})
        name=login_user["firstname"]+" "+login_user["lastname"]
        if login_user["username"] == "ADMIN":
            if request.method == "POST":
                new_hour=request.form["hour"]
                hour_value = list(hours.find({}))
                if len(hour_value)!= 0:
                    hours_value = hours.find({})
                    for hour in hours_value:
                        existing_hour = hour["hours"]
                        hours.update({"hours":existing_hour},{"$set":{"hours":new_hour}})
                        break
                else:
                    hours.insert({"hours" : new_hour})
                flash("Number of hours per day have been set to "+str(new_hour)+" successfully")
                return render_template('/admin/hours.html',username=name)
            else:
                return """<center><h2>Unautnorised Access found... You are not an admin<br><br> Click <a href="/Hours_page">here</a> to Go back</h2></center>"""
        else:
            return """<center><h2>Unautnorised Access found... You are not an admin<br><br> Click <a href="/Hours_page">here</a> to Go back</h2></center>"""

# ----------------------------------------- Admin Generates Encodings ----------------------------------------
@app.route('/Generate_Encodings',methods=['GET','POST'])
def Generate_Encodings():
    alert="alert"
    if request.method == "POST":
        dep=request.form["department"]
        year=request.form["year"]
        opath,ojsonpath,erpath,gpath,epath,extracted_erpath,cjsonpath=createpath(dep,year,"","")
        if os.path.isdir(opath) and os.path.isdir(erpath):
            for filename in os.listdir(erpath):
                ipath=str(erpath+filename)
                os.remove(ipath)
            print(erpath)
            error_image_filename=original.Encodings(opath,erpath,ojsonpath)
            print(error_image_filename)
            if len(error_image_filename)!=0:
                if 'username' in session:
                    users = mongo.db.users
                    login_user = users.find_one({'username' : session['username']})
                    name=login_user["firstname"]+" "+login_user["lastname"]
                    if login_user["username"] == "ADMIN":
                        flash("Please retake original images for the following students of "+dep+"-"+year)
                        return render_template('/admin/Generate_Encodes.html',username=name,filenames=error_image_filename,fail=alert)
                    else:
                        return """<center><h2>Unautnorised Access found... You are not an admin<br><br> Click <a href="/admin_page">here</a> to Go back</h2></center>"""
            else:
                flash("Encodings Generated successfully for the students of "+dep+"-"+year)
                return redirect(url_for("Generate_Encodings_page"))
        else:
            flash("Invalid details")
            if 'username' in session:
                users = mongo.db.users
                login_user = users.find_one({'username' : session['username']})
                name=login_user["firstname"]+" "+login_user["lastname"]
                if login_user["username"] == "ADMIN":
                    return render_template('/admin/Generate_Encodes.html',username=name,fail=alert)
                else:
                    return """<center><h2>Unautnorised Access found... You are not an admin<br><br> Click <a href="/Generate_Encodings_page">here</a> to Go back</h2></center>"""
    else:
        return """<center><h2>Unautnorised Access found... You are not an admin<br><br> Click <a href="/Generate_Encodings_page">here</a> to Go back</h2></center>"""

# ----------------------------------------- Admin Seperate Encodings ----------------------------------------
@app.route('/Seperate_Encodings',methods=['GET','POST'])
def Seperate_Encodings():
    alert="alert"
    users = mongo.db.users
    login_user = users.find_one({'username' : session['username']})
    name=login_user["firstname"]+" "+login_user["lastname"]
    if login_user["username"] == "ADMIN":
        if request.method == "POST":
            dep=request.form["department"].upper()
            year=request.form["year"].upper()   
            sub=request.form["subject_code"].upper()
            path=default+dep+"/"+year+"/subjects/"+sub+"/"
            if os.path.isdir(path):
                msg=json_Extract.json_extractor(dep,year,sub,default,path)
                if len(msg)==0:
                    flash("Encodings Seperated for "+dep+"-"+year+" "+sub+" subject")
                    return render_template('/admin/Seperate_Encodes.html',username=name)
                else:
                    flash(msg)
            else:
                flash("Invalid details")
            return render_template('/admin/Seperate_Encodes.html',username=name,fail=alert)
        else:
            return """<center><h2>Unautnorised Access found... You are not an admin<br><br> Click <a href="/Seperate_Encodings_page">here</a> to Go back</h2></center>"""
    else:
        return """<center><h2>Unautnorised Access found... You are not an admin<br><br> Click <a href="/Seperate_Encodings_page">here</a> to Go back</h2></center>"""

# ----------------------------------- File copier ----------------------------------------------
def file_copy(source):
    target=project+"templates/"+"register.html"
    shutil.copy(source,target)

# ------------------------------------ Open Registrations ---------------------------------------------
@app.route('/Open_registrations',methods=['GET','POST'])
def Open_registrations():
    if request.method == "POST":
        source=project+"templates/"+"register_template.html"
        file_copy(source)
        flash("Registrations are open now")
        return redirect(url_for('Registration_Control_page'))
    else:
        return """<center><h2>Unautnorised Access found... You are not an admin<br><br> Click <a href="/Registration_Control_page">here</a> to Go back</h2></center>"""
# ------------------------------------ close Registrations ---------------------------------------------
@app.route('/Close_registrations',methods=['GET','POST'])
def Close_registrations():
    users = mongo.db.users
    OTPS = mongo.db.OTPS
    Admin = users.find_one({'username' : 'ADMIN'})
    if(Admin):
        Admin_mailid = Admin['mailid']
        passcode = OTPS.find_one({'mailid': Admin_mailid})
    if request.method == "POST":
        source=project+"templates/"+"reg_closed_template.html"
        file_copy(source)
        OTPS.remove({'mailid': Admin_mailid },True)
        flash("Registrations are closed successfully")
        return redirect(url_for('Registration_Control_page'))
    else:
        return """<center><h2>Unautnorised Access found... You are not an admin<br><br> Click <a href="/Registration_Control_page">here</a> to Go back</h2></center>"""

# ------------------------------------ Generate Passcode ---------------------------------------------
@app.route('/Generate_Passcode',methods=['GET','POST'])
def Generate_Passcode():
    if request.method == "POST":
        users = mongo.db.users
        OTPS = mongo.db.OTPS
        Admin_valid = users.find_one({'username' : 'ADMIN' })
        Admin_mailid = Admin_valid['mailid']
        existing_mail = OTPS.find_one({'mailid' : Admin_mailid})
        
        if Admin_valid:
            OTPO = gmail.mail(Admin_mailid,0)
            OTP = bcrypt.hashpw(OTPO.encode('utf-8'), bcrypt.gensalt())
            if existing_mail:
                OTPS.update_one({'mailid' : Admin_mailid},{"$set" : {"OTP": OTP}})
            else:
                OTPS.insert_one({'OTP' : OTP , 'mailid' : Admin_mailid})
        flash('New passcode to Register : '+OTPO)
        return redirect(url_for('Registration_Control_page'))
    else:
        return """<center><h2>Unautnorised Access found... You are not an admin<br><br> Click <a href="/Generate_Passcode">here</a> to Go back</h2></center>"""

#---------------------------------- Locations page -------------------------------------------
@app.route('/Locations_page',methods=['GET','POST'])
def Locations_page():
    if 'username' in session:
        users = mongo.db.users
        login_user = users.find_one({'username' : session['username']})
        name=login_user["firstname"]+" "+login_user["lastname"]
        if login_user["username"] == "ADMIN":
            return render_template('/admin/Locations.html',username=name)
        else:
            return """<center><h2>Unautnorised Access found... You are not an admin<br><br> Click <a href="/Locations_page">here</a> to Go back</h2></center>"""
    else:
        return """<center><h2>Unautnorised Access found... You are not an admin<br><br> Click <a href="/Locations_page">here</a> to Go back</h2></center>"""
# -----------------------------------
@app.route('/save_locations',methods=['GET','POST'])
def save_locations():
    if 'username' in session:
        alert="alert"
        flag=0
        users = mongo.db.users
        locations = mongo.db.locations
        login_user = users.find_one({'username' : session['username']})
        name=login_user["firstname"]+" "+login_user["lastname"]
        if login_user["username"] == "ADMIN":
            if request.method == "POST":
                lat=request.form["latitude"]
                lon=request.form["longitude"]
                if(len(lat)==0 and len(lon)==0):
                    flash("Please get your current location to save")
                    return render_template('/admin/Locations.html',username=name,fail=alert)
                lat=float(lat)
                lon=float(lon)
                Locations=[float(lat),float(lon)]
                location_value = locations.find({})
                result = list(location_value)
                if len(result)!= 0:
                    location_value = locations.find({})
                    for loc in location_value:
                        existing_loc = loc['locations']
                        new_loc = []
                        for ls in existing_loc:
                            if Locations == ls:
                                flash("Location details already exist")
                                return render_template('/admin/Locations.html',username=name,fail=alert)
                                break
                            else:
                                new_loc.append(ls)
                        new_loc.append(Locations)
                        locations.update({'locations':existing_loc},{"$set":{"locations":new_loc}})
                        flag=1
                        break
                else:
                    locations.insert({'locations' : [Locations]})
                    flash("New location details are saved")
            if flag==1:
                flash("Location details updated successfully")
            return render_template('/admin/Locations.html',username=name)
        else:
            return """<center><h2>Unautnorised Access found... You are not an admin<br><br> Click <a href="/Locations_page">here</a> to Go back</h2></center>"""
    else:
        return """<center><h2>Unautnorised Access found... You are not an admin<br><br> Click <a href="/Locations_page">here</a> to Go back</h2></center>"""

#-----------------------------------------------------------Removing exisiting locations ----------------------------------------------
@app.route('/remove_locations',methods=['GET','POST'])
def remove_locations():
    if 'username' in session:
        users = mongo.db.users
        location = mongo.db.locations
        login_user = users.find_one({'username' : session['username']})
        name=login_user["firstname"]+" "+login_user["lastname"]
        if login_user["username"] == "ADMIN":
            if request.method == "POST":
                location.drop()
                flash("Location details removed successfully")
            return render_template('/admin/Locations.html',username=name)
        else:
            return """<center><h2>Unautnorised Access found... You are not an admin<br><br> Click <a href="/Locations_page">here</a> to Go back</h2></center>"""
    else:
        return """<center><h2>Unautnorised Access found... You are not an admin<br><br> Click <a href="/Locations_page">here</a> to Go back</h2></center>"""

# ---------------------------------------------------------------------------------------------------------------------------
if __name__=='__main__':
	def browser():
		webbrowser.open("http://0.0.0.0:8080")
	Timer(3,browser).start()
    app.run(host="0.0.0.0",port="8080")
