from flask import render_template, url_for, flash, redirect, request, jsonify
from insurance import app, db, bcrypt, mail
from insurance.forms import *
from insurance.models import *
from flask_login import login_user, current_user, logout_user, login_required
from insurance.flask_celery import make_celery
import insurance.EligibilityStatus.HPSJ.EligibilityCheck as HPSJEligibilityCheck
import insurance.EligibilityStatus.Prime.EligibilityCheck as PrimeEligibilityCheck
import insurance.EligibilityStatus.MediCal.EligibilityCheck as MediCalEligibilityCheck
import insurance.EligibilityStatus.PHP.EligibilityCheck as PHPEligibilityCheck
import insurance.NewRequest.HSPJ.AuthRequest as HSPJAuth
import insurance.NewRequest.Prime.AuthRequest as PrimeAuth
import insurance.NewRequest.MediCal.AuthRequest as MediCalAuth
import insurance.NewRequest.PHP.AuthRequest as PHPAuth
import insurance.PendingStatus.HPSJ.PendingStatus as HPSJPending
import insurance.PendingStatus.Prime.PendingStatus as PrimePending
import insurance.PendingStatus.MediCal.PendingStatus as MediCalPending
import insurance.PendingStatus.PHP.PendingStatus as PHPPending
import insurance.WebPT.WebPTEntry as WebPT
from datetime import datetime
import os, csv
from io import StringIO
from flask import make_response
from flask_mail import Message

import logging
import boto3
from botocore.exceptions import ClientError

from dotenv import load_dotenv
load_dotenv(verbose=True)


celery = make_celery(app)

ALLOWED_EXTENSIONS = set(['pdf', 'png', 'jpg', 'jpeg'])


def aws_session(region_name='us-east-1'):
    return boto3.session.Session(aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                                aws_secret_access_key=os.getenv('AWS_ACCESS_KEY_SECRET'),
                                region_name=region_name)


# def make_bucket(name, acl):
#     session = aws_session()
#     s3_resource = session.resource('s3')
#     return s3_resource.create_bucket(Bucket=name, ACL='public-read')


def upload_file_to_bucket(bucket_name, file_path, folder_name):
    session = aws_session()
    s3_resource = session.resource('s3')
    file_dir, file_name = os.path.split(file_path)

    bucket = s3_resource.Bucket(bucket_name)
    bucket.upload_file(
      Filename=file_path,
      Key=folder_name + "/" + file_name,
      ExtraArgs={'ACL': 'public-read'}
    )

    s3_url = f"https://{bucket_name}.s3.amazonaws.com/{file_name}"
    return s3_url


def delete_folder_from_bucket(bucket_name, folder_name):
    s3_client = boto3.client('s3')
    PREFIX = folder_name + '/'
    response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=PREFIX)

    for object in response['Contents']:
        print('Deleting', object['Key'])
        s3_client.delete_object(Bucket=bucket_name, Key=object['Key'])


def upload_file(file_name, bucket, object_name=None):
    """Upload a file to an S3 bucket

    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False
    """

    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = file_name

    # Upload the file
    s3_client = boto3.client('s3')
    buckets_list = s3_client.list_buckets()
    try:
        if not bucket in [bb["Name"] for bb in buckets_list["Buckets"]]:
            response = s3_client.create_bucket(
                Bucket=bucket,
                # CreateBucketConfiguration={
                #     'LocationConstraint': 'eu-west-1',
                # },
            )

        response = s3_client.upload_file(file_name, bucket, object_name)
    except ClientError as e:
        logging.error(e)
        return False
    return True

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/admin", methods=['GET', 'POST'])
def admin():
    if current_user.is_authenticated:
        if current_user.get_id() == '1':
            users = User.query\
            .join(Company, Company.id==User.company_id)\
            .add_columns(User.id, User.username, User.email, Company.name, User.admin).all()
            return render_template('admin.html', title='Admin', users=users)
        else:
            logout_user()
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data) and user.id == 1:
            login_user(user, remember=form.remember.data)
            return redirect(url_for('admin'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)

@app.route("/make_admin/<int:id>", methods=['POST'])
@login_required
def make_admin(id):
    if current_user.get_id() == '1':
        user = User.query.filter_by(id=id).first()
        try:
            user.active = True
            user.admin = True
            db.session.commit()
            flash('User successfully made admin', 'success')
        except:
            db.session.rollback()
            flash('User could not be made admin', 'danger')
    return redirect(url_for('admin'))

@app.route("/delete_user/<int:id>", methods=['POST'])
@login_required
def delete_user(id):
    if current_user.get_id() == '1':
        user = User.query.filter_by(id=id).first()
        try:
            db.session.delete(user)
            db.session.commit()
            flash('User successfully deleted', 'success')
        except:
            db.session.rollback()
            flash('User could not be deleted', 'danger')
    return redirect(url_for('admin'))

@app.route("/company", methods=['GET', 'POST'])
@login_required
def manage_company():
    if current_user.get_id() == '1':
        form = CompanyForm()
        if form.validate_on_submit():
            try:
                company = Company(name=form.name.data)
                db.session.add(company)
                db.session.commit()
                flash('Company successfully added', 'success')
            except:
                db.session.rollback()
                flash('Company could not be added', 'danger')
        else:
            companies = Company.query.all()
            return render_template('company.html', form=form, title='Admin', companies=companies)
    return redirect(url_for('manage_company'))

@app.route("/delete_company/<int:id>", methods=['POST'])
@login_required
def delete_company(id):
    if current_user.get_id() == '1':
        try:
            company = Company.query.filter_by(id=id).first()
            db.session.delete(company)
            db.session.commit()
            flash('Company successfully deleted', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Company could not be deleted', 'danger')
    return redirect(url_for('manage_company'))

@app.route("/company_admin", methods=['GET', 'POST'])
@login_required
def company_admin():
    user = User.query.get(current_user.get_id())
    if user.admin == True:
        users = User.query.filter_by(company_id=user.company_id).all()
        return render_template('companyadmin.html', title='CAdmin', users=users)
    return redirect(url_for('hpsj'))

@app.route("/activate_user/<int:id>", methods=['POST'])
@login_required
def activate_user(id):
    user = User.query.get(current_user.get_id())
    if user.admin == True:
        user = User.query.filter_by(id=id).first()
        try:
            user.active = True
            db.session.commit()
            flash('User successfully activated', 'success')
        except:
            db.session.rollback()
            flash('User could not be activated', 'danger')
    return redirect(url_for('company_admin'))

@app.route("/delete_company_user/<int:id>", methods=['POST'])
@login_required
def delete_company_user(id):
    user = User.query.get(current_user.get_id())
    if user.admin == True:
        user = User.query.filter_by(id=id).first()
        try:
            db.session.delete(user)
            db.session.commit()
            flash('User successfully deleted', 'success')
        except:
            db.session.rollback()
            flash('User could not be deleted', 'danger')
    return redirect(url_for('company_admin'))

@app.route("/")
@app.route("/hpsj")
@app.route("/home", methods=['GET', 'POST'])
@login_required
def hpsj():
    form = HPSJRequestForm()
    user = User.query.get(current_user.get_id())
    if request.method == 'POST' and not request.form.get('memberid'):
        icd10_1_data = form.icd10_1.data
        icd10_2_data = form.icd10_2.data
        icd10_3_data = form.icd10_3.data
        icd10_4_data = form.icd10_4.data
        icd10_5_data = form.icd10_5.data
        icd10_6_data = form.icd10_6.data
        icd10_7_data = form.icd10_7.data
        cpt_1_data = form.cpt_1.data
        cpt_2_data = form.cpt_2.data
        cpt_3_data = form.cpt_3.data
        cpt_4_data = form.cpt_4.data
        cpt_5_data = form.cpt_5.data
        cpt_6_data = form.cpt_6.data
        cpt_7_data = form.cpt_7.data
        unit_1_data = form.unit_1.data
        unit_2_data = form.unit_2.data
        unit_3_data = form.unit_3.data
        unit_4_data = form.unit_4.data
        unit_5_data = form.unit_5.data
        unit_6_data = form.unit_6.data
        unit_7_data = form.unit_7.data
        message = form.message.data
        frequency = form.frequency.data
        name = form.name.data
        template = HPSJTemplate(name=name, icd1=icd10_1_data, icd2=icd10_2_data, icd3=icd10_3_data,
                                icd4=icd10_4_data, icd5=icd10_5_data, icd6=icd10_6_data, icd7=icd10_7_data,
                                CPT1=cpt_1_data, CPT2=cpt_2_data, CPT3=cpt_3_data, CPT4=cpt_4_data,
                                CPT5=cpt_5_data, CPT6=cpt_6_data, CPT7=cpt_7_data, CPTUnit1=unit_1_data,
                                CPTUnit2=unit_2_data, CPTUnit3=unit_3_data, CPTUnit4=unit_4_data,
                                CPTUnit5=unit_5_data, CPTUnit6=unit_6_data, CPTUnit7=unit_7_data,
                                frequency=frequency, message=message, company_id=user.company_id)
        db.session.add(template)
        db.session.commit()
        return redirect(url_for('hpsj'))
    elif request.form.get('memberid'):
        company = Company.query.filter_by(id=user.company_id).first()
        if 'files[]' not in request.files:
            flash('No File', 'danger')
            return redirect(request.url)

        files = request.files.getlist('files[]')
        file_start = company.file_counter
        file_num = company.file_counter

        for file in files:
            if file and allowed_file(file.filename):
                file_num += 1
                extension = file.filename.rsplit('.', 1)[1].lower()
                upload_folder = os.getcwd() + '/uploads'
                if not os.path.isdir(upload_folder):
                    os.mkdir(upload_folder)
                file_path = os.path.join(upload_folder, file.filename)
                print("######### file path = " + file_path)

                # filename = company.name + '_{}.{}'.format(file_num, extension)
                if os.path.exists(file_path) :
                    os.remove(file_path)
                    print("file was removed.")
                try:
                    file.save(file_path)
                    print("file was saved.")
                except:
                    print("file save error")

                try:
                    upload_file_to_bucket('quickauths', file_path, "hpsj/" + company.name)
                except :
                    print("Upload error")
                
        
        company.file_counter = file_num
        if form.memberid.data:
            memberid = form.memberid.data
            icd10_1_data = form.icd10_1.data
            icd10_2_data = form.icd10_2.data
            icd10_3_data = form.icd10_3.data
            icd10_4_data = form.icd10_4.data
            icd10_5_data = form.icd10_5.data
            icd10_6_data = form.icd10_6.data
            icd10_7_data = form.icd10_7.data
            cpt_1_data = form.cpt_1.data
            cpt_2_data = form.cpt_2.data
            cpt_3_data = form.cpt_3.data
            cpt_4_data = form.cpt_4.data
            cpt_5_data = form.cpt_5.data
            cpt_6_data = form.cpt_6.data
            cpt_7_data = form.cpt_7.data
            unit_1_data = form.unit_1.data
            unit_2_data = form.unit_2.data
            unit_3_data = form.unit_3.data
            unit_4_data = form.unit_4.data
            unit_5_data = form.unit_5.data
            unit_6_data = form.unit_6.data
            unit_7_data = form.unit_7.data
            start_date = form.start_date.data
            end_date = form.end_date.data
            file_path = str(file_start) + ',' + str(file_num)
            message = form.message.data
            urgent = True
            if request.form.get('urgent') is None:
                urgent = False
            emr = True
            if request.form.get('emr') is None:
                emr = False
            case_name = form.case_name.data
            frequency = form.frequency.data
            temp_request = HPSJRequest(member_ID = memberid, icd1=icd10_1_data, icd2=icd10_2_data,
                            icd3=icd10_3_data, icd4=icd10_4_data, icd5=icd10_5_data, icd6=icd10_6_data,
                            icd7=icd10_7_data, CPT1=cpt_1_data, CPT2=cpt_2_data, CPT3=cpt_3_data, CPT4=cpt_4_data,
                            CPT5=cpt_5_data, CPT6=cpt_6_data, CPT7=cpt_7_data, CPTUnit1=unit_1_data,
                            CPTUnit2=unit_2_data, CPTUnit3=unit_3_data, CPTUnit4=unit_4_data, CPTUnit5=unit_5_data, caseName=case_name,
                            CPTUnit6=unit_6_data, CPTUnit7=unit_7_data, startDate=start_date, endDate=end_date, frequency=frequency,
                            files=file_path, message=message, urgent=urgent, emr=emr, status='Pending Submission', company_id=user.company_id)
            db.session.add(temp_request)
            db.session.commit()
            return redirect(url_for('hpsj'))
    else:
        templates = HPSJTemplate.query.filter_by(company_id=user.company_id).all()
        requests = HPSJRequest.query.filter_by(company_id=user.company_id).all()
        return render_template('hpsj.html', form=form, templates=templates, requests=requests, title='hpsj')

@app.route("/prime", methods=['GET', 'POST'])
@login_required
def prime():
    form = PrimeRequestForm()
    user = User.query.get(current_user.get_id())
    if request.method == 'POST' and not request.form.get('memberid'):
        icd10_1_data = form.icd10_1.data
        icd10_2_data = form.icd10_2.data
        icd10_3_data = form.icd10_3.data
        icd10_4_data = form.icd10_4.data
        icd10_5_data = form.icd10_5.data
        icd10_6_data = form.icd10_6.data
        icd10_7_data = form.icd10_7.data
        cpt_1_data = form.cpt_1.data
        cpt_2_data = form.cpt_2.data
        cpt_3_data = form.cpt_3.data
        cpt_4_data = form.cpt_4.data
        cpt_5_data = form.cpt_5.data
        cpt_6_data = form.cpt_6.data
        cpt_7_data = form.cpt_7.data
        unit_1_data = form.unit_1.data
        unit_2_data = form.unit_2.data
        unit_3_data = form.unit_3.data
        unit_4_data = form.unit_4.data
        unit_5_data = form.unit_5.data
        unit_6_data = form.unit_6.data
        unit_7_data = form.unit_7.data
        message = form.message.data
        frequency = form.frequency.data
        name = form.name.data
        template = PrimeTemplate(name=name, icd1=icd10_1_data, icd2=icd10_2_data, icd3=icd10_3_data,
                                icd4=icd10_4_data, icd5=icd10_5_data, icd6=icd10_6_data, icd7=icd10_7_data,
                                CPT1=cpt_1_data, CPT2=cpt_2_data, CPT3=cpt_3_data, CPT4=cpt_4_data,
                                CPT5=cpt_5_data, CPT6=cpt_6_data, CPT7=cpt_7_data, CPTUnit1=unit_1_data,
                                CPTUnit2=unit_2_data, CPTUnit3=unit_3_data, CPTUnit4=unit_4_data,
                                CPTUnit5=unit_5_data, CPTUnit6=unit_6_data, CPTUnit7=unit_7_data,
                                frequency=frequency, message=message, company_id=user.company_id)
        db.session.add(template)
        db.session.commit()
        return redirect(url_for('prime'))
    elif request.form.get('memberid'):
        company = Company.query.filter_by(id=user.company_id).first()
        if 'files[]' not in request.files:
            flash('No File', 'danger')
            return redirect(request.url)

        files = request.files.getlist('files[]')
        file_start = company.file_counter
        file_num = company.file_counter

        for file in files:
            if file and allowed_file(file.filename):
                file_num += 1
                extension = file.filename.rsplit('.', 1)[1].lower()
                upload_folder = os.getcwd() + '/uploads'
                if not os.path.isdir(upload_folder):
                    os.mkdir(upload_folder)
                file_path = os.path.join(upload_folder, file.filename)
                print("######### file path = " + file_path)

                # filename = company.name + '_{}.{}'.format(file_num, extension)
                if os.path.exists(file_path) :
                    os.remove(file_path)
                    print("file was removed.")
                try:
                    file.save(file_path)
                    print("file was saved.")
                except:
                    print("file save error")

                try:
                    upload_file_to_bucket('quickauths', file_path, "prime/" + company.name)
                except :
                    print("Upload error")

        company.file_counter = file_num
        if form.memberid.data:
            memberid = form.memberid.data
            icd10_1_data = form.icd10_1.data
            icd10_2_data = form.icd10_2.data
            icd10_3_data = form.icd10_3.data
            icd10_4_data = form.icd10_4.data
            icd10_5_data = form.icd10_5.data
            icd10_6_data = form.icd10_6.data
            icd10_7_data = form.icd10_7.data
            cpt_1_data = form.cpt_1.data
            cpt_2_data = form.cpt_2.data
            cpt_3_data = form.cpt_3.data
            cpt_4_data = form.cpt_4.data
            cpt_5_data = form.cpt_5.data
            cpt_6_data = form.cpt_6.data
            cpt_7_data = form.cpt_7.data
            unit_1_data = form.unit_1.data
            unit_2_data = form.unit_2.data
            unit_3_data = form.unit_3.data
            unit_4_data = form.unit_4.data
            unit_5_data = form.unit_5.data
            unit_6_data = form.unit_6.data
            unit_7_data = form.unit_7.data
            start_date = form.start_date.data
            end_date = form.end_date.data
            file_path = str(file_start) + ',' + str(file_num)
            message = form.message.data
            urgent = True
            if request.form.get('urgent') is None:
                urgent = False
            emr = True
            if request.form.get('emr') is None:
                emr = False
            case_name = form.case_name.data
            frequency = form.frequency.data
            temp_request = PrimeRequest(member_ID = memberid, icd1=icd10_1_data, icd2=icd10_2_data,
                            icd3=icd10_3_data, icd4=icd10_4_data, icd5=icd10_5_data, icd6=icd10_6_data,
                            icd7=icd10_7_data, CPT1=cpt_1_data, CPT2=cpt_2_data, CPT3=cpt_3_data, CPT4=cpt_4_data,
                            CPT5=cpt_5_data, CPT6=cpt_6_data, CPT7=cpt_7_data, CPTUnit1=unit_1_data,
                            CPTUnit2=unit_2_data, CPTUnit3=unit_3_data, CPTUnit4=unit_4_data, CPTUnit5=unit_5_data, caseName=case_name,
                            CPTUnit6=unit_6_data, CPTUnit7=unit_7_data, startDate=start_date, endDate=end_date, frequency=frequency,
                            files=file_path, message=message, urgent=urgent, emr=emr, status='Pending Submission', company_id=user.company_id)
            db.session.add(temp_request)
            db.session.commit()
            return redirect(url_for('prime'))
    else:
        templates = PrimeTemplate.query.filter_by(company_id=user.company_id).all()
        requests = PrimeRequest.query.filter_by(company_id=user.company_id).all()
        return render_template('prime.html', form=form, templates=templates, requests=requests, title='prime')

@app.route("/php", methods=['GET', 'POST'])
@login_required
def php():
    print("---- PHP module ##################")
    form = PHPRequestForm()
    user = User.query.get(current_user.get_id())
    if request.method == 'POST' and not request.form.get('memberid'):
        print("######### if")
        icd10_1_data = form.icd10_1.data
        icd10_2_data = form.icd10_2.data
        icd10_3_data = form.icd10_3.data
        icd10_4_data = form.icd10_4.data
        icd10_5_data = form.icd10_5.data
        icd10_6_data = form.icd10_6.data
        icd10_7_data = form.icd10_7.data
        cpt_1_data = form.cpt_1.data
        cpt_2_data = form.cpt_2.data
        cpt_3_data = form.cpt_3.data
        cpt_4_data = form.cpt_4.data
        cpt_5_data = form.cpt_5.data
        cpt_6_data = form.cpt_6.data
        cpt_7_data = form.cpt_7.data
        unit_1_data = form.unit_1.data
        unit_2_data = form.unit_2.data
        unit_3_data = form.unit_3.data
        unit_4_data = form.unit_4.data
        unit_5_data = form.unit_5.data
        unit_6_data = form.unit_6.data
        unit_7_data = form.unit_7.data
        message = form.message.data
        frequency = form.frequency.data
        emr = True
        if request.form.get('emr') is None:
            emr = False
        name = form.name.data
        template = PHPTemplate(name=name, icd1=icd10_1_data, icd2=icd10_2_data, icd3=icd10_3_data,
                                icd4=icd10_4_data, icd5=icd10_5_data, icd6=icd10_6_data, icd7=icd10_7_data,
                                CPT1=cpt_1_data, CPT2=cpt_2_data, CPT3=cpt_3_data, CPT4=cpt_4_data,
                                CPT5=cpt_5_data, CPT6=cpt_6_data, CPT7=cpt_7_data, CPTUnit1=unit_1_data,
                                CPTUnit2=unit_2_data, CPTUnit3=unit_3_data, CPTUnit4=unit_4_data,
                                CPTUnit5=unit_5_data, CPTUnit6=unit_6_data, CPTUnit7=unit_7_data, emr=emr,
                                frequency=frequency, message=message, company_id=user.company_id)
        db.session.add(template)
        db.session.commit()
        return redirect(url_for('php'))
    elif request.form.get('memberid'):
        print("######### else")
        company = Company.query.filter_by(id=user.company_id).first()
        if 'files[]' not in request.files:
            flash('No File', 'danger')
            return redirect(request.url)
        print("######### ok")

        files = request.files.getlist('files[]')
        file_start = company.file_counter
        file_num = company.file_counter

        print("######### before for")

        for file in files:
            if file and allowed_file(file.filename):
                file_num += 1
                extension = file.filename.rsplit('.', 1)[1].lower()
                upload_folder = os.getcwd() + '/uploads'
                if not os.path.isdir(upload_folder):
                    os.mkdir(upload_folder)
                file_path = os.path.join(upload_folder, file.filename)
                print("######### file path = " + file_path)

                # filename = company.name + '_{}.{}'.format(file_num, extension)
                if os.path.exists(file_path) :
                    os.remove(file_path)
                    print("file was removed.")
                try:
                    file.save(file_path)
                    print("file was saved.")
                except:
                    print("file save error")

                try:
                    upload_file_to_bucket('quickauths', file_path, "PHP/" + company.name)
                except :
                    print("Upload error")

        company.file_counter = file_num
        if form.memberid.data:
            memberid = form.memberid.data
            icd10_1_data = form.icd10_1.data
            icd10_2_data = form.icd10_2.data
            icd10_3_data = form.icd10_3.data
            icd10_4_data = form.icd10_4.data
            icd10_5_data = form.icd10_5.data
            icd10_6_data = form.icd10_6.data
            icd10_7_data = form.icd10_7.data
            cpt_1_data = form.cpt_1.data
            cpt_2_data = form.cpt_2.data
            cpt_3_data = form.cpt_3.data
            cpt_4_data = form.cpt_4.data
            cpt_5_data = form.cpt_5.data
            cpt_6_data = form.cpt_6.data
            cpt_7_data = form.cpt_7.data
            unit_1_data = form.unit_1.data
            unit_2_data = form.unit_2.data
            unit_3_data = form.unit_3.data
            unit_4_data = form.unit_4.data
            unit_5_data = form.unit_5.data
            unit_6_data = form.unit_6.data
            unit_7_data = form.unit_7.data
            start_date = form.start_date.data
            end_date = form.end_date.data
            file_path = str(file_start) + ',' + str(file_num)
            message = form.message.data
            urgent = True
            if request.form.get('urgent') is None:
                urgent = False
            emr = True
            if request.form.get('emr') is None:
                emr = False
            case_name = form.case_name.data
            frequency = form.frequency.data
            temp_request = PHPRequest(member_ID = memberid, icd1=icd10_1_data, icd2=icd10_2_data,
                            icd3=icd10_3_data, icd4=icd10_4_data, icd5=icd10_5_data, icd6=icd10_6_data,
                            icd7=icd10_7_data, CPT1=cpt_1_data, CPT2=cpt_2_data, CPT3=cpt_3_data, CPT4=cpt_4_data,
                            CPT5=cpt_5_data, CPT6=cpt_6_data, CPT7=cpt_7_data, CPTUnit1=unit_1_data,
                            CPTUnit2=unit_2_data, CPTUnit3=unit_3_data, CPTUnit4=unit_4_data, CPTUnit5=unit_5_data, caseName=case_name,
                            CPTUnit6=unit_6_data, CPTUnit7=unit_7_data, startDate=start_date, endDate=end_date, frequency=frequency,
                            files=file_path, message=message, urgent=urgent, emr=emr, status='Pending Submission', company_id=user.company_id)
            db.session.add(temp_request)
            db.session.commit()
            # try:
            #     elig = PHPEligibility(member_ID = memberid, company_id=user.company_id)
            #     db.session.add(elig)
            #     db.session.commit()
            # except Exception as e:
            #     db.session.rollback()
            return redirect(url_for('php'))
    else:
        templates = PHPTemplate.query.filter_by(company_id=user.company_id).all()
        requests = PHPRequest.query.filter_by(company_id=user.company_id).all()
        return render_template('php.html', form=form, templates=templates, requests=requests, title='php')

@app.route("/medical", methods=['GET', 'POST'])
@login_required
def medical():
    form = MediCalRequestForm()
    user = User.query.get(current_user.get_id())
    if request.method == 'POST' and not request.form.get('memberid'):
        icd10_1_data = form.icd10_1.data
        icd10_2_data = form.icd10_2.data
        icd10_3_data = form.icd10_3.data
        icd10_4_data = form.icd10_4.data
        icd10_5_data = form.icd10_5.data
        icd10_6_data = form.icd10_6.data
        icd10_7_data = form.icd10_7.data
        cpt_1_data = form.cpt_1.data
        cpt_2_data = form.cpt_2.data
        cpt_3_data = form.cpt_3.data
        cpt_4_data = form.cpt_4.data
        cpt_5_data = form.cpt_5.data
        cpt_6_data = form.cpt_6.data
        cpt_7_data = form.cpt_7.data
        unit_1_data = form.unit_1.data
        unit_2_data = form.unit_2.data
        unit_3_data = form.unit_3.data
        unit_4_data = form.unit_4.data
        unit_5_data = form.unit_5.data
        unit_6_data = form.unit_6.data
        unit_7_data = form.unit_7.data
        message = form.message.data
        medical_justification = form.medical_justification.data
        emr = True
        if request.form.get('emr') is None:
            emr = False
        name = form.name.data
        frequency = form.frequency.data
        template = MediCalTemplate(name=name, icd1=icd10_1_data, icd2=icd10_2_data, icd3=icd10_3_data, 
                                icd4=icd10_4_data, icd5=icd10_5_data, icd6=icd10_6_data, icd7=icd10_7_data, 
                                CPT1=cpt_1_data, CPT2=cpt_2_data, CPT3=cpt_3_data, CPT4=cpt_4_data, 
                                CPT5=cpt_5_data, CPT6=cpt_6_data, CPT7=cpt_7_data, CPTUnit1=unit_1_data, 
                                CPTUnit2=unit_2_data, CPTUnit3=unit_3_data, CPTUnit4=unit_4_data, 
                                CPTUnit5=unit_5_data, CPTUnit6=unit_6_data, CPTUnit7=unit_7_data, 
                                message=message, medicalJustification=medical_justification, emr=emr,
                                frequency=frequency, company_id=user.company_id)
        db.session.add(template)
        db.session.commit()
        return redirect(url_for('medical'))
    elif request.form.get('memberid'):
        company = Company.query.filter_by(id=user.company_id).first()
        if 'files[]' not in request.files:
            flash('No File', 'danger')
            return redirect(request.url)

        files = request.files.getlist('files[]')
        file_start = company.file_counter
        file_num = company.file_counter

        for file in files:
            if file and allowed_file(file.filename):
                file_num += 1
                extension = file.filename.rsplit('.', 1)[1].lower()
                upload_folder = os.getcwd() + '/uploads'
                if not os.path.isdir(upload_folder):
                    os.mkdir(upload_folder)
                file_path = os.path.join(upload_folder, file.filename)
                print("######### file path = " + file_path)

                # filename = company.name + '_{}.{}'.format(file_num, extension)
                if os.path.exists(file_path) :
                    os.remove(file_path)
                    print("file was removed.")
                try:
                    file.save(file_path)
                    print("file was saved.")
                except:
                    print("file save error")

                try:
                    upload_file_to_bucket('quickauths', file_path, "medical/" + company.name)
                except :
                    print("Upload error")

        company.file_counter = file_num
        if form.memberid.data:
            memberid = form.memberid.data.strip()
            icd10_1_data = form.icd10_1.data
            icd10_2_data = form.icd10_2.data
            icd10_3_data = form.icd10_3.data
            icd10_4_data = form.icd10_4.data
            icd10_5_data = form.icd10_5.data
            icd10_6_data = form.icd10_6.data
            icd10_7_data = form.icd10_7.data
            cpt_1_data = form.cpt_1.data
            cpt_2_data = form.cpt_2.data
            cpt_3_data = form.cpt_3.data
            cpt_4_data = form.cpt_4.data
            cpt_5_data = form.cpt_5.data
            cpt_6_data = form.cpt_6.data
            cpt_7_data = form.cpt_7.data
            unit_1_data = form.unit_1.data
            unit_2_data = form.unit_2.data
            unit_3_data = form.unit_3.data
            unit_4_data = form.unit_4.data
            unit_5_data = form.unit_5.data
            unit_6_data = form.unit_6.data
            unit_7_data = form.unit_7.data
            dob = form.dob.data
            start_date = form.start_date.data
            end_date = form.end_date.data
            prescription_date = form.prescription_date.data
            onset_date = form.onset_date.data
            file_path = str(file_start) + ',' + str(file_num)
            message = form.message.data
            medical_justification = form.medical_justification.data
            urgent = form.urgent.data
            gender = form.gender.data
            emr = True
            if request.form.get('emr') is None:
                emr = False
            case_name = form.case_name.data
            frequency = form.frequency.data
            referringMD = form.referring.data
            temp_request = MediCalRequest(member_ID = memberid, icd1=icd10_1_data, icd2=icd10_2_data, 
                            icd3=icd10_3_data, icd4=icd10_4_data, icd5=icd10_5_data, icd6=icd10_6_data, 
                            icd7=icd10_7_data, CPT1=cpt_1_data, CPT2=cpt_2_data, CPT3=cpt_3_data, CPT4=cpt_4_data, 
                            CPT5=cpt_5_data, CPT6=cpt_6_data, CPT7=cpt_7_data, CPTUnit1=unit_1_data, 
                            CPTUnit2=unit_2_data, CPTUnit3=unit_3_data, CPTUnit4=unit_4_data, CPTUnit5=unit_5_data, 
                            CPTUnit6=unit_6_data, CPTUnit7=unit_7_data, startDate=start_date, endDate=end_date, 
                            prescriptionDate=prescription_date, onsetDate=onset_date, files=file_path, 
                            caseName=case_name, message=message, medicalJustification=medical_justification, 
                            urgent=urgent, emr=emr, frequency=frequency, gender=gender, dob=dob,
                            referringMD=referringMD, status='Pending Submission', company_id=user.company_id)
            db.session.add(temp_request)
            db.session.commit()
            # try:
            #     elig = MediCalEligibility(member_ID = memberid, dob = dob, company_id=user.company_id)
            #     db.session.add(elig)
            #     db.session.commit()
            # except Exception as e:
            #     db.session.rollback()
            return redirect(url_for('medical'))
    else:
        templates = MediCalTemplate.query.filter_by(company_id=user.company_id).all()
        requests = MediCalRequest.query.filter_by(company_id=user.company_id, active=True).all()
        return render_template('medical.html', form=form, templates=templates, requests=requests, title='medical')

@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('hpsj'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password, company_id=request.form['company'])
        db.session.add(user)
        db.session.commit()
        user = User.query.filter_by(id=1).first()
        if user.id == 1:
            user.active = True
            user.admin = True
            db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    companies = Company.query.all()
    return render_template('register.html', title='Register', form=form, companies=companies)

def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Password Reset Request',
                  sender='noreply@quickauths.com',
                  recipients=[user.email])
    msg.body = f'''To reset your password, visit the following link:
{url_for('reset_token', token=token, _external=True)}
If you did not make this request then simply ignore this email and no changes will be made.
'''
    mail.send(msg)


@app.route("/reset_password", methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('An email (Check Junk Folder) has been sent with instructions to reset your password.', 'info')
        return redirect(url_for('login'))
    return render_template('reset_request.html', title='Reset Password', form=form)


@app.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    user = User.verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        flash('Your password has been updated! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('reset_token.html', title='Reset Password', form=form)

@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('hpsj'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data) and user.active == True:
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('hpsj'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('hpsj'))

@app.route("/hpsjsettings", methods=['GET', 'POST'])
@login_required
def hpsj_settings():
    form = HPSJSettingsForm()
    user = User.query.get(current_user.get_id())
    if form.validate_on_submit():
        results = HPSJSettings.query.filter_by(company_id=user.company_id).all()
        if(len(results) == 1):
            flash('Setting already exists, delete the previous one to add a new one', 'danger')
            return redirect(url_for('medical_settings'))
        else:
            username = form.username.data
            password = form.password.data
            company = form.company.data
            provider = form.provider.data
            fax = form.fax.data
            setting = HPSJSettings(username=username, password=password, company=company, provider=provider, fax=fax)
            db.session.add(setting)
            db.session.commit()
            return redirect(url_for('hpsj_settings'))
    user = User.query.get(current_user.get_id())
    credentials = HPSJSettings.query.filter_by(company_id=user.company_id).all()
    return render_template('hpsjsettings.html', form=form, credentials=credentials, title='hpsj')

@app.route("/primesettings", methods=['GET', 'POST'])
@login_required
def prime_settings():
    form = PrimeSettingsForm()
    user = User.query.get(current_user.get_id())
    if form.validate_on_submit():
        results = PrimeSettings.query.filter_by(company_id=user.company_id).all()
        if(len(results) == 1):
            flash('Setting already exists, delete the previous one to add a new one', 'danger')
            return redirect(url_for('medical_settings'))
        else:
            username = form.username.data
            password = form.password.data
            provider = form.provider.data
            fax = form.fax.data
            setting = PrimeSettings(username=username, password=password, company_id=user.company_id, provider=provider, fax=fax)
            db.session.add(setting)
            db.session.commit()
            return redirect(url_for('prime_settings'))
    credentials = PrimeSettings.query.filter_by(company_id=user.company_id).all()
    return render_template('primesettings.html', form=form, credentials=credentials, title='prime')

@app.route("/medicalsettings", methods=['GET', 'POST'])
@login_required
def medical_settings():
    form = MediCalSettingsForm()
    user = User.query.get(current_user.get_id())
    if form.validate_on_submit():
        results = MediCalSettings.query.filter_by(company_id=user.company_id).all()
        if(len(results) == 1):
            flash('Setting already exists, delete the previous one to add a new one', 'danger')
            return redirect(url_for('medical_settings'))
        else:
            username = form.username.data
            password = form.password.data
            npi = form.npi.data
            speciality = form.speciality.data
            contact_name = form.contact_name.data
            contact_phone = form.contact_phone.data
            setting = MediCalSettings(username=username, password=password, company_id=user.company_id, npi=npi, speciality=speciality, contactName=contact_name, contactPhone=contact_phone)
            db.session.add(setting)
            db.session.commit()
            return redirect(url_for('medical_settings'))
    credentials = MediCalSettings.query.filter_by(company_id=user.company_id).all()
    return render_template('medicalsettings.html', form=form, credentials=credentials, title='medical')

@app.route("/phpsettings", methods=['GET', 'POST'])
@login_required
def php_settings():
    form = PHPSettingsForm()
    user = User.query.get(current_user.get_id())
    if form.validate_on_submit():
        results = PHPSettings.query.filter_by(company_id=user.company_id).all()
        if(len(results) == 1):
            flash('Setting already exists, delete the previous one to add a new one', 'danger')
            return redirect(url_for('php_settings'))
        else:
            username = form.username.data
            password = form.password.data
            setting = PHPSettings(username=username, password=password, company_id=user.company_id)
            db.session.add(setting)
            db.session.commit()
            return redirect(url_for('php_settings'))
    credentials = PHPSettings.query.filter_by(company_id=user.company_id).all()
    return render_template('phpsettings.html', form=form, credentials=credentials, title='php')

@app.route("/hpsjpending")
@login_required
def hpsj_pending():
    user = User.query.get(current_user.get_id())
    pending = HPSJPendingRequest.query.filter_by(company_id=user.company_id).add_columns(HPSJPendingRequest.id, HPSJPendingRequest.member_ID, HPSJPendingRequest.refNumber,
                     HPSJPendingRequest.firstName, HPSJPendingRequest.lastName, HPSJPendingRequest.submittedDate,
                     HPSJPendingRequest.status, HPSJPendingRequest.case, HPSJPendingRequest.emr_entry,
                     HPSJPendingRequest.message, HPSJPendingRequest.dob).all()
    return render_template('hpsjpending.html', pending_requests=pending, title='hpsj')

@app.route("/primepending")
@login_required
def prime_pending():
    user = User.query.get(current_user.get_id())
    pending = PrimePendingRequest.query.filter_by(company_id=user.company_id).add_columns(PrimePendingRequest.id, PrimePendingRequest.member_ID, PrimePendingRequest.refNumber,
                     PrimePendingRequest.firstName, PrimePendingRequest.lastName, PrimePendingRequest.submittedDate,
                     PrimePendingRequest.status, PrimePendingRequest.case, PrimePendingRequest.emr_entry,
                     PrimePendingRequest.message, PrimePendingRequest.dob).all()
    return render_template('primepending.html', pending_requests=pending, title='prime')

@app.route("/medicalpending")
@login_required
def medical_pending():
    user = User.query.get(current_user.get_id())
    pending = MediCalPendingRequest.query.filter_by(company_id=user.company_id).add_columns(MediCalPendingRequest.id,
        MediCalPendingRequest.member_ID, MediCalPendingRequest.refNumber, MediCalPendingRequest.firstName,
        MediCalPendingRequest.lastName, MediCalPendingRequest.dob, MediCalPendingRequest.submittedDate,
        MediCalPendingRequest.status, MediCalPendingRequest.case, MediCalPendingRequest.emr_entry, MediCalPendingRequest.message).all()
    return render_template('medicalpending.html', pending_requests=pending, title='medical')

@app.route("/phppending")
@login_required
def php_pending():
    user = User.query.get(current_user.get_id())
    pending = PHPPendingRequest.query.filter_by(company_id=user.company_id).add_columns(PHPPendingRequest.id, PHPPendingRequest.member_ID, PHPPendingRequest.refNumber,
                     PHPPendingRequest.firstName, PHPPendingRequest.lastName, PHPPendingRequest.submittedDate,
                     PHPPendingRequest.status, PHPPendingRequest.case, PHPPendingRequest.emr_entry,
                     PHPPendingRequest.message, PHPPendingRequest.dob).all()
    return render_template('phppending.html', pending_requests=pending, title='php')

@app.route("/emr", methods=['GET', 'POST'])
@login_required
def emr():
    form = EMRForm()
    user = User.query.get(current_user.get_id())
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        entry = EMR(username=username, password=password, company_id=user.company_id)
        try:
            db.session.add(entry)
            db.session.commit()
            flash('Successfully added', 'success')
        except:
            db.session.rollback()
            flash('Username already exists', 'danger')
        return redirect(url_for('emr'))
    credentials = EMR.query.filter_by(company_id=user.company_id).all()
    return render_template('emr.html', form=form, title='EMR', credentials=credentials)

@app.route("/hpsjeligibility", methods=['GET', 'POST'])
@login_required
def hpsj_eligibility():
    form = EligibilityForm()
    user = User.query.get(current_user.get_id())
    if form.validate_on_submit():
        memberid = form.memberid.data
        eligibility = HPSJEligibility(member_ID=memberid, company_id=user.company_id)
        try:
            db.session.add(eligibility)
            db.session.commit()
            flash('Successfully added', 'success')
        except:
            db.session.rollback()
            flash('Member already exists', 'danger')
        return redirect(url_for('hpsj_eligibility'))
    eligibility_data = HPSJEligibility.query.filter(HPSJEligibility.company_id==user.company_id)\
        .add_columns(HPSJEligibility.member_ID, HPSJEligibility.firstName, HPSJEligibility.lastName, HPSJEligibility.thruDate, HPSJEligibility.eligibility, HPSJEligibility.status).all()
    temp_ids = []
    for member in eligibility_data:
        temp_ids.append(member.member_ID)
    temp_data = HPSJEligibility.query.filter_by(company_id=user.company_id).all()
    for member in temp_data:
        if member.member_ID not in temp_ids:
            eligibility_data.append(member)
    return render_template('hpsjeligibility.html', form=form, data=eligibility_data, title='hpsj')

@app.route("/primeeligibility", methods=['GET', 'POST'])
@login_required
def prime_eligibility():
    form = EligibilityForm()
    user = User.query.get(current_user.get_id())
    if form.validate_on_submit():
        memberid = form.memberid.data
        eligibility = PrimeEligibility(member_ID=memberid, company_id=user.company_id)
        try:
            db.session.add(eligibility)
            db.session.commit()
            flash('Successfully added', 'success')
        except:
            db.session.rollback()
            flash('Member already exists', 'danger')
        return redirect(url_for('prime_eligibility'))
    eligibility_data = PrimeEligibility.query.filter(PrimeEligibility.company_id==user.company_id)\
        .add_columns(PrimeEligibility.member_ID, PrimeEligibility.firstName, PrimeEligibility.lastName, PrimeEligibility.dob, PrimeEligibility.eligibility, PrimeEligibility.plan).all()
    temp_ids = []
    for member in eligibility_data:
        temp_ids.append(member.member_ID)
    temp_data = PrimeEligibility.query.filter_by(company_id=user.company_id).all()
    for member in temp_data:
        if member.member_ID not in temp_ids:
            eligibility_data.append(member)
    return render_template('primeeligibility.html', form=form, data=eligibility_data, title='prime')

@app.route("/medicaleligibility", methods=['GET', 'POST'])
@login_required
def medical_eligibility():
    form = EligibilityForm()
    user = User.query.get(current_user.get_id())
    if form.validate_on_submit():
        memberid = form.memberid.data
        dob = form.dob.data
        eligibility = MediCalEligibility(member_ID = memberid, dob=dob, company_id=user.company_id)
        try:
            db.session.add(eligibility)
            db.session.commit()
            flash('Successfully added', 'success')
        except:
            db.session.rollback()
            flash('Member already exists', 'danger')
        return redirect(url_for('medical_eligibility'))
    eligibility_data = MediCalEligibility.query.filter(MediCalEligibility.company_id==user.company_id)\
        .add_columns(MediCalEligibility.member_ID, MediCalEligibility.firstName, MediCalEligibility.lastName, MediCalEligibility.dob, MediCalEligibility.eligibility, MediCalEligibility.plan).all()
    temp_ids = []
    for member in eligibility_data:
        temp_ids.append(member.member_ID)
    temp_data = MediCalEligibility.query.filter_by(company_id=user.company_id).all()
    for member in temp_data:
        if member.member_ID not in temp_ids:
            eligibility_data.append(member)
    return render_template('medicaleligibility.html', form=form, data=eligibility_data, title='medical')

@app.route("/phpeligibility", methods=['GET', 'POST'])
@login_required
def php_eligibility():
    form = EligibilityForm()
    user = User.query.get(current_user.get_id())
    if form.validate_on_submit():
        memberid = form.memberid.data
        eligibility = PHPEligibility(member_ID=memberid, company_id=user.company_id)
        try:
            db.session.add(eligibility)
            db.session.commit()
            flash('Successfully added', 'success')
        except:
            db.session.rollback()
            flash('Member already exists', 'danger')
        return redirect(url_for('php_eligibility'))
    eligibility_data = PHPEligibility.query.filter(PHPEligibility.company_id==user.company_id)\
        .add_columns(PHPEligibility.member_ID, PHPEligibility.firstName, PHPEligibility.lastName, PHPEligibility.thruDate, PHPEligibility.eligibility, PHPEligibility.status, PHPEligibility.other_ins).all()
    temp_ids = []
    for member in eligibility_data:
        temp_ids.append(member.member_ID)
    temp_data = PHPEligibility.query.filter_by(company_id=user.company_id).all()
    for member in temp_data:
        if member.member_ID not in temp_ids:
            eligibility_data.append(member)
    return render_template('phpeligibility.html', form=form, data=eligibility_data, title='php')

@app.route("/hpsj/<int:request_id>/delete", methods=['POST'])
@login_required
def delete_hpsj_request(request_id):
    user = User.query.get(current_user.get_id())
    request = HPSJRequest.query.filter_by(company_id=user.company_id, id=request_id).first()
    try:
        db.session.delete(request)
        db.session.commit()
        flash('Request successfully deleted', 'success')
    except:
        db.session.rollback()
        flash('Request does not exist', 'danger')
    return redirect(url_for('hpsj'))

@app.route("/prime/<int:request_id>/delete", methods=['POST'])
@login_required
def delete_prime_request(request_id):
    user = User.query.get(current_user.get_id())
    request = PrimeRequest.query.filter_by(company_id=user.company_id, id=request_id).first()
    try:
        db.session.delete(request)
        db.session.commit()
        flash('Request successfully deleted', 'success')
    except:
        db.session.rollback()
        flash('Request does not exist', 'danger')
    return redirect(url_for('prime'))

@app.route("/medical/<int:request_id>/delete", methods=['POST'])
@login_required
def delete_medical_request(request_id):
    user = User.query.get(current_user.get_id())
    request = MediCalRequest.query.filter_by(company_id=user.company_id, id=request_id).first()
    company = Company.query.filter_by(id=user.company_id).first()
    for i in range(int(request.files.split(',')[0]) + 1, int(request.files.split(',')[1]) + 1):
        delete_folder_from_bucket("quickauths", "medical/" + company.name)
        # directory = os.getcwd() + '/uploads/{}'.format(company.name)
        # for file in os.listdir(directory):
        #     if file.split('.')[0] == company.name + '_{}'.format(i):
        #         os.remove(directory + '/' + file)
    try:
        db.session.delete(request)
        db.session.commit()
        flash('Request successfully deleted', 'success')
    except:
        db.session.rollback()
        flash('Request does not exist', 'danger')
    return redirect(url_for('medical'))

@app.route("/php/<int:request_id>/delete", methods=['POST'])
@login_required
def delete_php_request(request_id):
    user = User.query.get(current_user.get_id())
    request = PHPRequest.query.filter_by(company_id=user.company_id, id=request_id).first()
    company = Company.query.filter_by(id=user.company_id).first()
    for i in range(int(request.files.split(',')[0]) + 1, int(request.files.split(',')[1]) + 1):
        delete_folder_from_bucket("quickauths", "PHP/" + company.name)
        # directory = os.getcwd() + '/uploads/{}'.format(company.name)
        # for file in os.listdir(directory):
        #     if file.split('.')[0] == company.name + '_{}'.format(i):
        #         os.remove(directory + '/' + file)
    try:
        db.session.delete(request)
        db.session.commit()
        flash('Request successfully deleted', 'success')
    except:
        db.session.rollback()
        flash('Request does not exist', 'danger')
    return redirect(url_for('php'))

@app.route("/hpsj_pending/<int:request_id>/delete", methods=['POST'])
@login_required
def delete_hpsj_pending_request(request_id):
    user = User.query.get(current_user.get_id())
    request = HPSJPendingRequest.query.filter_by(company_id=user.company_id, id=request_id).first()
    try:
        db.session.delete(request)
        db.session.commit()
        flash('Request successfully deleted', 'success')
    except:
        db.session.rollback()
        flash('Request does not exist', 'danger')
    return redirect(url_for('hpsj_pending'))

@app.route("/prime_pending/<int:request_id>/delete", methods=['POST'])
@login_required
def delete_prime_pending_request(request_id):
    user = User.query.get(current_user.get_id())
    request = PrimePendingRequest.query.filter_by(company_id=user.company_id, id=request_id).first()
    try:
        db.session.delete(request)
        db.session.commit()
        flash('Request successfully deleted', 'success')
    except:
        db.session.rollback()
        flash('Request does not exist', 'danger')
    return redirect(url_for('prime_pending'))

@app.route("/medical_pending/<int:request_id>/delete", methods=['POST'])
@login_required
def delete_medical_pending_request(request_id):
    user = User.query.get(current_user.get_id())
    request = MediCalPendingRequest.query.filter_by(company_id=user.company_id, id=request_id).first()
    try:
        db.session.delete(request)
        db.session.commit()
        flash('Request successfully deleted', 'success')
    except:
        db.session.rollback()
        flash('Request does not exist', 'danger')
    return redirect(url_for('medical_pending'))

@app.route("/php_pending/<int:request_id>/delete", methods=['POST'])
@login_required
def delete_php_pending_request(request_id):
    user = User.query.get(current_user.get_id())
    request = PHPPendingRequest.query.filter_by(company_id=user.company_id, id=request_id).first()
    try:
        db.session.delete(request)
        db.session.commit()
        flash('Request successfully deleted', 'success')
    except:
        db.session.rollback()
        flash('Request does not exist', 'danger')
    return redirect(url_for('php_pending'))

@app.route("/hpsj_eligibility/<member_id>/delete", methods=['POST'])
@login_required
def delete_hpsj_member(member_id):
    user = User.query.get(current_user.get_id())
    member = HPSJEligibility.query.filter_by(company_id=user.company_id, member_ID=member_id).first()
    try:
        db.session.delete(member)
        db.session.commit()
    except:
        db.session.rollback()
    # member = Patients.query.filter_by(member_ID=member_id).first()
    # try:
    #     db.session.delete(member)
    #     db.session.commit()
    # except:
    #     db.session.rollback()
    return redirect(url_for('hpsj_eligibility'))

@app.route("/hpsj_eligibility/delete", methods=['POST'])
@login_required
def delete_all_hpsj_member():
    user = User.query.get(current_user.get_id())
    members = HPSJEligibility.query.filter_by(company_id=user.company_id).all()
    for member in members:
        try:
            db.session.delete(member)
            db.session.commit()
        except:
            db.session.rollback()
        # current_patient = Patients.query.filter_by(member_ID=member.member_ID).first()
        # try:
        #     db.session.delete(current_patient)
        #     db.session.commit()
        # except:
        #     db.session.rollback()
    return redirect(url_for('hpsj_eligibility'))

@app.route("/prime_eligibility/<member_id>/delete", methods=['POST'])
@login_required
def delete_prime_member(member_id):
    user = User.query.get(current_user.get_id())
    member = PrimeEligibility.query.filter_by(company_id=user.company_id, member_ID=member_id).first()
    try:
        db.session.delete(member)
        db.session.commit()
    except:
        db.session.rollback()
    # member = Patients.query.filter_by(member_ID=member_id).first()
    # try:
    #     db.session.delete(member)
    #     db.session.commit()
    # except:
    #     db.session.rollback()
    return redirect(url_for('prime_eligibility'))

@app.route("/prime_eligibility/delete", methods=['POST'])
@login_required
def delete_all_prime_member():
    user = User.query.get(current_user.get_id())
    members = PrimeEligibility.query.filter_by(company_id=user.company_id).all()
    for member in members:
        try:
            db.session.delete(member)
            db.session.commit()
        except:
            db.session.rollback()
        # current_patient = Patients.query.filter_by(member_ID=member.member_ID).first()
        # try:
        #     db.session.delete(current_patient)
        #     db.session.commit()
        # except:
        #     db.session.rollback()
    return redirect(url_for('prime_eligibility'))

@app.route("/medical_eligibility/<member_id>/delete", methods=['POST'])
@login_required
def delete_medical_member(member_id):
    user = User.query.get(current_user.get_id())
    member = MediCalEligibility.query.filter_by(company_id=user.company_id, member_ID=member_id).first()
    try:
        db.session.delete(member)
        db.session.commit()
    except:
        db.session.rollback()
    # member = Patients.query.filter_by(member_ID=member_id).first()
    # try:
    #     db.session.delete(member)
    #     db.session.commit()
    # except:
    #     db.session.rollback()
    return redirect(url_for('medical_eligibility'))

@app.route("/medical_eligibility/delete", methods=['POST'])
@login_required
def delete_all_medical_member():
    user = User.query.get(current_user.get_id())
    members = MediCalEligibility.query.filter_by(company_id=user.company_id).all()
    for member in members:
        try:
            db.session.delete(member)
            db.session.commit()
        except:
            db.session.rollback()
        # current_patient = Patients.query.filter_by(member_ID=member.member_ID).first()
        # try:
        #     db.session.delete(current_patient)
        #     db.session.commit()
        # except:
        #     db.session.rollback()
    return redirect(url_for('medical_eligibility'))

@app.route("/php_eligibility/<member_id>/delete", methods=['POST'])
@login_required
def delete_php_member(member_id):
    user = User.query.get(current_user.get_id())
    member = PHPEligibility.query.filter_by(company_id=user.company_id, member_ID=member_id).first()
    try:
        db.session.delete(member)
        db.session.commit()
    except:
        db.session.rollback()
    # member = Patients.query.filter_by(member_ID=member_id).first()
    # try:
    #     db.session.delete(member)
    #     db.session.commit()
    # except:
    #     db.session.rollback()
    return redirect(url_for('php_eligibility'))

@app.route("/php_eligibility/delete", methods=['POST'])
@login_required
def delete_all_php_member():
    user = User.query.get(current_user.get_id())
    members = PHPEligibility.query.filter_by(company_id=user.company_id).all()
    for member in members:
        try:
            db.session.delete(member)
            db.session.commit()
        except:
            db.session.rollback()
        # current_patient = Patients.query.filter_by(member_ID=member.member_ID).first()
        # try:
        #     db.session.delete(current_patient)
        #     db.session.commit()
        # except:
        #     db.session.rollback()
    return redirect(url_for('php_eligibility'))

@celery.task(name='routes.background_hpsj_eligibility')
def background_hpsj_eligibility(member_id, company_id):
    members = []
    if member_id == '0':
        members = HPSJEligibility.query.filter_by(company_id=company_id).all()
    else:
        members.append(HPSJEligibility.query.filter_by(company_id=company_id, member_ID=member_id).first())
    settings = HPSJSettings.query.filter_by(company_id=company_id).first()
    if not settings:
        flash('Update settings', 'danger')
        return redirect(url_for('hpsj_settings'))

    eligibility_request_results = []
    eligibility_request = HPSJEligibilityCheck.EligibilityCheck()
    eligibility_request_results.append(eligibility_request.SubmitRequest(
                    members, settings))

    if eligibility_request_results is None:
        flash('Error occurred. Please try again', 'danger')
        return redirect(url_for('hpsj_eligibility'))

    for temp in eligibility_request_results:
        for elig in temp:
            elig_model = HPSJEligibility.query.filter_by(
                member_ID=elig.MemberId).first()

            elig_model.firstName = elig.FirstName
            elig_model.lastName = elig.LastName
            elig_model.status = elig.Status
            elig_model.eligibility = elig.Eligibility
            if elig.ThruDate:
                elig_model.thruDate = datetime.strptime(elig.ThruDate, '%m/%d/%Y')
            elig_model.message = elig.Message
            db.session.commit()

@app.route("/submit_hpsj_eligibility/<member_id>", methods=['POST'])
@login_required
def submit_hpsj_eligibility(member_id):
    user = User.query.get(current_user.get_id())

    background_hpsj_eligibility.delay(member_id, user.company_id)
    flash('Bot Deployed. Refresh browser in a few minutes for results', 'success')
    return redirect(url_for('hpsj_eligibility'))

@celery.task(name='routes.background_prime_eligibility')
def background_prime_eligibility(member_id, company_id):
    members = []
    if member_id == '0':
        members = PrimeEligibility.query.filter_by(company_id=company_id).all()
    else:
        members.append(PrimeEligibility.query.filter_by(company_id=company_id, member_ID=member_id).first())
    settings = PrimeSettings.query.filter_by(company_id=company_id).first()
    if not settings:
        flash('Update settings', 'danger')
        return redirect(url_for('prime_settings'))

    eligibility_request_results = []
    eligibility_request = PrimeEligibilityCheck.EligibilityCheck()
    eligibility_request_results.append(eligibility_request.SubmitRequest(
                        members, settings))

    if eligibility_request_results is None:
        flash('Error occurred. Please try again', 'danger')
        return redirect(url_for('prime_eligibility'))

    for temp in eligibility_request_results:
        for elig in temp:
            elig_model = PrimeEligibility.query.filter_by(
                member_ID=elig.MemberId).first()
            # try:
            #     patient = Patients(firstName = elig.firstName, lastName = elig.lastName, member_ID = elig.MemberId)
            #     db.session.add(patient)
            #     db.session.commit()
            # except:
            #     db.session.rollback()
            elig_model.firstName = elig.FirstName
            elig_model.lastName = elig.LastName
            elig_model.status = elig.Status
            elig_model.eligibility = elig.Eligibility
            if elig.ThruValue:
                elig_model.thruDate = datetime.strptime(elig.ThruValue, '%m/%d/%Y')
            elig_model.message = elig.Message
            db.session.commit()

@app.route("/submit_prime_eligibility/<member_id>", methods=['POST'])
@login_required
def submit_prime_eligibility(member_id):
    user = User.query.get(current_user.get_id())

    background_prime_eligibility.delay(member_id, user.company_id)
    flash('Bot Deployed. Refresh browser in a few minutes for results', 'success')
    return redirect(url_for('prime_eligibility'))

@celery.task(name='routes.background_medical_eligibility')
def background_medical_eligibility(member_id, company_id):
    members = []
    if member_id == '0':
        members = MediCalEligibility.query.filter_by(company_id=company_id).all()
    else:
        members.append(MediCalEligibility.query.filter_by(company_id=company_id, member_ID=member_id).first())
    settings = MediCalSettings.query.filter_by(company_id=company_id).first()
    if not settings:
        flash('Update settings', 'danger')
        return redirect(url_for('medical_settings'))

    eligibility_request_results = []
    eligibility_request = MediCalEligibilityCheck.EligibilityCheck()
    eligibility_request_results.append(eligibility_request.SubmitRequest(
        members, settings))

    if eligibility_request_results is None:
        flash('Error occurred. Please try again', 'danger')
        return redirect(url_for('medical_eligibility'))

    for temp in eligibility_request_results:
        for elig in temp:
            elig_model = MediCalEligibility.query.filter_by(
                member_ID=elig.MemberId).first()
            elig_model.firstName = elig.firstName
            elig_model.lastName = elig.lastName
            elig_model.eligibility = elig.eligibility
            elig_model.message = elig.Message
            elig_model.plan = elig.plan
            elig_model.dateChecked = datetime.now()
            db.session.commit()

@app.route("/submit_medical_eligibility/<member_id>", methods=['POST'])
@login_required
def submit_medical_eligibility(member_id):
    user = User.query.get(current_user.get_id())

    background_medical_eligibility.delay(member_id, user.company_id)
    flash('Bot Deployed. Refresh browser in a few minutes for results', 'success')
    return redirect(url_for('medical_eligibility'))

@celery.task(name='routes.background_php_eligibility')
def background_php_eligibility(member_id, company_id):
    members = []
    if member_id == '0':
        members = PHPEligibility.query.filter_by(company_id=company_id).all()
    else:
        members.append(PHPEligibility.query.filter_by(company_id=company_id, member_ID=member_id).first())
    settings = PHPSettings.query.filter_by(company_id=company_id).first()
    if not settings:
        flash('Update settings', 'danger')
        return redirect(url_for('php_settings'))

    eligibility_request_results = []
    eligibility_request = PHPEligibilityCheck.EligibilityCheck()
    eligibility_request_results.append(eligibility_request.SubmitRequest(
        members, settings))

    if eligibility_request_results is None:
        flash('Error occurred. Please try again', 'danger')
        return redirect(url_for('php_eligibility'))

    print('About to go through Request Results')
    for temp in eligibility_request_results:
        for elig in temp:
            elig_model = PHPEligibility.query.filter_by(
                member_ID=elig.MemberId).first()
            elig_model.firstName = elig.FirstName
            elig_model.lastName = elig.LastName
            elig_model.status = elig.Status
            elig_model.eligibility = elig.Eligibility
            if elig.ThruDate:
                elig_model.thruDate = datetime.strptime(elig.ThruDate, '%m/%d/%Y')
            elig_model.other_ins = elig.OtherIns
            db.session.commit()

@app.route("/submit_php_eligibility/<member_id>", methods=['POST'])
@login_required
def submit_php_eligibility(member_id):
    user = User.query.get(current_user.get_id())

    background_php_eligibility.delay(member_id, user.company_id)
    flash('Bot Deployed. Refresh browser in a few minutes for results', 'success')
    return redirect(url_for('php_eligibility'))

@celery.task(name='routes.background_hpsj_authorization')
def background_hpsj_authorization(company_id):
    try:
        all_auth_request = HPSJRequest.query.filter_by(company_id=company_id).all()
        setting = PHPSettings.query.filter_by(company_id=company_id).first()
        members = []
        for model in all_auth_request:
            if model.status != 'success':
                ICDs = []
                if (model.icd1 != None):
                    ICDs.append(model.icd1)
                if (model.icd2 != None and len(model.icd2) > 0):
                    ICDs.append(model.icd2)
                if (model.icd3 != None and len(model.icd3) > 0):
                    ICDs.append(model.icd3)
                if (model.icd4 != None and len(model.icd4) > 0):
                    ICDs.append(model.icd4)
                if (model.icd5 != None and len(model.icd5) > 0):
                    ICDs.append(model.icd5)
                if (model.icd6 != None and len(model.icd6) > 0):
                    ICDs.append(model.icd6)
                if (model.icd7 != None and len(model.icd7) > 0):
                    ICDs.append(model.icd7)
                CPTs = []
                if (model.CPT1 != None and len(model.CPT1) > 0 and model.CPTUnit1 != None):
                    CPTs.append({'type': model.CPT1, 'value': model.CPTUnit1})
                if (model.CPT2 != None and len(model.CPT2) > 0 and model.CPTUnit2 != None):
                    CPTs.append({'type': model.CPT2, 'value': model.CPTUnit2})
                if (model.CPT3 != None and len(model.CPT3) > 0 and model.CPTUnit3 != None):
                    CPTs.append({'type': model.CPT3, 'value': model.CPTUnit3})
                if (model.CPT4 != None and len(model.CPT4) > 0 and model.CPTUnit4 != None):
                    CPTs.append({'type': model.CPT4, 'value': model.CPTUnit4})
                if (model.CPT5 != None and len(model.CPT5) > 0 and model.CPTUnit5 != None):
                    CPTs.append({'type': model.CPT5, 'value': model.CPTUnit5})
                if (model.CPT6 != None and len(model.CPT6) > 0 and model.CPTUnit6 != None):
                    CPTs.append({'type': model.CPT6, 'value': model.CPTUnit6})
                if (model.CPT7 != None and len(model.CPT7) > 0 and model.CPTUnit7 != None):
                    CPTs.append({'type': model.CPT7, 'value': model.CPTUnit7})
                files = ''
                company = Company.query.filter_by(id=company_id).first()
                try:
                    for i in range(int(model.files.split(',')[0])+1, int(model.files.split(',')[1])+1):
                        # directory = os.getcwd() + '/uploads/{}'.format(company.name)

                        s3 = boto3.client("s3")
                        all_objects = s3.list_objects_v2(Bucket="quickauths", Prefix="hpsj/" + company.name + "/")
                        for content in all_objects["Contents"]:
                            files += content["Key"]

                        # for file in os.listdir(directory):
                        #     if file.split('.')[0] == company.name + '_{}'.format(i):
                        #         files += directory + '/' + file + ','

                    files = files[:-1]
                except:
                    pass
                members.append({
                    'id': model.id,
                    'MemberId': model.member_ID,
                    'ICDs': ICDs,
                    'CPTs': CPTs,
                    'StartDateFormatted': model.startDate.strftime('%m/%d/%Y'),
                    'EndDateFormatted': model.endDate.strftime('%m/%d/%Y'),
                    'Message': model.message,
                    'Urgent': 'U' if model.urgent else 'S',
                    'FilePath': files,
                    'Case': model.caseName,
                    'Freq': model.frequency,
                    'PerWeeks': model.frequency.split('x')[1],
                    'VisitsPer': model.frequency.split('x')[0],
                    'requestID': model.id
                })

        authrequest = HSPJAuth.AuthRequest()
        patient_request_results = authrequest.SubmitAuthRequest(members, setting)

        if patient_request_results['success'] is False:
            pass

        elif patient_request_results['request_list'] is not None:
            for result in patient_request_results['request_list']:
                success = True if result.Success else False
                print(result.ReferenceNumber)
                args = {
                    'Id': result.Id,
                    'status': 'Submitted' if success else 'Failed',
                    'submissionMessage': result.Message
                }
                auth_model = HPSJRequest.query.filter_by(
                    member_ID=args['Id']).first()
                auth_model.status = args['status']
                auth_model.submissionMessage = args['submissionMessage']
                db.session.commit()

                if success:
                    args = {
                        'memberID': result.Id,
                        'refNumber': result.ReferenceNumber,
                        'firstName': result.FirstName,
                        'lastName': result.LastName,
                        'dob': datetime.strptime(result.DOB, '%m/%d/%Y').strftime('%m/%d/%Y'),
                        'submittedDate': datetime.today().strftime('%m/%d/%Y') if success else '',
                        'status': 'Submitted',
                        'message': result.Message
                    }
                    pending_model = HPSJPendingRequest(
                        member_ID=args['memberID'],
                        refNumber=args['refNumber'],
                        firstName=args['firstName'],
                        lastName=args['lastName'],
                        dob=datetime.strptime(args['dob'], '%m/%d/%Y'),
                        submittedDate = datetime.strptime(args['submittedDate'], '%m/%d/%Y'),
                        status=args['status'],
                        message=args['message'],
                        company_id=company_id
                    )
                    try:
                        db.session.add(pending_model)
                        db.session.commit()
                        flash('Auth Request Successfully Submitted', 'success')
                    except:
                        db.session.rollback()

    except Exception as ex:
        print(ex)

    print('Completed Auth Request')
    temp = PHPRequest.query.filter_by(company_id=company_id, emr=True, status='Submitted').all()
    if len(temp) > 0:
        print('Met Criteria to start EMR')
        background_emr_entry.delay('php', company_id)
    else:
        print('Did not meet criteria to run EMR')

@app.route("/hpsj_submit_authorization", methods=['POST'])
@login_required
def hpsj_submit_authorization():
    user = User.query.get(current_user.get_id())
    settings = HPSJSettings.query.filter_by(company_id=user.company_id).first()
    if not settings:
        flash('Update settings', 'danger')
        return redirect(url_for('php_settings'))
    else:
        background_hpsj_authorization.delay(user.company_id)
    flash('Bot Deployed. Refresh browser in a few minutes for results', 'success')
    return redirect(url_for('hpsj_pending'))

@app.route("/prime_submit_authorization", methods=['POST'])
@login_required
def prime_submit_authorization():
    user = User.query.get(current_user.get_id())
    try:
        all_auth_request = PrimeRequest.query.filter_by(company_id=user.company_id).all()
        members = []
        for model in all_auth_request:
            if model.status != 'success':
                ICDs = []
                if(model.icd1 != None):
                    ICDs.append(model.icd1)
                if(model.icd2 != None):
                    ICDs.append(model.icd2)
                if(model.icd3 != None and len(model.icd3) > 0):
                    ICDs.append(model.icd3)
                if(model.icd4 != None and len(model.icd4) > 0):
                    ICDs.append(model.icd4)
                if(model.icd5 != None and len(model.icd5) > 0):
                    ICDs.append(model.icd5)
                if(model.icd6 != None and len(model.icd6) > 0):
                    ICDs.append(model.icd6)
                if(model.icd7 != None and len(model.icd7) > 0):
                    ICDs.append(model.icd7)
                CPTs = []
                if(model.CPT1 != None and len(model.CPT1) > 0 and model.CPTUnit1 != None):
                    CPTs.append({'type': model.CPT1, 'value': model.CPTUnit1})
                if(model.CPT2 != None and len(model.CPT2) > 0 and model.CPTUnit2 != None):
                    CPTs.append({'type': model.CPT2, 'value': model.CPTUnit2})
                if(model.CPT3 != None and len(model.CPT3) > 0 and model.CPTUnit3 != None):
                    CPTs.append({'type': model.CPT3, 'value': model.CPTUnit3})
                if(model.CPT4 != None and len(model.CPT4) > 0 and model.CPTUnit4 != None):
                    CPTs.append({'type': model.CPT4, 'value': model.CPTUnit4})
                if(model.CPT5 != None and len(model.CPT5) > 0 and model.CPTUnit5 != None):
                    CPTs.append({'type': model.CPT5, 'value': model.CPTUnit5})
                if(model.CPT6 != None and len(model.CPT6) > 0 and model.CPTUnit6 != None):
                    CPTs.append({'type': model.CPT6, 'value': model.CPTUnit6})
                if(model.CPT7 != None and len(model.CPT7) > 0 and model.CPTUnit7 != None):
                    CPTs.append({'type': model.CPT7, 'value': model.CPTUnit7})
                files = ''
                company = Company.query.filter_by(id=user.company_id).first()
                for i in range(int(model.files.split(',')[0])+1, int(model.files.split(',')[1])+1):
                    # directory = os.getcwd() + '/uploads/{}'.format(company.name)

                    s3 = boto3.client("s3")
                    all_objects = s3.list_objects_v2(Bucket="quickauths", Prefix="prime/" + company.name + "/")
                    for content in all_objects["Contents"]:
                        files += content["Key"]

                    # for file in os.listdir(directory):
                    #     if file.split('.')[0] == company.name + '_{}'.format(i):
                    #         files += directory + '/' + file + ','

                files = files[:-1]
                members.append({
                    'id': model.id,
                    'MemberId': model.member_ID,
                    'ICDs': ICDs,
                    'CPTs': CPTs,
                    'StartDateFormatted': model.startDate,
                    'EndDateFormatted': model.endDate,
                    'Message': model.message,
                    'Urgent': 'U' if model.urgent == 'True' else 'S',
                    'FilePath': files,
                    'requestID': model.id
                })
        
        setting = PrimeSettings.query.filter_by(company_id=user.company_id).first()
        if not setting:
            flash('Update settings', 'danger')
            return redirect(url_for('prime_settings'))
        authrequest = PrimeAuth.AuthRequest()
        patient_request_results = authrequest.SubmitAuthRequest(
        members, setting)
        
        if patient_request_results['success'] is False:
            pass

        elif patient_request_results['request_list'] is not None:
            for result in patient_request_results['request_list']:
                success = True if result.Success else False
                args = {
                    'Id': result.Id,
                    'status': 'Submitted' if success else 'Failed'
                }
                auth_model = PrimeRequest.query.filter_by(
                    id=args['Id']).first()
                auth_model.status = args['status']
                db.session.commit()

                if success is True:
                    # insert pending record
                    args = {
                        'memberID':  result.MemberId,
                        'firstName': result.FirstName,
                        'lastName': result.LastName,
                        'submittedDate': datetime.date.today().strftime('%m/%d/%Y') if success else '',
                        'status': 'Submitted'
                    }
                    pending_model = PrimePendingRequest(
                        memberID=args['memberID'],
                        firstName=args['firstName'],
                        lastName=args['lastName'],
                        submittedDate=args['submittedDate'],
                        status=args['status'],
                        company_id = user.company_id
                    )
                    try:
                        db.session.add(pending_model)
                        db.session.commit()
                    except:
                        db.session.rollback()

    except Exception as ex:
        print(ex)

    return redirect(url_for('prime_pending'))

@celery.task(name='routes.background_medical_authorization')
def background_medical_authorization(company_id):
    try:
        all_auth_request = MediCalRequest.query.filter_by(company_id=company_id, active=True).all()
        setting = MediCalSettings.query.filter_by(company_id=company_id).first()
        members = []
        for model in all_auth_request:
            if model.status != 'success':
                ICDs = []
                if(model.icd1 != None):
                    ICDs.append(model.icd1)
                if(model.icd2 != None and len(model.icd2) > 0):
                    ICDs.append(model.icd2)
                if(model.icd3 != None and len(model.icd3) > 0):
                    ICDs.append(model.icd3)
                if(model.icd4 != None and len(model.icd4) > 0):
                    ICDs.append(model.icd4)
                if(model.icd5 != None and len(model.icd5) > 0):
                    ICDs.append(model.icd5)
                if(model.icd6 != None and len(model.icd6) > 0):
                    ICDs.append(model.icd6)
                if(model.icd7 != None and len(model.icd7) > 0):
                    ICDs.append(model.icd7)
                CPTs = []
                if(model.CPT1 != None and len(model.CPT1) > 0 and model.CPTUnit1 != None):
                    CPTs.append({'type': model.CPT1, 'value': model.CPTUnit1})
                if(model.CPT2 != None and len(model.CPT2) > 0 and model.CPTUnit2 != None):
                    CPTs.append({'type': model.CPT2, 'value': model.CPTUnit2})
                if(model.CPT3 != None and len(model.CPT3) > 0 and model.CPTUnit3 != None):
                    CPTs.append({'type': model.CPT3, 'value': model.CPTUnit3})
                if(model.CPT4 != None and len(model.CPT4) > 0 and model.CPTUnit4 != None):
                    CPTs.append({'type': model.CPT4, 'value': model.CPTUnit4})
                if(model.CPT5 != None and len(model.CPT5) > 0 and model.CPTUnit5 != None):
                    CPTs.append({'type': model.CPT5, 'value': model.CPTUnit5})
                if(model.CPT6 != None and len(model.CPT6) > 0 and model.CPTUnit6 != None):
                    CPTs.append({'type': model.CPT6, 'value': model.CPTUnit6})
                if(model.CPT7 != None and len(model.CPT7) > 0 and model.CPTUnit7 != None):
                    CPTs.append({'type': model.CPT7, 'value': model.CPTUnit7})
                files = ''
                company = Company.query.filter_by(id=company_id).first()
                try:
                    for i in range(int(model.files.split(',')[0])+1, int(model.files.split(',')[1])+1):
                        # directory = os.getcwd() + '/uploads/{}'.format(company.name)

                        s3 = boto3.client("s3")
                        all_objects = s3.list_objects_v2(Bucket="quickauths", Prefix="medical/" + company.name + "/")
                        for content in all_objects["Contents"]:
                            files += content["Key"]

                        # for file in os.listdir(directory):
                        #     if file.split('.')[0] == company.name + '_{}'.format(i):
                        #         files += directory + '/' + file + ','
                        
                    files = files[:-1]
                    print(files)
                except:
                    pass
                members.append({
                    'id': model.id,
                    'MemberId': model.member_ID,
                    'ICDs': ICDs,
                    'CPTs': CPTs,
                    'StartDateFormatted': model.startDate.strftime('%m/%d/%Y'),
                    'EndDateFormatted': model.endDate.strftime('%m/%d/%Y'),
                    'Message': model.message,
                    'Urgent': 'U' if model.urgent else 'S',
                    'FilePath': files,
                    'requestID': model.id,
                    'gender': model.gender,
                    'ContactName': setting.contactName,
                    'DOB': model.dob.strftime('%m/%d/%Y'),
                    'MedicalJustification': model.medicalJustification,
                    'RequestingMD': model.referringMD,
                    'PrescriptionDateFormatted': model.prescriptionDate.strftime('%m/%d/%Y'),
                    'Case': model.caseName,
                    'PerWeeks': model.frequency.split('x')[1],
                    'Freq': model.frequency,
                    'VisitsPer': model.frequency.split('x')[0],
                })

        authrequest = MediCalAuth.AuthRequest()
        patient_request_results = authrequest.SubmitAuthRequest(
        members, setting)

        # if patient_request_results['success'] is False:
        #     pass

        if patient_request_results['request_list'] is not None:
            for result in patient_request_results['request_list']:
                success = True if result.Success else False
                args = {
                    'Id': result.Id,
                    'submissionMessage': result.Message,
                    'status': 'Submitted' if success else 'Failed'
                }
                auth_model = MediCalRequest.query.filter_by(
                    member_ID=args['Id']).first()
                auth_model.status = args['status']
                auth_model.submissionMessage = args['submissionMessage']
                db.session.commit()
                success = True

                if success:
                    args = {
                        'memberID':  result.Id,
                        'firstName': result.FirstName,
                        'lastName': result.LastName,
                        'dob': datetime.strptime(result.DOB, '%m/%d/%Y').strftime('%m/%d/%Y'),
                        'submittedDate': datetime.today().strftime('%m/%d/%Y') if success else '',
                        'status': 'Submitted',
                        'refNumber': result.ReferenceNumber,
                        'message': result.Message,
                    }
                    pending_model = MediCalPendingRequest(
                        member_ID=args['memberID'],
                        refNumber=args['refNumber'],
                        firstName=args['firstName'],
                        lastName=args['lastName'],
                        dob=datetime.strptime(args['dob'], '%m/%d/%Y'),
                        submittedDate=datetime.strptime(args['submittedDate'], '%m/%d/%Y'),
                        status=args['status'],
                        company_id=company_id,
                        case=auth_model.caseName,
                        # emr=auth_model.emr
                    )
                    try:
                        auth_model.active = True
                        db.session.add(pending_model)
                        db.session.commit()
                        # flash('Auth Request Successfully Submitted', 'success')
                    except Exception as e:
                        db.session.rollback()

    except Exception as ex:
        print(ex)

    print('Completed Auth Request')
    temp = MediCalRequest.query.filter_by(company_id=company_id, emr=True, status='Submitted').all()
    if len(temp) > 0:
        print('Met Criteria to start EMR')
        background_emr_entry.delay('medical', company_id)
    else:
        print('Did not meet criteria to run EMR')

@app.route("/medical_submit_authorization", methods=['POST'])
@login_required
def medical_submit_authorization():
    user = User.query.get(current_user.get_id())
    settings = MediCalSettings.query.filter_by(company_id=user.company_id).first()
    if not settings:
        flash('Update settings', 'danger')
        return redirect(url_for('medical_settings'))
    else:
        background_medical_authorization.delay(user.company_id)
    flash('Bot Deployed. Refresh browser in a few minutes for results', 'success')
    return redirect(url_for('medical_pending'))


@celery.task(name='routes.background_php_authorization')
def background_php_authorization(company_id):
    try:
        all_auth_request = PHPRequest.query.filter_by(company_id=company_id).all()
        setting = PHPSettings.query.filter_by(company_id=company_id).first()
        members = []
        for model in all_auth_request:
            if model.status != 'success':
                ICDs = []
                if(model.icd1 != None):
                    ICDs.append(model.icd1)
                if(model.icd2 != None and len(model.icd2) > 0):
                    ICDs.append(model.icd2)
                if(model.icd3 != None and len(model.icd3) > 0):
                    ICDs.append(model.icd3)
                if(model.icd4 != None and len(model.icd4) > 0):
                    ICDs.append(model.icd4)
                if(model.icd5 != None and len(model.icd5) > 0):
                    ICDs.append(model.icd5)
                if(model.icd6 != None and len(model.icd6) > 0):
                    ICDs.append(model.icd6)
                if(model.icd7 != None and len(model.icd7) > 0):
                    ICDs.append(model.icd7)
                CPTs = []
                if(model.CPT1 != None and len(model.CPT1) > 0 and model.CPTUnit1 != None):
                    CPTs.append({'type': model.CPT1, 'value': model.CPTUnit1})
                if(model.CPT2 != None and len(model.CPT2) > 0 and model.CPTUnit2 != None):
                    CPTs.append({'type': model.CPT2, 'value': model.CPTUnit2})
                if(model.CPT3 != None and len(model.CPT3) > 0 and model.CPTUnit3 != None):
                    CPTs.append({'type': model.CPT3, 'value': model.CPTUnit3})
                if(model.CPT4 != None and len(model.CPT4) > 0 and model.CPTUnit4 != None):
                    CPTs.append({'type': model.CPT4, 'value': model.CPTUnit4})
                if(model.CPT5 != None and len(model.CPT5) > 0 and model.CPTUnit5 != None):
                    CPTs.append({'type': model.CPT5, 'value': model.CPTUnit5})
                if(model.CPT6 != None and len(model.CPT6) > 0 and model.CPTUnit6 != None):
                    CPTs.append({'type': model.CPT6, 'value': model.CPTUnit6})
                if(model.CPT7 != None and len(model.CPT7) > 0 and model.CPTUnit7 != None):
                    CPTs.append({'type': model.CPT7, 'value': model.CPTUnit7})
                files = ''
                company = Company.query.filter_by(id=company_id).first()
                try:
                    for i in range(int(model.files.split(',')[0])+1, int(model.files.split(',')[1])+1):
                        # directory = os.getcwd() + '/uploads/{}'.format(company.name)

                        s3 = boto3.client("s3")
                        all_objects = s3.list_objects_v2(Bucket="quickauths", Prefix="PHP/" + company.name + "/")
                        for content in all_objects["Contents"]:
                            files += content["Key"]

                        # for file in os.listdir(directory):
                        #     if file.split('.')[0] == company.name + '_{}'.format(i):
                        #         files += directory + '/' + file + ','
                        
                    files = files[:-1]
                except:
                    pass
                members.append({
                    'id': model.id,
                    'MemberId': model.member_ID,
                    'ICDs': ICDs,
                    'CPTs': CPTs,
                    'StartDateFormatted': model.startDate.strftime('%m/%d/%Y'),
                    'EndDateFormatted': model.endDate.strftime('%m/%d/%Y'),
                    'Message': model.message,
                    'Urgent': 'U' if model.urgent else 'S',
                    'FilePath': files,
                    'Case': model.caseName,
                    'Freq': model.frequency,
                    'PerWeeks': model.frequency.split('x')[1],
                    'VisitsPer': model.frequency.split('x')[0],
                    'requestID': model.id
                })

        authrequest = PHPAuth.AuthRequest()
        patient_request_results = authrequest.SubmitAuthRequest(
            members, setting)

        if patient_request_results['success'] is False:
            pass

        elif patient_request_results['request_list'] is not None:
            for result in patient_request_results['request_list']:
                success = True if result.Success else False
                print(result.ReferenceNumber)
                args = {
                    'Id': result.Id,
                    'status': 'Submitted' if success else 'Failed',
                    'submissionMessage': result.Message
                }
                auth_model = PHPRequest.query.filter_by(
                    member_ID=args['Id']).first()
                auth_model.status = args['status']
                auth_model.submissionMessage = args['submissionMessage']
                db.session.commit()

                if success:
                    args = {
                        'memberID': result.Id,
                        'refNumber': result.ReferenceNumber,
                        'firstName': result.FirstName,
                        'lastName': result.LastName,
                        'dob': datetime.strptime(result.DOB, '%m/%d/%Y').strftime('%m/%d/%Y'),
                        'submittedDate': datetime.today().strftime('%m/%d/%Y') if success else '',
                        'status': 'Submitted',
                        'message': result.Message
                    }
                    pending_model = PHPPendingRequest(
                        member_ID=args['memberID'],
                        refNumber=args['refNumber'],
                        firstName=args['firstName'],
                        lastName=args['lastName'],
                        dob=datetime.strptime(args['dob'], '%m/%d/%Y'),
                        submittedDate = datetime.strptime(args['submittedDate'], '%m/%d/%Y'),
                        status=args['status'],
                        message=args['message'],
                        company_id=company_id
                    )
                    try:
                        db.session.add(pending_model)
                        db.session.commit()
                        flash('Auth Request Successfully Submitted', 'success')
                    except:
                        db.session.rollback()

    except Exception as ex:
        print(ex)

    print('Completed Auth Request')
    temp = PHPRequest.query.filter_by(company_id=company_id, emr=True, status='Submitted').all()
    if len(temp) > 0:
        print('Met Criteria to start EMR')
        background_emr_entry.delay('php', company_id)
    else:
        print('Did not meet criteria to run EMR')

@app.route("/php_submit_authorization", methods=['POST'])
@login_required
def php_submit_authorization():
    user = User.query.get(current_user.get_id())
    settings = PHPSettings.query.filter_by(company_id=user.company_id).first()
    if not settings:
        flash('Update settings', 'danger')
        return redirect(url_for('php_settings'))
    else:
        background_php_authorization.delay(user.company_id)
    flash('Bot Deployed. Refresh browser in a few minutes for results', 'success')
    return redirect(url_for('php_pending'))

@celery.task(name='routes.background_emr_entry')
def background_emr_entry(insurance, company_id, member_ids = []):
    print('Inside Background EMR ENTRY')
    members = []
    if insurance == 'hpsj':
        pass
    elif insurance == 'prime':
        pass
    elif insurance == 'medical':
        if member_ids == []:
            print('Creating member_ids list')
            temp = MediCalRequest.query.filter_by(company_id=company_id, emr=True, status='Submitted').all()
        else:
            print('Creating temp list')
            temp = []
            for id in member_ids:
                temp.append(MediCalRequest.query.filter_by(company_id=company_id, member_ID=id).first())
        for model in temp:
            print('Starting Model')
            pending_details = MediCalPendingRequest.query.filter_by(member_ID=model.member_ID).first()
            ICDs = []
            if(model.icd1 != None):
                ICDs.append(model.icd1)
            if(model.icd2 != None and len(model.icd2) > 0):
                ICDs.append(model.icd2)
            if(model.icd3 != None and len(model.icd3) > 0):
                ICDs.append(model.icd3)
            if(model.icd4 != None and len(model.icd4) > 0):
                ICDs.append(model.icd4)
            if(model.icd5 != None and len(model.icd5) > 0):
                ICDs.append(model.icd5)
            if(model.icd6 != None and len(model.icd6) > 0):
                ICDs.append(model.icd6)
            if(model.icd7 != None and len(model.icd7) > 0):
                ICDs.append(model.icd7)
            CPTs = []
            if(model.CPT1 != None and len(model.CPT1) > 0 and model.CPTUnit1 != None):
                CPTs.append({'type': model.CPT1, 'value': model.CPTUnit1})
            if(model.CPT2 != None and len(model.CPT2) > 0 and model.CPTUnit2 != None):
                CPTs.append({'type': model.CPT2, 'value': model.CPTUnit2})
            if(model.CPT3 != None and len(model.CPT3) > 0 and model.CPTUnit3 != None):
                CPTs.append({'type': model.CPT3, 'value': model.CPTUnit3})
            if(model.CPT4 != None and len(model.CPT4) > 0 and model.CPTUnit4 != None):
                CPTs.append({'type': model.CPT4, 'value': model.CPTUnit4})
            if(model.CPT5 != None and len(model.CPT5) > 0 and model.CPTUnit5 != None):
                CPTs.append({'type': model.CPT5, 'value': model.CPTUnit5})
            if(model.CPT6 != None and len(model.CPT6) > 0 and model.CPTUnit6 != None):
                CPTs.append({'type': model.CPT6, 'value': model.CPTUnit6})
            if(model.CPT7 != None and len(model.CPT7) > 0 and model.CPTUnit7 != None):
                CPTs.append({'type': model.CPT7, 'value': model.CPTUnit7})
            case = 'Default'
            if model.caseName != '':
                case = model.caseName
            refNum = ''
            submittedDate = ''
            if pending_details:
                refNum = pending_details.refNumber
                submittedDate = pending_details.submittedDate.strftime('%m/%d/%Y')
            members.append({
                'id': model.id,
                'MemberId': model.member_ID,
                'FirstName': pending_details.firstName,
                'LastName': pending_details.lastName,
                'DateSubmitted': submittedDate,
                'ReferenceNumber': refNum,
                'DOB': pending_details.dob.strftime('%m/%d/%Y'),
                'Message': model.message,
                'ICD10': ICDs,
                'Case': case,
                'PrescriptionDate': model.prescriptionDate.strftime('%m/%d/%Y'),
                'Frequency': model.frequency,
                'PerWeeks': model.frequency.split('x')[1],
                'VisitsPer': model.frequency.split('x')[0],
                'Insurance': 'Medi-Cal',
                'Visits': int(model.frequency.split('x')[0])*int(model.frequency.split('x')[1])
            })
    elif insurance == 'php':
        if member_ids == []:
            print('Creating member_ids list')
            temp = PHPRequest.query.filter_by(company_id=company_id, emr=True, status='Submitted').all()
        else:
            print('Creating temp list')
            temp = []
            for id in member_ids:
                temp.append(MediCalRequest.query.filter_by(company_id=company_id, member_ID=id).first())
        for model in temp:
            print('Starting Model')
            pending_details = PHPPendingRequest.query.filter_by(member_ID=model.member_ID).first()
            ICDs = []
            if(model.icd1 != None):
                ICDs.append(model.icd1)
            if(model.icd2 != None and len(model.icd2) > 0):
                ICDs.append(model.icd2)
            if(model.icd3 != None and len(model.icd3) > 0):
                ICDs.append(model.icd3)
            if(model.icd4 != None and len(model.icd4) > 0):
                ICDs.append(model.icd4)
            if(model.icd5 != None and len(model.icd5) > 0):
                ICDs.append(model.icd5)
            if(model.icd6 != None and len(model.icd6) > 0):
                ICDs.append(model.icd6)
            if(model.icd7 != None and len(model.icd7) > 0):
                ICDs.append(model.icd7)
            CPTs = []
            if(model.CPT1 != None and len(model.CPT1) > 0 and model.CPTUnit1 != None):
                CPTs.append({'type': model.CPT1, 'value': model.CPTUnit1})
            if(model.CPT2 != None and len(model.CPT2) > 0 and model.CPTUnit2 != None):
                CPTs.append({'type': model.CPT2, 'value': model.CPTUnit2})
            if(model.CPT3 != None and len(model.CPT3) > 0 and model.CPTUnit3 != None):
                CPTs.append({'type': model.CPT3, 'value': model.CPTUnit3})
            if(model.CPT4 != None and len(model.CPT4) > 0 and model.CPTUnit4 != None):
                CPTs.append({'type': model.CPT4, 'value': model.CPTUnit4})
            if(model.CPT5 != None and len(model.CPT5) > 0 and model.CPTUnit5 != None):
                CPTs.append({'type': model.CPT5, 'value': model.CPTUnit5})
            if(model.CPT6 != None and len(model.CPT6) > 0 and model.CPTUnit6 != None):
                CPTs.append({'type': model.CPT6, 'value': model.CPTUnit6})
            if(model.CPT7 != None and len(model.CPT7) > 0 and model.CPTUnit7 != None):
                CPTs.append({'type': model.CPT7, 'value': model.CPTUnit7})
            case = 'Default'
            if model.caseName != '':
                case = model.caseName
            refNum = ''
            submittedDate = ''
            if pending_details:
                refNum = pending_details.refNumber
                submittedDate = pending_details.submittedDate.strftime('%m/%d/%Y')
            members.append({
                'id': model.id,
                'MemberId': model.member_ID,
                'FirstName': pending_details.firstName, #patient_details.firstName,
                'LastName': pending_details.lastName, #patient_details.lastName,
                'DateSubmitted': submittedDate,
                'ReferenceNumber': refNum,
                'DOB': pending_details.dob.strftime('%m/%d/%Y'),
                'Message': model.message,
                'ICD10': ICDs,
                'Case': case,
                'Frequency': model.frequency,
                'PerWeeks': model.frequency.split('x')[1],
                'VisitsPer': model.frequency.split('x')[0],
                'Insurance': 'PHP',
                'Visits': int(model.frequency.split('x')[0])*int(model.frequency.split('x')[1])
            })

    print('About to get settings for EMR')
    settings = EMR.query.filter_by(company_id=company_id).first()
    # if not settings:
    #     flash('Update settings', 'danger')
    #     return redirect(url_for('emr'))
    webpt = WebPT.WebPT()
    print('About to call EMR_Auth_Entry Function')
    output = webpt.EMR_Auth_Entry(members, settings)
    print('Out of EMR_Auth_Entry Function')
    for model in output:
        print('Inside for model in output')
        if insurance == 'medical':
            print('Starting pending details')
            pending_details = MediCalPendingRequest.query.filter_by(member_ID=model.member_ID).first()
        if insurance == 'php':
            pending_details = PHPPendingRequest.query.filter_by(member_ID=model.member_ID).first()
        if model.Message is not None:
            pending_details.message = model.Message
        if model.EMRMessage == 'Auth Entered':
            pending_details.emr_entry = 'Auth Entered'
        else:
            pending_details.emr_entry = 'Auth Pending'
        db.session.commit()

@celery.task(name='routes.background_emr_approval')
def background_emr_approval(approvals, company_id, insurance):
    print('Inside Background EMR Approval')
    settings = EMR.query.filter_by(company_id=company_id).first()
    print('got settings')

    webpt = WebPT.WebPT()
    print('About to start EMR_APPROVAL_ENTRY')
    output = webpt.EMR_Approval_Entry(approvals, settings)
    for model in output:
        if insurance == 'medical':
            pending_details = MediCalPendingRequest.query.filter_by(refNumber=model.ReferenceNumber).first()
        if insurance == 'php':
            pending_details = PHPPendingRequest.query.filter_by(refNumber=model.ReferenceNumber).first()
        print(insurance)
        if model.Message is not None:
            pending_details.message = model.Message
        print(f'model.Message:', model.Message)
        print(f'model.EMRMessage:', model.EMRMessage)
        if model.EMRMessage == 'Approval Entered':
            pending_details.emr_entry = 'Approval Entered'
        else:
            pending_details.emr_entry = 'Error Entering Approval'
        print(f'pending_details.emr:', pending_details.emr)
        db.session.commit()
    # return redirect(url_for(f'{insurance.lower()}_pending'))

@app.route("/export_medical_eligibility", methods=['POST'])
@login_required
def export_medical_eligibility():
    user = User.query.get(current_user.get_id())
    eligibility_data = MediCalEligibility.query.filter(MediCalEligibility.company_id==user.company_id)\
        .add_columns(MediCalEligibility.member_ID, MediCalEligibility.firstName, MediCalEligibility.lastName, MediCalEligibility.dob, MediCalEligibility.eligibility, MediCalEligibility.plan).all()
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['Member ID', 'First Name', 'Last Name', 'DOB', 'Eligibility', 'Plan'])
    for row in eligibility_data:
        temp = [row.member_ID, row.firstName, row.lastName, row.dob.strftime("%m/%d/%Y"), row.eligibility, row.plan]
        cw.writerow(temp)
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=MEDIeligEXPORT.csv"
    output.headers["Content-type"] = "text/csv"
    return output

@app.route("/export_hpsj_eligibility", methods=['POST'])
@login_required
def export_hpsj_eligibility():
    user = User.query.get(current_user.get_id())
    eligibility_data = HPSJEligibility.query.filter(HPSJEligibility.company_id==user.company_id)\
        .add_columns(HPSJEligibility.member_ID, HPSJEligibility.firstName, HPSJEligibility.lastName, HPSJEligibility.thruDate, HPSJEligibility.eligibility, HPSJEligibility.status).all()
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['Member ID', 'First Name', 'Last Name', 'Thru Date', 'Eligibility', 'Status'])
    for row in eligibility_data:
        temp = [row.member_ID, row.firstName, row.lastName, row.dob.strftime("%m/%d/%Y"), row.eligibility, row.status]
        cw.writerow(temp)
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=HPSJeligEXPORT.csv"
    output.headers["Content-type"] = "text/csv"
    return output

@app.route("/export_prime_eligibility", methods=['POST'])
@login_required
def export_prime_eligibility():
    user = User.query.get(current_user.get_id())
    eligibility_data = PrimeEligibility.query.filter(PrimeEligibility.company_id==user.company_id)\
        .add_columns(PrimeEligibility.member_ID, PrimeEligibility.firstName, PrimeEligibility.lastName, PrimeEligibility.dob, PrimeEligibility.eligibility, PrimeEligibility.plan).all()
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['Member ID', 'First Name', 'Last Name', 'DOB', 'Eligibility', 'Plan'])
    for row in eligibility_data:
        temp = [row.member_ID, row.firstName, row.lastName, row.dob.strftime("%m/%d/%Y"), row.eligibility, row.plan]
        cw.writerow(temp)
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=PRIMEeligEXPORT.csv"
    output.headers["Content-type"] = "text/csv"
    return output

@app.route("/export_php_eligibility", methods=['POST'])
@login_required
def export_php_eligibility():
    user = User.query.get(current_user.get_id())
    eligibility_data = PHPEligibility.query.filter(PHPEligibility.company_id==user.company_id)\
        .add_columns(PHPEligibility.member_ID, PHPEligibility.firstName, PHPEligibility.lastName, PHPEligibility.thruDate, PHPEligibility.eligibility, PHPEligibility.other_ins).all()
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['MEMBER ID', 'FIRST NAME', 'LAST NAME', 'THRU DATE', 'ELIGIBILITY', 'OTHER INS'])
    for row in eligibility_data:
        temp = [row.member_ID, row.firstName, row.lastName, row.thruDate, row.eligibility, row.other_ins]
        cw.writerow(temp)
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=phpeligEXPORT.csv"
    output.headers["Content-type"] = "text/csv"
    return output

@app.route("/upload_medical_eligibility", methods=['POST'])
def upload_medical_eligibility():
    uploaded_file = request.files['file']
    if '.' in uploaded_file.filename and uploaded_file.filename.rsplit('.', 1)[1].lower() == 'csv':
        rows = uploaded_file.read().decode('utf-8')
        row_num = 0
        for row in rows.split('\n'):
            if row_num == 0:
                row_num += 1
            elif len(row.split(',')) < 2:
                pass
            else:
                user = User.query.get(current_user.get_id())
                memberid = row.split(',')[0].strip()
                if len(row.split(',')[1].split('-')) > 1:
                    dob = datetime.strptime(row.split(',')[1].rstrip(), '%Y-%m-%d')
                elif row.split(',')[1][-3] == '/':
                    dob = datetime.strptime(row.split(',')[1].rstrip(), '%m/%d/%y')
                else:
                    dob = datetime.strptime(row.split(',')[1].rstrip(), '%m/%d/%Y')
                eligibility = MediCalEligibility(member_ID = memberid, dob=dob, company_id=user.company_id)
                try:
                    db.session.add(eligibility)
                    db.session.commit()
                except:
                    db.session.rollback()
        flash('Records uploaded', 'success')
    else:
        flash('Only CSV is accepted', 'danger')
        return redirect(url_for('medical_eligibility'))
    return redirect(url_for('medical_eligibility'))

@app.route("/upload_prime_eligibility", methods=['POST'])
def upload_prime_eligibility():
    uploaded_file = request.files['file']
    if '.' in uploaded_file.filename and uploaded_file.filename.rsplit('.', 1)[1].lower() == 'csv':
        rows = uploaded_file.read().decode('utf-8')
        row_num = 0
        for row in rows.split('\n'):
            if row_num == 0:
                row_num += 1
            elif len(row.split(',')[0]) < 5:
                pass
            else:
                user = User.query.get(current_user.get_id())
                memberid = row.split(',')[0].strip().rstrip('\n')
                eligibility = PHPEligibility(member_ID = memberid, company_id=user.company_id)
                try:
                    db.session.add(eligibility)
                    db.session.commit()
                except:
                    db.session.rollback()
        flash('Records uploaded', 'success')
    else:
        flash('Only CSV is accepted', 'danger')
        return redirect(url_for('prime_eligibility'))
    return redirect(url_for('prime_eligibility'))

@app.route("/upload_hpsj_eligibility", methods=['POST'])
def upload_hpsj_eligibility():
    uploaded_file = request.files['file']
    if '.' in uploaded_file.filename and uploaded_file.filename.rsplit('.', 1)[1].lower() == 'csv':
        rows = uploaded_file.read().decode('utf-8')
        row_num = 0
        for row in rows.split('\n'):
            if row_num == 0:
                row_num += 1
            elif len(row.split(',')[0]) < 5:
                pass
            else:
                user = User.query.get(current_user.get_id())
                memberid = row.split(',')[0].strip().rstrip('\n')
                eligibility = HPSJEligibility(member_ID = memberid, company_id=user.company_id)
                try:
                    db.session.add(eligibility)
                    db.session.commit()
                except:
                    db.session.rollback()
        flash('Records uploaded', 'success')
    else:
        flash('Only CSV is accepted', 'danger')
        return redirect(url_for('hpsj_eligibility'))
    return redirect(url_for('hpsj_eligibility'))

@app.route("/upload_php_eligibility", methods=['POST'])
def upload_php_eligibility():
    uploaded_file = request.files['file']
    if '.' in uploaded_file.filename and uploaded_file.filename.rsplit('.', 1)[1].lower() == 'csv':
        rows = uploaded_file.read().decode('utf-8')
        row_num = 0
        for row in rows.split('\n'):
            if row_num == 0:
                row_num += 1
            elif len(row.split(',')[0].strip()) < 10 or len(row.split(',')[0].strip()) >10:
                pass
            else:
                user = User.query.get(current_user.get_id())
                memberid = row.split(',')[0].strip().rstrip('\n')
                eligibility = PHPEligibility(member_ID = memberid, company_id=user.company_id)
                try:
                    db.session.add(eligibility)
                    db.session.commit()
                except:
                    db.session.rollback()
        flash('Records uploaded', 'success')
    else:
        flash('Only CSV is accepted', 'danger')
        return redirect(url_for('php_eligibility'))
    return redirect(url_for('php_eligibility'))

@app.route("/hpsj_template/delete/<template_id>", methods=['POST'])
@login_required
def delete_hpsj_template(template_id):
    user = User.query.get(current_user.get_id())
    template = HPSJTemplate.query.filter_by(company_id=user.company_id, id=template_id).first()
    try:
        db.session.delete(template)
        db.session.commit()
        flash('Template successfully deleted', 'success')
    except:
        db.session.rollback()
        flash('Template does not exist', 'danger')
    return jsonify({"redirect": "/hpsj"})

@app.route("/prime_template/delete/<template_id>", methods=['POST'])
@login_required
def delete_prime_template(template_id):
    user = User.query.get(current_user.get_id())
    template = PrimeTemplate.query.filter_by(company_id=user.company_id, id=template_id).first()
    try:
        db.session.delete(template)
        db.session.commit()
        flash('Template successfully deleted', 'success')
    except:
        db.session.rollback()
        flash('Template does not exist', 'danger')
    return jsonify({"redirect": "/prime"})

@app.route("/medical_template/delete/<template_id>", methods=['POST'])
@login_required
def delete_medical_template(template_id):
    user = User.query.get(current_user.get_id())
    template = MediCalTemplate.query.filter_by(company_id=user.company_id, id=template_id).first()
    try:
        db.session.delete(template)
        db.session.commit()
        flash('Template successfully deleted', 'success')
    except:
        db.session.rollback()
        flash('Template does not exist', 'danger')
    return jsonify({"redirect": "/medical"})

@app.route("/php_template/delete/<template_id>", methods=['POST'])
@login_required
def delete_php_template(template_id):
    user = User.query.get(current_user.get_id())
    template = PHPTemplate.query.filter_by(company_id=user.company_id, id=template_id).first()
    try:
        db.session.delete(template)
        db.session.commit()
        flash('Template successfully deleted', 'success')
    except:
        db.session.rollback()
        flash('Template does not exist', 'danger')
    return jsonify({"redirect": "/php"})

@app.route("/medical_settings/delete", methods=['POST'])
@login_required
def delete_medical_setting():
    user = User.query.get(current_user.get_id())
    request = MediCalSettings.query.filter_by(company_id=user.company_id).first()
    try:
        db.session.delete(request)
        db.session.commit()
        flash('Setting successfully deleted', 'success')
    except:
        db.session.rollback()
        flash('Setting does not exist', 'danger')
    return redirect(url_for('medical_settings'))

@app.route("/hpsj_settings/delete", methods=['POST'])
@login_required
def delete_hpsj_setting():
    user = User.query.get(current_user.get_id())
    request = HPSJSettings.query.filter_by(company_id=user.company_id).first()
    try:
        db.session.delete(request)
        db.session.commit()
        flash('Setting successfully deleted', 'success')
    except:
        db.session.rollback()
        flash('Setting does not exist', 'danger')
    return redirect(url_for('hpsj_settings'))

@app.route("/prime_settings/delete", methods=['POST'])
@login_required
def delete_prime_setting():
    user = User.query.get(current_user.get_id())
    request = PrimeSettings.query.filter_by(company_id=user.company_id).first()
    try:
        db.session.delete(request)
        db.session.commit()
        flash('Setting successfully deleted', 'success')
    except:
        db.session.rollback()
        flash('Setting does not exist', 'danger')
    return redirect(url_for('prime_settings'))

@app.route("/php_settings/delete", methods=['POST'])
@login_required
def delete_php_setting():
    user = User.query.get(current_user.get_id())
    request = PHPSettings.query.filter_by(company_id=user.company_id).first()
    try:
        db.session.delete(request)
        db.session.commit()
        flash('Setting successfully deleted', 'success')
    except:
        db.session.rollback()
        flash('Setting does not exist', 'danger')
    return redirect(url_for('php_settings'))

@app.route("/emr/delete", methods=['POST'])
@login_required
def delete_emr_setting():
    user = User.query.get(current_user.get_id())
    request = EMR.query.filter_by(company_id=user.company_id).first()
    try:
        db.session.delete(request)
        db.session.commit()
        flash('Setting successfully deleted', 'success')
    except:
        db.session.rollback()
        flash('Setting does not exist', 'danger')
    return redirect(url_for('emr'))

@app.route("/export_hpsj_pending", methods=['POST'])
@login_required
def export_hpsj_pending():
    user = User.query.get(current_user.get_id())
    eligibility_data = HPSJPendingRequest.query.filter(HPSJPendingRequest.company_id==user.company_id)\
        .add_columns(HPSJPendingRequest.member_ID, HPSJPendingRequest.firstName, HPSJPendingRequest.lastName, HPSJPendingRequest.refNumber, HPSJPendingRequest.dob, HPSJPendingRequest.submittedDate, HPSJPendingRequest.status,HPSJPendingRequest.case, HPSJPendingRequest.message).all()
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['Member ID', 'Reference Number', 'First Name', 'Last Name', 'DOB', 'Submitted Date', 'Status', 'Case', 'Message'])
    for row in eligibility_data:
        temp = [row.member_ID, row.refNumber, row.firstName, row.lastName, row.dob.strftime("%m/%d/%Y"), row.submittedDate.strftime("%m/%d/%Y"), row.status, row.case, row.message]
        cw.writerow(temp)
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=HPSJPendExport.csv"
    output.headers["Content-type"] = "text/csv"
    return output

@app.route("/export_prime_pending", methods=['POST'])
@login_required
def export_prime_pending():
    user = User.query.get(current_user.get_id())
    eligibility_data = PrimePendingRequest.query.filter(PrimePendingRequest.company_id==user.company_id)\
        .add_columns(PrimePendingRequest.member_ID, PrimePendingRequest.firstName, PrimePendingRequest.lastName, PrimePendingRequest.refNumber, PrimePendingRequest.dob, PrimePendingRequest.submittedDate, PrimePendingRequest.status,PrimePendingRequest.case, PrimePendingRequest.message).all()
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['Member ID', 'Reference Number', 'First Name', 'Last Name', 'DOB', 'Submitted Date', 'Status', 'Case', 'Message'])
    for row in eligibility_data:
        temp = [row.member_ID, row.refNumber, row.firstName, row.lastName, row.dob.strftime("%m/%d/%Y"), row.submittedDate.strftime("%m/%d/%Y"), row.status, row.case, row.message]
        cw.writerow(temp)
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=PrimePendExport.csv"
    output.headers["Content-type"] = "text/csv"
    return output

@app.route("/export_medical_pending", methods=['POST'])
@login_required
def export_medical_pending():
    user = User.query.get(current_user.get_id())
    eligibility_data = MediCalPendingRequest.query.filter(MediCalPendingRequest.company_id==user.company_id)\
        .add_columns(MediCalPendingRequest.member_ID, MediCalPendingRequest.firstName, MediCalPendingRequest.lastName, MediCalPendingRequest.refNumber, MediCalPendingRequest.dob, MediCalPendingRequest.submittedDate, MediCalPendingRequest.status, MediCalPendingRequest.case, MediCalPendingRequest.message).all()
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['Member ID', 'Reference Number', 'First Name', 'Last Name', 'DOB', 'Submitted Date', 'Status', 'Case', 'Message'])
    for row in eligibility_data:
        temp = [row.member_ID, row.refNumber, row.firstName, row.lastName, row.dob.strftime("%m/%d/%Y"), row.submittedDate.strftime("%m/%d/%Y"), row.status, row.case, row.message]
        cw.writerow(temp)
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=MediPendExport.csv"
    output.headers["Content-type"] = "text/csv"
    return output

@app.route("/export_php_pending", methods=['POST'])
@login_required
def export_php_pending():
    user = User.query.get(current_user.get_id())
    eligibility_data = PHPPendingRequest.query.filter(PHPPendingRequest.company_id==user.company_id)\
        .add_columns(PHPPendingRequest.member_ID,PHPPendingRequest.firstName, PHPPendingRequest.lastName, PHPPendingRequest.refNumber, PHPPendingRequest.dob, PHPPendingRequest.submittedDate,PHPPendingRequest.status, PHPPendingRequest.case, PHPPendingRequest.message).all()
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['Member ID', 'Reference Number', 'First Name', 'Last Name', 'DOB', 'Submitted Date', 'Status', 'Case', 'Message'])
    for row in eligibility_data:
        temp = [row.member_ID, row.refNumber, row.firstName, row.lastName, row.dob.strftime("%m/%d/%Y"), row.submittedDate.strftime("%m/%d/%Y"), row.status, row.case, row.message]
        cw.writerow(temp)
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=PHPPendExport.csv"
    output.headers["Content-type"] = "text/csv"
    return output

# @app.route("/medical_emr/check", methods=['POST'])
# @login_required
# def medical_emr_check():
#     data = request.get_json()
#     member_ids = data['ids']
#     user = User.query.get(current_user.get_id())
#     emr_entry('medical', user.company_id, member_ids)
#     return jsonify({"redirect": "/medicalpending"})

@celery.task(name='routes.background_update_prime_pending')
def background_update_hpsj_pending(company_id, emr):
    try:
        print('At the try in background_update_prime')
        all_pending_requests = HPSJPendingRequest.query.filter_by(company_id=company_id).all()
        settings = HPSJSettings.query.filter_by(company_id=company_id).first()
        print('About to start Pending_Status')
        pending_request = HPSJPending.HPSJPendingStatus()
        patient_request_results = pending_request.Pending_Status(all_pending_requests, settings)
        print('Out of Pending_Status')
        for member in patient_request_results['process_list']:
            model = HPSJPendingRequest.query.filter_by(refNumber=member.ReferenceNumber).first()
            model.status = member.AuthStatus
            model.message = member.Message
            db.session.commit()

    except Exception as ex:
        print(ex)

    print('About to check EMR')
    if emr:
        if len(patient_request_results['approvals_list']) > 0:
            print('About to start EMR Approval')
            approvals_list= []
            for member in patient_request_results['approvals_list']:
                approvals_list.append({
                    'ReferenceNumber': member.ReferenceNumber, 'Id': member.Id, 'LastName': member.LastName,
                    'FirstName': member.FirstName, 'DOB': member.DOB, 'DOBMonth': member.DOBMonth, 'DOBDay': member.DOBDay,
                    'DOBYear': member.DOBYear, 'DateSubmitted': member.DateSubmitted, 'ExpirationDate': member.ExpirationDate,
                    'Visits': member.Visits, 'Approved': member.Approved, 'Insurance': member.Insurance
                })
            insurance = 'php'
            background_emr_approval.delay(approvals_list, company_id, insurance)
            print('EMR Approval entry Complete')
        else:
            print('EMR Approval Not Run')

@app.route("/update_hpsj_pending", methods=['POST'])
@login_required
def update_hpsj_pending():
    user = User.query.get(current_user.get_id())
    settings = HPSJSettings.query.filter_by(company_id=user.company_id).first()
    if not settings:
        flash('Update settings', 'danger')
        return redirect(url_for('medical_settings'))
    if request.form.get('emr-checkbox'):
        print('EMR checked')
        emr = True
    else:
        print('EMR not checked')
        emr = False
    background_update_hpsj_pending.delay(user.company_id, emr)
    flash('Bot Deployed. Refresh browser in a few minutes for results', 'success')
    return redirect(url_for('hpsj_pending'))

@celery.task(name='routes.background_update_prime_pending')
def background_update_prime_pending(company_id, emr):
    try:
        print('At the try in background_update_prime')
        all_pending_requests = PrimePendingRequest.query.filter_by(company_id=company_id).all()
        settings = PrimeSettings.query.filter_by(company_id=company_id).first()
        print('About to start Pending_Status')
        pending_request = PrimePending.PrimePendingStatus()
        patient_request_results = pending_request.Pending_Status(all_pending_requests, settings)
        print('Out of Pending_Status')
        for member in patient_request_results['process_list']:
            model = PrimePendingRequest.query.filter_by(refNumber=member.ReferenceNumber).first()
            model.status = member.AuthStatus
            model.message = member.Message
            db.session.commit()

    except Exception as ex:
        print(ex)

    print('About to check EMR')
    if emr:
        if len(patient_request_results['approvals_list']) > 0:
            print('About to start EMR Approval')
            approvals_list= []
            for member in patient_request_results['approvals_list']:
                approvals_list.append({
                    'ReferenceNumber': member.ReferenceNumber, 'Id': member.Id, 'LastName': member.LastName,
                    'FirstName': member.FirstName, 'DOB': member.DOB, 'DOBMonth': member.DOBMonth, 'DOBDay': member.DOBDay,
                    'DOBYear': member.DOBYear, 'DateSubmitted': member.DateSubmitted, 'ExpirationDate': member.ExpirationDate,
                    'Visits': member.Visits, 'Approved': member.Approved, 'Insurance': member.Insurance
                })
            insurance = 'php'
            background_emr_approval.delay(approvals_list, company_id, insurance)
            print('EMR Approval entry Complete')
        else:
            print('EMR Approval Not Run')

@app.route("/update_prime_pending", methods=['POST'])
@login_required
def update_prime_pending():
    user = User.query.get(current_user.get_id())
    settings = PrimeSettings.query.filter_by(company_id=user.company_id).first()
    if not settings:
        flash('Update settings', 'danger')
        return redirect(url_for('medical_settings'))
    if request.form.get('emr-checkbox'):
        print('EMR checked')
        emr = True
    else:
        print('EMR not checked')
        emr = False
    background_update_prime_pending.delay(user.company_id, emr)
    flash('Bot Deployed. Refresh browser in a few minutes for results', 'success')
    return redirect(url_for('prime_pending'))

@celery.task(name='routes.background_update_medical_pending')
def background_update_medical_pending(company_id, emr):
    try:
        print('At the try in background_update_medical')
        all_pending_requests = MediCalPendingRequest.query.filter_by(company_id=company_id).all()
        settings = MediCalSettings.query.filter_by(company_id=company_id).first()
        print('About to start Pending_Status')
        pending_request = MediCalPending.MediCalPendingStatus()
        patient_request_results = pending_request.Pending_Status(all_pending_requests, settings)
        print('Out of Pending_Status')
        for member in patient_request_results['process_list']:
            model = MediCalPendingRequest.query.filter_by(refNumber=member.ReferenceNumber).first()
            model.status = member.AuthStatus
            model.message = member.Message
            db.session.commit()

    except Exception as ex:
        print(ex)

    print('About to check EMR')
    if emr:
        if len(patient_request_results['approvals_list']) > 0:
            print('About to start EMR Approval')
            approvals_list= []
            for member in patient_request_results['approvals_list']:
                approvals_list.append({
                    'ReferenceNumber': member.ReferenceNumber, 'Id': member.Id, 'LastName': member.LastName,
                    'FirstName': member.FirstName, 'DOB': member.DOB, 'DOBMonth': member.DOBMonth, 'DOBDay': member.DOBDay,
                    'DOBYear': member.DOBYear, 'DateSubmitted': member.DateSubmitted, 'ExpirationDate': member.ExpirationDate,
                    'Visits': member.Visits, 'Approved': member.Approved, 'Insurance': member.Insurance
                })
            insurance = 'medical'
            background_emr_approval.delay(approvals_list, company_id, insurance)
            print('EMR Approval entry Complete')
        else:
            print('EMR Approval Not Run')

@app.route("/update_medical_pending", methods=['POST'])
@login_required
def update_medical_pending():
    print('Starting')
    user = User.query.get(current_user.get_id())
    settings = MediCalSettings.query.filter_by(company_id=user.company_id).first()
    if not settings:
        flash('Update settings', 'danger')
        return redirect(url_for('medical_settings'))
    if request.form.get('emr-checkbox'):
        print('EMR checked')
        emr = True
    else:
        print('EMR not checked')
        emr = False
    background_update_medical_pending.delay(user.company_id, emr)
    flash('Bot Deployed. Refresh browser in a few minutes for results', 'success')
    return redirect(url_for('medical_pending'))

@celery.task(name='routes.background_update_php_pending')
def background_update_php_pending(company_id, emr):
    try:
        print('At the try in background_update_php')
        all_pending_requests = PHPPendingRequest.query.filter_by(company_id=company_id).all()
        settings = PHPSettings.query.filter_by(company_id=company_id).first()
        print('About to start Pending_Status')
        pending_request = PHPPending.PHPPendingStatus()
        patient_request_results = pending_request.Pending_Status(all_pending_requests, settings)
        print('Out of Pending_Status')
        for member in patient_request_results['process_list']:
            model = PHPPendingRequest.query.filter_by(refNumber=member.ReferenceNumber).first()
            model.status = member.AuthStatus
            model.message = member.Message
            db.session.commit()

    except Exception as ex:
        print(ex)

    print('About to check EMR')
    if emr:
        if len(patient_request_results['approvals_list']) > 0:
            print('About to start EMR Approval')
            approvals_list= []
            for member in patient_request_results['approvals_list']:
                approvals_list.append({
                    'ReferenceNumber': member.ReferenceNumber, 'Id': member.Id, 'LastName': member.LastName,
                    'FirstName': member.FirstName, 'DOB': member.DOB, 'DOBMonth': member.DOBMonth, 'DOBDay': member.DOBDay,
                    'DOBYear': member.DOBYear, 'DateSubmitted': member.DateSubmitted, 'ExpirationDate': member.ExpirationDate,
                    'Visits': member.Visits, 'Approved': member.Approved, 'Insurance': member.Insurance
                })
            insurance = 'php'
            background_emr_approval.delay(approvals_list, company_id, insurance)
            print('EMR Approval entry Complete')
        else:
            print('EMR Approval Not Run')

@app.route("/update_php_pending", methods=['POST'])
@login_required
def update_php_pending():
    user = User.query.get(current_user.get_id())
    settings = PHPSettings.query.filter_by(company_id=user.company_id).first()
    if not settings:
        flash('Update settings', 'danger')
        return redirect(url_for('medical_settings'))
    if request.form.get('emr-checkbox'):
        print('EMR checked')
        emr = True
    else:
        print('EMR not checked')
        emr = False
    background_update_php_pending.delay(user.company_id, emr)
    flash('Bot Deployed. Refresh browser in a few minutes for results', 'success')
    return redirect(url_for('php_pending'))

print("#"*50, "START")
dir_path = os.path.dirname(os.path.realpath(__file__))
print(dir_path)
session = aws_session()
s3_resource = session.resource('s3')    
# s3_url = upload_file_to_bucket('quickauths', os.path.join(dir_path, 'children.csv'), "PHP")
# print(s3_url) # https://tci-s3-demo.s3.amazonaws.com/children.csv