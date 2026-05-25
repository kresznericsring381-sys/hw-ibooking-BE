import jwt
import datetime
from config import JWT_SECRET_KEY

def generate_token(student_id):
    """生成JWT token"""
    payload = {
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24),
        'iat': datetime.datetime.utcnow(),
        'student_id': student_id
    }
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm='HS256')
    return token

def verify_token(token):
    """校验token，返回student_id"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=['HS256'])
        return payload.get('student_id')
    except:
        return None