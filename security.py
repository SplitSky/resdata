from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from datetime import datetime, timedelta, timezone
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

    def get_token(self):
        return self.access_token

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

    
### API call generating the token




### API call validating the token
@app.post("{username}/validate_token")
async def validate_token(token : Token, username : str):
    # check if token is not expired and if user exists
    user = User_Auth(username, "None")
    if user.check_username_exists():
        # access database and validate the token by looking up username
        auth = client["Authentication"]
        users = auth["Users"]
        result = users.find_one({"username" : username})
        # see if user exists
        if result == None:
            return False
        # if yes verify token
        else:
            token_in_db = result.get("token") # returns the hashed password from database
            # hashes the password in and compares
            if token_in_db == token.get_token():
                # the user has the matching token
                # get the expiry time from database
                expiry = result.get("expiry")
                if datetime.now(timezone.utc) == :
                    
                    raise HTTPException(
                        status_code=status.HTTP_200_OK,
                        detail="User authenticated",
                    )
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User doesn't exist",
                    headers={"WWW-Authenticate" : "Bearer"}
                )
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User doesn't exist",
            headers={"WWW-Authenticate" : "Bearer"}
        )
    


