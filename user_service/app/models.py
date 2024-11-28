from bson.objectid import ObjectId
import datetime
from database import get_db

db = get_db()

class UserModel:
    collection = db["users"]

    @staticmethod
    def create_user(name, email, password, phone):
        user = {
            "_id": ObjectId(),
            "name": name,
            "email": email,
            "password": password,
            "phone": phone,
            "create_date": datetime.datetime.now(),
            "update_date": None
        }
        result = UserModel.collection.insert_one(user)
        return str(result.inserted_id)

    @staticmethod
    def get_user_by_email(email):
        return UserModel.collection.find_one({"email": email})

    @staticmethod
    def get_user_by_id(user_id):
        return UserModel.collection.find_one({"_id": ObjectId(user_id)})
