from django import forms
from .models import *
from django.forms import DateInput, DateTimeInput, TimeInput, CheckboxInput, Textarea, TextInput
from user_management.models import Role

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


class UserSupplierCommonForm(forms.Form):
    # User Fields
    first_name = forms.CharField(
        label="First Name",
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter first name'})
    )
    last_name = forms.CharField(
        label="Last Name",
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter last name'})
    )
    email = forms.EmailField(
        label="Email Address",
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter email'})
    )
    phone_number = forms.CharField(
        label="Phone Number",
        max_length=15,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter phone number'})
    )
    password = forms.CharField(
        label="Password",
        required=True,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter password'})
    )

    is_staff = forms.BooleanField(
        label="Is Staff",
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    is_active = forms.BooleanField(
        label="Is Active",
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    is_admin = forms.BooleanField(
        label="Is Admin",
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    # SupplierUser Fields
    role = forms.ModelChoiceField(
        label="Role",
        queryset=Role.objects.none(),
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    supplierstore = forms.ModelMultipleChoiceField(
        label="Supplier Store",
        queryset=SupplierStore.objects.none(),
        required=True,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'})
    )

    def __init__(self, *args, **kwargs):
        # Get dynamic queryset if passed
        role_queryset = kwargs.pop('role_queryset', None)
        supplierstore_queryset = kwargs.pop('supplierstore_queryset', None)

        super(UserSupplierCommonForm, self).__init__(*args, **kwargs)

        # Set dynamic querysets
        if role_queryset is not None:
            self.fields['role'].queryset = role_queryset
        if supplierstore_queryset is not None:
            self.fields['supplierstore'].queryset = supplierstore_queryset


class ManualStockAdjustmentForm(GenericModelForm):
    class Meta:
        model = ManualStockAdjustment
        exclude = ('company',)

class SupplierOrderMainForm(GenericModelForm):
    class Meta:
        model = SupplierOrderMain
        fields = ['vendor', 'expected_delivery','po_number']

        widgets = {
            'vendor': forms.Select(attrs={'class': 'form-control', 'style': 'color: black !important;'}),
            'expected_delivery': forms.DateInput(attrs={'class': 'form-control', 'style': 'color: black !important;'}, format='%Y-%m-%d'),
           
        }
from django import forms
from .models import SupplierOrderItemSub

class SupplierOrderItemSubForm(GenericModelForm):
    class Meta:
        model = SupplierOrderItemSub
        fields = [
          
            "supplier",
            "supplierstore",
            "order",
            "item_unit",
            "package_size",
            "ordertype",
            "quantity",
            "unit_price",
            "total_price",
            "tax",
            "discount",
            "discount_type",
        ]
        widgets = {
            "ordertype": forms.Select(attrs={"class": "form-control"}),
            "discount_type": forms.Select(attrs={"class": "form-control"}),
            "quantity": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
            "unit_price": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "total_price": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "tax": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "discount": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
        }



class SupplierInventoryWastageForm(GenericModelForm):
    class Meta:
        model = SupplierInventoryWastage
        fields = ['reason','wastage_type', 'wastage_qty', 'remarks']

class FileUploadForm(forms.Form):
    file = forms.FileField()

class SupplierRoleForm(GenericModelForm):
    class Meta:
        model = SupplierRole
        fields = ['name', 'description']

class SupplierInvoiceForm(GenericModelForm):
    class Meta:
        model = SupplierInvoice
    
        exclude = ['company','supplier','store_to','po_number','GRN_number','invoice']
        widgets = {
            'received_date': forms.DateInput(attrs={'type': 'date'}),
        }

