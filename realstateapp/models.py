from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings
from django.contrib.auth.hashers import make_password, check_password
import shutil
import uuid
import os

# Create your models here.

class AdminData(models.Model):
    admin_id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=100, unique=True)
    password = models.CharField(max_length=255)
    name = models.CharField(max_length=100)

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    def __str__(self):
        return self.username

class Contact_table(models.Model):
    name = models.CharField(max_length=30)
    email = models.EmailField()
    subject = models.CharField(max_length=100)
    message = models.CharField(max_length=255)

    def __str__(self):
        return self.title

class Users(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    addr = models.TextField()
    phn = models.CharField(max_length=20)
    whatsapp = models.CharField(max_length=20)
    email = models.EmailField(unique=True)
    is_phone_verified = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=True)
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    password = models.CharField(max_length=255)

    def __str__(self):
        return self.name
    
class ScheduledVisit(models.Model):
    visit_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    user = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='scheduled_visits')
    apartment = models.ForeignKey('Apartment', on_delete=models.CASCADE, related_name='visits')

    visit_date_str = models.CharField(max_length=100)
    visit_datetime = models.DateTimeField()
    status = models.CharField(max_length=10, default='pending')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Scheduled Visit"
        verbose_name_plural = "Scheduled Visits"
        ordering = ['visit_datetime']

    def __str__(self):
        return f"Visit for {self.apartment.property_name} by {self.user.name} on {self.visit_date_str}"

def apartment_image_path(instance, filename):
    return f"appartment_images/{instance.property_id}/{filename}"

class Apartment(models.Model):
    property_id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False
    )
    created_by = models.ForeignKey('AdminData', on_delete=models.CASCADE)
    property_name = models.CharField(max_length=200, unique=True)
    status = models.TextField(max_length=10, default='On Sale')
    booked_date = models.DateTimeField(auto_now=True)
    type = models.CharField(max_length=30)
    address = models.CharField(max_length=200)
    price = models.IntegerField()
    bedrooms = models.IntegerField()
    bathrooms = models.IntegerField()
    area = models.CharField(max_length=100)
    floor = models.IntegerField()
    parking = models.IntegerField()
    city = models.TextField(max_length=30)
    pincode = models.IntegerField(null=False, blank=False)
    main_image = models.ImageField(upload_to=apartment_image_path)

    def delete_all(self, *args, **kwargs):
        for brochure in self.brochure_images.all():
            brochure.delete()

        if self.main_image and os.path.isfile(self.main_image.path):
            try:
                os.remove(self.main_image.path)
            except Exception as e:
                print(f"Failed to delete main image: {e}")

        property_folder = os.path.join(settings.MEDIA_ROOT, "appartment_images", str(self.property_id))
        try:
            if os.path.exists(property_folder):
                shutil.rmtree(property_folder)
        except Exception as e:
            print(f"Error deleting folder: {e}")

        super().delete(*args, **kwargs)

    def delete_main_image(self):
        if self.main_image and os.path.isfile(self.main_image.path):
            try:
                os.remove(self.main_image.path)
            except Exception as e:
                print(f"Failed to delete main image: {e}")
        self.main_image = None
        self.save()

    def __str__(self):
        return f"{self.address} ({self.property_id})"

def brochure_image_path(instance, filename):
    return f"appartment_images/{instance.apartment.property_id}/brochures/{filename}"

class BrochureImage(models.Model):
    apartment = models.ForeignKey(
        Apartment, related_name='brochure_images', on_delete=models.CASCADE
    )
    image = models.ImageField(upload_to=brochure_image_path, null=False, blank=False)

    def delete(self, *args, **kwargs):
        if self.image and os.path.isfile(self.image.path):
            try:
                os.remove(self.image.path)
            except Exception as e:
                print(f"Failed to delete brochure image: {e}")
        super().delete(*args, **kwargs)

    @classmethod
    def create_with_validation(cls, apartment, image):
        if apartment.brochure_images.count() >= 10:
            raise ValidationError("You can only upload up to 10 brochure images.")
        return cls.objects.create(apartment=apartment, image=image)

class SoldProperty(models.Model):
    apartment = models.OneToOneField(Apartment, on_delete=models.CASCADE)
    buyer_name = models.CharField(max_length=100)
    buyer_address = models.TextField()
    purchase_date = models.DateField()
    purchase_price = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.buyer_name} bought {self.apartment.address} on {self.purchase_date}"
