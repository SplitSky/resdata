from __future__ import annotations
from typing import Mapping, Any
# Crypto
import hashlib as h
import random
from secrets import compare_digest
from datetime import datetime, timedelta
# Server communications
from fastapi import HTTPException, status
from jose import jwt, JWTError
from pymongo.mongo_client import MongoClient
# Internal
from variables import secret_key, algorithm


# User verification object
class User_Auth:
    def __init__(self, username_in: str, password_in: str, db_client_in: MongoClient) -> None:
        self.username = username_in
        self.password = password_in
        self.client = db_client_in

    def check_password_valid(self) -> bool:
        # lookup the database for user
        auth = self.client["Authentication"]
        users = auth["Users"]
        result = users.find_one({"username": self.username})
        # see if user exists
        if result is None:
            return False
        # if yes verify password
        else:
            pass_in_db = result.get("hash")  # returns the hashed password from database
            # hashes the password in and compares
            return pass_in_db == self.return_final_hash(None)

    def return_final_hash(self, salt_in: int = None) -> str:
        if salt_in is not None:
            # user provided salt
            password = str(salt_in) + self.password
            temp = h.shake_256()
            temp.update(password.encode('utf8'))
            return temp.hexdigest(64)  # return a string
        else:
            # fetch the salt from the database
            auth = self.client["Authentication"]
            users = auth["Users"]
            result = users.find_one({"username": self.username})
            if result is not None:
                salt = result.get("salt")
                temp = h.shake_256()
                password = salt + self.password
                temp.update(password.encode('utf8'))
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User doesn't exist"
                )
            return temp.hexdigest(64)  # return a string from bytes

    def create_access_token(self, expires_delta: timedelta = None) -> str:
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=30)
        to_encode = {'sub': self.username, 'expiry': str(expire)}
        encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=algorithm)

        authentication_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="The user doesn't exist. Can't generate token"
        )
        # update the token in the database
        auth = self.client["Authentication"]
        users = auth["Users"]

        temp_list = [{'$set': {'disabled': False}}, {'$set': {'token': encoded_jwt}}, {'$set': {"expiry": expire}}]
        # update the user database fields
        for change in temp_list:
            result = users.find_one_and_update({"username": self.username}, change)
            if result is None:
                raise authentication_exception
        return encoded_jwt

    def check_username_exists(self) -> bool:
        auth = self.client["Authentication"]
        users = auth["Users"]
        result = users.find_one({"username": self.username})
        return result is not None

    def activate_user(self) -> bool:
        auth = self.client["Authentication"]
        users = auth["Users"]
        result = users.find_one_and_update({"username": self.username}, {'$set': {"disabled": False}})
        return result is not None

    def deactivate_user(self) -> bool:
        auth = self.client["Authentication"]
        users = auth["Users"]
        result = users.find_one_and_update({"username": self.username}, {'$set': {"disabled": True}})
        return result is not None

    def add_user(self, full_name: str, email: str) -> bool:
        auth = self.client["Authentication"]
        users = auth["Users"]
        salt_init = random.SystemRandom().getrandbits(256)

        # check user exists
        if not self.check_username_exists():
            user_dict = {
                "username": self.username,
                "hash": self.return_final_hash(salt_init),
                "full_name": full_name,
                "email": email,
                "disabled": True,
                "salt": str(salt_init),
                "expiry": str(datetime.utcnow()),
                "token": ""
            }
            users.insert_one(user_dict)
            return True
        else:
            return False

    def fetch_token(self) -> str:
        # fetches the token associated with the user
        auth = self.client["Authentication"]
        users = auth["Users"]
        result = users.find_one({"username": self.username})
        return result.get("token")

    def fetch_user(self) -> Mapping[str, Any]:
        auth = self.client["Authentication"]
        users = auth["Users"]
        result = users.find_one({"username": self.username})
        return result

    def authenticate_token(self) -> bool:
        # self.password contains the token value
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )
        try:
            payload = jwt.decode(self.password, secret_key, algorithms=[algorithm])
            # payload contains the username and expiry date of the token as a string
            username = payload.get("sub")
            if username is None:
                raise credentials_exception
            # username recovered successfully
        except JWTError:
            self.deactivate_user()
            raise credentials_exception

        if username == self.username:
            # username matches the token
            # check the token matches the one in the database
            fetched_user = self.fetch_user()  # fetches the user data
            if fetched_user is None:
                raise credentials_exception

            if compare_digest(self.password, fetched_user.get("token")):  # compares tokens
                # successfully compared tokens
                # check the token is valid
                # check the token expiry date matches the one in the database
                now = datetime.utcnow()
                # check the token is not expired
                if now < fetched_user.get("expiry"):
                    # user successfully validated
                    # activate user
                    self.activate_user()
                    return True
        # deactivate user
        self.deactivate_user()
        raise credentials_exception
