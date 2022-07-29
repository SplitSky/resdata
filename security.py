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
#from passlib.context import CryptContext

### BaseModel classes
class Token(BaseModel):
    access_token: str
    token_type: str

    def get_token(self):
        return self.access_token

class TokenData(BaseModel):
    username: str | None = None


class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    hash_in: str

    def get_username(self):
        return self.username

    def get_email(self):
        return self.email

    def get_full_name(self):
        return self.full_name

    def get_hash_in(self):
        return self.hash_in



class UserInDB(User):
    hashed_password: str
    disabled: bool | None = None


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
            if pass_in_db == self.return_final_hash():
                return True
            else:
                return False
            
    def return_final_hash(self):
        auth = client["Authentication"]
        users = auth["Users"]
        result = users.find_one({"username" : self.username})
        if result != None:
            salt = result.get("salt")
            temp = h.shake_256()
            password = salt + self.password
            temp.update(password.encode('utf8'))
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
    
### API call generating the token
@app.get("/generate_token")
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
            if token_in_db == token.get_token():
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
    


