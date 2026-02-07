from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse
import pymysql
from .crypt import vigenereEncryption, polybiusEncryption, polybiusDecryption, vigenereDecryption
import datetime
import random
import string
import smtplib
from email.message import EmailMessage
from django.conf import settings

# Database connection helper
def get_db_connection():
    return pymysql.connect(
        host=settings.DATABASES['default']['HOST'],
        port=int(settings.DATABASES['default']['PORT']),
        user=settings.DATABASES['default']['USER'],
        password=settings.DATABASES['default']['PASSWORD'],
        database=settings.DATABASES['default']['NAME'],
        charset='utf8'
    )

def sendEmail(decrypt_key, recipient_email):
    # PRINT KEY TO CONSOLE FOR TESTING
    print("="*50)
    print(f"DECRYPTION KEY FOR {recipient_email}: {decrypt_key}")
    print("="*50)

    msg = EmailMessage()
    msg.set_content("Key to decrypt message: " + decrypt_key)
    msg['Subject'] = 'Message From Military Application'
    msg['From'] = "evotingotp4@gmail.com"
    msg['To'] = recipient_email

    try:
        s = smtplib.SMTP('smtp.gmail.com', 587)
        s.starttls()
        s.login("evotingotp4@gmail.com", "xowpojqyiygprhgr")
        s.send_message(msg)
        s.quit()
    except Exception as e:
        print(f"Error sending email: {e}")

def index(request):
    return render(request, 'index.html', {})

def AdminLogin(request):
    return render(request, 'AdminLogin.html', {})

def UserLogin(request):
    return render(request, 'UserLogin.html', {})

def Signup(request):
    return render(request, 'Signup.html', {})

def AdminLoginAction(request):
    if request.method == 'POST':
        username = request.POST.get('t1', False)
        password = request.POST.get('t2', False)
        if username == 'admin' and password == 'admin':
            request.session['uname'] = username
            context = {'data': 'welcome ' + username}
            return render(request, 'AdminScreen.html', context)
        else:
            context = {'data': 'invalid login details'}
            return render(request, 'AdminLogin.html', context)
    return render(request, 'AdminLogin.html', {})

def UserLoginAction(request):
    if request.method == 'POST':
        username = request.POST.get('t1', False)
        password = request.POST.get('t2', False)
        usertype = request.POST.get('t3', False)
        
        con = get_db_connection()
        try:
            with con.cursor() as cur:
                cur.execute("select username, password, user_type, email FROM signup where status='Approved' and username=%s", (username,))
                row = cur.fetchone()
                
                if row and row[1] == password:
                    request.session['uname'] = username
                    request.session['email'] = row[3]
                    request.session['utype'] = row[2]
                    
                    db_usertype = row[2]
                    
                    if usertype == db_usertype:
                        if usertype == 'Major General':
                            return render(request, 'MajorScreen.html', {'data': f'welcome {username} You Logged in as {usertype}'})
                        elif usertype == 'Brigadier':
                            return render(request, 'BrigadierScreen.html', {'data': f'welcome {username} You Logged in as {usertype}'})
                        elif usertype == 'Colonel':
                            return render(request, 'ColonelScreen.html', {'data': f'welcome {username} You Logged in as {usertype}'})
                    
        finally:
            con.close()
            
        context = {'data': 'invalid login details or account not yet approved by your superior'}
        return render(request, 'UserLogin.html', context)
    return render(request, 'UserLogin.html', {})

def SignupAction(request):
    if request.method == 'POST':
        username = request.POST.get('t1')
        password = request.POST.get('t2')
        contact = request.POST.get('t3')
        gender = request.POST.get('t4')
        email = request.POST.get('t5')
        address = request.POST.get('t6')
        usertype = request.POST.get('t7')
        
        con = get_db_connection()
        try:
            with con.cursor() as cur:
                cur.execute("select username FROM signup where username=%s", (username,))
                if cur.fetchone():
                    return render(request, 'Signup.html', {'data': f"{username} Username already exists"})
                
                sql = "INSERT INTO signup(username,password,contact_no,gender,email,address,user_type,status) VALUES(%s,%s,%s,%s,%s,%s,%s,'Pending')"
                cur.execute(sql, (username, password, contact, gender, email, address, usertype))
                con.commit()
                return render(request, 'Signup.html', {'data': 'Signup Process Completed'})
        finally:
            con.close()
    return render(request, 'Signup.html', {})

# Colonel Views
def SendColonelMessages(request):
    uname = request.session.get('uname')
    output = '<option value="" disabled selected>Select Receiver</option>'
    
    con = get_db_connection()
    try:
        with con.cursor() as cur:
            cur.execute("select username, user_type from signup where status='Approved' and username != %s", (uname,))
            rows = cur.fetchall()
            for row in rows:
                output += f'<option value="{row[0]}">{row[0]} ({row[1]})</option>'
    finally:
        con.close()
        
    context = {'receivers': output, 'sender': uname}
    return render(request, 'SendColonelMessages.html', context)

def SendColonelMessagesAction(request):
    if request.method == 'POST':
        receiver = request.POST.get('t1')
        sender = request.session.get('uname')
        message = request.POST.get('t4').upper()
        
        now = datetime.datetime.now()
        current_time = now.strftime("%Y-%m-%d %H:%M:%S")
        
        words = message.split()
        keys = []
        mykeys = ""
        
        for word in words:
            temp = ''.join((random.choice(string.ascii_uppercase) for x in range(len(word))))
            keys.append(temp)
            mykeys += temp + " "
            
        hybrid_cipher = ""
        mykeys = mykeys.strip()
        
        for i in range(len(words)):
            temp1 = vigenereEncryption(words[i], keys[i])
            temp2 = polybiusEncryption(temp1)
            hybrid_cipher += temp2 + " "
            
        con = get_db_connection()
        try:
            with con.cursor() as cur:
                # Get next ID (auto-increment is better but following logic)
                cur.execute("select count(*) FROM messages")
                count = cur.fetchone()[0] + 1
                
                sql = "INSERT INTO messages(message_id,sender_name,receiver_name,message,encrypt_keys,msg_time) VALUES(%s,%s,%s,%s,%s,%s)"
                cur.execute(sql, (count, sender, receiver, hybrid_cipher, mykeys, current_time))
                con.commit()
        finally:
            con.close()
            
        return render(request, 'ColonelScreen.html', {'data': f"Encrypted message sent to {receiver}"})
    return render(request, 'ColonelScreen.html', {})

def ViewColonelMessages(request):
    uname = request.session.get('uname')
    output = ""
    
    con = get_db_connection()
    try:
        with con.cursor() as cur:
            cur.execute("select * from messages where receiver_name=%s", (uname,))
            rows = cur.fetchall()
            for row in rows:
                output += f"<tr><td>{row[0]}</td><td>{row[1]}</td><td>{row[2]}</td><td>{row[3]}</td><td>{row[5]}</td>"
                output += f"<td><a href='ReadColonelMessageView?t1={row[0]}'>Click Here</a></td></tr>"
    finally:
        con.close()
        
    return render(request, 'ViewColonelMessages.html', {'data': output})

def ReadColonelMessageView(request):
    msg_id = request.GET.get('t1')
    email = request.session.get('email')
    
    con = get_db_connection()
    try:
        with con.cursor() as cur:
            cur.execute("select encrypt_keys from messages where message_id=%s", (msg_id,))
            row = cur.fetchone()
            if row:
                mykeys = row[0]
                sendEmail(mykeys, email)
    finally:
        con.close()
        
    return render(request, 'ReadColonelMessageView.html', {'msg_id': msg_id})

def ReadColonelMessage(request):
    if request.method == 'POST':
        msg_id = request.POST.get('t1')
        enter_key = request.POST.get('t2')
        
        con = get_db_connection()
        try:
            with con.cursor() as cur:
                cur.execute("select message, encrypt_keys from messages where message_id=%s", (msg_id,))
                row = cur.fetchone()
                if row:
                    decrypt_msg = row[0]
                    mykeys = row[1]
                    
                    if enter_key == mykeys:
                        keys = mykeys.split()
                        ciphers = decrypt_msg.split()
                        
                        output = ""
                        index = 0
                        # The logic in original code was a bit weird with index.
                        # ciphers is a list of encrypted words. keys is a list of keys.
                        # They should match 1-to-1.
                        
                        for i, key in enumerate(keys):
                            if i < len(ciphers):
                                temp1 = polybiusDecryption(ciphers[i])
                                temp2 = vigenereDecryption(temp1, key)
                                output += temp2 + " "
                                
                        return render(request, 'ColonelScreen.html', {'data': "Decrypted Message: " + output.lower()})
                    else:
                        return render(request, 'ColonelScreen.html', {'data': "Invalid key entered"})
        finally:
            con.close()
    return render(request, 'ColonelScreen.html', {})

# Brigadier Views
def SendBrigadierMessages(request):
    uname = request.session.get('uname')
    output = '<option value="" disabled selected>Select Receiver</option>'
    
    con = get_db_connection()
    try:
        with con.cursor() as cur:
            cur.execute("select username, user_type from signup where status='Approved' and username != %s", (uname,))
            rows = cur.fetchall()
            for row in rows:
                output += f'<option value="{row[0]}">{row[0]} ({row[1]})</option>'
    finally:
        con.close()
        
    context = {'receivers': output, 'sender': uname}
    return render(request, 'SendBrigadierMessages.html', context)

def SendBrigadierMessagesAction(request):
    # Same logic as Colonel
    # Removed early return reusing Colonel action as we want to control template rendering
    if request.method == 'POST':
        receiver = request.POST.get('t1')
        sender = request.session.get('uname')
        message = request.POST.get('t4').upper()
        
        now = datetime.datetime.now()
        current_time = now.strftime("%Y-%m-%d %H:%M:%S")
        
        words = message.split()
        keys = []
        mykeys = ""
        
        for word in words:
            temp = ''.join((random.choice(string.ascii_uppercase) for x in range(len(word))))
            keys.append(temp)
            mykeys += temp + " "
            
        hybrid_cipher = ""
        mykeys = mykeys.strip()
        
        for i in range(len(words)):
            temp1 = vigenereEncryption(words[i], keys[i])
            temp2 = polybiusEncryption(temp1)
            hybrid_cipher += temp2 + " "
            
        con = get_db_connection()
        try:
            with con.cursor() as cur:
                cur.execute("select count(*) FROM messages")
                count = cur.fetchone()[0] + 1
                
                sql = "INSERT INTO messages(message_id,sender_name,receiver_name,message,encrypt_keys,msg_time) VALUES(%s,%s,%s,%s,%s,%s)"
                cur.execute(sql, (count, sender, receiver, hybrid_cipher, mykeys, current_time))
                con.commit()
        finally:
            con.close()
            
        return render(request, 'BrigadierScreen.html', {'data': f"Encrypted message sent to {receiver}"})
    return render(request, 'BrigadierScreen.html', {})

def ViewBrigadierMessages(request):
    uname = request.session.get('uname')
    output = ""
    
    con = get_db_connection()
    try:
        with con.cursor() as cur:
            cur.execute("select * from messages where receiver_name=%s", (uname,))
            rows = cur.fetchall()
            for row in rows:
                output += f"<tr><td>{row[0]}</td><td>{row[1]}</td><td>{row[2]}</td><td>{row[3]}</td><td>{row[5]}</td>"
                output += f"<td><a href='ReadBrigadierMessageView?t1={row[0]}'>Click Here</a></td></tr>"
    finally:
        con.close()
        
    return render(request, 'ViewBrigadierMessages.html', {'data': output})

def ReadBrigadierMessageView(request):
    msg_id = request.GET.get('t1')
    email = request.session.get('email')
    
    con = get_db_connection()
    try:
        with con.cursor() as cur:
            cur.execute("select encrypt_keys from messages where message_id=%s", (msg_id,))
            row = cur.fetchone()
            if row:
                mykeys = row[0]
                sendEmail(mykeys, email)
    finally:
        con.close()
        
    return render(request, 'ReadBrigadierMessageView.html', {'msg_id': msg_id})

def ReadBrigadierMessage(request):
    if request.method == 'POST':
        msg_id = request.POST.get('t1')
        enter_key = request.POST.get('t2')
        
        con = get_db_connection()
        try:
            with con.cursor() as cur:
                cur.execute("select message, encrypt_keys from messages where message_id=%s", (msg_id,))
                row = cur.fetchone()
                if row:
                    decrypt_msg = row[0]
                    mykeys = row[1]
                    
                    if enter_key == mykeys:
                        keys = mykeys.split()
                        ciphers = decrypt_msg.split()
                        
                        output = ""
                        for i, key in enumerate(keys):
                            if i < len(ciphers):
                                temp1 = polybiusDecryption(ciphers[i])
                                temp2 = vigenereDecryption(temp1, key)
                                output += temp2 + " "
                                
                        return render(request, 'BrigadierScreen.html', {'data': "Decrypted Message: " + output.lower()})
                    else:
                        return render(request, 'BrigadierScreen.html', {'data': "Invalid key entered"})
        finally:
            con.close()
    return render(request, 'BrigadierScreen.html', {})

def ApproveColonel(request):
    output = ''
    con = get_db_connection()
    try:
        with con.cursor() as cur:
            cur.execute("select * from signup where user_type='Colonel' and status='Pending'")
            rows = cur.fetchall()
            for row in rows:
                output += f"<tr><td>{row[0]}</td><td>{row[1]}</td><td>{row[2]}</td><td>{row[3]}</td><td>{row[4]}</td><td>{row[5]}</td><td>{row[6]}</td><td>{row[7]}</td>"
                output += f"<td><a href='ApproveColonelUser?t1={row[0]}'>Click Here</a></td></tr>"
    finally:
        con.close()
    return render(request, 'ApproveColonel.html', {'data': output})

def ApproveColonelUser(request):
    user = request.GET.get('t1')
    con = get_db_connection()
    try:
        with con.cursor() as cur:
            cur.execute("update signup set status='Approved' where username=%s", (user,))
            con.commit()
    finally:
        con.close()
    return render(request, 'BrigadierScreen.html', {'data': "Colonel account approved"})

# Major Views
def SendMessages(request): # Major sending messages
    uname = request.session.get('uname')
    output = '<option value="" disabled selected>Select Receiver</option>'
    
    con = get_db_connection()
    try:
        with con.cursor() as cur:
            cur.execute("select username, user_type from signup where status='Approved' and username != %s", (uname,))
            rows = cur.fetchall()
            for row in rows:
                output += f'<option value="{row[0]}">{row[0]} ({row[1]})</option>'
    finally:
        con.close()
        
    context = {'receivers': output, 'sender': uname}
    return render(request, 'SendMessages.html', context)

def SendMessagesAction(request):
    if request.method == 'POST':
        receiver = request.POST.get('t1')
        sender = request.session.get('uname')
        message = request.POST.get('t4').upper()
        
        now = datetime.datetime.now()
        current_time = now.strftime("%Y-%m-%d %H:%M:%S")
        
        words = message.split()
        keys = []
        mykeys = ""
        
        for word in words:
            temp = ''.join((random.choice(string.ascii_uppercase) for x in range(len(word))))
            keys.append(temp)
            mykeys += temp + " "
            
        hybrid_cipher = ""
        mykeys = mykeys.strip()
        
        for i in range(len(words)):
            temp1 = vigenereEncryption(words[i], keys[i])
            temp2 = polybiusEncryption(temp1)
            hybrid_cipher += temp2 + " "
            
        con = get_db_connection()
        try:
            with con.cursor() as cur:
                cur.execute("select count(*) FROM messages")
                count = cur.fetchone()[0] + 1
                
                sql = "INSERT INTO messages(message_id,sender_name,receiver_name,message,encrypt_keys,msg_time) VALUES(%s,%s,%s,%s,%s,%s)"
                cur.execute(sql, (count, sender, receiver, hybrid_cipher, mykeys, current_time))
                con.commit()
        finally:
            con.close()
            
        return render(request, 'MajorScreen.html', {'data': f"Encrypted message sent to {receiver}"})
    return render(request, 'MajorScreen.html', {})

def ViewMajorMessages(request):
    uname = request.session.get('uname')
    output = ""
    
    con = get_db_connection()
    try:
        with con.cursor() as cur:
            cur.execute("select * from messages where receiver_name=%s", (uname,))
            rows = cur.fetchall()
            for row in rows:
                output += f"<tr><td>{row[0]}</td><td>{row[1]}</td><td>{row[2]}</td><td>{row[3]}</td><td>{row[5]}</td>"
                output += f"<td><a href='ReadMajorMessageView?t1={row[0]}'>Click Here</a></td></tr>"
    finally:
        con.close()
        
    return render(request, 'ViewMajorMessages.html', {'data': output})

def ReadMajorMessageView(request):
    msg_id = request.GET.get('t1')
    email = request.session.get('email')
    
    con = get_db_connection()
    try:
        with con.cursor() as cur:
            cur.execute("select encrypt_keys from messages where message_id=%s", (msg_id,))
            row = cur.fetchone()
            if row:
                mykeys = row[0]
                sendEmail(mykeys, email)
    finally:
        con.close()
        
    return render(request, 'ReadMajorMessageView.html', {'msg_id': msg_id})

def ReadMajorMessage(request):
    if request.method == 'POST':
        msg_id = request.POST.get('t1')
        enter_key = request.POST.get('t2')
        
        con = get_db_connection()
        try:
            with con.cursor() as cur:
                cur.execute("select message, encrypt_keys from messages where message_id=%s", (msg_id,))
                row = cur.fetchone()
                if row:
                    decrypt_msg = row[0]
                    mykeys = row[1]
                    
                    if enter_key == mykeys:
                        keys = mykeys.split()
                        ciphers = decrypt_msg.split()
                        
                        output = ""
                        for i, key in enumerate(keys):
                            if i < len(ciphers):
                                temp1 = polybiusDecryption(ciphers[i])
                                temp2 = vigenereDecryption(temp1, key)
                                output += temp2 + " "
                                
                        return render(request, 'MajorScreen.html', {'data': "Decrypted Message: " + output.lower()})
                    else:
                        return render(request, 'MajorScreen.html', {'data': "Given key is not valid"})
        finally:
            con.close()
    return render(request, 'MajorScreen.html', {})

def ApproveBrigadier(request):
    output = ''
    con = get_db_connection()
    try:
        with con.cursor() as cur:
            cur.execute("select * from signup where user_type='Brigadier' and status='Pending'")
            rows = cur.fetchall()
            for row in rows:
                output += f"<tr><td>{row[0]}</td><td>{row[1]}</td><td>{row[2]}</td><td>{row[3]}</td><td>{row[4]}</td><td>{row[5]}</td><td>{row[6]}</td><td>{row[7]}</td>"
                output += f"<td><a href='ApproveBrigadierUser?t1={row[0]}'>Click Here</a></td></tr>"
    finally:
        con.close()
    return render(request, 'ApproveBrigadier.html', {'data': output})

def ApproveBrigadierUser(request):
    user = request.GET.get('t1')
    con = get_db_connection()
    try:
        with con.cursor() as cur:
            cur.execute("update signup set status='Approved' where username=%s", (user,))
            con.commit()
    finally:
        con.close()
    return render(request, 'MajorScreen.html', {'data': "Brigadier account approved"})

def ApproveMajor(request):
    output = ''
    con = get_db_connection()
    try:
        with con.cursor() as cur:
            cur.execute("select * from signup where user_type='Major General' and status='Pending'")
            rows = cur.fetchall()
            for row in rows:
                output += f"<tr><td>{row[0]}</td><td>{row[1]}</td><td>{row[2]}</td><td>{row[3]}</td><td>{row[4]}</td><td>{row[5]}</td><td>{row[6]}</td><td>{row[7]}</td>"
                output += f"<td><a href='ApproveMajorUser?t1={row[0]}'>Click Here</a></td></tr>"
    finally:
        con.close()
    return render(request, 'ApproveMajor.html', {'data': output})

def ApproveMajorUser(request):
    user = request.GET.get('t1')
    con = get_db_connection()
    try:
        with con.cursor() as cur:
            cur.execute("update signup set status='Approved' where username=%s", (user,))
            con.commit()
    finally:
        con.close()
    return render(request, 'AdminScreen.html', {'data': "Major General account approved"})
