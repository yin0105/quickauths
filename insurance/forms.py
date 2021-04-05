from wtforms.fields.core import DateField
from wtforms.fields.simple import FileField
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, IntegerField, SelectField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, Optional
from insurance.models import User


class RegistrationForm(FlaskForm):
    username = StringField('Username',
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is taken. Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is taken. Please choose a different one.')


class LoginForm(FlaskForm):
    username = StringField('Username',
                        validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class HPSJRequestForm(FlaskForm):
    memberid = StringField('Member ID', validators=[Optional()])
    name = StringField('Template Name', validators=[Optional()])
    case_name = StringField('Case Name', validators=[Optional()])
    frequency = StringField('Frequency', validators=[Optional()])
    icd10_1 = StringField('ICD10', validators=[Optional()])
    icd10_2 = StringField('ICD10', validators=[Optional()])
    icd10_3 = StringField('ICD10', validators=[Optional()])
    icd10_4 = StringField('ICD10', validators=[Optional()])
    icd10_5 = StringField('ICD10', validators=[Optional()])
    icd10_6 = StringField('ICD10', validators=[Optional()])
    icd10_7 = StringField('ICD10', validators=[Optional()])
    cpt_1 = StringField('CPT', validators=[Optional()])
    cpt_2 = StringField('CPT', validators=[Optional()])
    cpt_3 = StringField('CPT', validators=[Optional()])
    cpt_4 = StringField('CPT', validators=[Optional()])
    cpt_5 = StringField('CPT', validators=[Optional()])
    cpt_6 = StringField('CPT', validators=[Optional()])
    cpt_7 = StringField('CPT', validators=[Optional()])
    unit_1 = IntegerField('Unit', validators=[Optional()])
    unit_2 = IntegerField('Unit', validators=[Optional()])
    unit_3 = IntegerField('Unit', validators=[Optional()])
    unit_4 = IntegerField('Unit', validators=[Optional()])
    unit_5 = IntegerField('Unit', validators=[Optional()])
    unit_6 = IntegerField('Unit', validators=[Optional()])
    unit_7 = IntegerField('Unit', validators=[Optional()])
    start_date = DateField('Start Date', format='%m/%d/%Y', validators=[Optional()])
    end_date = DateField('End Date', format='%m/%d/%Y', validators=[Optional()])
    file = FileField('File')
    message = StringField('Message', validators=[Optional()])
    urgent = BooleanField('Urgent', validators=[Optional()])
    emr = BooleanField('EMR', validators=[Optional()])
    submit = SubmitField('Add Member')

class EligibilityForm(FlaskForm):
    memberid = StringField('Member ID', validators=[DataRequired()])
    dob = DateField('Date of Birthh', format='%m/%d/%Y', validators=[Optional()])
    submit = SubmitField('Add')

class HPSJSettingsForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = StringField('Password', validators=[DataRequired()])
    company = StringField('Company', validators=[DataRequired()])
    provider = StringField('Provider', validators=[DataRequired()])
    speciality = StringField('Speciality', validators=[DataRequired()])
    fax = StringField('Fax Number', validators=[DataRequired()])
    submit = SubmitField('Add')

class PrimeSettingsForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = StringField('Password', validators=[DataRequired()])
    provider = StringField('Provider', validators=[DataRequired()])
    fax = StringField('Fax Number', validators=[DataRequired()])
    submit = SubmitField('Add')

class MediCalSettingsForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = StringField('Password', validators=[DataRequired()])
    npi = StringField('NPI', validators=[DataRequired()])
    speciality = StringField('Speciality', validators=[DataRequired()])
    contact_name = StringField('Contact Name', validators=[DataRequired()])
    contact_phone = StringField('Contact Phone', validators=[DataRequired()])
    submit = SubmitField('Add')

class PHPSettingsForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = StringField('Password', validators=[DataRequired()])
    submit = SubmitField('Add')

class PrimeRequestForm(FlaskForm):
    memberid = StringField('Member ID', validators=[Optional()])
    name = StringField('Template Name', validators=[Optional()])
    case_name = StringField('Case Name', validators=[Optional()])
    frequency = StringField('Frequency', validators=[Optional()])
    icd10_1 = StringField('ICD10', validators=[Optional()])
    icd10_2 = StringField('ICD10', validators=[Optional()])
    icd10_3 = StringField('ICD10', validators=[Optional()])
    icd10_4 = StringField('ICD10', validators=[Optional()])
    icd10_5 = StringField('ICD10', validators=[Optional()])
    icd10_6 = StringField('ICD10', validators=[Optional()])
    icd10_7 = StringField('ICD10', validators=[Optional()])
    cpt_1 = StringField('CPT', validators=[Optional()])
    cpt_2 = StringField('CPT', validators=[Optional()])
    cpt_3 = StringField('CPT', validators=[Optional()])
    cpt_4 = StringField('CPT', validators=[Optional()])
    cpt_5 = StringField('CPT', validators=[Optional()])
    cpt_6 = StringField('CPT', validators=[Optional()])
    cpt_7 = StringField('CPT', validators=[Optional()])
    unit_1 = IntegerField('Unit', validators=[Optional()])
    unit_2 = IntegerField('Unit', validators=[Optional()])
    unit_3 = IntegerField('Unit', validators=[Optional()])
    unit_4 = IntegerField('Unit', validators=[Optional()])
    unit_5 = IntegerField('Unit', validators=[Optional()])
    unit_6 = IntegerField('Unit', validators=[Optional()])
    unit_7 = IntegerField('Unit', validators=[Optional()])
    start_date = DateField('Start Date', format='%m/%d/%Y', validators=[Optional()])
    end_date = DateField('End Date', format='%m/%d/%Y', validators=[Optional()])
    file = FileField('File')
    message = StringField('Message', validators=[Optional()])
    urgent = BooleanField('Urgent', validators=[Optional()])
    emr = BooleanField('EMR', validators=[Optional()])
    submit = SubmitField('Add Member')

class MediCalRequestForm(FlaskForm):
    memberid = StringField('Member ID', validators=[Optional()])
    name = StringField('Template Name', validators=[Optional()])
    case_name = StringField('Case Name', validators=[Optional()])
    frequency = StringField('Frequency', validators=[Optional()])
    referring = StringField('Referring MD', validators=[Optional()])
    icd10_1 = StringField('ICD10', validators=[Optional()])
    icd10_2 = StringField('ICD10', validators=[Optional()])
    icd10_3 = StringField('ICD10', validators=[Optional()])
    icd10_4 = StringField('ICD10', validators=[Optional()])
    icd10_5 = StringField('ICD10', validators=[Optional()])
    icd10_6 = StringField('ICD10', validators=[Optional()])
    icd10_7 = StringField('ICD10', validators=[Optional()])
    cpt_1 = StringField('CPT', validators=[Optional()])
    cpt_2 = StringField('CPT', validators=[Optional()])
    cpt_3 = StringField('CPT', validators=[Optional()])
    cpt_4 = StringField('CPT', validators=[Optional()])
    cpt_5 = StringField('CPT', validators=[Optional()])
    cpt_6 = StringField('CPT', validators=[Optional()])
    cpt_7 = StringField('CPT', validators=[Optional()])
    unit_1 = IntegerField('Unit', validators=[Optional()])
    unit_2 = IntegerField('Unit', validators=[Optional()])
    unit_3 = IntegerField('Unit', validators=[Optional()])
    unit_4 = IntegerField('Unit', validators=[Optional()])
    unit_5 = IntegerField('Unit', validators=[Optional()])
    unit_6 = IntegerField('Unit', validators=[Optional()])
    unit_7 = IntegerField('Unit', validators=[Optional()])
    dob = DateField('DOB', format='%m/%d/%Y', validators=[Optional()])
    start_date = DateField('Start Date', format='%m/%d/%Y', validators=[Optional()])
    end_date = DateField('End Date', format='%m/%d/%Y', validators=[Optional()])
    prescription_date = DateField('Prescription Date', format='%m/%d/%Y', validators=[Optional()])
    onset_date = DateField('Onset Date', format='%m/%d/%Y', validators=[Optional()])
    file = FileField('File')
    message = StringField('Message', validators=[Optional()])
    medical_justification = StringField('Medical Justification', validators=[Optional()])
    urgent = BooleanField('Urgent', validators=[Optional()])
    emr = BooleanField('EMR', validators=[Optional()])
    gender = SelectField('Gender', choices=[('M', 'Male'), ('F', 'Female') ])
    submit = SubmitField('Add Member')

class PHPRequestForm(FlaskForm):
    memberid = StringField('Member ID', validators=[Optional()])
    name = StringField('Template Name', validators=[Optional()])
    case_name = StringField('Case Name', validators=[Optional()])
    frequency = StringField('Frequency', validators=[Optional()])
    icd10_1 = StringField('ICD10', validators=[Optional()])
    icd10_2 = StringField('ICD10', validators=[Optional()])
    icd10_3 = StringField('ICD10', validators=[Optional()])
    icd10_4 = StringField('ICD10', validators=[Optional()])
    icd10_5 = StringField('ICD10', validators=[Optional()])
    icd10_6 = StringField('ICD10', validators=[Optional()])
    icd10_7 = StringField('ICD10', validators=[Optional()])
    cpt_1 = StringField('CPT', validators=[Optional()])
    cpt_2 = StringField('CPT', validators=[Optional()])
    cpt_3 = StringField('CPT', validators=[Optional()])
    cpt_4 = StringField('CPT', validators=[Optional()])
    cpt_5 = StringField('CPT', validators=[Optional()])
    cpt_6 = StringField('CPT', validators=[Optional()])
    cpt_7 = StringField('CPT', validators=[Optional()])
    unit_1 = IntegerField('Unit', validators=[Optional()])
    unit_2 = IntegerField('Unit', validators=[Optional()])
    unit_3 = IntegerField('Unit', validators=[Optional()])
    unit_4 = IntegerField('Unit', validators=[Optional()])
    unit_5 = IntegerField('Unit', validators=[Optional()])
    unit_6 = IntegerField('Unit', validators=[Optional()])
    unit_7 = IntegerField('Unit', validators=[Optional()])
    start_date = DateField('Start Date', format='%m/%d/%Y', validators=[Optional()])
    end_date = DateField('End Date', format='%m/%d/%Y', validators=[Optional()])
    file = FileField('File')
    message = StringField('Message', validators=[Optional()])
    urgent = BooleanField('Urgent', validators=[Optional()])
    emr = BooleanField('EMR', validators=[Optional()])
    submit = SubmitField('Add Member')

class EMRForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = StringField('Password', validators=[DataRequired()])
    emr = SelectField('EMR', choices=[('webpt', 'WebPT')])
    submit = SubmitField('Submit')

class CompanyForm(FlaskForm):
    name = StringField('Company Name', validators=[DataRequired()])
    submit = SubmitField('Add')

class RequestResetForm(FlaskForm):
    email = StringField('Enter Account Email:',
                        validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is None:
            raise ValidationError('There is no account with this email. You must register first.')


class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset Password')