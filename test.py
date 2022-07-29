import json
import random
from datetime import datetime, timezone
import time

now = datetime.now(timezone.utc)
# now is current date
time.sleep(2)


token = datetime.now(timezone.utc)
token_db = str(token)
token = datetime.fromisoformat(token_db)
# token is db token


if token > now:
    print("Yes")
else:
    print("No")
