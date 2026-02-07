import bcrypt
import pymysql
from django.conf import settings
from decouple import config
import datetime

def get_db_connection():
    """Get database connection"""
    return pymysql.connect(
        host=settings.DATABASES['default']['HOST'],
        port=int(settings.DATABASES['default']['PORT']),
        user=settings.DATABASES['default']['USER'],
        password=settings.DATABASES['default']['PASSWORD'],
        database=settings.DATABASES['default']['NAME'],
        charset='utf8'
    )

def hash_password(password):
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password, hashed):
    """Verify a password against a hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def log_audit(username, action, details, ip_address='127.0.0.1'):
    """Log an audit event to the database"""
    con = get_db_connection()
    try:
        with con.cursor() as cur:
            sql = "INSERT INTO audit_log(username, action, details, ip_address) VALUES(%s, %s, %s, %s)"
            cur.execute(sql, (username, action, details, ip_address))
            con.commit()
    except Exception as e:
        print(f"Audit log error: {e}")
    finally:
        con.close()

def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
    return ip

def login_required_check(request):
    """Check if user is logged in"""
    return request.session.get('uname') is not None

def create_notification(username, notification_type, message):
    """Create a notification for a user"""
    con = get_db_connection()
    try:
        with con.cursor() as cur:
            sql = "INSERT INTO notifications(username, notification_type, message) VALUES(%s, %s, %s)"
            cur.execute(sql, (username, notification_type, message))
            con.commit()
    except Exception as e:
        print(f"Notification creation error: {e}")
    finally:
        con.close()

def get_admin_credentials():
    """Get admin credentials from environment"""
    return {
        'username': config('ADMIN_USERNAME', default='admin'),
        'password': config('ADMIN_PASSWORD', default='admin')
    }

def get_smtp_credentials():
    """Get SMTP credentials from environment"""
    return {
        'email': config('SMTP_EMAIL', default='evotingotp4@gmail.com'),
        'password': config('SMTP_PASSWORD', default='xowpojqyiygprhgr')
    }
