from typing import Union
# Crypto
import hashlib as h
import random
from secrets import compare_digest
from datetime import datetime, timedelta

# cryptography module
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import padding, rsa
# Server communications
from fastapi import HTTPException, status
from jose import jwt, JWTError
from pymongo.mongo_client import MongoClient
# Internal
from variables import secret_key, algorithm, access_token_expire
# declare constants for the authentication
SECRET_KEY = secret_key
ALGORITHM = algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = access_token_expire

### key manager object
class key_manager(object):
    def __init__(self):
        self.public_file_name = 'public_key.pem'
        self.private_file_name = 'private_key.pem'

    def generate_keys(self):
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048, backend=default_backend())
        public_key = private_key.public_key()
        self.save_keys(private_key,public_key)
        return private_key, public_key

    def convert_keys_for_storage(self, private_key, public_key):
        pem = private_key.private_bytes(encoding=serialization.Encoding.PEM, format=serialization.PrivateFormat.PKCS8, encryption_algorithm=serialization.NoEncryption())
        pem2 = public_key.public_bytes(encoding=serialization.Encoding.PEM, format=serialization.PublicFormat.SubjectPublicKeyInfo)
        return pem,pem2

    def save_keys(self, private_key, public_key):
        pem, pem2 = self.convert_keys_for_storage(private_key, public_key)
        
        with open(self.private_file_name, 'wb') as f:
            f.write(pem)
            f.close()

        with open(self.public_file_name, 'wb') as f:
            f.write(pem2)
            f.close()
        
    def read_keys(self):
        with open(self.private_file_name, "rb") as f:
            private_key = serialization.load_pem_private_key(
                f.read(),password=None, backend=default_backend()
            )
            f.close()
        with open(self.public_file_name, "rb") as f:
            public_key = serialization.load_pem_public_key(
                f.read(), backend=default_backend()
            )
        return private_key, public_key
    def encrypt_message(self,message : str, public_key)->str:
        message_temp = bytes(message, encoding='latin-1')
        temp = public_key.encrypt(message_temp,
                                       padding.OAEP(
                                                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                                                algorithm=hashes.SHA256(),label=None
                                            )
                                        )
        temp = temp.decode('latin-1')
        return temp

    def decrypt_message(self, message : str, private_key)->str:
        message_temp = bytes(message, encoding='latin-1')
        temp = private_key.decrypt(message_temp, 
                                   padding.OAEP(mgf=padding.MGF1(
                                                    algorithm=hashes.SHA256()),
                                                algorithm=hashes.SHA256(),
                                                label=None)
                                   )
        temp = temp.decode('latin-1')
        return temp

    def serialize_public_key(self, pem):
         
        key =  serialization.load_pem_public_key(
                pem, backend=default_backend()
            )
        return key



### User verification object
class User_Auth(key_manager):
    def __init__(self, username_in : str, password_in : str, db_client_in: MongoClient) -> None:
        self.username = username_in
        self.password = password_in
        self.client = db_client_in
        key_manager.__init__(self)

    def check_password_valid(self) -> bool:
        """Verifies that the password is valid"""
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

    def return_final_hash(self, salt_in: Union[int,None] = None) -> str:
        """This returns the hash for the algorithm used within the database. Used for verification."""
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

    def create_access_token(self, expires_delta: Union[timedelta, None] = None):
        """Generates a jwt token for authentication between the interface and the API"""
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
            if result is None:
                raise authentication_exception
        return encoded_jwt

    def check_username_exists(self) -> bool:
        """Checks that the user with the given username exists within the database"""
        auth = self.client["Authentication"]
        users = auth["Users"]
        result = users.find_one({"username": self.username})
        return result is not None


    def activate_user(self) -> bool:
        """Changes the disabled variable within the user to False"""
        auth = self.client["Authentication"]
        users = auth["Users"]
        result = users.find_one_and_update({"username": self.username}, {'$set': {"disabled": False}})
        if result == None:  # failed to find user
            return False
        else:
            return True

    def deactivate_user(self) -> bool:
        """Changes the disabled variable within the user to True"""
        auth = self.client["Authentication"]
        users = auth["Users"]
        result = users.find_one_and_update({"username": self.username}, {'$set': {"disabled": True}})
        return result is not None

    def add_user(self, full_name: str, email: str) -> bool:
        """Adds a user to the database"""
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
            return False

    def fetch_token(self) -> str:
        """Fetches the token variable from the database"""
        # fetches the token associated with the user
        auth = self.client["Authentication"]
        users = auth["Users"]
        result = users.find_one({"username": self.username})
        if result != None:
            return result.get("token")
        else:
            raise HTTPException(status_code=status.HTTP_204_NO_CONTENT, detail="User doesn't exist")
    def fetch_user(self):
        """Fetches the full user document from the database"""
        auth = self.client["Authentication"]
        users = auth["Users"]
        result = users.find_one({"username": self.username})
        if result != None:
            return result
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="The user was not found")

    def authenticate_token(self) -> bool:
        """Authenticates the token within the class to be one matching and valid for the username in self.username"""
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

    def update_disable_status(self):
        """Book-keeping function which updates the disabled variable within the user document. Used to ensure that the authentication is still valid"""
        # fetch user and compare the expiry date to now.
        now = datetime.utcnow()
        user = self.fetch_user()
        if user != None:
            if user.get("expiry") < now:
                self.deactivate_user()
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User doesn't exist")

    def check_author(self, project_id, experiment_id, dataset_id) -> bool:
        """Verifies the dataset in the given path has the specified author and returns True if access is allowed"""
        experiment = self.client[project_id][experiment_id]
        result = experiment.find_one({"name" : dataset_id})
        if result != None:
            author_list = result.get("author")
            for author in author_list:
                if author.get("name") == self.username:
                    return True
        return False

# def check_user_permission(self, username, permission_requested, project_id, experiment_id):
   #     """Checks whether a user has the requested permission or higher"""
   #     collection_variable = self.client[project_id][experiment_id]
   #     result = collection_variable.find_one({"name" : experiment_id})
   #     if result == None:
   #         raise HTTPException(status_code=status.HTTP_400_NO_CONTENT,
   #                             detail="The dataset wasn't found")
   #     author_list = result.get("author")
   #     for entry in author_list:
   #         if entry.get("name") == username:
   #             # username found
   #             if entry.get("permission") == permission_requested or entry.get("permission") == "admin":
   #                 return True
   #     return False
                    
   # def get_signed_message(self, private_key, ui_public_key, message):
   #     final_message = self.decrypt_message(message, private_key)
   #     return self.decrypt_message(final_message, ui_public_key)

   # def encrypt_and_sign_message(self, public_key, ui_private_key, message):
   #     # sign
   #     message_final = self.encrypt_message(message, ui_private_key) 
   #     # encrypt
   #     return self.encrypt_message(message_final, public_key)
    
        
