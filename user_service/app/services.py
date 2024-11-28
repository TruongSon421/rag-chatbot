from app.models import UserModel
import datetime

# Tạo người dùng
def create_user(name, email, password, phone):
    user = UserModel.get_user_by_email(email)
    if user:
        return {"message": "User already exists"}
    user_id = UserModel.create_user(name, email, password, phone)
    return {"user_id": user_id}

# Đăng nhập người dùng
def login_user(email, password):
    user = UserModel.get_user_by_email(email)
    if user and UserModel.verify_password(user['password'], password):
        return {"name": user['name'], "email": user['email'], "phone": user['phone'], "role": user.get('role', 'user')}
    return None

# Cập nhật thông tin người dùng
def update_user(user_id, name=None, email=None, password=None, phone=None):
        update_data = {}
        
        if name:
            update_data["name"] = name
        if email:
            update_data["email"] = email
        if password:
            update_data["password"] = password
        if phone:
            update_data["phone"] = phone

        if update_data:
            update_data["update_date"] = datetime.datetime.now()  # Gán thời gian hiện tại cho update_date
        
        result = UserModel.collection.update_one(
            {"_id": user_id}, 
            {"$set": update_data}
        )
        return result.modified_count 
