from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
import pymysql
from .crypt import (vigenereEncryption, polybiusEncryption, polybiusDecryption, 
                    vigenereDecryption, hybrid_encrypt, hybrid_decrypt)
from .utils import (hash_password, verify_password, log_audit, get_client_ip, 
                    login_required_check, create_notification, get_admin_credentials, 
                    get_smtp_credentials, get_db_connection)
from .steganography import hide_message_in_image, extract_message_from_image
import datetime
import random
import string
import smtplib
from email.message import EmailMessage
from django.conf import settings
from functools import wraps
import os
import base64

from functools import wraps
import os
import base64

# Login required decorator
def login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not login_required_check(request):
            return redirect('UserLogin')
        return view_func(request, *args, **kwargs)
    return wrapper

def sendEmail(decrypt_key, recipient_email, aes_key=None):
    """Send decryption keys to recipient via email"""
    # PRINT KEY TO CONSOLE FOR TESTING
    print("="*50)
    print(f"DECRYPTION KEY FOR {recipient_email}: {decrypt_key}")
    if aes_key:
        print(f"AES KEY: {aes_key}")
    print("="*50)

    smtp_creds = get_smtp_credentials()
    
    email_content = f"Vigenere Key to decrypt message: {decrypt_key}"
    if aes_key:
        email_content += f"\n\nAES-256 Key: {aes_key}"
    
    msg = EmailMessage()
    msg.set_content(email_content)
    msg['Subject'] = 'Message From Military Application'
    msg['From'] = smtp_creds['email']
    msg['To'] = recipient_email

    try:
        s = smtplib.SMTP('smtp.gmail.com', 587)
        s.starttls()
        s.login(smtp_creds['email'], smtp_creds['password'])
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
        
        admin_creds = get_admin_credentials()
        
        if username == admin_creds['username'] and password == admin_creds['password']:
            request.session['uname'] = username
            request.session['utype'] = 'Admin'
            
            # Log successful admin login
            log_audit(username, 'admin_login', 'Admin logged in successfully', get_client_ip(request))
            
            context = {'data': 'welcome ' + username}
            return render(request, 'AdminScreen.html', context)
        else:
            # Log failed admin login
            log_audit(username or 'unknown', 'failed_admin_login', 'Failed admin login attempt', get_client_ip(request))
            
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
                
                if row and verify_password(password, row[1]):
                    request.session['uname'] = username
                    request.session['email'] = row[3]
                    request.session['utype'] = row[2]
                    
                    db_usertype = row[2]
                    
                    # Log successful login
                    log_audit(username, 'user_login', f'User logged in as {db_usertype}', get_client_ip(request))
                    
                    if usertype == db_usertype:
                        if usertype == 'Major General':
                            return render(request, 'MajorScreen.html', {'data': f'welcome {username} You Logged in as {usertype}'})
                        elif usertype == 'Brigadier':
                            return render(request, 'BrigadierScreen.html', {'data': f'welcome {username} You Logged in as {usertype}'})
                        elif usertype == 'Colonel':
                            return render(request, 'ColonelScreen.html', {'data': f'welcome {username} You Logged in as {usertype}'})
                else:
                    # Log failed login
                    log_audit(username or 'unknown', 'failed_login', f'Failed login attempt for user type {usertype}', get_client_ip(request))
                    
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
                
                # Hash password before storing
                hashed_password = hash_password(password)
                
                sql = "INSERT INTO signup(username,password,contact_no,gender,email,address,user_type,status) VALUES(%s,%s,%s,%s,%s,%s,%s,'Pending')"
                cur.execute(sql, (username, hashed_password, contact, gender, email, address, usertype))
                con.commit()
                
                # Log signup
                log_audit(username, 'signup', f'New user signup as {usertype}', get_client_ip(request))
                
                return render(request, 'Signup.html', {'data': 'Signup Process Completed'})
        finally:
            con.close()
    return render(request, 'Signup.html', {})

def Logout(request):
    """Logout view to clear session"""
    username = request.session.get('uname', 'unknown')
    
    # Log logout
    log_audit(username, 'logout', 'User logged out', get_client_ip(request))
    
    # Clear session
    request.session.flush()
    
    return redirect('index')

# Colonel Views
@login_required
def SendColonelMessages(request):
    uname = request.session.get('uname')
    receivers = []
    
    con = get_db_connection()
    try:
        with con.cursor() as cur:
            cur.execute("select username, user_type from signup where status='Approved' and username != %s", (uname,))
            rows = cur.fetchall()
            for row in rows:
                receivers.append({
                    'username': row[0],
                    'usertype': row[1]
                })
    finally:
        con.close()
        
    context = {'receivers': receivers, 'sender': uname}
    return render(request, 'SendColonelMessages.html', context)

@login_required
def SendColonelMessagesAction(request):
    if request.method == 'POST':
        receiver = request.POST.get('t1')
        sender = request.session.get('uname')
        message = request.POST.get('t4').upper()
        priority = request.POST.get('t5', 'ROUTINE')
        
        now = datetime.datetime.now()
        current_time = now.strftime("%Y-%m-%d %H:%M:%S")
        
        # Generate Vigenere key for entire message
        vigenere_key = ''.join((random.choice(string.ascii_uppercase) for x in range(len(message))))
        
        # Use hybrid encryption
        encrypted_message, aes_key = hybrid_encrypt(message, vigenere_key)
        
        con = get_db_connection()
        try:
            with con.cursor() as cur:
                # Get receiver email for sending keys
                cur.execute("select email FROM signup where username=%s", (receiver,))
                receiver_row = cur.fetchone()
                receiver_email = receiver_row[0] if receiver_row else None
                
                # Get next ID
                cur.execute("select count(*) FROM messages")
                count = cur.fetchone()[0] + 1
                
                sql = "INSERT INTO messages(message_id,sender_name,receiver_name,message,encrypt_keys,aes_key,msg_time,priority,is_read) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)"
                cur.execute(sql, (count, sender, receiver, encrypted_message, vigenere_key, aes_key, current_time, priority, False))
                con.commit()
                
                # Send keys via email
                if receiver_email:
                    sendEmail(vigenere_key, receiver_email, aes_key)
                
                # Log audit
                log_audit(sender, 'message_sent', f'Sent {priority} message to {receiver}', get_client_ip(request))
        finally:
            con.close()
            
        return render(request, 'ColonelScreen.html', {'data': f"Encrypted message sent to {receiver}"})
    return render(request, 'ColonelScreen.html', {})

@login_required
def ViewColonelMessages(request):
    uname = request.session.get('uname')
    messages = []
    
    con = get_db_connection()
    try:
        with con.cursor() as cur:
            cur.execute("select message_id, sender_name, receiver_name, message, encrypt_keys, msg_time, priority from messages where receiver_name=%s", (uname,))
            rows = cur.fetchall()
            for row in rows:
                messages.append({
                    'id': row[0],
                    'sender': row[1],
                    'receiver': row[2],
                    'message': row[3],
                    'time': row[5],
                    'priority': row[6]
                })
    finally:
        con.close()
        
    return render(request, 'ViewColonelMessages.html', {'messages': messages})

@login_required
def ReadColonelMessageView(request):
    msg_id = request.GET.get('t1')
    email = request.session.get('email')
    
    con = get_db_connection()
    try:
        with con.cursor() as cur:
            cur.execute("select encrypt_keys, aes_key from messages where message_id=%s", (msg_id,))
            row = cur.fetchone()
            if row:
                vigenere_key = row[0]
                aes_key = row[1]
                sendEmail(vigenere_key, email, aes_key)
    finally:
        con.close()
        
    return render(request, 'ReadColonelMessageView.html', {'msg_id': msg_id})

@login_required
def ReadColonelMessage(request):
    if request.method == 'POST':
        msg_id = request.POST.get('t1')
        vigenere_key = request.POST.get('t2')
        aes_key = request.POST.get('t3')
        username = request.session.get('uname')
        
        con = get_db_connection()
        try:
            with con.cursor() as cur:
                cur.execute("select message, encrypt_keys, aes_key from messages where message_id=%s", (msg_id,))
                row = cur.fetchone()
                if row:
                    encrypted_message = row[0]
                    stored_vigenere_key = row[1]
                    stored_aes_key = row[2]
                    
                    if vigenere_key == stored_vigenere_key and aes_key == stored_aes_key:
                        # Use hybrid decryption
                        decrypted_message = hybrid_decrypt(encrypted_message, vigenere_key, aes_key)
                        
                        # Mark message as read
                        cur.execute("UPDATE messages SET is_read=TRUE WHERE message_id=%s", (msg_id,))
                        con.commit()
                        
                        # Log audit
                        log_audit(username, 'message_decrypted', f'Decrypted message {msg_id}', get_client_ip(request))
                        
                        return render(request, 'ColonelScreen.html', {'data': "Decrypted Message: " + decrypted_message.lower()})
                    else:
                        return render(request, 'ColonelScreen.html', {'data': "Invalid key entered"})
        finally:
            con.close()
    return render(request, 'ColonelScreen.html', {})

# Brigadier Views
@login_required
def SendBrigadierMessages(request):
    uname = request.session.get('uname')
    receivers = []
    
    con = get_db_connection()
    try:
        with con.cursor() as cur:
            cur.execute("select username, user_type from signup where status='Approved' and username != %s", (uname,))
            rows = cur.fetchall()
            for row in rows:
                receivers.append({
                    'username': row[0],
                    'usertype': row[1]
                })
    finally:
        con.close()
        
    context = {'receivers': receivers, 'sender': uname}
    return render(request, 'SendBrigadierMessages.html', context)

@login_required
def SendBrigadierMessagesAction(request):
    if request.method == 'POST':
        receiver = request.POST.get('t1')
        sender = request.session.get('uname')
        message = request.POST.get('t4').upper()
        priority = request.POST.get('t5', 'ROUTINE')
        
        now = datetime.datetime.now()
        current_time = now.strftime("%Y-%m-%d %H:%M:%S")
        
        # Generate Vigenere key for entire message
        vigenere_key = ''.join((random.choice(string.ascii_uppercase) for x in range(len(message))))
        
        # Use hybrid encryption
        encrypted_message, aes_key = hybrid_encrypt(message, vigenere_key)
        
        con = get_db_connection()
        try:
            with con.cursor() as cur:
                # Get receiver email for sending keys
                cur.execute("select email FROM signup where username=%s", (receiver,))
                receiver_row = cur.fetchone()
                receiver_email = receiver_row[0] if receiver_row else None
                
                # Get next ID
                cur.execute("select count(*) FROM messages")
                count = cur.fetchone()[0] + 1
                
                sql = "INSERT INTO messages(message_id,sender_name,receiver_name,message,encrypt_keys,aes_key,msg_time,priority,is_read) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)"
                cur.execute(sql, (count, sender, receiver, encrypted_message, vigenere_key, aes_key, current_time, priority, False))
                con.commit()
                
                # Send keys via email
                if receiver_email:
                    sendEmail(vigenere_key, receiver_email, aes_key)
                
                # Log audit
                log_audit(sender, 'message_sent', f'Sent {priority} message to {receiver}', get_client_ip(request))
        finally:
            con.close()
            
        return render(request, 'BrigadierScreen.html', {'data': f"Encrypted message sent to {receiver}"})
    return render(request, 'BrigadierScreen.html', {})

@login_required
def ViewBrigadierMessages(request):
    uname = request.session.get('uname')
    messages = []
    
    con = get_db_connection()
    try:
        with con.cursor() as cur:
            cur.execute("select message_id, sender_name, receiver_name, message, encrypt_keys, msg_time, priority from messages where receiver_name=%s", (uname,))
            rows = cur.fetchall()
            for row in rows:
                messages.append({
                    'id': row[0],
                    'sender': row[1],
                    'receiver': row[2],
                    'message': row[3],
                    'time': row[5],
                    'priority': row[6]
                })
    finally:
        con.close()
        
    return render(request, 'ViewBrigadierMessages.html', {'messages': messages})

@login_required
def ReadBrigadierMessageView(request):
    msg_id = request.GET.get('t1')
    email = request.session.get('email')
    
    con = get_db_connection()
    try:
        with con.cursor() as cur:
            cur.execute("select encrypt_keys, aes_key from messages where message_id=%s", (msg_id,))
            row = cur.fetchone()
            if row:
                vigenere_key = row[0]
                aes_key = row[1]
                sendEmail(vigenere_key, email, aes_key)
    finally:
        con.close()
        
    return render(request, 'ReadBrigadierMessageView.html', {'msg_id': msg_id})

@login_required
def ReadBrigadierMessage(request):
    if request.method == 'POST':
        msg_id = request.POST.get('t1')
        vigenere_key = request.POST.get('t2')
        aes_key = request.POST.get('t3')
        username = request.session.get('uname')
        
        con = get_db_connection()
        try:
            with con.cursor() as cur:
                cur.execute("select message, encrypt_keys, aes_key from messages where message_id=%s", (msg_id,))
                row = cur.fetchone()
                if row:
                    encrypted_message = row[0]
                    stored_vigenere_key = row[1]
                    stored_aes_key = row[2]
                    
                    if vigenere_key == stored_vigenere_key and aes_key == stored_aes_key:
                        # Use hybrid decryption
                        decrypted_message = hybrid_decrypt(encrypted_message, vigenere_key, aes_key)
                        
                        # Mark message as read
                        cur.execute("UPDATE messages SET is_read=TRUE WHERE message_id=%s", (msg_id,))
                        con.commit()
                        
                        # Log audit
                        log_audit(username, 'message_decrypted', f'Decrypted message {msg_id}', get_client_ip(request))
                        
                        return render(request, 'BrigadierScreen.html', {'data': "Decrypted Message: " + decrypted_message.lower()})
                    else:
                        return render(request, 'BrigadierScreen.html', {'data': "Invalid key entered"})
        finally:
            con.close()
    return render(request, 'BrigadierScreen.html', {})

@login_required
def ApproveColonel(request):
    users = []
    con = get_db_connection()
    try:
        with con.cursor() as cur:
            cur.execute("select username, password, contact_no, gender, email, address, user_type, status from signup where user_type='Colonel' and status='Pending'")
            rows = cur.fetchall()
            for row in rows:
                users.append({
                    'username': row[0],
                    'password': row[1],
                    'contact': row[2],
                    'gender': row[3],
                    'email': row[4],
                    'address': row[5],
                    'usertype': row[6],
                    'status': row[7]
                })
    finally:
        con.close()
    return render(request, 'ApproveColonel.html', {'users': users})

@login_required
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
@login_required
def SendMessages(request): # Major sending messages
    uname = request.session.get('uname')
    receivers = []
    
    con = get_db_connection()
    try:
        with con.cursor() as cur:
            cur.execute("select username, user_type from signup where status='Approved' and username != %s", (uname,))
            rows = cur.fetchall()
            for row in rows:
                receivers.append({
                    'username': row[0],
                    'usertype': row[1]
                })
    finally:
        con.close()
        
    context = {'receivers': receivers, 'sender': uname}
    return render(request, 'SendMessages.html', context)

@login_required
def SendMessagesAction(request):
    if request.method == 'POST':
        receiver = request.POST.get('t1')
        sender = request.session.get('uname')
        message = request.POST.get('t4').upper()
        priority = request.POST.get('t5', 'ROUTINE')
        
        now = datetime.datetime.now()
        current_time = now.strftime("%Y-%m-%d %H:%M:%S")
        
        # Generate Vigenere key for entire message
        vigenere_key = ''.join((random.choice(string.ascii_uppercase) for x in range(len(message))))
        
        # Use hybrid encryption
        encrypted_message, aes_key = hybrid_encrypt(message, vigenere_key)
        
        con = get_db_connection()
        try:
            with con.cursor() as cur:
                # Get receiver email for sending keys
                cur.execute("select email FROM signup where username=%s", (receiver,))
                receiver_row = cur.fetchone()
                receiver_email = receiver_row[0] if receiver_row else None
                
                # Get next ID
                cur.execute("select count(*) FROM messages")
                count = cur.fetchone()[0] + 1
                
                sql = "INSERT INTO messages(message_id,sender_name,receiver_name,message,encrypt_keys,aes_key,msg_time,priority,is_read) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)"
                cur.execute(sql, (count, sender, receiver, encrypted_message, vigenere_key, aes_key, current_time, priority, False))
                con.commit()
                
                # Send keys via email
                if receiver_email:
                    sendEmail(vigenere_key, receiver_email, aes_key)
                
                # Log audit
                log_audit(sender, 'message_sent', f'Sent {priority} message to {receiver}', get_client_ip(request))
        finally:
            con.close()
            
        return render(request, 'MajorScreen.html', {'data': f"Encrypted message sent to {receiver}"})
    return render(request, 'MajorScreen.html', {})

@login_required
def ViewMajorMessages(request):
    uname = request.session.get('uname')
    messages = []
    
    con = get_db_connection()
    try:
        with con.cursor() as cur:
            cur.execute("select message_id, sender_name, receiver_name, message, encrypt_keys, msg_time, priority from messages where receiver_name=%s", (uname,))
            rows = cur.fetchall()
            for row in rows:
                messages.append({
                    'id': row[0],
                    'sender': row[1],
                    'receiver': row[2],
                    'message': row[3],
                    'time': row[5],
                    'priority': row[6]
                })
    finally:
        con.close()
        
    return render(request, 'ViewMajorMessages.html', {'messages': messages})

@login_required
def ReadMajorMessageView(request):
    msg_id = request.GET.get('t1')
    email = request.session.get('email')
    
    con = get_db_connection()
    try:
        with con.cursor() as cur:
            cur.execute("select encrypt_keys, aes_key from messages where message_id=%s", (msg_id,))
            row = cur.fetchone()
            if row:
                vigenere_key = row[0]
                aes_key = row[1]
                sendEmail(vigenere_key, email, aes_key)
    finally:
        con.close()
        
    return render(request, 'ReadMajorMessageView.html', {'msg_id': msg_id})

@login_required
def ReadMajorMessage(request):
    if request.method == 'POST':
        msg_id = request.POST.get('t1')
        vigenere_key = request.POST.get('t2')
        aes_key = request.POST.get('t3')
        username = request.session.get('uname')
        
        con = get_db_connection()
        try:
            with con.cursor() as cur:
                cur.execute("select message, encrypt_keys, aes_key from messages where message_id=%s", (msg_id,))
                row = cur.fetchone()
                if row:
                    encrypted_message = row[0]
                    stored_vigenere_key = row[1]
                    stored_aes_key = row[2]
                    
                    if vigenere_key == stored_vigenere_key and aes_key == stored_aes_key:
                        # Use hybrid decryption
                        decrypted_message = hybrid_decrypt(encrypted_message, vigenere_key, aes_key)
                        
                        # Mark message as read
                        cur.execute("UPDATE messages SET is_read=TRUE WHERE message_id=%s", (msg_id,))
                        con.commit()
                        
                        # Log audit
                        log_audit(username, 'message_decrypted', f'Decrypted message {msg_id}', get_client_ip(request))
                        
                        return render(request, 'MajorScreen.html', {'data': "Decrypted Message: " + decrypted_message.lower()})
                    else:
                        return render(request, 'MajorScreen.html', {'data': "Given key is not valid"})
        finally:
            con.close()
    return render(request, 'MajorScreen.html', {})

@login_required
def ApproveBrigadier(request):
    users = []
    con = get_db_connection()
    try:
        with con.cursor() as cur:
            cur.execute("select username, password, contact_no, gender, email, address, user_type, status from signup where user_type='Brigadier' and status='Pending'")
            rows = cur.fetchall()
            for row in rows:
                users.append({
                    'username': row[0],
                    'password': row[1],
                    'contact': row[2],
                    'gender': row[3],
                    'email': row[4],
                    'address': row[5],
                    'usertype': row[6],
                    'status': row[7]
                })
    finally:
        con.close()
    return render(request, 'ApproveBrigadier.html', {'users': users})

@login_required
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

@login_required
def ApproveMajor(request):
    users = []
    con = get_db_connection()
    try:
        with con.cursor() as cur:
            cur.execute("select username, password, contact_no, gender, email, address, user_type, status from signup where user_type='Major General' and status='Pending'")
            rows = cur.fetchall()
            for row in rows:
                users.append({
                    'username': row[0],
                    'password': row[1],
                    'contact': row[2],
                    'gender': row[3],
                    'email': row[4],
                    'address': row[5],
                    'usertype': row[6],
                    'status': row[7]
                })
    finally:
        con.close()
    return render(request, 'ApproveMajor.html', {'users': users})

@login_required
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
