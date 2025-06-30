Step 1: Install django ---> pip install django
Step 2: Create a virtual environment ---> python -m venv myenv
Step 3: Activate virtual environment ---> myenv/scripts/activate
Step 4: Install all dependencies ---> pip install -r requirements.txt
Setp 5: Setup Mysql server ---> Create a mysql databse and set password
Step 6: Setup Email OTP/ See OTP at terminal ---> create a app password for gmail to send otp for signup
Step 7: Setup .env file ---> use keys to access database and email otp (DB_NAME, SQL_PASS, SQL_USER, EMAIL_ID, EMAIL_PASS)
Step 8: Create mysql tables ---> python manage.py makemigrations realstateapp python manage.py migrate
Step 9: Create admin id pass --->
------------------------COMMAND ON PROJECT DIRECTORY----------------
python manage.py shell

from realstateapp.models import AdminData
from django.contrib.auth.hashers import make_password

# Create an admin record manually with admin_id and hashed password
admin_id = <admin-id> 
username = <your-username>
password = make_password(<your-password>)  # Make sure to hash the password
name = <your-name> 

admin = AdminData(admin_id=admin_id, username=username, password=password, name=name)
admin.save()
-----------------------------------------------------------------------------

Step 10: Run server ---> python manage.py runserver
