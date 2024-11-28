from werkzeug.security import generate_password_hash, check_password_hash
import datetime


def hash_password(password):
    return generate_password_hash(password)


def verify_password(stored_password, input_password):
    return check_password_hash(stored_password, input_password)


def get_current_time():
    return datetime.datetime.now()
