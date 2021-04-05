class PatientNewRequestData:
    Id = str = ''
    ReferenceNumber = str = ''
    Message = str = ''
    FirstName = str = ''
    LastName = str = ''
    DOB = str = ''
    DOBMonth = str = ''
    DOBDay = str = ''
    DOBYear = str = ''
    ICD10 = []
    DateSubmitted = str = ''
    Plan = str = ''
    Eligibility = str = ''
    AuthStatus = str = ''
    AuthReason = str = ''
    Frequency = str = ''
    Visits = str = ''
    VisitsPer = str = ''
    PerWeeks = str = ''
    EMRMessage = str = ''
    CPTs = []
    Units = []
    Approved = []
    ExpirationDate = str = ''
    Case = str = ''
    Insurance = str = ''
    PrescriptionDate = str = ''
    Success = bool = False