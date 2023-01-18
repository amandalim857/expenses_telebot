class ExpenseItem():
    def __init__(self):
        self.userid = None
        self.title = None
        self.amount = None
        self.paymentmode = None
        self.date = None
        self.remarks = None
    
    def tuple_form(self):
        return (self.userid, self.title, self.amount, self.paymentmode,self.date, self.remarks)
        
    def __str__(self) -> str:
        return f"({self.userid}, {self.title}, \
         {self.amount}, {self.paymentmode}, {self.date}, {self.remarks})"
         