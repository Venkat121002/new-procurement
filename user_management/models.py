from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import (
    AbstractBaseUser,
    PermissionsMixin,
    BaseUserManager,
)

import string
import random

# ================== mainsupply chain management company====================
class Company(models.Model):
    RoundAmt = [('1','1'),('2','2'),('3','3')]
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=255, blank=True, null=True)
    contact_number = models.PositiveBigIntegerField()
    email = models.EmailField(unique=True)
    country = models.CharField(max_length=100,blank=True, null=True)
    state = models.CharField(max_length=100,blank=True, null=True)    
    city = models.CharField(max_length=100,blank=True, null=True)
    company_logo = models.FileField(upload_to='user profile/', null=True, blank=True)
    local_currency = models.CharField(max_length=100,blank=True, null=True)
    incorporation_number = models.CharField(max_length=100,blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    number_of_branches = models.IntegerField()
    number_of_staffs = models.IntegerField()
    end_of_financial_year = models.DateField(blank=True,null=True)
    end_of_month_date = models.DateField(blank=True,null=True)
    amount_rounded_to = models.CharField(max_length=100,choices=RoundAmt,blank=True,null=True)
    company_api_id = models.CharField(max_length=100,blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey("User", on_delete=models.CASCADE, related_name="company_created_by",
                                   blank=True, null=True)
    update_by = models.ForeignKey("User", on_delete=models.CASCADE, related_name="company_update_by",
                                  blank=True, null=True)
    def __str__(self):
        return self.name


class Function(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='%(class)s_companies')
    function_name=models.CharField(max_length=100)
    function_id=models.CharField(max_length=100, unique=True,blank=True,null=True)
    description = models.TextField(max_length=800,blank=True, null=True)
    created_by = models.ForeignKey('User', on_delete=models.CASCADE,related_name="Function_created_by")
    created_at = models.DateTimeField(auto_now_add=True)
    update_by = models.ForeignKey('User', on_delete=models.CASCADE, blank=True, null=True,related_name="Function_update_by")
    update_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.function_name 

class Role(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='%(class)s_companies')
    name = models.CharField(max_length=200)
    description = models.TextField(max_length=800,blank=True, null=True)
    user_type = models.CharField(max_length=20,choices=[('Supplier', 'Supplier'),('Customer', 'Customer'), ('logistics', 'Logistics')],blank=True, null=True,)
    permissions = models.ManyToManyField(Function)
    created_by = models.ForeignKey('User', on_delete=models.CASCADE,related_name="Role_created_by")
    update_by = models.ForeignKey('User', on_delete=models.CASCADE, blank=True, null=True,related_name="Role_update_by")
    created_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)       
    def __str__(self):
        return self.name
    
class CustomUserManager(BaseUserManager):
    def create_superuser(self, email, password, **other_fields):
        other_fields.setdefault("is_staff", True)
        other_fields.setdefault("is_superuser", True)
        other_fields.setdefault("is_active", True)
        other_fields.setdefault("checker", True)
        return self.create_user(email, password, **other_fields)
    
    
    def create_user(self, email, password, **other_fields):
        if not email:
            raise ValueError(_("You must provide a valid email address"))

        email = self.normalize_email(email)
        user = self.model(email=email, **other_fields)
        user.set_password(password)
        user.save()
        return user
    
class User(AbstractBaseUser, PermissionsMixin):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='%(class)s_companies',blank=False, null=True)
    first_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(_("email address"), unique=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    password=models.CharField(max_length=100, blank=False, null=False)
    roles = models.ForeignKey(Role, on_delete=models.CASCADE, blank=True, null=True)
    user_type = models.CharField(max_length=20,choices=[('Supplier', 'Supplier'), ('Customer', 'Customer'), ('logistics', 'Logistics')],default="Supplier")
    supplier = models.ForeignKey('mainapp.Supplier',on_delete=models.CASCADE, related_name='%(class)s_supplier',blank=False, null=True)
    buyer_id = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    is_company_admin = models.BooleanField(default=False)
    maker = models.BooleanField(default=False)
    checker = models.BooleanField(default=False)
    objects = CustomUserManager()
    REQUIRED_FIELDS = ["first_name"]
    USERNAME_FIELD = "email"
    def __str__(self) -> str:
        return f"{self.first_name}{self.last_name}-{self.email}"
    

class UserSubscription(models.Model):
    company = models.ForeignKey("Company", on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    module = models.CharField(max_length=255)

    no_of_user_is_limited = models.BooleanField(default=False)
    no_of_user_value = models.IntegerField(null=True, blank=True)

    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.company.name} Subscription"
    

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user.first_name} - {self.message}"

class Currency(models.Model):
    currency_id = models.CharField(max_length=10, primary_key=True, editable=False)
    currency_code = models.CharField(max_length=10, unique=True)
    currency_name = models.CharField(max_length=100)
    symbol = models.CharField(max_length=10)
    reference_id =  models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)
    branch = models.ForeignKey("Branch",on_delete=models.CASCADE,related_name="Currency_branch",null=True, blank=True)
    
    def save(self, *args, **kwargs):
        if not self.currency_id:
            self.currency_id = self.generate_unique_currency_id()
        super().save(*args, **kwargs)

    def generate_unique_currency_id(self):
        length = 10
        chars = string.ascii_uppercase + string.digits  # You can customize the charset if needed
        while True:
            new_id = ''.join(random.choices(chars, k=length))
            if not Currency.objects.filter(currency_id=new_id).exists():  # Ensure uniqueness
                return new_id
    def __str__(self):
        return self.currency_code


class Feedback_Reasons(models.Model):
    reason = models.CharField(max_length=255)

    def __str__(self):
            return self.reason
    
class Feedback(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE , null=True, blank=True )
    endpoint = models.CharField(max_length=255 , null=True, blank=True )
    name = models.CharField(max_length=255 , null=True, blank=True )
    feedback = models.TextField( null=True, blank=True)
    reason = models.ForeignKey(Feedback_Reasons, on_delete=models.CASCADE , null=True, blank=True , related_name="feedback_reason" )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback for {self.user.first_name} - {self.feedback}"

# Distributor branches
class Branch(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='branches_on',blank=True,null=True,)
    # customer = models.ForeignKey('mainapp.CustomerRegistrations',on_delete=models.CASCADE,blank=True, null=True)
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=255)
    phone_number = models.PositiveBigIntegerField()
    manager_name = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    state = models.CharField(max_length=100)    
    city = models.CharField(max_length=100)
    local_currency = models.CharField(max_length=100,blank=False, null=False)
    description = models.TextField()
    branch_api_id = models.CharField(max_length=100,blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey("User", on_delete=models.CASCADE, related_name="branch_created_by",
                                   blank=True, null=True)
    update_by = models.ForeignKey("User", on_delete=models.CASCADE, related_name="branch_update_by",
                                blank=True, null=True)


    def _str_(self):
        return f"{self.name} - {self.company.name}"



