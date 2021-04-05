class PatientNewRequestData:
    MemberId = str = ''
    ReferenceNumber = str = ''
    Message = str = ''
    FirstName = str = ''
    LastName = str = ''
    DOB = str = ''
    DateSubmitted = str = ''
    Plan = str = ''
    Eligibility = str = ''
    Status = str = ''
    AuthReason = str = ''
    ThruValue = str = ''

    def __repr__(self) -> str:
        return f"Patient('{self.MemberId}', '{self.ReferenceNumber}')"