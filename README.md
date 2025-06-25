Step 1: Install django ---> pip install django
Step 2: Create a virtual environment ---> python -m venv myenv
Step 3: Activate virtual environment ---> myenv/scripts/activate
Step 4: Install all dependencies ---> pip install -r requirements.txt
Setp 5: Setup Mysql server ---> Create a mysql databse and set password
Step 6: Setup Email OTP/ See OTP at terminal ---> create a app password for gmail to send otp for signup
Step 7: Setup .env file ---> use keys to access database and email otp (DB_NAME, SQL_PASS, SQL_USER, EMAIL_ID, EMAIL_PASS)
Step 8: Create mysql tables ---> python manage.py makemigrations  python manage.py migrate
Step 9: Run server ---> python manage.py runserver
