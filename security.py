from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from datetime import datetime, timedelta
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
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


class TokenData(BaseModel):
    username: str | None = None


class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None


class UserInDB(User):
    hashed_password: str


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

def get_user(username):
    user = User_Auth(username, "none")
    if user.check_username_exists(username):
        user_dict = user.
        return UserInDB(**user_dict)

async def login_for_access_token(form_data : OAuth2PasswordRequestForm = Depends()):
    user = User_Auth(form_data.username, form_data.password)
    if not user.check_password_valid():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        headers={"WWW-Authenticate": "Bearer"}
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
    return {"access_token" : access_token, "token_type" : "bearer"}
# to get a string like this run:
# openssl rand -hex 32


async def get_current_user(token : str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate" : "Bearer"}
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username : str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTErrorL
        raise credentials_exception
    user = get_user()

fake_users_db = {
    "johndoe": {
        "username": "johndoe",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
        "disabled": False,
    }
}



