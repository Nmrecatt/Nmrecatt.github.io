import smtplib
import random
import math
def mail(email,fp):
    # storing strings in a list
    digits = [i for i in range(0, 10)]
    # initializing a string
    OTP = ""
    for i in range(6):
    # generating a random index
        index = math.floor(random.random() * 10)
        OTP += str(digits[index])
    # content to be sent
    if fp==1:
        content = '\nHello! \nyou recently requested for password change please enter the given OTP to reset your password : '+ OTP +' .\nIf you did not request a password reset, please ignore this email or reply to let us know.This reset is only valid for the next 30 minutes.\n\nThanks....\nFaceRecognition based attendance system NMREC'
        username = "nmrecattndc83@gmail.com"
        password = "nmrec@frba"
        sender = "nmrecattndc83@gmail.com"
        recipient = email
        mail = smtplib.SMTP("smtp.gmail.com",587)
        mail.ehlo() # identify the computer
        mail.starttls() # transport layer security - encrypt the details
        mail.login("attendance@nmrec.edu.in","nmrec@frba")
        header = 'To:' + recipient + '\n' + 'From:' + sender + '\n' + 'Subject: Reset password OTP \n'
        content = header+content
        print(content)
        mail.sendmail(sender,recipient,content)
        mail.close
    return(OTP)
