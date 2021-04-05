class PatientNewRequestData:
    Id = int
    MemberId = str = ''
    ReferenceNumber = str = ''
    Message = str = ''
    FirstName = str = ''
    LastName = str = ''
    DOB = str = ''
    DateSubmitted = str = ''
    Plan = str = ''
    Eligibility = str = ''
    AuthStatus = str = ''
    AuthReason = str = ''
    Success = bool = False