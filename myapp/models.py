from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import AbstractUser

class Navigation(models.Model):
    name=models.CharField(max_length=100,null=True,blank=True,unique=True)
    def __str__(self):
        return self.name

class Robot(models.Model):
    stock_id=models.CharField(null=True,blank=True,max_length=200)
    active_status=models.BooleanField(default=False)
    battery_status=models.CharField(null=True,blank=True,max_length=100)
    quality=models.CharField(null=True,blank=True,max_length=100)
    going_home=models.BooleanField(default=False)
    motor_brake_released=models.BooleanField(default=False)
    emergency_stop=models.BooleanField(default=False)
    charging=models.BooleanField(default=False)
    dockingStatus=models.CharField(max_length=200,null=True,blank=True)


class LastClickedNavigation(models.Model):
    navigation_id = models.IntegerField()
    navigation_name = models.CharField(max_length=255)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.navigation_name} (ID: {self.navigation_id})"
    
class BaseStatus(models.Model):
    status = models.BooleanField(default=False)
    last_updated = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Status: {self.status}, Updated: {self.last_updated}"


class FullTour(models.Model):
    full_tour_name=models.CharField(null=True,blank=True,max_length=200)
    navigations = models.JSONField(default=list)
    tour_date = models.DateField(null=True,blank=True)       # customer sets manually
    tour_time = models.TimeField(null=True,blank=True)       # customer sets manually

    def __str__(self):
        return f"Tour on {self.tour_date} at {self.tour_time}"

class PowerOn(models.Model):
    status = models.BooleanField(default=True) 

    def __str__(self):
        return f"PowerOn status: {self.status}"


class RebootStatus(models.Model):
    status = models.BooleanField(default=False)

    def __str__(self):
        return f"Reboot Status: {self.status}"
    

class IPAddress(models.Model):
    stock_id=models.CharField(null=True,blank=True,max_length=200)
    ip_address = models.CharField(max_length=255,null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)  # Timestamp when added

    def __str__(self):
        return f" {self.ip_address}"
    

class Sound(models.Model):
    value = models.CharField(
        max_length=151,
        default="60"
    )

    def __str__(self):
        return f"Sound Value: {self.value}"
    

class Speed(models.Model):
    value = models.CharField(
        max_length=10,
        default="0.1"
    )

    def __str__(self):
        return f"Sound Value: {self.value}"
    



class Charge(models.Model):
    low_battery_entry = models.IntegerField(default=0)
    back_to_home_entry = models.IntegerField(default=0)

    def __str__(self):
        return f"Low Battery: {self.low_battery_entry}, Back to Home: {self.back_to_home_entry}"
    

class RobotFile(models.Model):
    robot = models.ForeignKey(Robot, related_name='files', on_delete=models.CASCADE)
    zip_file = models.FileField(upload_to='robot_zips/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f" {self.zip_file.name}"
    

class Charging(models.Model):
    status = models.BooleanField(default=False)

    def __str__(self):
        return "Charging" if self.status else "Not Charging"
    

class NavigationCancel(models.Model):
    status = models.BooleanField(default=False)

    def __str__(self):
        return "Cancelled" if self.status else "Not Cancelled"
    

# py dev

class RefreshButton(models.Model):

    status = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.status}"
    

from django.db import models

class APICredential(models.Model):
    username = models.CharField(max_length=150)
    password = models.CharField(max_length=128)
    access_token = models.TextField()
    refresh_token = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.username} {self.access_token}"

class Scheduler(models.Model):
    scheduler_id = models.IntegerField(unique=True)
    scheduler_name = models.CharField(max_length=255)
    scheduler_date = models.DateTimeField()
    scheduler_time = models.TimeField()
    all_day = models.CharField(max_length=10)
    modified = models.CharField(max_length=10)
    notified = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.scheduler_name} on {self.scheduler_date} : {self.scheduler_time}"
    
class CustomerConnectionData(models.Model):
    customer_url = models.CharField(max_length=2048, unique=True)
    customer_id = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return f"{self.customer_url} for {self.customer_id}"

class GeneralNotification(models.Model):
    title = models.CharField(max_length=255)
    notification = models.CharField(max_length=10000)
    created_at = models.DateTimeField(auto_now_add=True)
    seen = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.notification} on {self.created_at} : {self.seen}"