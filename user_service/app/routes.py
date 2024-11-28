from flask import Blueprint, request, jsonify
from app.services import create_user, login_user, update_user

user_bp = Blueprint('user', __name__)

# Đăng ký người dùng
@user_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")
    phone = data.get("phone")
    
    # Tạo người dùng mới
    user_id = create_user(name, email, password, phone)
    return jsonify({"message": "User created", "user_id": user_id}), 201

# Đăng nhập người dùng
@user_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")
    
    user = login_user(email, password)
    if user:
        return jsonify({"message": "Login successful", "user": user}), 200
    else:
        return jsonify({"message": "Invalid credentials"}), 401

# Cập nhật thông tin người dùng
@user_bp.route('/update/<user_id>', methods=['PUT'])
def update(user_id):
    data = request.get_json()
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")
    phone = data.get("phone")
    
    success = update_user(user_id, name, email, password, phone)
    if success:
        return jsonify({"message": "User updated successfully"}), 200
    else:
        return jsonify({"message": "User not found or no changes made"}), 404
