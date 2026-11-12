
from utils.security import hash_password, verify_password

password = "Test@12345"

hashed_password = hash_password(password)

#print("Original password:", password)
#print("Hashed password:", hashed_password)

#print("Correct password:", verify_password("Test@12345", hashed_password))

#print("Incorrect password:", verify_password("Wrong@12345", hashed_password))
