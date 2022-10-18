import smtplib, ssl
from random import randint

def finishedEmail(email, fun = False):

    port = 465  # For SSL
    smtp_server = "smtp.gmail.com"
    sender_email = "Triton12messenger@gmail.com"  # Enter your address
    receiver_email = email  # Enter receiver address
    password = "T12arthur"

    if fun == False:
        message = """\
        Subject: Task complete! :)

        This message is sent from T12."""
    if fun == True:
        i = randint(0,5)
        resp = {
            0:"""\
            Subject: It is done. I took care of it.

            T12.""",
            1:"""\
            Subject: Job done Master.

            Your loyal slave,T12.""",
            2: """\
            Subject: The dark deed is done, My Lord.

            Your loyal minion,T12.""",
            3:"""\
            Subject: Job done.

            More work?.""",
            4: """\
            Subject: Task complete!

            Stop drinking coffee and set up a new task!""",

            5: """\
            Subject: Task complete Oni-Chan ~!

            More work for T12? UwU"""
            }
        message = resp[i]




    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message)


def warningEmail(email, text):

    port = 465  # For SSL
    smtp_server = "smtp.gmail.com"
    sender_email = "Triton12messenger@gmail.com"  # Enter your address
    receiver_email = email  # Enter receiver address
    password = "T12arthur"

    if fun == False:
        message = """\
        Subject: Warning

        {}""".format(text)


    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message)