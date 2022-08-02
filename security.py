from fastapi import Depends, FastAPI, HTTPException, status
#from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, timedelta, timezone
from fastapi import Depends, FastAPI, HTTPException, status
#from fastapi.security import OAuth2PasswordBearer, HTTPBasicCredentials
from jose import JWTError, jwt
#from main import app, client # imports of api variables
import hashlib as h
from variables import secret_key, algorithm, access_token_expire
import random
#from passlib.context import CryptContext
import logging
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
        result = users.find_one({"username" : self.username})
        # see if user exists
        if result == None:
            return False
        # if yes verify password
        else:
            pass_in_db = result.get("hash") # returns the hashed password from database
            # hashes the password in and compares
            if pass_in_db == self.return_final_hash(None):
                return True
            else:
                return False
            
    def return_final_hash(self, salt_in):
        if salt_in != None:
            password = str(salt_in) + self.password
            temp = h.shake_256()
            temp.update(password.encode('utf8'))
            return temp.hexdigest(64) # return a string
        else:

            auth = self.client["Authentication"]
            users = auth["Users"]
            result = users.find_one({"username" : self.username})
            if result != None:
                salt = result.get("salt")
                temp = h.shake_256()
                password = salt + self.password
                temp.update(password.encode('utf8'))
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail = "User doesn't exist"
                )
            return temp.hexdigest(64) # return a string from bytes

    def create_access_token(self,data: dict, expires_delta: timedelta | None = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=30)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    def check_username_exists(self):
        auth = self.client["Authentication"]
        users = auth["Users"]
        result = users.find_one({"username" : self.username})
        if result == None:
            return False
        else: 
            return True

    def activate_user(self):
        auth = self.client["Authentication"]
        users = auth["Users"]
        result = users.find_one_and_update({"username" : self.username}, {"disabled" : False})
        if result == None: # failed to find user
            return False
        else:
            return True

    def deactive_user(self):
        auth = self.client["Authentication"]
        users = auth["Users"]
        result = users.find_one_and_update({"username" : self.username}, {"disabled" : True})
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
                "username" : self.username,
                "hash" : self.return_final_hash(salt_init),
                "full_name" : full_name,
                "email" : email,
                "disabled" : True,
                "salt" : str(salt_init),
                "expiry" : str(datetime.now(timezone.utc))
            }
            result = users.insert_one(user_dict)
            return result
        else:
            raise HTTPException(
                status_code=status.HTTP_302_FOUND,
                detail = "User already exists"
            )


