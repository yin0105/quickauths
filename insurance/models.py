from insurance import db, login_manager, app
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask_login import UserMixin


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    admin = db.Column(db.Boolean, default=False)
    active = db.Column(db.Boolean, default=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)

    def get_reset_token(self, expires_sec=1800):
        s = Serializer(app.config['SECRET_KEY'], expires_sec)
        return s.dumps({'user_id': self.id}).decode('utf-8')

    @staticmethod
    def verify_reset_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token)['user_id']
        except:
            return None
        return User.query.get(user_id)

    def __repr__(self):
        return f"User('{self.id}', '{self.username}', '{self.email}', '{self.company_id}')"

# class Patients(db.Model):
#     member_ID = db.Column(db.String(20), primary_key=True, nullable=False)
#     firstName = db.Column(db.String(20), nullable=False)
#     lastName = db.Column(db.String(20), nullable=False)
#
#     def __repr__(self):
#         return f"Patient('{self.firstName}', '{self.memberID}')"

class Company(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    file_counter = db.Column(db.Integer, default=0)
    
    def __repr__(self):
        return f"Company('{self.id}', '{self.name}', '{self.file_counter})'"

class HPSJSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    fax = db.Column(db.String(15), nullable=False)
    provider = db.Column(db.String(100), nullable=False)
    speciality = db.Column(db.String(100), nullable=False)
    
    def __repr__(self):
        return f"Credentials('{self.username}')"

class PrimeSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    fax = db.Column(db.String(15), nullable=False)
    provider = db.Column(db.String(100), nullable=False)
    
    def __repr__(self):
        return f"Credentials('{self.username}')"

class MediCalSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    contactName = db.Column(db.String(60), nullable=False)
    contactPhone = db.Column(db.String(60), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    npi = db.Column(db.String(20), nullable=False)
    speciality = db.Column(db.String(100), nullable=False)
    
    def __repr__(self):
        return f"Credentials('{self.username}')"

class PHPSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)

    def __repr__(self):
        return f"Credentials('{self.username}')"

class HPSJEligibility(db.Model):
    member_ID = db.Column(db.String(20), primary_key=True)
    firstName = db.Column(db.String(30))
    lastName = db.Column(db.String(30))
    eligibility = db.Column(db.String(100))
    thruDate = db.Column(db.DateTime)
    dob = db.Column(db.DateTime)
    status = db.Column(db.String(100))
    plan = db.Column(db.String(200))
    message = db.Column(db.String(200))
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)

    def __repr__(self):
        return f"Eligibility('{self.member_ID}', '{self.status}')"

class PrimeEligibility(db.Model):
    member_ID = db.Column(db.String(20), primary_key=True)
    firstName = db.Column(db.String(30))
    lastName = db.Column(db.String(30))
    eligibility = db.Column(db.String(100))
    dateChecked = db.Column(db.DateTime)
    dob = db.Column(db.DateTime)
    plan = db.Column(db.String(200))
    message = db.Column(db.String(200))
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)

    def __repr__(self):
        return f"Eligibility('{self.member_ID}', '{self.status}')"

class MediCalEligibility(db.Model):
    member_ID = db.Column(db.String(20), primary_key=True)
    firstName = db.Column(db.String(30))
    lastName = db.Column(db.String(30))
    eligibility = db.Column(db.String(100))
    dateChecked = db.Column(db.DateTime)
    dob = db.Column(db.DateTime)
    plan = db.Column(db.String(200))
    message = db.Column(db.String(200))
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)

    def __repr__(self):
        return f"Eligibility('{self.member_ID}', '{self.plan}')"

class PHPEligibility(db.Model):
    member_ID = db.Column(db.String(20), primary_key=True)
    firstName = db.Column(db.String(30))
    lastName = db.Column(db.String(30))
    eligibility = db.Column(db.String(100))
    thruDate = db.Column(db.DateTime)
    status = db.Column(db.String(100))
    other_ins = db.Column(db.String(200))
    message = db.Column(db.String(200))
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)

    def __repr__(self):
        return f"Eligibility('{self.member_ID}', '{self.status}')"

class icd10(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), nullable=False)
    name = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f"ic_d10('{self.code}', '{self.name}')"

class HPSJPendingRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    member_ID = db.Column(db.String(20), nullable=False)
    firstName = db.Column(db.String(30))
    lastName = db.Column(db.String(30))
    dob = db.Column(db.DateTime)
    refNumber = db.Column(db.String(30), nullable=False)
    submittedDate = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(100))
    message = db.Column(db.String(200))
    case = db.Column(db.String(100))
    emr_entry = db.Column(db.String(100))
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)

    def __repr__(self):
        return f"PendingRequest('{self.refNumber}', '{self.submittedDate}')"

class HPSJRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    member_ID = db.Column(db.String(20), nullable=False)
    caseName = db.Column(db.String(30))
    frequency = db.Column(db.String(20))
    icd1 = db.Column(db.String(20))
    icd2 = db.Column(db.String(20))
    icd3 = db.Column(db.String(20))
    icd4 = db.Column(db.String(20))
    icd5 = db.Column(db.String(20))
    icd6 = db.Column(db.String(20))
    icd7 = db.Column(db.String(20))
    CPT1 = db.Column(db.String(20))
    CPTUnit1 = db.Column(db.Integer)
    CPT2 = db.Column(db.String(20))
    CPTUnit2 = db.Column(db.Integer)
    CPT3 = db.Column(db.String(20))
    CPTUnit3 = db.Column(db.Integer)
    CPT4 = db.Column(db.String(20))
    CPTUnit4 = db.Column(db.Integer)
    CPT5 = db.Column(db.String(20))
    CPTUnit5 = db.Column(db.Integer)
    CPT6 = db.Column(db.String(20))
    CPTUnit6 = db.Column(db.Integer)
    CPT7 = db.Column(db.String(20))
    CPTUnit7 = db.Column(db.Integer)
    urgent = db.Column(db.Boolean, default=False)
    emr = db.Column(db.Boolean, default=False)
    startDate = db.Column(db.DateTime, nullable=False)
    endDate = db.Column(db.DateTime, nullable=False)
    message = db.Column(db.String(300))
    files = db.Column(db.String(100))
    status = db.Column(db.String(100), nullable=False)
    submissionMessage = db.Column(db.String(300))
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)

    def __repr__(self):
        return f"Request('{self.member_ID}', '{self.status}')"

class HPSJTemplate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(40), nullable=False)
    frequency = db.Column(db.String(20))
    emr = db.Column(db.Boolean, default=False)
    icd1 = db.Column(db.String(10))
    icd2 = db.Column(db.String(10))
    icd3 = db.Column(db.String(10))
    icd4 = db.Column(db.String(10))
    icd5 = db.Column(db.String(10))
    icd6 = db.Column(db.String(10))
    icd7 = db.Column(db.String(10))
    CPT1 = db.Column(db.String(20))
    CPTUnit1 = db.Column(db.Integer)
    CPT2 = db.Column(db.String(20))
    CPTUnit2 = db.Column(db.Integer)
    CPT3 = db.Column(db.String(20))
    CPTUnit3 = db.Column(db.Integer)
    CPT4 = db.Column(db.String(20))
    CPTUnit4 = db.Column(db.Integer)
    CPT5 = db.Column(db.String(20))
    CPTUnit5 = db.Column(db.Integer)
    CPT6 = db.Column(db.String(20))
    CPTUnit6 = db.Column(db.Integer)
    CPT7 = db.Column(db.String(20))
    CPTUnit7 = db.Column(db.Integer)
    message = db.Column(db.String(300))
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)

    def __repr__(self):
        return f"Template('{self.name}', '{self.message}')"

class PrimePendingRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    member_ID = db.Column(db.String(20), nullable=False)
    firstName = db.Column(db.String(30))
    lastName = db.Column(db.String(30))
    refNumber = db.Column(db.String(30), nullable=False)
    submittedDate = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(100))
    message = db.Column(db.String(300))
    case = db.Column(db.String(100))
    emr_entry = db.Column(db.String(100))
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)

    def __repr__(self):
        return f"PendingRequest('{self.refNumber}', '{self.submittedDate}')"

class PrimeRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    member_ID = db.Column(db.String(20), nullable=False)
    caseName = db.Column(db.String(30))
    frequency = db.Column(db.String(20))
    icd1 = db.Column(db.String(20))
    icd2 = db.Column(db.String(20))
    icd3 = db.Column(db.String(20))
    icd4 = db.Column(db.String(20))
    icd5 = db.Column(db.String(20))
    icd6 = db.Column(db.String(20))
    icd7 = db.Column(db.String(20))
    CPT1 = db.Column(db.String(20))
    CPTUnit1 = db.Column(db.Integer)
    CPT2 = db.Column(db.String(20))
    CPTUnit2 = db.Column(db.Integer)
    CPT3 = db.Column(db.String(20))
    CPTUnit3 = db.Column(db.Integer)
    CPT4 = db.Column(db.String(20))
    CPTUnit4 = db.Column(db.Integer)
    CPT5 = db.Column(db.String(20))
    CPTUnit5 = db.Column(db.Integer)
    CPT6 = db.Column(db.String(20))
    CPTUnit6 = db.Column(db.Integer)
    CPT7 = db.Column(db.String(20))
    CPTUnit7 = db.Column(db.Integer)
    urgent = db.Column(db.Boolean, default=False)
    emr = db.Column(db.Boolean, default=False)
    startDate = db.Column(db.DateTime, nullable=False)
    endDate = db.Column(db.DateTime, nullable=False)
    message = db.Column(db.String(300))
    files = db.Column(db.String(100))
    status = db.Column(db.String(100), nullable=False)
    submissionMessage = db.Column(db.String(300))
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)

    def __repr__(self):
        return f"Request('{self.member_ID}', '{self.status}')"

class PrimeTemplate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(40), nullable=False)
    frequency = db.Column(db.String(20))
    emr = db.Column(db.Boolean, default=False)
    icd1 = db.Column(db.String(10))
    icd2 = db.Column(db.String(10))
    icd3 = db.Column(db.String(10))
    icd4 = db.Column(db.String(10))
    icd5 = db.Column(db.String(10))
    icd6 = db.Column(db.String(10))
    icd7 = db.Column(db.String(10))
    CPT1 = db.Column(db.String(20))
    CPTUnit1 = db.Column(db.Integer)
    CPT2 = db.Column(db.String(20))
    CPTUnit2 = db.Column(db.Integer)
    CPT3 = db.Column(db.String(20))
    CPTUnit3 = db.Column(db.Integer)
    CPT4 = db.Column(db.String(20))
    CPTUnit4 = db.Column(db.Integer)
    CPT5 = db.Column(db.String(20))
    CPTUnit5 = db.Column(db.Integer)
    CPT6 = db.Column(db.String(20))
    CPTUnit6 = db.Column(db.Integer)
    CPT7 = db.Column(db.String(20))
    CPTUnit7 = db.Column(db.Integer)
    message = db.Column(db.String(300))
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)

    def __repr__(self):
        return f"Template('{self.name}', '{self.message}')"

class MediCalPendingRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    member_ID = db.Column(db.String(20), nullable=False)
    firstName = db.Column(db.String(30))
    lastName = db.Column(db.String(30))
    dob = db.Column(db.DateTime)
    refNumber = db.Column(db.String(30))
    submittedDate = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(100), nullable=False)
    message = db.Column(db.String(300))
    case = db.Column(db.String(100))
    emr = db.Column(db.String(100))
    emr_entry = db.Column(db.String(100))
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)

    def __repr__(self):
        return f"PendingRequest('{self.refNumber}', '{self.submittedDate}')"

class MediCalRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    member_ID = db.Column(db.String(20), nullable=False)
    caseName = db.Column(db.String(30))
    referringMD = db.Column(db.String(20))
    frequency = db.Column(db.String(20))
    dob = db.Column(db.DateTime)
    icd1 = db.Column(db.String(20))
    icd2 = db.Column(db.String(20))
    icd3 = db.Column(db.String(20))
    icd4 = db.Column(db.String(20))
    icd5 = db.Column(db.String(20))
    icd6 = db.Column(db.String(20))
    icd7 = db.Column(db.String(20))
    CPT1 = db.Column(db.String(20))
    CPTUnit1 = db.Column(db.Integer)
    CPT2 = db.Column(db.String(20))
    CPTUnit2 = db.Column(db.Integer)
    CPT3 = db.Column(db.String(20))
    CPTUnit3 = db.Column(db.Integer)
    CPT4 = db.Column(db.String(20))
    CPTUnit4 = db.Column(db.Integer)
    CPT5 = db.Column(db.String(20))
    CPTUnit5 = db.Column(db.Integer)
    CPT6 = db.Column(db.String(20))
    CPTUnit6 = db.Column(db.Integer)
    CPT7 = db.Column(db.String(20))
    CPTUnit7 = db.Column(db.Integer)
    urgent = db.Column(db.Boolean, default=False)
    emr = db.Column(db.Boolean, default=False)
    startDate = db.Column(db.DateTime, nullable=False)
    endDate = db.Column(db.DateTime, nullable=False)
    prescriptionDate = db.Column(db.DateTime)
    onsetDate = db.Column(db.DateTime)
    message = db.Column(db.String(300))
    medicalJustification = db.Column(db.String(300))
    files = db.Column(db.String(100))
    status = db.Column(db.String(100), nullable=False)
    submissionMessage = db.Column(db.String(300))
    gender = db.Column(db.String(10))
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f"Request('{self.member_ID}', '{self.status}')"

class MediCalTemplate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(40), nullable=False)
    frequency = db.Column(db.String(20))
    emr = db.Column(db.Boolean, default=False)
    icd1 = db.Column(db.String(10))
    icd2 = db.Column(db.String(10))
    icd3 = db.Column(db.String(10))
    icd4 = db.Column(db.String(10))
    icd5 = db.Column(db.String(10))
    icd6 = db.Column(db.String(10))
    icd7 = db.Column(db.String(10))
    CPT1 = db.Column(db.String(20))
    CPTUnit1 = db.Column(db.Integer)
    CPT2 = db.Column(db.String(20))
    CPTUnit2 = db.Column(db.Integer)
    CPT3 = db.Column(db.String(20))
    CPTUnit3 = db.Column(db.Integer)
    CPT4 = db.Column(db.String(20))
    CPTUnit4 = db.Column(db.Integer)
    CPT5 = db.Column(db.String(20))
    CPTUnit5 = db.Column(db.Integer)
    CPT6 = db.Column(db.String(20))
    CPTUnit6 = db.Column(db.Integer)
    CPT7 = db.Column(db.String(20))
    CPTUnit7 = db.Column(db.Integer)
    message = db.Column(db.String(300))
    medicalJustification = db.Column(db.String(300))
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)

    def __repr__(self):
        return f"Template('{self.name}', '{self.message}')"

class PHPPendingRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    member_ID = db.Column(db.String(20), nullable=False)
    firstName = db.Column(db.String(30))
    lastName = db.Column(db.String(30))
    dob = db.Column(db.DateTime)
    refNumber = db.Column(db.String(30))
    submittedDate = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(100), nullable=False)
    message = db.Column(db.String(300))
    case = db.Column(db.String(50))
    emr = db.Column(db.String(100))
    emr_entry = db.Column(db.String(100))
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)

    def __repr__(self):
        return f"PendingRequest('{self.refNumber}', '{self.submittedDate}')"

class PHPRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    member_ID = db.Column(db.String(20), nullable=False)
    caseName = db.Column(db.String(30))
    frequency = db.Column(db.String(20))
    icd1 = db.Column(db.String(20))
    icd2 = db.Column(db.String(20))
    icd3 = db.Column(db.String(20))
    icd4 = db.Column(db.String(20))
    icd5 = db.Column(db.String(20))
    icd6 = db.Column(db.String(20))
    icd7 = db.Column(db.String(20))
    CPT1 = db.Column(db.String(20))
    CPTUnit1 = db.Column(db.Integer)
    CPT2 = db.Column(db.String(20))
    CPTUnit2 = db.Column(db.Integer)
    CPT3 = db.Column(db.String(20))
    CPTUnit3 = db.Column(db.Integer)
    CPT4 = db.Column(db.String(20))
    CPTUnit4 = db.Column(db.Integer)
    CPT5 = db.Column(db.String(20))
    CPTUnit5 = db.Column(db.Integer)
    CPT6 = db.Column(db.String(20))
    CPTUnit6 = db.Column(db.Integer)
    CPT7 = db.Column(db.String(20))
    CPTUnit7 = db.Column(db.Integer)
    urgent = db.Column(db.Boolean, default=False)
    emr = db.Column(db.Boolean, default=False)
    startDate = db.Column(db.DateTime, nullable=False)
    endDate = db.Column(db.DateTime, nullable=False)
    message = db.Column(db.String(300))
    files = db.Column(db.String(100))
    status = db.Column(db.String(100), nullable=False)
    submissionMessage = db.Column(db.String(300))
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)

    def __repr__(self):
        return f"Request('{self.member_ID}', '{self.status}')"

class PHPTemplate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(40), nullable=False)
    frequency = db.Column(db.String(20))
    emr = db.Column(db.Boolean, default=False)
    icd1 = db.Column(db.String(10))
    icd2 = db.Column(db.String(10))
    icd3 = db.Column(db.String(10))
    icd4 = db.Column(db.String(10))
    icd5 = db.Column(db.String(10))
    icd6 = db.Column(db.String(10))
    icd7 = db.Column(db.String(10))
    CPT1 = db.Column(db.String(20))
    CPTUnit1 = db.Column(db.Integer)
    CPT2 = db.Column(db.String(20))
    CPTUnit2 = db.Column(db.Integer)
    CPT3 = db.Column(db.String(20))
    CPTUnit3 = db.Column(db.Integer)
    CPT4 = db.Column(db.String(20))
    CPTUnit4 = db.Column(db.Integer)
    CPT5 = db.Column(db.String(20))
    CPTUnit5 = db.Column(db.Integer)
    CPT6 = db.Column(db.String(20))
    CPTUnit6 = db.Column(db.Integer)
    CPT7 = db.Column(db.String(20))
    CPTUnit7 = db.Column(db.Integer)
    message = db.Column(db.String(300))
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)

    def __repr__(self):
        return f"Template('{self.name}', '{self.message}')"

class EMR(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)

    def __repr__(self):
        return f"EMR('{self.username}')"