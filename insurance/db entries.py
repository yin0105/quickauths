from insurance import db
from insurance.models import Company, User, PHPSettings, PHPEligibility, MediCalPendingRequest, MediCalRequest
import datetime
# db.create_all()
###Adding Rows###
# companies = User.query.all()
# print(companies)
# sspt = Company(2, 'sspt', 1)
# # adventist = Company(3, "AdventistOrtho", 1)
# # ethan = User(5, 'advenortho', 'admin@adven.com', 'admin', 3)
# db.session.add_all([sspt])
# db.session.commit()
# pending = MediCalPendingRequest.query.filter_by(id=1).all()
# print(pending)
# pending = MediCalPendingRequest.query.filter_by(id=1).all()
# print(pending)
# patient_1 = MediCalPendingRequest(1, '95339712D', '0535776515', 'datetime', 'Submitted' )
# patient_1 = MediCalPendingRequest(2, '90605242G', '0536016799', datetime(2012, 3, 3, 10, 10, 10), 1)
# db.session.add_all([patient_1])
# db.session.commit()
###Deleting Rows###
# user1 = User.query.filter_by(id=1).all()
# print(user1)
# user1 = PHPSettings.query.filter_by(id=1).all()
# print(user1)
# db.session.query(PHPSettings).filter(PHPSettings.id==1).delete()
# db.session.commit()
# print(User.query.all())

###Deleting User Account###
# user1 = PHPEligibility.query.filter_by(member_ID='').first()
# print(user1)
# db.session.query(PHPEligibility).filter(PHPEligibility.member_ID=='').delete()
# db.session.commit()
# #
# # db.session.query(PHPSettings).delete()

# INSERT INTO medi_cal_pending_request (id, member_id, refnumber, submitteddate, status, emr, company_id, dob, firstname, lastname)
# VALUES ('4', '95339712D', '0536075448' , '2021-03-11 00:00:00.000000', 'Submitted', '1', '1', '1997-04-02 00:00:00.000000', 'Marquis', 'Cole');

# INSERT INTO php_pending_request (id, member_id, refnumber, submitteddate, status, emr, company_id, dob, firstname, lastname, message)
# VALUES ('4', '1', 'PA2103100158' , '2021-03-11 00:00:00.000000', 'Submitted', '1', '1', '1988-12-09 00:00:00.000000', 'JUAN', 'ROSA', 'n/a')