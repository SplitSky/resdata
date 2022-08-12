from typing import Union
from datetime import datetime, timedelta
from fastapi import HTTPException, status
from jose import JWTError, jwt
import hashlib as h
from pydantic.typing import NoneType
from variables import secret_key, algorithm, access_token_expire
import random
from secrets import compare_digest

# declare constants for the

SECRET_KEY = secret_key
ALGORITHM = algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = access_token_expire


### User verification object
class User_Auth(object):
    def __init__(self, username_in, password_in, db_client_in):
        self.username = username_in
        self.password = password_in
        self.client = db_client_in

    def check_password_valid(self):
        # lookup the database for user
        auth = self.client["Authentication"]
        users = auth["Users"]
        result = users.find_one({"username": self.username})
        # see if user exists
        if result == None:
            return False
        # if yes verify password
        else:
            pass_in_db = result.get("hash")  # returns the hashed password from database
            # hashes the password in and compares
            if pass_in_db == self.return_final_hash(None):
                return result
            else:
                return False

    def return_final_hash(self, salt_in):
        if salt_in != None:
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
            if result != None:
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

    def create_access_token(self, expires_delta: Union[timedelta, NoneType] = None):

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=30)
        to_encode = {'sub': self.username, 'expiry': str(expire)}
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
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
            if result == None:
                raise authentication_exception
        return encoded_jwt

    def check_username_exists(self):
        auth = self.client["Authentication"]
        users = auth["Users"]
        result = users.find_one({"username": self.username})
        if result == None:
            return False
        else:
            return True

    def activate_user(self):
        auth = self.client["Authentication"]
        users = auth["Users"]
        result = users.find_one_and_update({"username": self.username}, {'$set': {"disabled": False}})
        if result == None:  # failed to find user
            return False
        else:
            return True

    def deactive_user(self):
        auth = self.client["Authentication"]
        users = auth["Users"]
        result = users.find_one_and_update({"username": self.username}, {'$set': {"disabled": True}})
        if result == None:
            return False
        else:
            return True

    def add_user(self, full_name, email):
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
                "expiry": datetime.utcnow(),
                "token": ""
            }
            users.insert_one(user_dict)
            return True
        else:
            return False  # returns boolean to raise exception in api call
            # raise HTTPException(
            #    status_code=status.HTTP_302_FOUND,
            #    detail = "User already exists"
            # )

    def fetch_token(self):
        # fetches the token associated with the user
        auth = self.client["Authentication"]
        users = auth["Users"]
        result = users.find_one({"username": self.username})
        return result.get("token")

    def fetch_user(self):
        auth = self.client["Authentication"]
        users = auth["Users"]
        result = users.find_one({"username": self.username})
        return result

    def authenticate_token(self):
        # self.password contains the token value
        # decode token
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )
        try:
            payload = jwt.decode(self.password, SECRET_KEY, algorithms=[ALGORITHM])
            # payload contains the username and expiry date of the token as a string
            username = payload.get("sub")
            if username is None:
                raise credentials_exception
            # username recovered successfully
        except JWTError:
            self.deactive_user()
            raise credentials_exception

        if username == self.username:
            # user name matches the token
            # check the token matches the one in the database
            fetched_user = self.fetch_user()  # fetches the user data
            if fetched_user == None:
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
        self.deactive_user()
        raise credentials_exception

    def update_disable_status(self):
        # fetch user and compare the expiry date to now.
        now = datetime.utcnow()
        user = self.fetch_user()
        if user.get("expiry") < now:
            self.deactive_user()
