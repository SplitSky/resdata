from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from datetime import datetime, timedelta, timezone
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, HTTPBasicCredentials
from jose import JWTError, jwt
from pydantic import BaseModel
from main import app, client # imports of api variables
import hashlib as h
from variables import secret_key, algorithm, access_token_expire
from datastructure import User, UserInDB, Token
import random
#from passlib.context import CryptContext

# declare constants for the 

SECRET_KEY = secret_key
ALGORITHM = algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = access_token_expire
### User verification object
class User_Auth(object):
    def __init__(self, username_in, password_in):
        self.username = username_in
        self.password = password_in

    def check_password_valid(self):
        # lookup the database for user
        auth = client["Authentication"]
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
            password = salt_in + self.password
            temp = h.shake_256()
            temp.update(password.encode('utf8'))
            return temp.digest(64)
        else:

            auth = client["Authentication"]
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
            return temp.digest(64)

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
        auth = client["Authentication"]
        users = auth["Users"]
        result = users.find_one({"username" : self.username})
        if result == None:
            return False
        else: 
            return True

    def activate_user(self):
        auth = client["Authentication"]
        users = auth["Users"]
        result = users.find_one_and_update({"username" : self.username}, {"disabled" : False})
        if result == None: # failed to find user
            return False
        else:
            return True

    def deactive_user(self):
        auth = client["Authentication"]
        users = auth["Users"]
        result = users.find_one_and_update({"username" : self.username}, {"disabled" : True})
        if result == None:
            return False
        else:
            return True

    def add_user(self, full_name, email):
        auth = client["Authentication"]
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
                "salt" : salt_init,
                "expiry" : str(datetime.now(timezone.utc))
            }
            result = users.insert_one(user_dict)
            return result
        else:
            raise HTTPException(
                status_code=status.HTTP_302_FOUND,
                detail = "User already exists"
            )

### API call generating the token
@app.get("/generate_token", response_model=Token)
async def login_for_access_token(credentials : HTTPBasicCredentials):
    user_in = User(username=credentials.username , hash_in=credentials.password) # remove the object declaration once the authentiation method is standardised
    user = User_Auth(user_in.get_username(), user_in.get_hash_in()) 
    if user.check_username_exists():
        if user.check_password_valid():
            # authentication complete
            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            temp = user.create_access_token({"username" : user_in.get_username()},expires_delta=access_token_expires)
            expiry_date = datetime.now(timezone.utc) + access_token_expires

            # update user data
            auth = client["Authentication"]
            users = auth["Users"]
            result = users.find_one({"username" : user_in.get_username()})
            if result != None:
                # updates the database to verify the user generated a token
                user.activate_user()
                users.find_one_and_update({"username": user_in.get_username()}, {"expire" : str(expiry_date)})
                return Token(access_token=temp, token_type="bearer")
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="The credentials failed to validate"
    )

### API call validating the token
@app.post("{username}/validate_token")
async def validate_token(token : Token):
    # check if token is not expired and if user exists
    payload = jwt.decode(token.get_token(), SECRET_KEY, algorithms=[ALGORITHM])
    if payload.get("sub") == None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token is invalid"
        )
    else:
        username = payload.get("sub")
    user = User_Auth(username, "None")
    if user.check_username_exists():
        # access database and validate the token by looking up username
        auth = client["Authentication"]
        users = auth["Users"]

        result = users.find_one({"username" : username})
        # see if user exists
        if result != None:
            token_in_db = result.get("token") # returns the hashed password from database
            # hashes the password in and compares
            if token_in_db == token.get_token(): #### change to digest comparison to stop timing attack 
                # the user has the matching token
                # get the expiry time from database
                expiry = datetime.fromisoformat(result.get("expiry")) # converts string to date
                if datetime.now(timezone.utc) <= expiry: # check if token is not expired
                    raise HTTPException(
                        status_code=status.HTTP_200_OK,
                        detail="User authenticated",
                    )
                else:
                    # deactivate the user
                    user.deactive_user()
                    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="User doesn't exist",
        headers={"WWW-Authenticate" : "Bearer"}
    )

@app.get("{full_name}/{email}/create_user")
async def create_user(full_name, email,credentials : HTTPBasicCredentials):
    username = credentials.username
    password = credentials.password
    user = User_Auth(username, password)
    response = user.add_user(full_name, email)
    return {"message" : response}

