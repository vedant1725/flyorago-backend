import os
import sys
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

def promote_user(email):
    user = User.objects.filter(email__iexact=email).first()
    if not user:
        print(f"Error: User with email '{email}' not found.")
        all_users = User.objects.all()
        if all_users.exists():
            print("\nHere are the emails currently registered in the database:")
            for u in all_users:
                print(f" - {u.email} (Role: {u.role})")
        else:
            print("\nThere are currently no users registered in the database.")
            print("Please sign up first in the web interface (http://localhost:5173/signup) before promoting.")
        return False
    
    user.role = 'admin'
    user.is_staff = True
    user.is_superuser = True
    user.is_verified = True
    user.save()
    print(f"Success: User '{email}' has been promoted to Admin!")
    print("They can now access the KYC Admin Panel at http://localhost:5173/admin/kyc")
    return True

if __name__ == '__main__':
    if len(sys.argv) < 2:
        email = input("Enter email address of the user to promote to admin: ").strip()
    else:
        email = sys.argv[1].strip()
    
    if email:
        promote_user(email)
    else:
        print("No email provided.")
