from django.contrib.auth.hashers import PBKDF2PasswordHasher

class FastPBKDF2PasswordHasher(PBKDF2PasswordHasher):
    """
    A subclass of PBKDF2PasswordHasher that uses 1 iteration.
    This is for development/testing ONLY, to speed up login and signup.
    """
    iterations = 1
