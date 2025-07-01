from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.hashers import check_password
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.db.models import Count
from django.http import HttpResponse, JsonResponse
from .models import AdminData, Apartment, BrochureImage, Users, ScheduledVisit
from realstateapp.models import Contact_table
from django.core.exceptions import ValidationError
from django.utils.timezone import now
from django.core.mail import send_mail
from django.contrib.auth.hashers import make_password
from django.views.decorators.http import require_http_methods
from django.db import IntegrityError
from django.conf import settings
from django.utils import timezone
from datetime import datetime, timedelta
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models.functions import TruncMonth
import pytz
import json
import random
import threading
import time

# Create your views here.

def index(request):
    properties = Apartment.objects.filter(status='On Sale')
    is_logged_in = request.session.get('is_logged_in', False)
    return render(request, 'main/index.html', {'properties': properties, 'is_logged_in': is_logged_in})

 
# ========Contact Form start=========
def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')

        try:
            Contact_table.objects.create(name=name, email=email, subject=subject, message=message)

        except Exception as e:
            print("Error saving data", e)

        print(f"Name: {name}, Email: {email}, Subject: {subject}, Message: {message}")
        return HttpResponse("Thank you for your message!")

    return render(request, 'main/contact.html')
   
# ===========properties_details start==========

def apartment_detail_view(request, property_id):
    apartment = get_object_or_404(Apartment, property_id=property_id)
    brochures = apartment.brochure_images.all()
    
    is_logged_in = request.session.get('is_logged_in', False)
    user_id = request.user.id if is_logged_in else None

    min_date_str = now().date().isoformat()

    context = {
        'apartment': apartment,
        'brochures': brochures,
        'user_id': user_id,
        'is_logged_in': is_logged_in,
        'min_date_str': min_date_str,
    }
    return render(request, 'main/properties_details.html', context)

# ==========properties===========
def properties(request):
    properties = Apartment.objects.all()
    return render(request, 'main/properties.html', {'properties': properties})

email_otp_store = {}

def generate_otp():
    return str(random.randint(100000, 999999))

@csrf_exempt
def send_email_otp(request):
    """
    API endpoint to send an OTP to the provided email address.
    Checks if the email is already registered before sending OTP.
    Expects JSON POST data.
    """
    if request.method == "POST":
        try:
            # Parse the JSON data from the request body
            data = json.loads(request.body.decode('utf-8'))
            email = data.get("email")
            print("email received from frontend:", email) # This will now print the email

            if not email:
                return JsonResponse({"status": "error", "message": "Email is required."}, status=400)

            # Basic email format validation (optional, frontend should also do this)
            # from django.core.validators import validate_email
            # from django.core.exceptions import ValidationError
            # try:
            #     validate_email(email)
            # except ValidationError:
            #     return JsonResponse({"status": "error", "message": "Invalid email format."}, status=400)

            if Users.objects.filter(email=email).exists():
                return JsonResponse({"status": "error", "message": "This email is already registered. Please login or use a different email."}, status=409) # 409 Conflict

            otp = generate_otp()
            email_otp_store[email] = otp

            def remove_otp_after_delay(email_to_remove, otp_sent):
                time.sleep(300) # 5 minutes
                # Only remove if the OTP hasn't been replaced (e.g., by a new send OTP request)
                if email_to_remove in email_otp_store and email_otp_store[email_to_remove] == otp_sent:
                    email_otp_store.pop(email_to_remove, None)

            threading.Thread(target=remove_otp_after_delay, args=(email, otp), daemon=True).start()

            try:
                send_mail(
                    "Your Apartelle Verification OTP",
                    f"Your One-Time Password (OTP) for Apartelle signup is: {otp}\n\nThis OTP is valid for 5 minutes.",
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    fail_silently=False,
                )
                return JsonResponse({"status": "success", "message": "OTP sent to your email. Please check your inbox and spam folder."})
            except Exception as e:
                # If email sending fails, remove the stored OTP to avoid stale data
                email_otp_store.pop(email, None)
                return JsonResponse({"status": "error", "message": f"Failed to send OTP: {str(e)}. Please try again."}, status=500)

        except json.JSONDecodeError:
            return JsonResponse({"status": "error", "message": "Invalid JSON in request body."}, status=400)
        except Exception as e:
            return JsonResponse({"status": "error", "message": f"An unexpected error occurred: {str(e)}"}, status=400)

    return JsonResponse({"status": "error", "message": "Invalid request method."}, status=405) # 405 Method Not Allowed

@csrf_exempt
def verify_email_otp_api(request):
    """
    API endpoint to verify the OTP provided by the user.
    Expects JSON POST data.
    """
    if request.method == "POST":
        try:
            data = request.POST # For form-urlencoded data from JS
            email = data.get("email")
            user_otp = data.get("otp")

            if not all([email, user_otp]):
                return JsonResponse({"status": "error", "message": "Email and OTP are required."}, status=400)

            correct_otp = email_otp_store.get(email)

            if not correct_otp:
                return JsonResponse({"status": "error", "message": "OTP expired or not found. Please request a new OTP."}, status=400)

            if str(user_otp) == correct_otp:
                # OTP is kept in email_otp_store until successful signup,
                # allowing the user to retry signup without re-verifying email if
                # other signup validations fail. It will eventually expire.
                return JsonResponse({"status": "success", "message": "OTP verified successfully."})
            else:
                return JsonResponse({"status": "error", "message": "Invalid OTP. Please check the 6-digit code."}, status=400)

        except Exception as e:
            return JsonResponse({"status": "error", "message": f"Invalid request data: {str(e)}"}, status=400)

    return JsonResponse({"status": "error", "message": "Invalid request method."}, status=405)


@csrf_exempt
def user_signup(request):
    """
    Handles user signup by processing form data, validating it,
    and creating a new user account.
    Expects POST data (form-urlencoded or JSON if adjusted in JS).
    """
    if request.method == "POST":
        data = request.POST

        name = data.get("name")
        email = data.get("email")
        password = data.get("password")
        confirm_password = data.get("confirm_password")
        phn = data.get("phn")
        whatsapp = data.get("whatsapp")
        confirm_whatsapp = data.get("confirm_whatsapp")
        addr = data.get("addr")
        agree_terms = data.get("agreeTerms") # Assuming 'on' or None

        # 1. Basic validation: Check if all required fields are present
        if not all([name, email, password, confirm_password, phn, addr, agree_terms == 'on']):
            return JsonResponse({"status": "error", "message": "All required fields are missing or empty, or terms not agreed."}, status=400)

        if password != confirm_password:
            return JsonResponse({"status": "error", "message": "Passwords do not match."}, status=400)

        # Validate WhatsApp number match, only if WhatsApp is provided
        # The frontend JS already handles regex for 10 digits, so just check match
        if whatsapp and whatsapp != confirm_whatsapp:
            return JsonResponse({"status": "error", "message": "WhatsApp numbers do not match."}, status=400)

        # 2. Verify Email OTP status (MUST have been verified via verify_email_otp_api already)
        if email not in email_otp_store:
            return JsonResponse({"status": "error", "message": "Email not verified with OTP. Please send and verify OTP before signing up."}, status=400)

        # Prepare phone numbers with country code
        full_phone_primary = '+91' + phn
        full_phone_secondary = '+91' + whatsapp if whatsapp else ''

        if Users.objects.filter(email=email).exists():
            return JsonResponse({"status": "error", "message": "This email is already registered. Please login or use a different email."}, status=409)

        if Users.objects.filter(phone_primary=full_phone_primary).exists():
            return JsonResponse({"status": "error", "message": "This primary phone number is already registered. Please login or use a different phone number."}, status=409)

        try:
            Users.objects.create(
                name=name,
                email=email,
                password=make_password(password),
                phone_primary=full_phone_primary,
                phone_secondary=full_phone_secondary,
                address=addr,
                is_verified=True
            )

            email_otp_store.pop(email, None)

            return JsonResponse({"status": "success", "message": "Account created successfully! You can now log in."})

        except IntegrityError:
            return JsonResponse({"status": "error", "message": "A user with this email or phone number already exists."}, status=409)
        except Exception as e:
            return JsonResponse({"status": "error", "message": f"An error occurred during signup: {str(e)}. Please try again."}, status=500)

    return render(request, 'main/signup.html')

def user_login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        try:
            user = Users.objects.get(email=email)

            if not user.is_active:
                messages.error(request, "Your account is disabled. Please contact support.")
                return redirect('user_login')

            if check_password(password, user.password):
                # Set session
                request.session['user_id'] = str(user.id)
                request.session['is_logged_in'] = True
                request.session['user_name'] = user.name
                request.session['user_email'] = user.email

                messages.success(request, "Login successful!")
                return redirect('index')
            else:
                messages.error(request, "Invalid password.")
        except Users.DoesNotExist:
            messages.error(request, "No account found with that email.")

        return redirect('user_login')
    return render(request, 'main/user_login.html')


def user_logout(request):
    logout(request)
    return redirect('index')

#============For Admin Panel==================

def admin_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        try:
            admin = AdminData.objects.get(username=username)

            if check_password(password, admin.password):
                user, created = User.objects.get_or_create(username=username)
                user.set_password(password)
                user.save()
                login(request, user)
                request.session['admin_id'] = admin.admin_id
                return redirect('admin_dashboard')
            else:
                messages.error(request, 'Invalid username or password')
        except AdminData.DoesNotExist:
            messages.error(request, 'Admin does not exist')

    return render(request, 'admin/login.html')

@login_required
def admin_dashboard(request):
    total_users = Users.objects.count()
    total_booked = Apartment.objects.filter(status='booked').count()
    ten_days_ago = timezone.now() - timedelta(days=10)
    new_bookings = Apartment.objects.filter(
        status='booked',
        booked_date__gte=ten_days_ago
    ).count()

    context = {
        "total_users": total_users,
        "total_booked": total_booked,
        "new_bookings": new_bookings,
    }
    return render(request, 'admin/dashboard.html', context)

def bookings_monthly_data(request):
    now = timezone.now()
    year_start = now.replace(month=1, day=1, hour=0, minute=0, second=0)

    # Get monthly booking counts
    bookings = (
        Apartment.objects.filter(
            status='booked',
            booked_date__year=now.year
        )
        .annotate(month=TruncMonth('booked_date'))
        .values('month')
        .annotate(count=Count('property_id'))
        .order_by('month')
    )

    # Create mapping: {1: 0, 2: 0, ..., 12: 0}
    month_data = {i: 0 for i in range(1, 13)}
    for entry in bookings:
        month = entry['month'].month
        month_data[month] = entry['count']

    # Prepare response
    labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    data = [month_data[i] for i in range(1, 13)]

    return JsonResponse({
        'labels': labels,
        'data': data
    })

def monthly_summary_view(request):
    now = timezone.now()
    current_year = now.year

    # Step 1: Monthly user signups
    user_counts = (
        Users.objects.filter(created_at__year=current_year)
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(count=Count('id'))
    )

    # Step 2: Monthly bookings
    booking_counts = (
        Apartment.objects.filter(booked_date__year=current_year, status='booked')
        .annotate(month=TruncMonth('booked_date'))
        .values('month')
        .annotate(count=Count('property_id'))
    )

    # Step 3: Prepare dicts with month numbers as keys
    user_data = {i: 0 for i in range(1, 13)}
    booking_data = {i: 0 for i in range(1, 13)}

    for entry in user_counts:
        user_data[entry['month'].month] = entry['count']

    for entry in booking_counts:
        booking_data[entry['month'].month] = entry['count']

    # Step 4: Build final response arrays
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    customers = []
    bookings = []
    not_booked = []

    for i in range(1, 13):
        cust = user_data[i]
        book = booking_data[i]
        customers.append(cust)
        bookings.append(book)
        not_booked.append(max(cust - book, 0))

    return JsonResponse({
        'months': months,
        'customers': customers,
        'bookings': bookings,
        'not_booked': not_booked
    })

@login_required
def admin_logout(request):
    logout(request)
    return redirect('index')

@login_required
def admin_add_category(request):
    return render(request, 'admin/add-category.html')

@login_required
def admin_add_property(request):
    if request.method == "POST":
        admin_id = request.session.get('admin_id')
        if not admin_id:
            messages.error(request, "Admin not logged in properly.")
            return redirect('admin_login')

        admin = get_object_or_404(AdminData, admin_id=admin_id)

        property_name = request.POST.get('property_name')
        category = request.POST.get('category')
        area = request.POST.get('area')
        address = request.POST.get('address')
        price = request.POST.get('price')
        bedrooms = request.POST.get('bedrooms')
        bathrooms = request.POST.get('bathrooms')
        floor = request.POST.get('floor')
        city = request.POST.get('city')
        pincode = request.POST.get('pincode')
        parking = request.POST.get('parking')

        main_image = request.FILES.get('main_image')

        brochure_images = request.FILES.getlist('brochure')

        apartment = Apartment(
            created_by=admin,
            property_name=property_name,
            type=category,
            address=address,
            price=price,
            bedrooms=bedrooms,
            bathrooms=bathrooms,
            area=area,
            floor=floor,
            parking=parking,
            city=city,
            pincode=pincode,
            main_image=main_image,
        )
        apartment.save()

        for image in brochure_images:
            if apartment.brochure_images.count() < 10:
                BrochureImage.objects.create(apartment=apartment, image=image)
            else:
                raise ValidationError("You can only upload up to 10 brochure images.")
        
        return redirect('all_property')

    return render(request, 'admin/add-property.html')

def delete_brochure_image(request, image_id):
    brochure = get_object_or_404(BrochureImage, id=image_id)
    if request.method == 'POST':
        brochure.delete()
    return redirect('admin_add_property')

@login_required
def admin_add_sub_category(request):
    return render(request, 'admin/add-sub-category.html')

def verify_admin_credentials(username, password):
    """
    Verifies admin username and password against the AdminData model.
    Returns the AdminData object if credentials are valid, False otherwise.
    """
    try:
        admin_user = AdminData.objects.get(username=username)
        if admin_user.check_password(password):
            return admin_user
        return False
    except AdminData.DoesNotExist:
        return False
    except Exception as e:
        print(f"Error during admin verification: {e}")
        return False

@login_required
def admin_all_property(request):
    apartments_queryset = Apartment.objects.all().order_by('property_name')

    # Apply filters if present in GET request
    property_type = request.GET.get('property_type')
    property_name = request.GET.get('property_name')
    city = request.GET.get('city')

    if property_type:
        apartments_queryset = apartments_queryset.filter(type=property_type)
    if property_name:
        apartments_queryset = apartments_queryset.filter(property_name=property_name)
    if city:
        apartments_queryset = apartments_queryset.filter(city=city)

    apartments = apartments_queryset.annotate(visit_count=Count('visits'))

    property_types = Apartment.objects.values_list('type', flat=True).distinct().order_by('type')
    property_names = Apartment.objects.values_list('property_name', flat=True).distinct().order_by('property_name')
    cities = Apartment.objects.values_list('city', flat=True).distinct().order_by('city')


    context = {
        'apartments': apartments,
        'property_types': property_types,
        'property_names': property_names,
        'cities': cities,
    }

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'admin/apartment_table.html', context)
    return render(request, 'admin/all-property.html', context)

@csrf_exempt
def update_apartment_status(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            property_id = data.get("property_id")
            new_status = data.get("status")

            apartment = Apartment.objects.get(property_id=property_id)
            apartment.status = new_status
            apartment.save()

            return JsonResponse({"success": True})
        except Apartment.DoesNotExist:
            return JsonResponse({"success": False, "error": "Apartment not found"})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Invalid request"})

@login_required
def delete_apartment(request, property_id):
    if request.method == 'POST':
        try:
            apartment = Apartment.objects.get(property_id=property_id)
            apartment.delete_all()  # or .delete()
            return JsonResponse({'status': 'success'})
        except Apartment.DoesNotExist:
            return JsonResponse({'status': 'not found'}, status=404)
    return JsonResponse({'status': 'invalid request'}, status=400)

def scheduled_visits_view(request):
    visits = ScheduledVisit.objects.select_related('user', 'apartment').all()
    context = {
        'visits': visits
    }
    return render(request, 'admin/scheduled_visits.html', context)

@require_http_methods(["GET"])
def approve_visit(request, visit_id):
    visit = get_object_or_404(ScheduledVisit, visit_id=visit_id)
    if visit.status != 'approved':
        visit.status = 'approved'
        visit.save()
        messages.success(request, f"Visit for {visit.user.name} to {visit.apartment.property_name} has been approved.")
    else:
        messages.info(request, "This visit is already approved.")
    return redirect('scheduled_visits')


@require_http_methods(["POST"])
def update_visit(request):
    """
    Updates the date and time of a scheduled visit and sets its status to 'approved'.
    """
    visit_id = request.POST.get('visit_id')
    new_date_str = request.POST.get('visit_date')
    new_time_str = request.POST.get('visit_time')

    visit = get_object_or_404(ScheduledVisit, id=visit_id) # Using 'id' as per your HTML's data-id

    if not all([new_date_str, new_time_str]):
        messages.error(request, "Both date and time are required for the update.")
        return redirect('scheduled_visits')

    try:
        datetime_str = f"{new_date_str} {new_time_str}"
        
        new_datetime = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M')
        current_timezone = pytz.timezone(timezone.get_current_timezone().zone)
        new_datetime_aware = current_timezone.localize(new_datetime)

        visit.visit_datetime = new_datetime_aware
        visit.visit_date_str = new_datetime_aware.strftime('%b %d, %Y %I:%M %p') # Format as needed for display
        visit.status = 'approved' # Automatically approve on update
        visit.save()
        messages.success(request, f"Visit for {visit.user.name} updated and approved successfully to {visit.visit_date_str}.")
    except ValueError:
        messages.error(request, "Invalid date or time format provided.")
    except Exception as e:
        messages.error(request, f"An error occurred: {e}")

    return redirect('scheduled_visits')

@require_http_methods(["GET"])
def delete_brochure_image(request, image_id):
    """
    Deletes a specific brochure image.
    This is called via a direct link in the template.
    """
    brochure_image = get_object_or_404(BrochureImage, id=image_id)
    apartment_id = brochure_image.apartment.property_id
    try:
        brochure_image.delete()
        messages.success(request, "Brochure image deleted successfully.")
    except Exception as e:
        messages.error(request, f"Error deleting image: {e}")
    
    return redirect('edit_apartment', property_id=apartment_id)


def edit_apartment_view(request, property_id):
    """
    Handles displaying and updating apartment details, including main image replacement
    and adding/removing brochure images.
    """
    apartment = get_object_or_404(Apartment, property_id=property_id)

    if request.method == 'POST':
        try:
            with transaction.atomic():
                apartment.property_name = request.POST.get('property_name', apartment.property_name)
                apartment.status = request.POST.get('status', apartment.status)
                apartment.type = request.POST.get('type', apartment.type)
                apartment.address = request.POST.get('address', apartment.address)
                apartment.price = int(request.POST.get('price', apartment.price))
                apartment.bedrooms = int(request.POST.get('bedrooms', apartment.bedrooms))
                apartment.bathrooms = int(request.POST.get('bathrooms', apartment.bathrooms))
                apartment.area = request.POST.get('area', apartment.area)
                apartment.floor = int(request.POST.get('floor')) if request.POST.get('floor') else None
                apartment.parking = int(request.POST.get('parking')) if request.POST.get('parking') else None
                apartment.city = request.POST.get('city', apartment.city)
                apartment.pincode = int(request.POST.get('pincode', apartment.pincode))

                if 'replace_main_image' in request.FILES:
                    new_main_image = request.FILES['replace_main_image']
                    if apartment.main_image:
                        apartment.delete_main_image()
                    apartment.main_image = new_main_image

                apartment.save()

                if 'new_brochure_images' in request.FILES:
                    for f in request.FILES.getlist('new_brochure_images'):
                        try:
                            BrochureImage.create_with_validation(apartment=apartment, image=f)
                        except ValidationError as e:
                            messages.warning(request, f"Could not add brochure image '{f.name}': {e.message}")
                        except Exception as e:
                            messages.error(request, f"Error adding brochure image '{f.name}': {e}")
                
                messages.success(request, f"Apartment '{apartment.property_name}' updated successfully.")
                return redirect('edit_apartment', property_id=apartment.property_id)
        
        except IntegrityError as e:
            messages.error(request, f"Error updating apartment: A property with this name already exists. {e}")
        except ValidationError as e:
            messages.error(request, f"Validation error: {e.message}")
        except ValueError:
            messages.error(request, "Invalid numeric input for price, bedrooms, bathrooms, floor, parking, or pincode.")
        except Exception as e:
            messages.error(request, f"An unexpected error occurred: {e}")
        
        return render(request, 'admin/edit_apartment.html', {'apartment': apartment})

    context = {'apartment': apartment}
    return render(request, 'admin/edit_apartment.html', context)


@require_http_methods(["GET"])
def delete_brochure_image(request, image_id):
    brochure_image = get_object_or_404(BrochureImage, id=image_id)
    apartment_id = brochure_image.apartment.property_id
    
    try:
        brochure_image.delete()
        messages.success(request, "Brochure image deleted successfully.")
    except Exception as e:
        messages.error(request, f"Error deleting image: {e}")
    
    return redirect('edit_apartment', property_id=apartment_id)


@require_POST
def book_apartment_view(request):
    """
    Marks an apartment as 'Booked' after verifying admin credentials.
    Returns JSON response for AJAX calls.
    """
    property_id = request.POST.get('property_id')
    username = request.POST.get('username')
    password = request.POST.get('password')

    admin_user = verify_admin_credentials(username, password)
    if not admin_user:
        return JsonResponse({'success': False, 'message': 'Invalid admin credentials.'}, status=403)

    try:
        apartment = get_object_or_404(Apartment, property_id=property_id)

        if apartment.status != 'Booked':
            apartment.status = 'Booked'
            apartment.save()
            messages.success(request, f"Apartment '{apartment.property_name}' successfully marked as Booked.")
            return JsonResponse({'success': True, 'message': 'Apartment marked as booked.'})
        else:
            return JsonResponse({'success': False, 'message': 'Apartment is already booked.'}, status=400)

    except Apartment.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Apartment not found.'}, status=404)
    except Exception as e:
        messages.error(request, f"Error marking apartment as booked: {e}")
        return JsonResponse({'success': False, 'message': f'An error occurred: {e}'}, status=500)


@require_POST
def delete_apartment_view(request, property_id):
    """
    Deletes an apartment after verifying admin credentials.
    Returns JSON response for AJAX calls.
    """
    username = request.POST.get('username')
    password = request.POST.get('password')

    admin_user = verify_admin_credentials(username, password)
    if not admin_user:
        return JsonResponse({'success': False, 'error': 'Invalid admin credentials.'}, status=403)

    try:
        apartment = get_object_or_404(Apartment, property_id=property_id)
        apartment.delete_all()
        messages.success(request, f"Apartment '{apartment.property_name}' and all its associated data deleted successfully.")
        return JsonResponse({'success': True, 'message': 'Apartment deleted successfully.'})

    except Apartment.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Apartment not found.'}, status=404)
    except Exception as e:
        messages.error(request, f"Error deleting apartment: {e}")
        return JsonResponse({'success': False, 'error': f'An error occurred: {e}'}, status=500)

@login_required
def admin_banner_management(request):
    return render(request, 'admin/banner-management.html')

@login_required
def admin_booking(request):
    return render(request, 'admin/bookings.html')

@login_required
def admin_change_password(request):
    return render(request, 'admin/change-password.html')

@login_required
def admin_contact_inquiry(request):
    return render(request, 'admin/contact-inquiry.html')
    