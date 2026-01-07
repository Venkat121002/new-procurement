from django import forms
from .models import *
from django.forms import DateInput, DateTimeInput, TimeInput, CheckboxInput, Textarea, TextInput

class GenericModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(GenericModelForm, self).__init__(*args, **kwargs)
        
        # Loop through each field in the form
        for field_name, field in self.fields.items():
            field_type = type(field)
            
            # Generic CSS class for all fields
            field.widget.attrs['class'] = 'form-control'

            # Custom widgets for specific field types
            if isinstance(field, forms.DateField):
                field.widget = DateInput(attrs={'class': 'form-control', 'type': 'date'})
            elif isinstance(field, forms.DateTimeField):
                field.widget = DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'})
            elif isinstance(field, forms.TimeField):
                field.widget = TimeInput(attrs={'class': 'form-control', 'type': 'time'})
            elif isinstance(field, forms.BooleanField):
                field.widget = CheckboxInput()
            elif isinstance(field, forms.CharField) and isinstance(field.widget, forms.Textarea):
                field.widget = Textarea(attrs={'class': 'form-control', 'rows': 3})
            elif isinstance(field, forms.CharField):
                field.widget = TextInput(attrs={'class': 'form-control'})

class UserRegistrationForm(GenericModelForm):
    # profile_image=forms.FileField(required=False)
    is_superadmin = forms.BooleanField(required=False, initial=False)
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email',"supplier",'phone_number', 'password','roles','user_type','is_admin','maker','checker')


    def __init__(self, *args, **kwargs):
        branch_id = kwargs.pop('branch', None)  # Get branch ID from kwargs
        is_superuser = kwargs.pop('is_superuser', False)  # Get superuser status
        super(UserRegistrationForm, self).__init__(*args, **kwargs)

        # Add Bootstrap 'form-control' class to fields
        # for field_name in self.fields:
        #     self.fields[field_name].widget.attrs.setdefault('class')

        # Set queryset for 'psp_type' based on user role
        if is_superuser:
            # self.fields['country_code'].queryset = CountryCode.objects.all()
            # self.fields['country'].queryset = Country.objects.all()
            # # self.fields['state'].queryset = State.objects.all()
            # self.fields['state'].queryset = State.objects.none()  # Initially empty
            self.fields['roles'].queryset = Role.objects.all()
        else:
            # self.fields['country_code'].queryset = CountryCode.objects.filter(branch_id=branch_id) if branch_id else CountryCode.objects.none()
            # self.fields['country'].queryset = Country.objects.filter(branch_id=branch_id) if branch_id else Country.objects.none()
            # self.fields['state'].queryset = State.objects.filter(branch_id=branch_id) if branch_id else State.objects.none()
            # self.fields['state'].queryset = State.objects.filter(branch_id=branch_id) if branch_id else State.objects.none() # Initially empty
            self.fields['roles'].queryset = Role.objects.all()

        # Set initial values only if queryset has data
        # self.initial['country_code'] = self.fields['country_code'].queryset.first() if self.fields['country_code'].queryset.exists() else None
        # self.initial['country'] = self.fields['country'].queryset.first() if self.fields['country'].queryset.exists() else None
        # self.initial['state'] = self.fields['state'].queryset.first() if self.fields['state'].queryset.exists() else None

        # Pre-fill fields when updating (if instance exists)
        # if self.instance and self.instance.pk:
            # self.initial['country_code'] = self.instance.country_code
            # self.initial['country'] = self.instance.country
            # self.initial['roles'] = self.instance.roles
            # self.initial['state'] = self.instance.state
            # self.fields['state'].queryset = State.objects.filter(country_id=self.instance.country,branch_id=branch_id)

        # self.fields['country_code'].required = True
        # self.fields['country'].required = True
        # self.fields['location'].required = True

class LoginForm(forms.Form):
    email=forms.EmailField()
    password=forms.CharField()

class RoleForm(GenericModelForm):
    class Meta:
        model = Role
        exclude = ('created_by','update_by','permissions')


class CompanyForm(forms.ModelForm):
    company_logo=forms.ImageField(required=False)
    application_logo=forms.ImageField(required=False)
    class Meta:
        model = Company
        exclude = ['created_by','update_by','company_api_id']
        
        widgets = {
            'end_of_financial_year': forms.DateTimeInput(attrs={'type': 'date'}),
            'end_of_month_date': forms.DateTimeInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        
        super(CompanyForm, self).__init__(*args, **kwargs)
        
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'

class BranchForm(forms.ModelForm):
    class Meta:
        model = Branch
        exclude = ('created_by', 'update_by', 'branch_api_id')

    def __init__(self, *args, **kwargs):
        super(BranchForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'

            # self.fields['company'].disabled=True
class BranchcompanyForm(forms.ModelForm):
    class Meta:
        model = Branch
        exclude = ('created_by','update_by','branch_api_id','company')
      
    def _init_(self, *args, **kwargs):
        super(BranchcompanyForm, self)._init_(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] ='form-control'


