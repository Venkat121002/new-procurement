
from django import forms
from .models import *
from django.forms import DateInput, DateTimeInput, TimeInput, CheckboxInput, Textarea, TextInput

from django import forms
from .models import Invite

class LoginForm(forms.Form):
    email=forms.CharField()
    password=forms.CharField()

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


class CustomerRegistrationsForm(GenericModelForm):
    class Meta:
        model = CustomerRegistrations
        exclude = ('company','rejection_reason','verified_by_admin','approved_by')

class ItemCategoryMasterForm(GenericModelForm):
    class Meta:
        model = ItemCategoryMaster
        exclude = ('company',)

class UnitOfMeasureForm(GenericModelForm):
    class Meta:
        model = UnitOfMeasure
        exclude = ('company',)

class SupplierForm(GenericModelForm):
    class Meta:
        model = Supplier
        exclude = ('company','verified_by_admin','rejection_reason','status')
        labels = {
            'supplier_name': 'Branch Name',
            'contact_person': 'Contact Person',
            'phone_number': 'Mobile Number',
            'email': 'Email Address',
            'address': 'Branch Address',
        }

class CountryMasterForm(GenericModelForm):
    class Meta:
        model = CountryMaster
        exclude = ('company',)

class LogisticsPartnerForm(GenericModelForm):
    class Meta:
        model = LogisticsPartner
        exclude = ('company',)

class BrandMasterForm(GenericModelForm):
    class Meta:
        model = BrandMaster
        exclude = ('company',)


class StoreTypeMasterForm(GenericModelForm):
    class Meta:
        model = StoreTypeMaster
        exclude = ('company',)

class CustomerstoreForm(GenericModelForm):
    class Meta:
        model = Customerstore
        exclude = ('company',)

class ItemSubCategoryMasterForm(GenericModelForm):
    class Meta:
        model = ItemSubCategoryMaster
        exclude = ('company',)
    
    def __init__(self, *args, **kwargs):
        company_id = kwargs.pop('company', None)   # get company from view
        super().__init__(*args, **kwargs)
    
        if company_id:
            print("company_id in form init:", company_id)
            
            self.fields['category'].queryset = ItemCategoryMaster.objects.filter(company_id=company_id)
            # self.fields['storetype'].queryset = StoreTypeMaster.objects.filter(company_id=company)

    
class SupplierCustomerMappingForm(GenericModelForm):
    class Meta:
        model = SupplierCustomerMapping
        exclude = ('company',)

    def __init__(self, *args, **kwargs):
        
        super(SupplierCustomerMappingForm, self).__init__(*args, **kwargs)
        # Filter only verified customers
        self.fields['customer'].queryset = CustomerRegistrations.objects.filter(verified_by_admin=True)
        self.fields['supplier'].queryset = Supplier.objects.filter(verified_by_admin=True)

class ManufacturerForm(GenericModelForm):
    class Meta:
        model = Manufacturer
        exclude = ('company',)

class SubCountryMasterForm(GenericModelForm):
    class Meta:
        model = SubCountryMaster
        exclude = ('company',)

class SupplierStoreForm(GenericModelForm):
    class Meta:
        model = SupplierStore
        exclude = ('company',)
        labels = {
            'supplier': 'Branch',
          
        }
    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)   # get company from view
        super().__init__(*args, **kwargs)

        if company:
            self.fields['supplier'].queryset = Supplier.objects.filter(company_id=company)
            self.fields['storetype'].queryset = StoreTypeMaster.objects.filter(company_id=company)


class ItemMasterForm(GenericModelForm):
    class Meta:
        model = ItemMaster
        exclude = ('company','barcode')
    # def __init__(self,*args,**kwargs):
    #     company = kwargs.pop('company', None)  
    #     super().__init__(*args, **kwargs)
    #     if company:
    #         self.fields['category'].queryset = ItemCategoryMaster.objects.filter(company_id=company)
    
    def __init__(self, *args, **kwargs):
        company_id = kwargs.pop('company', None)   
        super().__init__(*args, **kwargs)
    
        if company_id:
            print("company_id in form init:", company_id)
            
            self.fields['category'].queryset =  ItemCategoryMaster.objects.filter(company_id=company_id)
            self.fields['subcategory'].queryset =  ItemSubCategoryMaster.objects.filter(company_id=company_id)

class OrderRequestParentForm(GenericModelForm):
    class Meta:
        model = OrderRequestParent
        exclude = ('company',)

class StockTransferRouteMainForm(GenericModelForm):
    class Meta:
        model = StockTransferRouteMain
        exclude = ('company',)

class ItemUnitForm(GenericModelForm):
    class Meta:
        model = ItemUnit
        exclude = ('company','barcode_image','barcode_value')
    def __init__(self,*args,**kwargs):
        company = kwargs.pop('company', None)   # get company from view
        super().__init__(*args, **kwargs)
        if company: 
            self.fields['item'].queryset = ItemMaster.objects.filter(company_id=company)  
            self.fields['brand'].queryset = BrandMaster.objects.filter(company_id=company)
            self.fields['unit'].queryset = UnitOfMeasure.objects.filter(company_id=company)
        
class InvoiceForm(GenericModelForm):
    class Meta:
        model = Invoice
        exclude = ('company',)

class StockTransferParentForm(GenericModelForm):
    class Meta:
        model = StockTransferParent
        exclude = ('company',)

class StockTransferRouteSubForm(GenericModelForm):
    class Meta:
        model = StockTransferRouteSub
        exclude = ('company',)

class PackageSizeMasterForm(GenericModelForm):
    class Meta:
        model = PackageSizeMaster
        exclude = ('company',)
    
    def __init__(self, *args, **kwargs):
        company_id = kwargs.pop('company', None)   
        super().__init__(*args, **kwargs)
    
        if company_id:
            print("company_id in form init:", company_id)
            
            self.fields['itemunit'].queryset =  ItemUnit.objects.filter(company_id=company_id)
            self.fields['brand'].queryset =  BrandMaster.objects.filter(company_id=company_id)



class PackageAssignmentForm(GenericModelForm):
    class Meta:
        model = PackageAssignment
        exclude = ('company',)


class OrderRequestChildForm(GenericModelForm):
    class Meta:
        model = OrderRequestChild
        exclude = ('company',)



class StockTransferChildForm(GenericModelForm):
    class Meta:
        model = StockTransferChild
        exclude = ('company',)



class InviteForm(forms.ModelForm):
    email = forms.EmailField(
        max_length=255,
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter your email'})
    )

    class Meta:
        model = Invite
        fields = ['email']  # Only email field in the form






# class RoleForm(GenericModelForm):
#     class Meta:
#         model = Role
#         exclude = ('company',)

class ProductMasterForm(GenericModelForm):
    class Meta:
        model = ProductMaster
        exclude = ('company',)

class VendorForm(GenericModelForm):
    class Meta:
        model = Vendor
        exclude = ('company',)

class LogisticsVehicleForm(GenericModelForm):
    class Meta:
        model = LogisticsVehicle
        fields = ['partner', 'vehicle_number', 'transport_mode', 'capacity', 'is_active']

class MultiApproverForm(GenericModelForm):
    class Meta:
        model = MultiApprover
        fields = ['process', 'user', 'description']
       
    def __init__(self, *args, **kwargs):
        company_id = kwargs.pop('company', None)   
        super().__init__(*args, **kwargs)
    
        if company_id:
            print("company_id in form init:", company_id)
            
            # self.fields['process'].queryset =  Company.objects.filter(company_id=company_id)
            self.fields['user'].queryset =  User.objects.filter(company_id=company_id)
    