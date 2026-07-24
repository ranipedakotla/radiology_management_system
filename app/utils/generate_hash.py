from passlib.hash import argon2

hashed = argon2.hash("lucky")
print(hashed)