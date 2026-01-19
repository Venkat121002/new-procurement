
from django.shortcuts import render, redirect
from django.db.models.functions import TruncMonth
from django.db.models import Sum, F, FloatField
from django.db.models import Avg

from SupplierPortal.forms import ManualStockAdjustmentForm
from .forms import *
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from bb_id_gen_app.scripts import generate_id
from django.contrib.auth.decorators import login_required
from user_management.models import *
from django.shortcuts import get_object_or_404
from user_management.decorators import company_session_required, check_permission
from django.http import JsonResponse
from django.contrib.auth.hashers import make_password
from django.core.mail import send_mail
from django.conf import settings
from .forms import InviteForm
from SupplierPortal.models import *

import re
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import NotFound
import json
from user_management.serializers import *
from .api_call import *
PACKAGE_URL='http://127.0.0.1:8501/'


def user_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password')
            user = authenticate(request, email=email, password=password)
            
            if user is not None:
                login(request, user)
          
                request.session['user_name']=user.first_name
                request.session['is_superuser'] = user.is_superuser
                request.session['is_admin'] = user.is_admin
                request.session['user_type']=user.user_type
                users = User.objects.get(id = user.id)

                buyer_id = user.buyer_id
                print('buyter id--',buyer_id)
                request.session['buyer_id'] = buyer_id
    
                # ================ Super Admin =================
                if user.is_superuser:
                    records=Function.objects.all()
                    permission_id_list = [data.function_name for data in records]
                    request.session['permission']=permission_id_list
                    return redirect('select_company') 
                
                elif user.is_company_admin:
                    if user.company is not None:
                        records = Function.objects.all()
                        permission_id_list = [data.function_name for data in records]
                        request.session['permission'] = permission_id_list

                        # ---- Package Check (ROISOUK) ----
                        package_data = json.dumps({'buyer_id': buyer_id})
                        package_check = call_post_method_for_without_token(
                            PACKAGE_URL, 'package_check/', package_data
                        )
                        print('package status code---',package_check.status_code)
                        if package_check.status_code in [200, 201]:
                            print('dddddddd',package_check.json())
                            message = package_check.json().get('message')
                            print("messss",message)
                            alert_message = Notification.objects.create(
                                user = request.user,
                                message = message
                            )
                            print('alert_message',alert_message)
                            alert_message.save()
                            request.session['company'] = user.company.pk if user.company else None
                            return redirect('dashboard')
                        elif package_check.status_code == 400:
                            return render(request, "pack_expried.html")
                        else:
                            print('else working')
                            messages.error(request, "Unexpected error occurred")
                            return redirect("login")

                # # ================ supplier users =================
                
                elif user.user_type == 'Supplier' and not user.is_company_admin:
                    request.session['company'] = user.company.pk if user.company else None
                    
                    if users.is_admin:
                        # ---- Package Check (ROISOUK) ----
                        package_data = json.dumps({'buyer_id': buyer_id})
                        package_check = call_post_method_for_without_token(
                            PACKAGE_URL, 'package_check/', package_data
                        )
                        print('package status code---',package_check.status_code)
                        if package_check.status_code in [200, 201]:
                            print('dddddddd',package_check.json())
                            return redirect('select_supplier_store',pk=users.id)  # pk is a user id
                    else:
                        supplieruser = SupplierUser.objects.get(user_id = user.id)
                        role_obj =Role.objects.filter(pk=supplieruser.role.id, company_id=user.company.pk).first()
                        
                        if role_obj:
                            permission_records = role_obj.permissions.all()
                            permission_id_list = [data.function_name for data in permission_records]
                            request.session['permission'] = permission_id_list
                        else:
                            request.session['permission'] = []

                        #=========== need to check howmany stores access this user have ==================
                        getstores = supplieruser.store.all()
                        if getstores.count() > 1:
                            # ---- Package Check (ROISOUK) ----
                            package_data = json.dumps({'buyer_id': buyer_id})
                            package_check = call_post_method_for_without_token(
                                PACKAGE_URL, 'package_check/', package_data
                            )
                            print('package status code---',package_check.status_code)
                            if package_check.status_code in [200, 201]:
                                print('dddddddd',package_check.json())
                                return redirect('select_supplier_store',pk=user.id)  # pk is a user id
                        else:
                            getstores1 = getstores.first()
                            request.session['supplier_store_id'] = getstores1.id
                            # ---- Package Check (ROISOUK) ----
                            package_data = json.dumps({'buyer_id': buyer_id})
                            package_check = call_post_method_for_without_token(
                                PACKAGE_URL, 'package_check/', package_data
                            )
                            print('package status code---',package_check.status_code)
                            if package_check.status_code in [200, 201]:
                                print('dddddddd',package_check.json())
                                return redirect('dashboard')

                else:
                    if user.roles is not None:
                        # request.session['company']=None
                        role_obj = Role.objects.get(pk=user.roles.id,company_id=user.company.pk)
                        permission_records = role_obj.permissions.all()
                        permission_id_list = [data.function_name for data in permission_records]
                   
                        request.session['permission']=permission_id_list
                        request.session['company'] = user.company.pk if user.company.pk else None

                    else:
                        # request.session['company']=None
                        request.session['company'] = user.company.pk if user.company.pk else None
                        request.session['permission']=[]
                    # ---- Package Check (ROISOUK) ----
                    package_data = json.dumps({'buyer_id': buyer_id})
                    package_check = call_post_method_for_without_token(
                        PACKAGE_URL, 'package_check/', package_data
                    )
                    print('package status code---',package_check.status_code)
                    if package_check.status_code in [200, 201]:
                        print('dddddddd',package_check.json())
                    
                        return redirect('dashboard')
                
            

            else:
                print('Invalid email or password')
                form.add_error(None, 'Invalid email or password')
        else:
            print('form', form.errors)
    else:
        form = LoginForm()

    context = {
        'form': form
    }
    return render(request, 'Auth/login.html', context)



class CompanyCreateAPIView(APIView):
    def post(self, request, format=None):
        print('the request data is ', request.data)
        data = request.data.copy()

        # Separate company and user data from request
        company_data = data.get('company', {})
        user_data = data.get('user', {})

        print('company_data---', company_data)
        print('user_data---', user_data)

        password = "1234"

        # ================= Currency Logic (LOCAL ONLY) =================
        currency, created = Currency.objects.get_or_create(
            currency_name=company_data.get('curreny_name'),
            currency_code=company_data.get('curreny_code'),
            symbol=company_data.get('currency_symbol'),
        )

        # Use local currency_code as reference_id
        reference_id = currency.currency_code

        # Save reference_id locally
        currency.reference_id = reference_id
        currency.save()

        # ================= Company Creation =================
        currency_pk = currency.currency_id

        company_data['company_api_id'] = company_data.get('company_id')
        company_data['name'] = company_data.get('name')
        company_data['contact_number'] = company_data.get('contact_number')
        company_data['local_currency'] = currency_pk

        company_serializer = CompanySerializer(data=company_data)

        print('company_dataaa---', company_data)
        print('company_serializer---', company_serializer.is_valid())
        print('company_serializer_errors---', company_serializer.errors)

        if company_serializer.is_valid():
            company = company_serializer.save()
            company.reference_id = reference_id
            company.save()

            company_id = Company.objects.get(company_api_id=company_data.get('company_id')).pk
            print('company_id---', company_id)

            # ================= User Creation =================
            if user_data:
                user_data['company'] = company_id
                user_data['username'] = user_data.get('email')
                user_data['password'] = password
                user_data['is_company_admin'] = True

                user_serializer = UserSerializer(data=user_data)
                print('user_serializer---', user_serializer.is_valid())
                print('user_serializer_errors---', user_serializer.errors)

                if user_serializer.is_valid():
                    user = user_serializer.save()
                    print("user---",user)
                    user.set_password(user.password)
                    user.save()
                    print("user after set password---",user)

                    print('company and user created successfully')
                    return Response(
                        {
                            'company': company_serializer.data,
                            'user': user_serializer.data
                        },
                        status=status.HTTP_201_CREATED
                    )
                    
                else:
                    # Rollback company if user fails
                    company.delete()
                    print('aaaaaaaaaaaaaaaa')
                    return Response(
                        {'user_errors': user_serializer.errors},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                    
            print('company created successfully')
            return Response(company_serializer.data, status=status.HTTP_201_CREATED)
            
        print('cccccccccccccc')
        return Response(company_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        


class UserSubscriptionAPIView(APIView):
    def post(self, request, *args, **kwargs):
        company_id = request.data.get('company')
        
        # Check if company exists (if company_id is valid)
        try:
            company = Company.objects.get(company_api_id=company_id)
            print('company---',company)
        except Company.DoesNotExist:
            raise NotFound("Company not found.")
        print('========company.pk---',company.pk)
        # Check if UserSubscription already exists for this company
        subscription, created = UserSubscription.objects.update_or_create(
            company_id=company.pk,
            defaults={
                'start_date': request.data.get('start_date'),
                'end_date': request.data.get('end_date'),
                'module': request.data.get('module'),
                'no_of_user_is_limited': request.data.get('no_of_user_is_limited', False),
                'no_of_user_value': request.data.get('no_of_user_value'),
                'is_active': request.data.get('is_active', True),
            }
        )
        
        # Serialize and return response
        serializer = UserSubscriptionSerializer(subscription)
        print('created---',created)
        print('serializer.data---',serializer.data)
        if created:
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.data, status=status.HTTP_200_OK)

def response_message(status, message=None, record_id=None):
    message = {
        'status': status,
        'message': message,
        'record_id': record_id
    }
    return message

class NotifyExpiredview(APIView):
    def get(self, request, *args, **kwargs):
        try:
            records = Notification.objects.all()
            serializer = NotificationSerializer(records, many=True)
            return Response(data=serializer.data, status=status.HTTP_200_OK)
        except Exception as error:
            message = response_message('Failed', message=f"{error}")
            return Response(data=message, status=status.HTTP_400_BAD_REQUEST)
        
    def post(self, request, *args, **kwargs):
        data=request.data.copy()
        print('===data====',data)
        try:
            user=User.objects.get(email=data.get('email'))
            print('user====',user)
            data['user']=user.id
            data['message']=data.get('messages')
            serializer = NotificationSerializer(data=data)
            if serializer.is_valid():
                obj = serializer.save()
                message = response_message('Success', message="Its Success", record_id=obj.pk)
                return Response(data=message, status=status.HTTP_201_CREATED)
            print('serializer.errors===',serializer.errors )
            return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as error:
            print('eeeeeeeeeeeeeeeeeeeeeeeeeeee',str(error))
            message = response_message('Failed', message=f"{error}")
            return Response(data=message, status=status.HTTP_400_BAD_REQUEST)


@company_session_required
def overall_setupscreen(request):
    try:
        supplier_screens = ['StockOrder','StockReceive','StockReturn','Invoice','Payment','InventoryTrack','Report','StockTransfer']
        distributor_screen = ['PurchaseOrder','POApproval','StockEntry','ReturnToSupplier','Invoice','Payment','InventoryTrack','Report','StockTransfer']
        if request.method == "POST":
            for data in supplier_screens:
                SupplierFunction.objects.create(
                    company_id = request.company,
                    function_name = data,
                    function_id = f'{data}',
                    description = data,
                )
            for data in distributor_screen:
                DistributorFunction.objects.create(
                    company_id = request.company,
                    function_name = data,
                    function_id = f'{data}',
                    description = data,
                )
                
            return redirect("dashboard")

        return render(request,'overall_setupscreen.html')
    except Exception as error:
        return render(request, '500.html', {'error': error})
    
def dashboard(request):
    
    user_details = User.objects.get(id = request.user.id)

    if request.user.is_admin or request.user.is_company_admin or request.user.is_superuser: 

        return redirect('admin_dashboard')
        # base_template = 'AdminPortal/base.html'
    elif user_details.user_type == 'Supplier':

        return redirect('supplierdashboard')

        # base_template = 'SupplierPortal/supplier_base.html'

    else:

        return redirect('customer_dashboard')

        # base_template = 'CustomerPortal/customer_base.html'

    return render(request, 'dashboard.html', {'dashboard': 'active', 'base_template': base_template})

def user_logout(request):
    if request.user.is_authenticated:
        logout(request)
        return redirect('user_login')
    else:
        return redirect('user_login')

# Create
@company_session_required
@login_required(login_url='/')
@check_permission('customerregistrations_create')
def customerregistrations_create(request):
    """
    Handles the creation of a new CustomerRegistrations record.

    - If the request method is POST, the form data is validated and, if valid, the new record is saved.
    - If the request method is GET, an empty form is displayed.
    - Upon successful creation, redirects to the list view.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        
        company = Company.objects.get(id=request.company)
        if request.method == "POST":
            form = CustomerRegistrationsForm(request.POST)
            if form.is_valid():
                obj = form.save(commit=False)
                obj.company_id=company.id
                obj.save()
                  # Save the form data as a new record
                return redirect('customerregistrations_list')
        else:
            form = CustomerRegistrationsForm()  # Display an empty form
        context = {
            'form': form, 'screen_name': 'Distributor Registrations'
        }
        return render(request, 'AdminPortal/create.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Read - List View
@company_session_required
@login_required(login_url='/')
@check_permission('customerregistrations_view')
def customerregistrations_list(request):
    """
    Displays a list of all CustomerRegistrations records.

    - Fetches all records from the CustomerRegistrations model.
    - Passes the records to the template for rendering.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        
        company = Company.objects.get(id=request.company)
        records = CustomerRegistrations.objects.filter(company_id=company.id)
        print("ssdsjdjsd",records)
        context = {
            'records': records, 'screen_name': 'Distributor List'
        }
        return render(request, 'AdminPortal/customerregistrations_list.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})


# Read - Detail View
@company_session_required
@login_required(login_url='/')
@check_permission('customerregistrations_view')
def customerregistrations_detail(request, pk):
    """
    Displays the details of a specific CustomerRegistrations record.

    - Fetches the record based on the primary key (pk).
    - Passes the record to the form for viewing.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        
        company = Company.objects.get(id=request.company)
        record = get_object_or_404(CustomerRegistrations, pk=pk,company_id=company.id)
        form = CustomerRegistrationsForm(instance=record)
        context = {
            'screen_name': 'Distributor Registrations', 'view': True, 'form': form
        }
        return render(request, 'AdminPortal/create.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Update
@company_session_required
@login_required(login_url='/')
def customerregistrations_update(request, pk):
    """
    Handles the updating of an existing CustomerRegistrations record.

    - If the request method is POST, the form data is validated and, if valid, the record is updated.
    - If the request method is GET, the existing record is displayed in the form.
    - Upon successful update, redirects to the list view.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        
        company = Company.objects.get(id=request.company)
        customerregistrations = get_object_or_404(CustomerRegistrations, pk=pk,company_id=company.id)
        if request.method == "POST":
            form = CustomerRegistrationsForm(request.POST, instance=customerregistrations)
            if form.is_valid():
                obj = form.save(commit=False)

                obj.company_id=company.id
                obj.save()  # Save the updated record
                return redirect('customerregistrations_list')
        else:
            form = CustomerRegistrationsForm(instance=customerregistrations)  # Display the existing record in the form
        context = {
            'form': form, 'screen_name': 'Distributor Registrations'
        }
        return render(request, 'AdminPortal/create.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Delete
@company_session_required
@login_required(login_url='/')
@check_permission('customerregistrations_delete')
def customerregistrations_delete(request, pk):
    """
    Handles the deletion of an existing CustomerRegistrations record.
    - Fetches the record based on the primary key (pk).
    - Deletes the record from the database.
    - Upon successful deletion, redirects to the list view.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        
        company = Company.objects.get(id=request.company)
        record = get_object_or_404(CustomerRegistrations, pk=pk,company_id=company.id)
        record.delete()  # Delete the record
        return redirect('customerregistrations_list')
    except Exception as error:
        return render(request, '500.html', {'error': error})
# Create
@company_session_required
@login_required(login_url='/')
@check_permission('itemcategorymaster_create')
def itemcategorymaster_create(request):
    """
    Handles the creation of a new ItemCategoryMaster record.

    - If the request method is POST, the form data is validated and, if valid, the new record is saved.
    - If the request method is GET, an empty form is displayed.
    - Upon successful creation, redirects to the list view.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        
        company = Company.objects.get(id=request.company)
        if request.method == "POST":
            form = ItemCategoryMasterForm(request.POST)
            if form.is_valid():
                obj = form.save(commit=False)

                obj.company_id=company.id
                obj.save()
                  # Save the form data as a new record
                return redirect('itemcategorymaster_list')
        else:
            form = ItemCategoryMasterForm()  # Display an empty form
        context = {
            'form': form, 'screen_name': 'ItemCategoryMaster'
        }
        return render(request, 'AdminPortal/create.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Read - List View
@company_session_required
@login_required(login_url='/')
# @check_permission('itemcategorymaster_view')
def itemcategorymaster_list(request):
    """
    Displays a list of all ItemCategoryMaster records.

    - Fetches all records from the ItemCategoryMaster model.
    - Passes the records to the template for rendering.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        
        company = Company.objects.get(id=request.company)
        records = ItemCategoryMaster.objects.filter(company_id=company.id)
        context = {
            'records': records, 'screen_name': 'ItemCategoryMaster'
        }
        return render(request, 'AdminPortal/itemcategorymaster_list.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Read - Detail View
@company_session_required
@login_required(login_url='/')
@check_permission('itemcategorymaster_view')
def itemcategorymaster_detail(request, pk):
    """
    Displays the details of a specific ItemCategoryMaster record.

    - Fetches the record based on the primary key (pk).
    - Passes the record to the form for viewing.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        
        company = Company.objects.get(id=request.company)
        record = get_object_or_404(ItemCategoryMaster, pk=pk,company_id=company.id)
        form = ItemCategoryMasterForm(instance=record)
        context = {
            'screen_name': 'ItemCategoryMaster', 'view': True, 'form': form
        }
        return render(request, 'AdminPortal/create.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Update
@company_session_required
@login_required(login_url='/')
@check_permission('itemcategorymaster_update')
def itemcategorymaster_update(request, pk):
    """
    Handles the updating of an existing ItemCategoryMaster record.

    - If the request method is POST, the form data is validated and, if valid, the record is updated.
    - If the request method is GET, the existing record is displayed in the form.
    - Upon successful update, redirects to the list view.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        
        company = Company.objects.get(id=request.company)
        itemcategorymaster = get_object_or_404(ItemCategoryMaster, pk=pk,company_id=company.id)
        if request.method == "POST":
            form = ItemCategoryMasterForm(request.POST, instance=itemcategorymaster)
            if form.is_valid():
                obj = form.save(commit=False)

                obj.company_id=company.id
                obj.save()  # Save the updated record
                return redirect('itemcategorymaster_list')
        else:
            form = ItemCategoryMasterForm(instance=itemcategorymaster)  # Display the existing record in the form
        context = {
            'form': form, 'screen_name': 'ItemCategoryMaster'
        }
        return render(request, 'AdminPortal/create.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Delete
@company_session_required
@login_required(login_url='/')
@check_permission('itemcategorymaster_delete')
def itemcategorymaster_delete(request, pk):
    """
    Handles the deletion of an existing ItemCategoryMaster record.

    - Fetches the record based on the primary key (pk).
    - Deletes the record from the database.
    - Upon successful deletion, redirects to the list view.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        
        company = Company.objects.get(id=request.company)
        record = get_object_or_404(ItemCategoryMaster, pk=pk,company_id=company.id)
        record.delete()  # Delete the record
        return redirect('itemcategorymaster_list')
    except Exception as error:
        return render(request, '500.html', {'error': error})
# Create
@company_session_required
@login_required(login_url='/')
@check_permission('unitofmeasure_create')
def unitofmeasure_create(request):
    """
    Handles the creation of a new UnitOfMeasure record.

    - If the request method is POST, the form data is validated and, if valid, the new record is saved.
    - If the request method is GET, an empty form is displayed.
    - Upon successful creation, redirects to the list view.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        
        company = Company.objects.get(id=request.company)
        if request.method == "POST":
            form = UnitOfMeasureForm(request.POST)
            if form.is_valid():
                obj = form.save(commit=False)

                obj.company_id=company.id
                obj.save()
                  # Save the form data as a new record
                return redirect('unitofmeasure_list')
        else:
            form = UnitOfMeasureForm()  # Display an empty form
        context = {
            'form': form, 'screen_name': 'UnitOfMeasure'
        }
        return render(request, 'AdminPortal/create.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Read - List View
@company_session_required
@login_required(login_url='/')
@check_permission('unitofmeasure_view')
def unitofmeasure_list(request):
    """
    Displays a list of all UnitOfMeasure records.

    - Fetches all records from the UnitOfMeasure model.
    - Passes the records to the template for rendering.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        
        company = Company.objects.get(id=request.company)
        records = UnitOfMeasure.objects.filter(company_id=company.id)
        context = {
            'records': records, 'screen_name': 'UnitOfMeasure'
        }
        return render(request, 'AdminPortal/unitofmeasure_list.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Read - Detail View
@company_session_required
@login_required(login_url='/')
@check_permission('unitofmeasure_view')
def unitofmeasure_detail(request, pk):
    """
    Displays the details of a specific UnitOfMeasure record.

    - Fetches the record based on the primary key (pk).
    - Passes the record to the form for viewing.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        
        company = Company.objects.get(id=request.company)
        record = get_object_or_404(UnitOfMeasure, pk=pk,company_id=company.id)
        form = UnitOfMeasureForm(instance=record)
        context = {
            'screen_name': 'UnitOfMeasure', 'view': True, 'form': form
        }
        return render(request, 'AdminPortal/create.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Update
@company_session_required
@login_required(login_url='/')
@check_permission('unitofmeasure_update')
def unitofmeasure_update(request, pk):
    """
    Handles the updating of an existing UnitOfMeasure record.

    - If the request method is POST, the form data is validated and, if valid, the record is updated.
    - If the request method is GET, the existing record is displayed in the form.
    - Upon successful update, redirects to the list view.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        
        company = Company.objects.get(id=request.company)
        unitofmeasure = get_object_or_404(UnitOfMeasure, pk=pk,company_id=company.id)
        if request.method == "POST":
            form = UnitOfMeasureForm(request.POST, instance=unitofmeasure)
            if form.is_valid():
                obj = form.save(commit=False)

                obj.company_id=company.id
                obj.save()  # Save the updated record
                return redirect('unitofmeasure_list')
        else:
            form = UnitOfMeasureForm(instance=unitofmeasure)  # Display the existing record in the form
        context = {
            'form': form, 'screen_name': 'UnitOfMeasure'
        }
        return render(request, 'AdminPortal/create.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Delete
@company_session_required
@login_required(login_url='/')
@check_permission('unitofmeasure_delete')
def unitofmeasure_delete(request, pk):
    try:
        
        company = Company.objects.get(id=request.company)
        record = get_object_or_404(UnitOfMeasure, pk=pk,company_id=company.id)
        record.delete()  # Delete the record
        return redirect('unitofmeasure_list')
    except Exception as error:
        return render(request, '500.html', {'error': error})
    
# Create
@company_session_required
@login_required(login_url='/')
# @check_permission('supplier_create')
def supplier_create(request):
    try:
    
        company = Company.objects.get(id=request.company)
        if request.method == "POST":
            form = SupplierForm(request.POST)
            if form.is_valid():
              
                obj = form.save(commit=False)
                obj.company_id=company.id
                obj.save()
                  # Save the form data as a new record
                return redirect('supplier_list')
        else:
            form = SupplierForm()  # Display an empty form
        context = {
            'form': form, 'screen_name':'Register Branch'
        }
        return render(request, 'AdminPortal/create.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})


def invite(request):
    try:

        form=InviteForm()
        if request.method == "POST":
            form = InviteForm(request.POST)
            if form.is_valid():
                obj=form.save(commit=False)
                email = obj.email # Extract email from form
                print("Form Data:", form.cleaned_data)  # Debugging
                # Email Content
                subject = "Welcome to Our Service"
                message = "http://127.0.0.1:9001/customerregistrations/new"
                from_email = "deepakrajagopal55@gmail.com"  # Update with your sender email
                recipient_list = [email]  # Convert email to list
                # Send Email
                send_mail(subject, message, from_email, recipient_list)
                messages.success(request, "Registration form  sent to your mail successfully!")
                return redirect('invite')
        return render(request, 'invite.html',{'form':form})      
    except Exception as error:
        return render(request, '500.html', {'error': error})




# Read - List View
@company_session_required
@login_required(login_url='/')
# @check_permission('supplier_view')
def supplier_list(request):
    """
    Displays a list of all Supplier records.

    - Fetches all records from the Supplier model.
    - Passes the records to the template for rendering.
    - In case of an error, renders a custom 500 error page.
    """
    try:
    
        company = Company.objects.get(id=request.company)
        records = Supplier.objects.filter(company_id=company.id)
        context = {
            'records': records, 'screen_name': 'Branch'
        }
        return render(request, 'AdminPortal/supplier_list.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Read - Detail View
@company_session_required
@login_required(login_url='/')
@check_permission('supplier_view')
def supplier_detail(request, pk):
    """
    Displays the details of a specific Supplier record.

    - Fetches the record based on the primary key (pk).
    - Passes the record to the form for viewing.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        
        company = Company.objects.get(id=request.company)
        record = get_object_or_404(Supplier, pk=pk,company_id=company.id)
        form = SupplierForm(instance=record)
        context = {
            'screen_name': 'Branch', 'view': True, 'form': form
        }
        return render(request, 'create.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Update
@company_session_required
@login_required(login_url='/')
@check_permission('supplier_update')
def supplier_update(request, pk):
    """
    Handles the updating of an existing Supplier record.

    - If the request method is POST, the form data is validated and, if valid, the record is updated.
    - If the request method is GET, the existing record is displayed in the form.
    - Upon successful update, redirects to the list view.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        
        company = Company.objects.get(id=request.company)
        supplier = get_object_or_404(Supplier, pk=pk,company_id=company.id)
        if request.method == "POST":
            form = SupplierForm(request.POST, instance=supplier)
            if form.is_valid():
                obj = form.save(commit=False)

                obj.company_id=company.id
                obj.save()  # Save the updated record
                return redirect('supplier_list')
        else:
            form = SupplierForm(instance=supplier)  # Display the existing record in the form
        context = {
            'form': form, 'screen_name': 'Branch'
        }
        return render(request, 'create.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Delete
@company_session_required
@login_required(login_url='/')
@check_permission('supplier_delete')
def supplier_delete(request, pk):
    """
    Handles the deletion of an existing Supplier record.

    - Fetches the record based on the primary key (pk).
    - Deletes the record from the database.
    - Upon successful deletion, redirects to the list view.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        
        company = Company.objects.get(id=request.company)
        record = get_object_or_404(Supplier, pk=pk,company_id=company.id)
        record.delete()  # Delete the record
        return redirect('supplier_list')
    except Exception as error:
        return render(request, '500.html', {'error': error})
# Create
@company_session_required
@login_required(login_url='/')
@check_permission('countrymaster_create')
def countrymaster_create(request):
    """
    Handles the creation of a new CountryMaster record.

    - If the request method is POST, the form data is validated and, if valid, the new record is saved.
    - If the request method is GET, an empty form is displayed.
    - Upon successful creation, redirects to the list view.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        
        company = Company.objects.get(id=request.company)
        if request.method == "POST":
            form = CountryMasterForm(request.POST)
            if form.is_valid():
                obj = form.save(commit=False)

                obj.company_id=company.id
                obj.save()
                  # Save the form data as a new record
                return redirect('countrymaster_list')
        else:
            form = CountryMasterForm()  # Display an empty form
        context = {
            'form': form, 'screen_name': 'CountryMaster'
        }
        return render(request, 'AdminPortal/create.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Read - List View
@company_session_required
@login_required(login_url='/')
@check_permission('countrymaster_view')
def countrymaster_list(request):
    """
    Displays a list of all CountryMaster records.

    - Fetches all records from the CountryMaster model.
    - Passes the records to the template for rendering.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        
        company = Company.objects.get(id=request.company)
        records = CountryMaster.objects.filter(company_id=company.id)
        context = {
            'records': records, 'screen_name': 'CountryMaster'
        }
        return render(request, 'AdminPortal/countrymaster_list.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Read - Detail View
@company_session_required
@login_required(login_url='/')
@check_permission('countrymaster_view')
def countrymaster_detail(request, pk):
    """
    Displays the details of a specific CountryMaster record.

    - Fetches the record based on the primary key (pk).
    - Passes the record to the form for viewing.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        
        company = Company.objects.get(id=request.company)
        record = get_object_or_404(CountryMaster, pk=pk,company_id=company.id)
        form = CountryMasterForm(instance=record)
        context = {
            'screen_name': 'CountryMaster', 'view': True, 'form': form
        }
        return render(request, 'AdminPortal/create.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Update
@company_session_required
@login_required(login_url='/')
@check_permission('countrymaster_update')
def countrymaster_update(request, pk):
    """
    Handles the updating of an existing CountryMaster record.
    - If the request method is POST, the form data is validated and, if valid, the record is updated.
    - If the request method is GET, the existing record is displayed in the form.
    - Upon successful update, redirects to the list view.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        
        company = Company.objects.get(id=request.company)
        countrymaster = get_object_or_404(CountryMaster, pk=pk,company_id=company.id)
        if request.method == "POST":
            form = CountryMasterForm(request.POST, instance=countrymaster)
            if form.is_valid():
                obj = form.save(commit=False)

                obj.company_id=company.id
                obj.save()  # Save the updated record
                return redirect('countrymaster_list')
        else:
            form = CountryMasterForm(instance=countrymaster)  # Display the existing record in the form
        context = {
            'form': form, 'screen_name': 'CountryMaster'
        }
        return render(request, 'AdminPortal/create.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Delete
@company_session_required
@login_required(login_url='/')
@check_permission('countrymaster_delete')
def countrymaster_delete(request, pk):
    """
    Handles the deletion of an existing CountryMaster record.

    - Fetches the record based on the primary key (pk).
    - Deletes the record from the database.
    - Upon successful deletion, redirects to the list view.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        
        company = Company.objects.get(id=request.company)
        record = get_object_or_404(CountryMaster, pk=pk,company_id=company.id)
        record.delete()  # Delete the record
        return redirect('countrymaster_list')
    except Exception as error:
        return render(request, '500.html', {'error': error})
# Create
@company_session_required
@login_required(login_url='/')
@check_permission('logisticspartner_create')
def logisticspartner_create(request):
    """
    Handles the creation of a new LogisticsPartner record.

    - If the request method is POST, the form data is validated and, if valid, the new record is saved.
    - If the request method is GET, an empty form is displayed.
    - Upon successful creation, redirects to the list view.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        
        company = Company.objects.get(id=request.company)
        if request.method == "POST":
            form = LogisticsPartnerForm(request.POST)
            if form.is_valid():
                obj = form.save(commit=False)

                obj.company_id=company.id
                obj.save()
                  # Save the form data as a new record
                return redirect('logisticspartner_list')
        else:
            form = LogisticsPartnerForm()  # Display an empty form
        context = {
            'form': form, 'screen_name': 'LogisticsPartner'
        }
        return render(request, 'AdminPortal/create.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Read - List View
@company_session_required
@login_required(login_url='/')
@check_permission('logisticspartner_view')
def logisticspartner_list(request):
    try: 
        company = Company.objects.get(id=request.company)
        records = LogisticsPartner.objects.filter(company_id=company.id)
        context = {
            'records': records, 'screen_name': 'LogisticsPartner'
        }
        return render(request, 'AdminPortal/logisticspartner_list.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Read - Detail View
@company_session_required
@login_required(login_url='/')
@check_permission('logisticspartner_view')
def logisticspartner_detail(request, pk):
    """
    Displays the details of a specific LogisticsPartner record.

    - Fetches the record based on the primary key (pk).
    - Passes the record to the form for viewing.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        
        company = Company.objects.get(id=request.company)
        record = get_object_or_404(LogisticsPartner, pk=pk,company_id=company.id)
        form = LogisticsPartnerForm(instance=record)
        context = {
            'screen_name': 'LogisticsPartner', 'view': True, 'form': form
        }
        return render(request, 'AdminPortal/create.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Update
@company_session_required
@login_required(login_url='/')
@check_permission('logisticspartner_update')
def logisticspartner_update(request, pk):
    """
    Handles the updating of an existing LogisticsPartner record.

    - If the request method is POST, the form data is validated and, if valid, the record is updated.
    - If the request method is GET, the existing record is displayed in the form.
    - Upon successful update, redirects to the list view.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        
        company = Company.objects.get(id=request.company)
        logisticspartner = get_object_or_404(LogisticsPartner, pk=pk,company_id=company.id)
        if request.method == "POST":
            form = LogisticsPartnerForm(request.POST, instance=logisticspartner)
            if form.is_valid():
                obj = form.save(commit=False)

                obj.company_id=company.id
                obj.save()  # Save the updated record
                return redirect('logisticspartner_list')
        else:
            form = LogisticsPartnerForm(instance=logisticspartner)  # Display the existing record in the form
        context = {
            'form': form, 'screen_name': 'LogisticsPartner'
        }
        return render(request, 'AdminPortal/create.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Delete
@company_session_required
@login_required(login_url='/')
@check_permission('logisticspartner_delete')
def logisticspartner_delete(request, pk):
    """
    Handles the deletion of an existing LogisticsPartner record.

    - Fetches the record based on the primary key (pk).
    - Deletes the record from the database.
    - Upon successful deletion, redirects to the list view.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        
        company = Company.objects.get(id=request.company)
        record = get_object_or_404(LogisticsPartner, pk=pk,company_id=company.id)
        record.delete()  # Delete the record
        return redirect('logisticspartner_list')
    except Exception as error:
        return render(request, '500.html', {'error': error})
# Create
@company_session_required
@login_required(login_url='/')
@check_permission('brandmaster_create')
def brandmaster_create(request):

    company_id = request.company
    """
    Handles the creation of a new BrandMaster record.

    - If the request method is POST, the form data is validated and, if valid, the new record is saved.
    - If the request method is GET, an empty form is displayed.
    - Upon successful creation, redirects to the list view.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        
        if request.method == "POST":
            form = BrandMasterForm(request.POST)
            if form.is_valid():
                obj = form.save(commit=False)
                obj.company_id=company_id
                obj.save()
                  # Save the form data as a new record
                return redirect('brandmaster_list')
        else:
            form = BrandMasterForm()  # Display an empty form
        context = {
            'form': form, 'screen_name': 'BrandMaster'
        }
        return render(request, 'AdminPortal/create.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Read - List View
@company_session_required
@login_required(login_url='/')
@check_permission('brandmaster_view')
def brandmaster_list(request):
    """
    Displays a list of all BrandMaster records.

    - Fetches all records from the BrandMaster model.
    - Passes the records to the template for rendering.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        records = BrandMaster.objects.filter(company_id=company.id)
        context = {
            'records': records, 'screen_name': 'BrandMaster'
        }
        return render(request, 'AdminPortal/brandmaster_list.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Read - Detail View
@company_session_required
@login_required(login_url='/')
@check_permission('brandmaster_view')
def brandmaster_detail(request, pk):
    """
    Displays the details of a specific BrandMaster record.

    - Fetches the record based on the primary key (pk).
    - Passes the record to the form for viewing.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        record = get_object_or_404(BrandMaster, pk=pk,company_id=company.id)
        form = BrandMasterForm(instance=record)
        context = {
            'screen_name': 'BrandMaster', 'view': True, 'form': form
        }
        return render(request, 'AdminPortal/create.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Update
@company_session_required
@login_required(login_url='/')
@check_permission('brandmaster_update')
def brandmaster_update(request, pk):
    """
    Handles the updating of an existing BrandMaster record.

    - If the request method is POST, the form data is validated and, if valid, the record is updated.
    - If the request method is GET, the existing record is displayed in the form.
    - Upon successful update, redirects to the list view.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        brandmaster = get_object_or_404(BrandMaster, pk=pk,company_id=company.id)
        if request.method == "POST":
            form = BrandMasterForm(request.POST, instance=brandmaster)
            if form.is_valid():
                obj = form.save(commit=False)

                obj.company_id=company.id
                obj.save()  # Save the updated record
                return redirect('brandmaster_list')
        else:
            form = BrandMasterForm(instance=brandmaster)  # Display the existing record in the form
        context = {
            'form': form, 'screen_name': 'BrandMaster'
        }
        return render(request, 'AdminPortal/create.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Delete
@company_session_required
@login_required(login_url='/')
@check_permission('brandmaster_delete')
def brandmaster_delete(request, pk):
    """
    Handles the deletion of an existing BrandMaster record.

    - Fetches the record based on the primary key (pk).
    - Deletes the record from the database.
    - Upon successful deletion, redirects to the list view.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        record = get_object_or_404(BrandMaster, pk=pk,company_id=company.id)
        record.delete()  # Delete the record
        return redirect('brandmaster_list')
    except Exception as error:
        return render(request, '500.html', {'error': error})
# Create
@company_session_required
@login_required(login_url='/')
@check_permission('storetypemaster_create')
def storetypemaster_create(request):
    """
    Handles the creation of a new StoreTypeMaster record.

    - If the request method is POST, the form data is validated and, if valid, the new record is saved.
    - If the request method is GET, an empty form is displayed.
    - Upon successful creation, redirects to the list view.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        if request.method == "POST":
            form = StoreTypeMasterForm(request.POST)
            if form.is_valid():
                obj = form.save(commit=False)

                obj.company_id=company.id
                obj.save()
                  # Save the form data as a new record
                return redirect('storetypemaster_list')
        else:
            form = StoreTypeMasterForm()  # Display an empty form
        context = {
            'form': form, 'screen_name': 'StoreTypeMaster'
        }
        return render(request, 'AdminPortal/create.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Read - List View
@company_session_required
@login_required(login_url='/')
@check_permission('storetypemaster_view')
def storetypemaster_list(request):
    """
    Displays a list of all StoreTypeMaster records.

    - Fetches all records from the StoreTypeMaster model.
    - Passes the records to the template for rendering.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        records = StoreTypeMaster.objects.filter(company_id=company.id)
        context = {
            'records': records, 'screen_name': 'StoreTypeMaster'
        }
        return render(request, 'AdminPortal/storetypemaster_list.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Read - Detail View
@company_session_required
@login_required(login_url='/')
@check_permission('storetypemaster_view')
def storetypemaster_detail(request, pk):
    """
    Displays the details of a specific StoreTypeMaster record.

    - Fetches the record based on the primary key (pk).
    - Passes the record to the form for viewing.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        record = get_object_or_404(StoreTypeMaster, pk=pk,company_id=company.id)
        form = StoreTypeMasterForm(instance=record)
        context = {
            'screen_name': 'StoreTypeMaster', 'view': True, 'form': form
        }
        return render(request, 'AdminPortal/create.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Update
@company_session_required
@login_required(login_url='/')
@check_permission('storetypemaster_update')
def storetypemaster_update(request, pk):
    """
    Handles the updating of an existing StoreTypeMaster record.

    - If the request method is POST, the form data is validated and, if valid, the record is updated.
    - If the request method is GET, the existing record is displayed in the form.
    - Upon successful update, redirects to the list view.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        storetypemaster = get_object_or_404(StoreTypeMaster, pk=pk,company_id=company.id)
        if request.method == "POST":
            form = StoreTypeMasterForm(request.POST, instance=storetypemaster)
            if form.is_valid():
                obj = form.save(commit=False)

                obj.company_id=company.id
                obj.save()  # Save the updated record
                return redirect('storetypemaster_list')
        else:
            form = StoreTypeMasterForm(instance=storetypemaster)  # Display the existing record in the form
        context = {
            'form': form, 'screen_name': 'StoreTypeMaster'
        }
        return render(request, 'AdminPortal/create.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Delete
@company_session_required
@login_required(login_url='/')
@check_permission('storetypemaster_delete')
def storetypemaster_delete(request, pk):
    """
    Handles the deletion of an existing StoreTypeMaster record.

    - Fetches the record based on the primary key (pk).
    - Deletes the record from the database.
    - Upon successful deletion, redirects to the list view.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        record = get_object_or_404(StoreTypeMaster, pk=pk,company_id=company.id)
        record.delete()  # Delete the record
        return redirect('storetypemaster_list')
    except Exception as error:
        return render(request, '500.html', {'error': error})
# Create
@company_session_required
@login_required(login_url='/')
def customerstore_create(request):
    """
    Handles the creation of a new Customerstore record without using Django Forms.

    - If POST, manually extract and save data.
    - If GET, render the empty form page.
    - On success, redirect to list view.
    - On error, render a 500 error page.
    """
    # try:
    company = Company.objects.get(id=request.company)
    distributor=Customerstore.objects.filter(company_id=request.company)

    customer_register=CustomerRegistrations.objects.all()
    branches = DistributorBranch.objects.all()
    branch_data = {}
    for branch in branches:
        customer_id = str(branch.customer.id)
        if customer_id not in branch_data:
            branch_data[customer_id] = []
        branch_data[customer_id].append({
            'id': branch.id,
            'name': branch.name
        })
    

    if request.method == "POST":
            name = request.POST.get('name')
            branch = request.POST.get('branch')
            purchase = request.POST.get('purchase_access') == 'on'
            print('ss-------------->',branch)
            customer = request.POST.get('customer')
            print('customer',customer)
         
            phone_number = request.POST.get('phone_number')
        
            manager_name = request.POST.get('manager_name')
            city = request.POST.get('city')
          
            country = request.POST.get('country')
            description = request.POST.get('description')
            print('company',request.company)
          
            Customerstore.objects.create(
                customer_id=customer,
                company_id=request.company,
                branch_id=branch,
                name=name,
                contact_number=phone_number,
                manager_name=manager_name,
                location=city,
                description=description,
                purchase_access=purchase,
            )

            return redirect('customerstore_list')
        
        # For GET method
    return render(request, 'customerstore_create.html', {'distributor': distributor,'customer_register':customer_register,'branch_data': branch_data})

    # except Exception as error:
    #     return render(request, '500.html', {'error': error})


# Read - List View
@company_session_required
@login_required(login_url='/')

def customerstore_list(request):
    """
    Displays a list of all Customerstore records.

    - Fetches all records from the Customerstore model.
    - Passes the records to the template for rendering.
    - In case of an error, renders a custom 500 error page.
    """
    try:
    
        company = Company.objects.get(id=request.company)
        records = Customerstore.objects.filter(company_id=company.id)
        context = {
            'records': records, 'screen_name': 'Customerstore'
        }
        return render(request, 'AdminPortal/customerstore_list.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Read - Detail View
@company_session_required
@login_required(login_url='/')

def customerstore_detail(request, pk):
    """
    Displays the details of a specific Customerstore record.

    - Fetches the record based on the primary key (pk).
    - Passes the record to the form for viewing.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        record = get_object_or_404(Customerstore, pk=pk,company_id=company.id)
        form = CustomerstoreForm(instance=record)
        context = {
            'screen_name': 'Customerstore', 'view': True, 'form': form
        }
        return render(request, 'AdminPortal/create.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Update
@company_session_required
@login_required(login_url='/')

def customerstore_update(request, pk):
    """
    Handles the updating of an existing Customerstore record.

    - If the request method is POST, the form data is validated and, if valid, the record is updated.
    - If the request method is GET, the existing record is displayed in the form.
    - Upon successful update, redirects to the list view.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        customerstore = get_object_or_404(Customerstore, pk=pk,company_id=company.id)
        if request.method == "POST":
            form = CustomerstoreForm(request.POST, instance=customerstore)
            if form.is_valid():
                obj = form.save(commit=False)

                obj.company_id=company.id
                obj.save()  # Save the updated record
                return redirect('customerstore_list')
        else:
            form = CustomerstoreForm(instance=customerstore)  # Display the existing record in the form
        context = {
            'form': form, 'screen_name': 'Customerstore'
        }
        return render(request, 'AdminPortal/create.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Delete
@company_session_required
@login_required(login_url='/')
def customerstore_delete(request, pk):
    """
    Handles the deletion of an existing Customerstore record.

    - Fetches the record based on the primary key (pk).
    - Deletes the record from the database.
    - Upon successful deletion, redirects to the list view.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        record = get_object_or_404(Customerstore, pk=pk,company_id=company.id)
        record.delete()  # Delete the record
        return redirect('customerstore_list')
    except Exception as error:
        return render(request, '500.html', {'error': error})
    
# Create
@company_session_required
@login_required(login_url='/')
@check_permission('itemsubcategorymaster_create')
def itemsubcategorymaster_create(request):
    """
    Handles the creation of a new ItemSubCategoryMaster record.

    - If the request method is POST, the form data is validated and, if valid, the new record is saved.
    - If the request method is GET, an empty form is displayed.
    - Upon successful creation, redirects to the list view.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        if request.method == "POST":
            form = ItemSubCategoryMasterForm(request.POST)
            if form.is_valid():
                obj = form.save(commit=False)

                obj.company_id=company.id
                obj.save()
                  # Save the form data as a new record
                return redirect('itemsubcategorymaster_list')
        else:
            form = ItemSubCategoryMasterForm()  # Display an empty form
        context = {
            'form': form, 'screen_name': 'ItemSubCategoryMaster'
        }
        return render(request, 'AdminPortal/create.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Read - List View
@company_session_required
@login_required(login_url='/')
@check_permission('itemsubcategorymaster_view')
def itemsubcategorymaster_list(request):
    """
    Displays a list of all ItemSubCategoryMaster records.

    - Fetches all records from the ItemSubCategoryMaster model.
    - Passes the records to the template for rendering.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        records = ItemSubCategoryMaster.objects.filter(company_id=company.id)
        context = {
            'records': records, 'screen_name': 'ItemSubCategoryMaster'
        }
        return render(request, 'AdminPortal/itemsubcategorymaster_list.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Read - Detail View
@company_session_required
@login_required(login_url='/')
@check_permission('itemsubcategorymaster_view')
def itemsubcategorymaster_detail(request, pk):
    """
    Displays the details of a specific ItemSubCategoryMaster record.

    - Fetches the record based on the primary key (pk).
    - Passes the record to the form for viewing.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        record = get_object_or_404(ItemSubCategoryMaster, pk=pk,company_id=company.id)
        form = ItemSubCategoryMasterForm(instance=record)
        context = {
            'screen_name': 'ItemSubCategoryMaster', 'view': True, 'form': form
        }
        return render(request, 'AdminPortal/create.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Update
@company_session_required
@login_required(login_url='/')
@check_permission('itemsubcategorymaster_update')
def itemsubcategorymaster_update(request, pk):
    """
    Handles the updating of an existing ItemSubCategoryMaster record.

    - If the request method is POST, the form data is validated and, if valid, the record is updated.
    - If the request method is GET, the existing record is displayed in the form.
    - Upon successful update, redirects to the list view.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        itemsubcategorymaster = get_object_or_404(ItemSubCategoryMaster, pk=pk,company_id=company.id)
        if request.method == "POST":
            form = ItemSubCategoryMasterForm(request.POST, instance=itemsubcategorymaster)
            if form.is_valid():
                obj = form.save(commit=False)

                obj.company_id=company.id
                obj.save()  # Save the updated record
                return redirect('itemsubcategorymaster_list')
        else:
            form = ItemSubCategoryMasterForm(instance=itemsubcategorymaster)  # Display the existing record in the form
        context = {
            'form': form, 'screen_name': 'ItemSubCategoryMaster'
        }
        return render(request, 'AdminPortal/create.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Delete
@company_session_required
@login_required(login_url='/')
@check_permission('itemsubcategorymaster_delete')
def itemsubcategorymaster_delete(request, pk):
    """
    Handles the deletion of an existing ItemSubCategoryMaster record.

    - Fetches the record based on the primary key (pk).
    - Deletes the record from the database.
    - Upon successful deletion, redirects to the list view.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        record = get_object_or_404(ItemSubCategoryMaster, pk=pk,company_id=company.id)
        record.delete()  # Delete the record
        return redirect('itemsubcategorymaster_list')
    except Exception as error:
        return render(request, '500.html', {'error': error})
# Create
@company_session_required
@login_required(login_url='/')
@check_permission('suppliercustomermapping_create')
def suppliercustomermapping_create(request):
    """
    Handles the creation of a new SupplierCustomerMapping record.

    - If the request method is POST, the form data is validated and, if valid, the new record is saved.
    - If the request method is GET, an empty form is displayed.
    - Upon successful creation, redirects to the list view.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        if request.method == "POST":
            form = SupplierCustomerMappingForm(request.POST)
            if form.is_valid():
                obj = form.save(commit=False)

                obj.company_id=company.id
                obj.save()
                  # Save the form data as a new record
                return redirect('suppliercustomermapping_list')
        else:
            form = SupplierCustomerMappingForm()  # Display an empty form
        context = {
            'form': form, 'screen_name': 'SupplierCustomerMapping'
        }
        return render(request, 'AdminPortal/create.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Read - List View
@company_session_required
@login_required(login_url='/')
@check_permission('suppliercustomermapping_view')
def suppliercustomermapping_list(request):
    """
    Displays a list of all SupplierCustomerMapping records.

    - Fetches all records from the SupplierCustomerMapping model.
    - Passes the records to the template for rendering.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        records = SupplierCustomerMapping.objects.filter(company_id=company.id)
        context = {
            'records': records, 'screen_name': 'Customer-Supplier View'
        }
        return render(request, 'AdminPortal/suppliercustomermapping_list.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Read - Detail View
@company_session_required
@login_required(login_url='/')
@check_permission('suppliercustomermapping_view')
def suppliercustomermapping_detail(request, pk):
    """
    Displays the details of a specific SupplierCustomerMapping record.

    - Fetches the record based on the primary key (pk).
    - Passes the record to the form for viewing.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        record = get_object_or_404(SupplierCustomerMapping, pk=pk,company_id=company.id)
        form = SupplierCustomerMappingForm(instance=record)
        context = {
            'screen_name': 'SupplierCustomerMapping', 'view': True, 'form': form
        }
        return render(request, 'AdminPortal/create.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Update
@company_session_required
@login_required(login_url='/')
@check_permission('suppliercustomermapping_update')
def suppliercustomermapping_update(request, pk):
    """
    Handles the updating of an existing SupplierCustomerMapping record.

    - If the request method is POST, the form data is validated and, if valid, the record is updated.
    - If the request method is GET, the existing record is displayed in the form.
    - Upon successful update, redirects to the list view.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        suppliercustomermapping = get_object_or_404(SupplierCustomerMapping, pk=pk,company_id=company.id)
        if request.method == "POST":
            form = SupplierCustomerMappingForm(request.POST, instance=suppliercustomermapping)
            if form.is_valid():
                obj = form.save(commit=False)

                obj.company_id=company.id
                obj.save()  # Save the updated record
                return redirect('suppliercustomermapping_list')
        else:
            form = SupplierCustomerMappingForm(instance=suppliercustomermapping)  # Display the existing record in the form
        context = {
            'form': form, 'screen_name': 'SupplierCustomerMapping'
        }
        return render(request, 'AdminPortal/create.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Delete
@company_session_required
@login_required(login_url='/')
@check_permission('suppliercustomermapping_delete')
def suppliercustomermapping_delete(request, pk):
    """
    Handles the deletion of an existing SupplierCustomerMapping record.

    - Fetches the record based on the primary key (pk).
    - Deletes the record from the database.
    - Upon successful deletion, redirects to the list view.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        record = get_object_or_404(SupplierCustomerMapping, pk=pk,company_id=company.id)
        record.delete()  # Delete the record
        return redirect('suppliercustomermapping_list')
    except Exception as error:
        return render(request, '500.html', {'error': error})
# Create
@company_session_required
@login_required(login_url='/')
@check_permission('manufacturer_create')
def manufacturer_create(request):
    """
    Handles the creation of a new Manufacturer record.

    - If the request method is POST, the form data is validated and, if valid, the new record is saved.
    - If the request method is GET, an empty form is displayed.
    - Upon successful creation, redirects to the list view.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        if request.method == "POST":
            form = ManufacturerForm(request.POST)
            if form.is_valid():
                obj = form.save(commit=False)

                obj.company_id=company.id
                obj.save()
                  # Save the form data as a new record
                return redirect('manufacturer_list')
        else:
            form = ManufacturerForm()  # Display an empty form
        context = {
            'form': form, 'screen_name': 'Manufacturer'
        }
        return render(request, 'AdminPortal/create.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Read - List View
@company_session_required
@login_required(login_url='/')
@check_permission('manufacturer_view')
def manufacturer_list(request):
    """
    Displays a list of all Manufacturer records.

    - Fetches all records from the Manufacturer model.
    - Passes the records to the template for rendering.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        records = Manufacturer.objects.filter(company_id=company.id)
        context = {
            'records': records, 'screen_name': 'Manufacturer'
        }
        return render(request, 'AdminPortal/manufacturer_list.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Read - Detail View
@company_session_required
@login_required(login_url='/')
@check_permission('manufacturer_view')
def manufacturer_detail(request, pk):
    """
    Displays the details of a specific Manufacturer record.

    - Fetches the record based on the primary key (pk).
    - Passes the record to the form for viewing.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        record = get_object_or_404(Manufacturer, pk=pk,company_id=company.id)
        form = ManufacturerForm(instance=record)
        context = {
            'screen_name': 'Manufacturer', 'view': True, 'form': form
        }
        return render(request, 'AdminPortal/create.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Update
@company_session_required
@login_required(login_url='/')
@check_permission('manufacturer_update')
def manufacturer_update(request, pk):
    """
    Handles the updating of an existing Manufacturer record.

    - If the request method is POST, the form data is validated and, if valid, the record is updated.
    - If the request method is GET, the existing record is displayed in the form.
    - Upon successful update, redirects to the list view.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        manufacturer = get_object_or_404(Manufacturer, pk=pk,company_id=company.id)
        if request.method == "POST":
            form = ManufacturerForm(request.POST, instance=manufacturer)
            if form.is_valid():
                obj = form.save(commit=False)

                obj.company_id=company.id
                obj.save()  # Save the updated record
                return redirect('manufacturer_list')
        else:
            form = ManufacturerForm(instance=manufacturer)  # Display the existing record in the form
        context = {
            'form': form, 'screen_name': 'Manufacturer'
        }
        return render(request, 'AdminPortal/create.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Delete
@company_session_required
@login_required(login_url='/')
@check_permission('manufacturer_delete')
def manufacturer_delete(request, pk):
    """
    Handles the deletion of an existing Manufacturer record.

    - Fetches the record based on the primary key (pk).
    - Deletes the record from the database.
    - Upon successful deletion, redirects to the list view.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        record = get_object_or_404(Manufacturer, pk=pk,company_id=company.id)
        record.delete()  # Delete the record
        return redirect('manufacturer_list')
    except Exception as error:
        return render(request, '500.html', {'error': error})
# Create
@company_session_required
@login_required(login_url='/')
@check_permission('subcountrymaster_create')
def subcountrymaster_create(request):
    """
    Handles the creation of a new SubCountryMaster record.

    - If the request method is POST, the form data is validated and, if valid, the new record is saved.
    - If the request method is GET, an empty form is displayed.
    - Upon successful creation, redirects to the list view.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        if request.method == "POST":
            form = SubCountryMasterForm(request.POST)
            if form.is_valid():
                obj = form.save(commit=False)

                obj.company_id=company.id
                obj.save()
                  # Save the form data as a new record
                return redirect('subcountrymaster_list')
        else:
            form = SubCountryMasterForm()  # Display an empty form
        context = {
            'form': form, 'screen_name': 'SubCountryMaster'
        }
        return render(request, 'AdminPortal/create.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Read - List View
@company_session_required
@login_required(login_url='/')
@check_permission('subcountrymaster_view')
def subcountrymaster_list(request):
    """
    Displays a list of all SubCountryMaster records.

    - Fetches all records from the SubCountryMaster model.
    - Passes the records to the template for rendering.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        records = SubCountryMaster.objects.filter(company_id=company.id)
        context = {
            'records': records, 'screen_name': 'SubCountryMaster'
        }
        return render(request, 'AdminPortal/subcountrymaster_list.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Read - Detail View
@company_session_required
@login_required(login_url='/')
@check_permission('subcountrymaster_view')
def subcountrymaster_detail(request, pk):
    """
    Displays the details of a specific SubCountryMaster record.

    - Fetches the record based on the primary key (pk).
    - Passes the record to the form for viewing.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        record = get_object_or_404(SubCountryMaster, pk=pk,company_id=company.id)
        form = SubCountryMasterForm(instance=record)
        context = {
            'screen_name': 'SubCountryMaster', 'view': True, 'form': form
        }
        return render(request, 'AdminPortal/create.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Update
@company_session_required
@login_required(login_url='/')
@check_permission('subcountrymaster_update')
def subcountrymaster_update(request, pk):
    """
    Handles the updating of an existing SubCountryMaster record.

    - If the request method is POST, the form data is validated and, if valid, the record is updated.
    - If the request method is GET, the existing record is displayed in the form.
    - Upon successful update, redirects to the list view.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        subcountrymaster = get_object_or_404(SubCountryMaster, pk=pk,company_id=company.id)
        if request.method == "POST":
            form = SubCountryMasterForm(request.POST, instance=subcountrymaster)
            if form.is_valid():
                obj = form.save(commit=False)

                obj.company_id=company.id
                obj.save()  # Save the updated record
                return redirect('subcountrymaster_list')
        else:
            form = SubCountryMasterForm(instance=subcountrymaster)  # Display the existing record in the form
        context = {
            'form': form, 'screen_name': 'SubCountryMaster'
        }
        return render(request, 'AdminPortal/create.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Delete
@company_session_required
@login_required(login_url='/')
@check_permission('subcountrymaster_delete')
def subcountrymaster_delete(request, pk):
    """
    Handles the deletion of an existing SubCountryMaster record.

    - Fetches the record based on the primary key (pk).
    - Deletes the record from the database.
    - Upon successful deletion, redirects to the list view.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        record = get_object_or_404(SubCountryMaster, pk=pk,company_id=company.id)
        record.delete()  # Delete the record
        return redirect('subcountrymaster_list')
    except Exception as error:
        return render(request, '500.html', {'error': error})
# Create
@company_session_required
@login_required(login_url='/')
@check_permission('supplierstore_create')
def supplierstore_create(request):
    """
    Handles the creation of a new SupplierStore record.

    - If the request method is POST, the form data is validated and, if valid, the new record is saved.
    - If the request method is GET, an empty form is displayed.
    - Upon successful creation, redirects to the list view.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        print('company----',company)
        if request.method == "POST":
            form = SupplierStoreForm(request.POST,company = company.id)
            print('form---',form)
            if form.is_valid():
                obj = form.save(commit=False)

                obj.company_id=company.id
                obj.save()
                  # Save the form data as a new record
                return redirect('supplierstore_list')
        else:
            form = SupplierStoreForm(company = company.id)  # Display an empty form
        context = {
            'form': form, 'screen_name': 'Branch Store','Portal': 'Supplier'
        }
        return render(request, 'AdminPortal/create.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Read - List View
@company_session_required
@login_required(login_url='/')
def supplierstore_list(request):
    """
    Displays a list of all SupplierStore records.

    - Fetches all records from the SupplierStore model.
    - Passes the records to the template for rendering.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        records = SupplierStore.objects.filter(company_id=company.id)
        context = {
            'records': records, 'screen_name': 'Branch Store'
        }
        return render(request, 'AdminPortal/supplierstore_list.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Read - Detail View
@company_session_required
@login_required(login_url='/')
@check_permission('supplierstore_view')
def supplierstore_detail(request, pk):
    """
    Displays the details of a specific SupplierStore record.

    - Fetches the record based on the primary key (pk).
    - Passes the record to the form for viewing.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        record = get_object_or_404(SupplierStore, pk=pk,company_id=company.id)
        form = SupplierStoreForm(instance=record,company = company.id)
        context = {
            'screen_name': 'Branch Store', 'view': True, 'form': form
        }
        return render(request, 'AdminPortal/create.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Update
@company_session_required
@login_required(login_url='/')
@check_permission('supplierstore_update')
def supplierstore_update(request, pk):
    """
    Handles the updating of an existing SupplierStore record.

    - If the request method is POST, the form data is validated and, if valid, the record is updated.
    - If the request method is GET, the existing record is displayed in the form.
    - Upon successful update, redirects to the list view.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        supplierstore = get_object_or_404(SupplierStore, pk=pk,company_id=company.id)
        if request.method == "POST":
            form = SupplierStoreForm(request.POST, instance=supplierstore,company = company.id)
            if form.is_valid():
                obj = form.save(commit=False)

                obj.company_id=company.id
                obj.save()  # Save the updated record
                return redirect('supplierstore_list')
        else:
            form = SupplierStoreForm(instance=supplierstore,company = company.id)  # Display the existing record in the form
        context = {
            'form': form, 'screen_name': 'branch Store'
        }
        return render(request, 'AdminPortal/create.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Delete
@company_session_required
@login_required(login_url='/')
@check_permission('supplierstore_delete')
def supplierstore_delete(request, pk):
    """
    Handles the deletion of an existing SupplierStore record.

    - Fetches the record based on the primary key (pk).
    - Deletes the record from the database.
    - Upon successful deletion, redirects to the list view.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        record = get_object_or_404(SupplierStore, pk=pk,company_id=company.id)
        record.delete()  # Delete the record
        return redirect('supplierstore_list')
    except Exception as error:
        return render(request, '500.html', {'error': error})
# Create
@company_session_required
@login_required(login_url='/')
@check_permission('itemmaster_create')
def itemmaster_create(request):
    """
    Handles the creation of a new ItemMaster record.

    - If the request method is POST, the form data is validated and, if valid, the new record is saved.
    - If the request method is GET, an empty form is displayed.
    - Upon successful creation, redirects to the list view.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        if request.method == "POST":
            form = ItemMasterForm(request.POST,company = company.id)
            if form.is_valid():
                obj = form.save(commit=False)

                obj.company_id=company.id
                obj.save()
                  # Save the form data as a new record
                return redirect('itemmaster_list')
        else:
            form = ItemMasterForm(request.POST,company = company.id)
            form = ItemMasterForm()  # Display an empty form
        context = {
            'form': form, 'screen_name': 'ItemMaster'
        }
        return render(request, 'AdminPortal/create.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Read - List View
@company_session_required
@login_required(login_url='/')
@check_permission('itemmaster_view')
def itemmaster_list(request):
    """
    Displays a list of all ItemMaster records.

    - Fetches all records from the ItemMaster model.
    - Passes the records to the template for rendering.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        records = ItemMaster.objects.filter(company_id=company.id)
        context = {
            'records': records, 'screen_name': 'ItemMaster'
        }
        return render(request, 'AdminPortal/itemmaster_list.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Read - Detail View
@company_session_required
@login_required(login_url='/')
@check_permission('itemmaster_view')
def itemmaster_detail(request, pk):
    """
    Displays the details of a specific ItemMaster record.

    - Fetches the record based on the primary key (pk).
    - Passes the record to the form for viewing.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        record = get_object_or_404(ItemMaster, pk=pk,company_id=company.id)
        form = ItemMasterForm(instance=record,company = company.id)
        context = {
            'screen_name': 'ItemMaster', 'view': True, 'form': form
        }
        return render(request, 'AdminPortal/create.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Update
@company_session_required
@login_required(login_url='/')
@check_permission('itemmaster_update')
def itemmaster_update(request, pk):
    """
    Handles the updating of an existing ItemMaster record.

    - If the request method is POST, the form data is validated and, if valid, the record is updated.
    - If the request method is GET, the existing record is displayed in the form.
    - Upon successful update, redirects to the list view.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        itemmaster = get_object_or_404(ItemMaster, pk=pk,company_id=company.id)
        if request.method == "POST":
            form = ItemMasterForm(request.POST, instance=itemmaster,company = company.id)
            if form.is_valid():
                obj = form.save(commit=False)

                obj.company_id=company.id
                obj.save()  # Save the updated record
                return redirect('itemmaster_list')
        else:
            form = ItemMasterForm(instance=itemmaster,company = company.id)  # Display the existing record in the form
        context = {
            'form': form, 'screen_name': 'ItemMaster'
        }
        return render(request, 'AdminPortal/create.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Delete
@company_session_required
@login_required(login_url='/')
@check_permission('itemmaster_delete')
def itemmaster_delete(request, pk):
    """
    Handles the deletion of an existing ItemMaster record.

    - Fetches the record based on the primary key (pk).
    - Deletes the record from the database.
    - Upon successful deletion, redirects to the list view.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        record = get_object_or_404(ItemMaster, pk=pk,company_id=company.id)
        record.delete()  # Delete the record
        return redirect('itemmaster_list')
    except Exception as error:
        return render(request, '500.html', {'error': error})
# Create
@company_session_required
@login_required(login_url='/')
@check_permission('orderrequestparent_create')
def orderrequestparent_create(request):
    """
    Handles the creation of a new OrderRequestParent record.

    - If the request method is POST, the form data is validated and, if valid, the new record is saved.
    - If the request method is GET, an empty form is displayed.
    - Upon successful creation, redirects to the list view.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        if request.method == "POST":
            form = OrderRequestParentForm(request.POST)
            if form.is_valid():
                obj = form.save(commit=False)

                obj.company_id=company.id
                obj.save()
                  # Save the form data as a new record
                return redirect('orderrequestparent_list')
        else:
            form = OrderRequestParentForm()  # Display an empty form
        context = {
            'form': form, 'screen_name': 'OrderRequestParent'
        }
        return render(request, 'create.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Read - List View
@company_session_required
@login_required(login_url='/')
@check_permission('orderrequestparent_view')
def orderrequestparent_list(request):
    """
    Displays a list of all OrderRequestParent records.

    - Fetches all records from the OrderRequestParent model.
    - Passes the records to the template for rendering.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        records = OrderRequestParent.objects.filter(company_id=company.id)
        context = {
            'records': records, 'screen_name': 'OrderRequestParent'
        }
        return render(request, 'orderrequestparent_list.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Read - Detail View
@company_session_required
@login_required(login_url='/')
@check_permission('orderrequestparent_view')
def orderrequestparent_detail(request, pk):
    """
    Displays the details of a specific OrderRequestParent record.

    - Fetches the record based on the primary key (pk).
    - Passes the record to the form for viewing.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        record = get_object_or_404(OrderRequestParent, pk=pk,company_id=company.id)
        form = OrderRequestParentForm(instance=record)
        context = {
            'screen_name': 'OrderRequestParent', 'view': True, 'form': form
        }
        return render(request, 'create.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Update
@company_session_required
@login_required(login_url='/')
@check_permission('orderrequestparent_update')
def orderrequestparent_update(request, pk):
    """
    Handles the updating of an existing OrderRequestParent record.

    - If the request method is POST, the form data is validated and, if valid, the record is updated.
    - If the request method is GET, the existing record is displayed in the form.
    - Upon successful update, redirects to the list view.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        orderrequestparent = get_object_or_404(OrderRequestParent, pk=pk,company_id=company.id)
        if request.method == "POST":
            form = OrderRequestParentForm(request.POST, instance=orderrequestparent)
            if form.is_valid():
                obj = form.save(commit=False)

                obj.company_id=company.id
                obj.save()  # Save the updated record
                return redirect('orderrequestparent_list')
        else:
            form = OrderRequestParentForm(instance=orderrequestparent)  # Display the existing record in the form
        context = {
            'form': form, 'screen_name': 'OrderRequestParent'
        }
        return render(request, 'create.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Delete
@company_session_required
@login_required(login_url='/')
@check_permission('orderrequestparent_delete')
def orderrequestparent_delete(request, pk):
    """
    Handles the deletion of an existing OrderRequestParent record.

    - Fetches the record based on the primary key (pk).
    - Deletes the record from the database.
    - Upon successful deletion, redirects to the list view.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        record = get_object_or_404(OrderRequestParent, pk=pk,company_id=company.id)
        record.delete()  # Delete the record
        return redirect('orderrequestparent_list')
    except Exception as error:
        return render(request, '500.html', {'error': error})
# Create
@company_session_required
@login_required(login_url='/')
@check_permission('stocktransferroutemain_create')
def stocktransferroutemain_create(request):
    """
    Handles the creation of a new StockTransferRouteMain record.

    - If the request method is POST, the form data is validated and, if valid, the new record is saved.
    - If the request method is GET, an empty form is displayed.
    - Upon successful creation, redirects to the list view.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        if request.method == "POST":
            form = StockTransferRouteMainForm(request.POST)
            if form.is_valid():
                obj = form.save(commit=False)
                obj.company_id=company.id
                obj.save()
                  # Save the form data as a new record
                return redirect('stocktransferroutemain_list')
        else:
            form = StockTransferRouteMainForm()  # Display an empty form
        context = {
            'form': form, 'screen_name': 'StockTransferRouteMain'
        }
        return render(request, 'SupplierPortal/create.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Read - List View
@company_session_required
@login_required(login_url='/')
@check_permission('stocktransferroutemain_view')
def stocktransferroutemain_list(request):
    """
    Displays a list of all StockTransferRouteMain records.

    - Fetches all records from the StockTransferRouteMain model.
    - Passes the records to the template for rendering.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
    
        records = StockTransferRouteMain.objects.filter(company_id=company.id)
        context = {
            'records': records, 'screen_name': 'StockTransferRouteMain'
        }
        return render(request, 'SupplierPortal/stocktransferroutemain_list.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Read - Detail View
@company_session_required
@login_required(login_url='/')
@check_permission('stocktransferroutemain_view')
def stocktransferroutemain_detail(request, pk):
    """
    Displays the details of a specific StockTransferRouteMain record.

    - Fetches the record based on the primary key (pk).
    - Passes the record to the form for viewing.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        record = get_object_or_404(StockTransferRouteMain, pk=pk,company_id=company.id)
        form = StockTransferRouteMainForm(instance=record)
        context = {
            'screen_name': 'StockTransferRouteMain', 'view': True, 'form': form
        }
        return render(request, 'create.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Update
@company_session_required
@login_required(login_url='/')
@check_permission('stocktransferroutemain_update')
def stocktransferroutemain_update(request, pk):
    """
    Handles the updating of an existing StockTransferRouteMain record.

    - If the request method is POST, the form data is validated and, if valid, the record is updated.
    - If the request method is GET, the existing record is displayed in the form.
    - Upon successful update, redirects to the list view.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        stocktransferroutemain = get_object_or_404(StockTransferRouteMain, pk=pk,company_id=company.id)
        if request.method == "POST":
            form = StockTransferRouteMainForm(request.POST, instance=stocktransferroutemain)
            if form.is_valid():
                obj = form.save(commit=False)

                obj.company_id=company.id
                obj.save()  # Save the updated record
                return redirect('stocktransferroutemain_list')
        else:
            form = StockTransferRouteMainForm(instance=stocktransferroutemain)  # Display the existing record in the form
        context = {
            'form': form, 'screen_name': 'StockTransferRouteMain'
        }
        return render(request, 'create.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Delete
@company_session_required
@login_required(login_url='/')
@check_permission('stocktransferroutemain_delete')
def stocktransferroutemain_delete(request, pk):
    """
    Handles the deletion of an existing StockTransferRouteMain record.

    - Fetches the record based on the primary key (pk).
    - Deletes the record from the database.
    - Upon successful deletion, redirects to the list view.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        record = get_object_or_404(StockTransferRouteMain, pk=pk,company_id=company.id)
        record.delete()  # Delete the record
        return redirect('stocktransferroutemain_list')
    except Exception as error:
        return render(request, '500.html', {'error': error})
# Create
@company_session_required
@login_required(login_url='/')
@check_permission('itemunit_create')
def itemunit_create(request):
    """
    Handles the creation of a new ItemUnit record.

    - If the request method is POST, the form data is validated and, if valid, the new record is saved.
    - If the request method is GET, an empty form is displayed.
    - Upon successful creation, redirects to the list view.
    - In case of an error, renders a custom 500 error page.
    """
    # try:
    company = Company.objects.get(id=request.company)
    if request.method == "POST":
        form = ItemUnitForm(request.POST,company = company.id)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.company_id=company.id
            obj.save()
                # Save the form data as a new record
            return redirect('itemunit_list')
    else:
        form = ItemUnitForm(company = company.id)  # Display an empty form
    context = {
        'form': form, 'screen_name': 'ItemUnit'
    }
    return render(request, 'AdminPortal/create.html', context)
    # except Exception as error:
    #     return render(request, '500.html', {'error': error})

# Read - List View
@company_session_required
@login_required(login_url='/')
@check_permission('itemunit_view')
def itemunit_list(request):
    """
    Displays a list of all ItemUnit records.

    - Fetches all records from the ItemUnit model.
    - Passes the records to the template for rendering.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        records = ItemUnit.objects.filter(company_id=company.id)
        context = {
            'records': records, 'screen_name': 'Item Unit View'
        }
        return render(request, 'AdminPortal/itemunit_list.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Read - Detail View
@company_session_required
@login_required(login_url='/')
@check_permission('itemunit_view')
def itemunit_detail(request, pk):
    """
    Displays the details of a specific ItemUnit record.

    - Fetches the record based on the primary key (pk).
    - Passes the record to the form for viewing.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        record = get_object_or_404(ItemUnit, pk=pk,company_id=company.id)
        form = ItemUnitForm(instance=record,company = company.id)
        context = {
            'screen_name': 'ItemUnit', 'view': True, 'form': form
        }
        return render(request, 'AdminPortal/create.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Update
@company_session_required
@login_required(login_url='/')
@check_permission('itemunit_update')
def itemunit_update(request, pk):
    """
    Handles the updating of an existing ItemUnit record.

    - If the request method is POST, the form data is validated and, if valid, the record is updated.
    - If the request method is GET, the existing record is displayed in the form.
    - Upon successful update, redirects to the list view.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        itemunit = get_object_or_404(ItemUnit, pk=pk,company_id=company.id)
        if request.method == "POST":
            form = ItemUnitForm(request.POST, instance=itemunit,company = company.id)
            if form.is_valid():
                obj = form.save(commit=False)

                obj.company_id=company.id
                obj.save()  # Save the updated record
                return redirect('itemunit_list')
        else:
            form = ItemUnitForm(instance=itemunit,company = company.id)  # Display the existing record in the form
        context = {
            'form': form, 'screen_name': 'ItemUnit'
        }
        return render(request, 'AdminPortal/create.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Delete
@company_session_required
@login_required(login_url='/')
@check_permission('itemunit_delete')
def itemunit_delete(request, pk):
    """
    Handles the deletion of an existing ItemUnit record.

    - Fetches the record based on the primary key (pk).
    - Deletes the record from the database.
    - Upon successful deletion, redirects to the list view.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        record = get_object_or_404(ItemUnit, pk=pk,company_id=company.id)
        record.delete()  # Delete the record
        return redirect('itemunit_list')
    except Exception as error:
        return render(request, '500.html', {'error': error})
# Create
@company_session_required
@login_required(login_url='/')
@check_permission('invoice_create')
def invoice_create(request):
    """
    Handles the creation of a new Invoice record.

    - If the request method is POST, the form data is validated and, if valid, the new record is saved.
    - If the request method is GET, an empty form is displayed.
    - Upon successful creation, redirects to the list view.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        if request.method == "POST":
            form = InvoiceForm(request.POST)
            if form.is_valid():
                obj = form.save(commit=False)

                obj.company_id=company.id
                obj.save()
                  # Save the form data as a new record
                return redirect('invoice_list')
        else:
            form = InvoiceForm()  # Display an empty form
        context = {
            'form': form, 'screen_name': 'Invoice'
        }
        return render(request, 'create.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Read - List View
@company_session_required
@login_required(login_url='/')
@check_permission('invoice_view')
def invoice_list(request):
    """
    Displays a list of all Invoice records.

    - Fetches all records from the Invoice model.
    - Passes the records to the template for rendering.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        records = Invoice.objects.filter(company_id=company.id)
        context = {
            'records': records, 'screen_name': 'Invoice'
        }
        return render(request, 'invoice_list.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Read - Detail View
@company_session_required
@login_required(login_url='/')
@check_permission('invoice_view')
def invoice_detail(request, pk):
    """
    Displays the details of a specific Invoice record.

    - Fetches the record based on the primary key (pk).
    - Passes the record to the form for viewing.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        record = get_object_or_404(Invoice, pk=pk,company_id=company.id)
        form = InvoiceForm(instance=record)
        context = {
            'screen_name': 'Invoice', 'view': True, 'form': form
        }
        return render(request, 'create.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Update
@company_session_required
@login_required(login_url='/')
@check_permission('invoice_update')
def invoice_update(request, pk):
    """
    Handles the updating of an existing Invoice record.

    - If the request method is POST, the form data is validated and, if valid, the record is updated.
    - If the request method is GET, the existing record is displayed in the form.
    - Upon successful update, redirects to the list view.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        invoice = get_object_or_404(Invoice, pk=pk,company_id=company.id)
        if request.method == "POST":
            form = InvoiceForm(request.POST, instance=invoice)
            if form.is_valid():
                obj = form.save(commit=False)

                obj.company_id=company.id
                obj.save()  # Save the updated record
                return redirect('invoice_list')
        else:
            form = InvoiceForm(instance=invoice)  # Display the existing record in the form
        context = {
            'form': form, 'screen_name': 'Invoice'
        }
        return render(request, 'create.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Delete
@company_session_required
@login_required(login_url='/')
@check_permission('invoice_delete')
def invoice_delete(request, pk):
    """
    Handles the deletion of an existing Invoice record.

    - Fetches the record based on the primary key (pk).
    - Deletes the record from the database.
    - Upon successful deletion, redirects to the list view.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        record = get_object_or_404(Invoice, pk=pk,company_id=company.id)
        record.delete()  # Delete the record
        return redirect('invoice_list')
    except Exception as error:
        return render(request, '500.html', {'error': error})
# Create
@company_session_required
@login_required(login_url='/')
@check_permission('stocktransferparent_create')
def stocktransferparent_create(request):
    """
    Handles the creation of a new StockTransferParent record.

    - If the request method is POST, the form data is validated and, if valid, the new record is saved.
    - If the request method is GET, an empty form is displayed.
    - Upon successful creation, redirects to the list view.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        if request.method == "POST":
            form = StockTransferParentForm(request.POST)
            if form.is_valid():
                obj = form.save(commit=False)

                obj.company_id=company.id
                obj.save()
                  # Save the form data as a new record
                return redirect('stocktransferparent_list')
        else:
            form = StockTransferParentForm()  # Display an empty form
        context = {
            'form': form, 'screen_name': 'StockTransferParent'
        }
        return render(request, 'create.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Read - List View
@company_session_required
@login_required(login_url='/')
@check_permission('stocktransferparent_view')
def stocktransferparent_list(request):
    """
    Displays a list of all StockTransferParent records.

    - Fetches all records from the StockTransferParent model.
    - Passes the records to the template for rendering.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        records = StockTransferParent.objects.filter(company_id=company.id)
        context = {
            'records': records, 'screen_name': 'StockTransferParent'
        }
        return render(request, 'SupplierPortal/stocktransferparent_list.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Read - Detail View
@company_session_required
@login_required(login_url='/')
@check_permission('stocktransferparent_view')
def stocktransferparent_detail(request, pk):
    """
    Displays the details of a specific StockTransferParent record.

    - Fetches the record based on the primary key (pk).
    - Passes the record to the form for viewing.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        record = get_object_or_404(StockTransferParent, pk=pk,company_id=company.id)
        form = StockTransferParentForm(instance=record)
        context = {
            'screen_name': 'StockTransferParent', 'view': True, 'form': form
        }
        return render(request, 'create.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Update
@company_session_required
@login_required(login_url='/')
@check_permission('stocktransferparent_update')
def stocktransferparent_update(request, pk):
    """
    Handles the updating of an existing StockTransferParent record.

    - If the request method is POST, the form data is validated and, if valid, the record is updated.
    - If the request method is GET, the existing record is displayed in the form.
    - Upon successful update, redirects to the list view.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        stocktransferparent = get_object_or_404(StockTransferParent, pk=pk,company_id=company.id)
        if request.method == "POST":
            form = StockTransferParentForm(request.POST, instance=stocktransferparent)
            if form.is_valid():
                obj = form.save(commit=False)

                obj.company_id=company.id
                obj.save()  # Save the updated record
                return redirect('stocktransferparent_list')
        else:
            form = StockTransferParentForm(instance=stocktransferparent)  # Display the existing record in the form
        context = {
            'form': form, 'screen_name': 'StockTransferParent'
        }
        return render(request, 'create.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Delete
@company_session_required
@login_required(login_url='/')
@check_permission('stocktransferparent_delete')
def stocktransferparent_delete(request, pk):
    """
    Handles the deletion of an existing StockTransferParent record.

    - Fetches the record based on the primary key (pk).
    - Deletes the record from the database.
    - Upon successful deletion, redirects to the list view.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        record = get_object_or_404(StockTransferParent, pk=pk,company_id=company.id)
        record.delete()  # Delete the record
        return redirect('stocktransferparent_list')
    except Exception as error:
        return render(request, '500.html', {'error': error})
# Create
@company_session_required
@login_required(login_url='/')
@check_permission('stocktransferroutesub_create')
def stocktransferroutesub_create(request):
    """
    Handles the creation of a new StockTransferRouteSub record.

    - If the request method is POST, the form data is validated and, if valid, the new record is saved.
    - If the request method is GET, an empty form is displayed.
    - Upon successful creation, redirects to the list view.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        if request.method == "POST":
            form = StockTransferRouteSubForm(request.POST)
            if form.is_valid():
                obj = form.save(commit=False)

                obj.company_id=company.id
                obj.save()
                  # Save the form data as a new record
                return redirect('stocktransferroutesub_list')
        else:
            form = StockTransferRouteSubForm()  # Display an empty form
        context = {
            'form': form, 'screen_name': 'StockTransferRouteSub'
        }
        return render(request, 'SupplierPortal/create.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Read - List View
@company_session_required
@login_required(login_url='/')
@check_permission('stocktransferroutesub_view')
def stocktransferroutesub_list(request):
    """
    Displays a list of all StockTransferRouteSub records.

    - Fetches all records from the StockTransferRouteSub model.
    - Passes the records to the template for rendering.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        records = StockTransferRouteSub.objects.filter(company_id=company.id)
        context = {
            'records': records, 'screen_name': 'StockTransferRouteSub'
        }
        return render(request, 'SupplierPortal/stocktransferroutesub_list.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Read - Detail View
@company_session_required
@login_required(login_url='/')
@check_permission('stocktransferroutesub_view')
def stocktransferroutesub_detail(request, pk):
    """
    Displays the details of a specific StockTransferRouteSub record.

    - Fetches the record based on the primary key (pk).
    - Passes the record to the form for viewing.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        record = get_object_or_404(StockTransferRouteSub, pk=pk,company_id=company.id)
        form = StockTransferRouteSubForm(instance=record)
        context = {
            'screen_name': 'StockTransferRouteSub', 'view': True, 'form': form
        }
        return render(request, 'SupplierPortal/create.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Update
@company_session_required
@login_required(login_url='/')
@check_permission('stocktransferroutesub_update')
def stocktransferroutesub_update(request, pk):
    """
    Handles the updating of an existing StockTransferRouteSub record.

    - If the request method is POST, the form data is validated and, if valid, the record is updated.
    - If the request method is GET, the existing record is displayed in the form.
    - Upon successful update, redirects to the list view.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        stocktransferroutesub = get_object_or_404(StockTransferRouteSub, pk=pk,company_id=company.id)
        if request.method == "POST":
            form = StockTransferRouteSubForm(request.POST, instance=stocktransferroutesub)
            if form.is_valid():
                obj = form.save(commit=False)

                obj.company_id=company.id
                obj.save()  # Save the updated record
                return redirect('stocktransferroutesub_list')
        else:
            form = StockTransferRouteSubForm(instance=stocktransferroutesub)  # Display the existing record in the form
        context = {
            'form': form, 'screen_name': 'StockTransferRouteSub'
        }
        return render(request, 'SupplierPortal/create.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Delete
@company_session_required
@login_required(login_url='/')
@check_permission('stocktransferroutesub_delete')
def stocktransferroutesub_delete(request, pk):
    """
    Handles the deletion of an existing StockTransferRouteSub record.

    - Fetches the record based on the primary key (pk).
    - Deletes the record from the database.
    - Upon successful deletion, redirects to the list view.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        record = get_object_or_404(StockTransferRouteSub, pk=pk,company_id=company.id)
        record.delete()  # Delete the record
        return redirect('stocktransferroutesub_list')
    except Exception as error:
        return render(request, '500.html', {'error': error})
# Create
@company_session_required
@login_required(login_url='/')
@check_permission('packagesizemaster_create')
def packagesizemaster_create(request):
    """
    Handles the creation of a new PackageSizeMaster record.

    - If the request method is POST, the form data is validated and, if valid, the new record is saved.
    - If the request method is GET, an empty form is displayed.
    - Upon successful creation, redirects to the list view.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        if request.method == "POST":
            form = PackageSizeMasterForm(request.POST)
            if form.is_valid():
                obj = form.save(commit=False)

                obj.company_id=company.id
                obj.save()
                  # Save the form data as a new record
                return redirect('packagesizemaster_list')
        else:
            form = PackageSizeMasterForm()  # Display an empty form
        context = {
            'form': form, 'screen_name': 'PackageSizeMaster'
        }
        return render(request, 'AdminPortal/create.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Read - List View
@company_session_required
@login_required(login_url='/')
@check_permission('packagesizemaster_view')
def packagesizemaster_list(request):
    """
    Displays a list of all PackageSizeMaster records.

    - Fetches all records from the PackageSizeMaster model.
    - Passes the records to the template for rendering.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        records = PackageSizeMaster.objects.filter(company_id=company.id)
        context = {
            'records': records, 'screen_name': 'PackageSizeMaster'
        }
        return render(request, 'AdminPortal/packagesizemaster_list.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Read - Detail View
@company_session_required
@login_required(login_url='/')
@check_permission('packagesizemaster_view')
def packagesizemaster_detail(request, pk):
    """
    Displays the details of a specific PackageSizeMaster record.

    - Fetches the record based on the primary key (pk).
    - Passes the record to the form for viewing.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        record = get_object_or_404(PackageSizeMaster, pk=pk,company_id=company.id)
        form = PackageSizeMasterForm(instance=record)
        context = {
            'screen_name': 'PackageSizeMaster', 'view': True, 'form': form
        }
        return render(request, 'AdminPortal/create.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Update
@company_session_required
@login_required(login_url='/')
@check_permission('packagesizemaster_update')
def packagesizemaster_update(request, pk):
    """
    Handles the updating of an existing PackageSizeMaster record.

    - If the request method is POST, the form data is validated and, if valid, the record is updated.
    - If the request method is GET, the existing record is displayed in the form.
    - Upon successful update, redirects to the list view.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        packagesizemaster = get_object_or_404(PackageSizeMaster, pk=pk,company_id=company.id)
        if request.method == "POST":
            form = PackageSizeMasterForm(request.POST, instance=packagesizemaster)
            if form.is_valid():
                obj = form.save(commit=False)

                obj.company_id=company.id
                obj.save()  # Save the updated record
                return redirect('packagesizemaster_list')
        else:
            form = PackageSizeMasterForm(instance=packagesizemaster)  # Display the existing record in the form
        context = {
            'form': form, 'screen_name': 'PackageSizeMaster'
        }
        return render(request, 'AdminPortal/create.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Delete
@company_session_required
@login_required(login_url='/')
@check_permission('packagesizemaster_delete')
def packagesizemaster_delete(request, pk):
    """
    Handles the deletion of an existing PackageSizeMaster record.

    - Fetches the record based on the primary key (pk).
    - Deletes the record from the database.
    - Upon successful deletion, redirects to the list view.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        record = get_object_or_404(PackageSizeMaster, pk=pk,company_id=company.id)
        record.delete()  # Delete the record
        return redirect('packagesizemaster_list')
    except Exception as error:
        return render(request, '500.html', {'error': error})
# Create
@company_session_required
@login_required(login_url='/')
@check_permission('packageassignment_create')
def packageassignment_create(request):
    """
    Handles the creation of a new PackageAssignment record.

    - If the request method is POST, the form data is validated and, if valid, the new record is saved.
    - If the request method is GET, an empty form is displayed.
    - Upon successful creation, redirects to the list view.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        if request.method == "POST":
            form = PackageAssignmentForm(request.POST)
            if form.is_valid():
                obj = form.save(commit=False)

                obj.company_id=company.id
                obj.save()
                  # Save the form data as a new record
                return redirect('packageassignment_list')
        else:
            form = PackageAssignmentForm()  # Display an empty form
        context = {
            'form': form, 'screen_name': 'PackageAssignment'
        }
        return render(request, 'create.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Read - List View
@company_session_required
@login_required(login_url='/')
@check_permission('packageassignment_view')
def packageassignment_list(request):
    """
    Displays a list of all PackageAssignment records.

    - Fetches all records from the PackageAssignment model.
    - Passes the records to the template for rendering.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        records = PackageAssignment.objects.filter(company_id=company.id)
        context = {
            'records': records, 'screen_name': 'PackageAssignment'
        }
        return render(request, 'packageassignment_list.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Read - Detail View
@company_session_required
@login_required(login_url='/')
@check_permission('packageassignment_view')
def packageassignment_detail(request, pk):
    """
    Displays the details of a specific PackageAssignment record.

    - Fetches the record based on the primary key (pk).
    - Passes the record to the form for viewing.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        record = get_object_or_404(PackageAssignment, pk=pk,company_id=company.id)
        form = PackageAssignmentForm(instance=record)
        context = {
            'screen_name': 'PackageAssignment', 'view': True, 'form': form
        }
        return render(request, 'create.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Update
@company_session_required
@login_required(login_url='/')
@check_permission('packageassignment_update')
def packageassignment_update(request, pk):
    """
    Handles the updating of an existing PackageAssignment record.

    - If the request method is POST, the form data is validated and, if valid, the record is updated.
    - If the request method is GET, the existing record is displayed in the form.
    - Upon successful update, redirects to the list view.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        packageassignment = get_object_or_404(PackageAssignment, pk=pk,company_id=company.id)
        if request.method == "POST":
            form = PackageAssignmentForm(request.POST, instance=packageassignment)
            if form.is_valid():
                obj = form.save(commit=False)

                obj.company_id=company.id
                obj.save()  # Save the updated record
                return redirect('packageassignment_list')
        else:
            form = PackageAssignmentForm(instance=packageassignment)  # Display the existing record in the form
        context = {
            'form': form, 'screen_name': 'PackageAssignment'
        }
        return render(request, 'create.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Delete
@company_session_required
@login_required(login_url='/')
@check_permission('packageassignment_delete')
def packageassignment_delete(request, pk):
    """
    Handles the deletion of an existing PackageAssignment record.

    - Fetches the record based on the primary key (pk).
    - Deletes the record from the database.
    - Upon successful deletion, redirects to the list view.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        record = get_object_or_404(PackageAssignment, pk=pk,company_id=company.id)
        record.delete()  # Delete the record
        return redirect('packageassignment_list')
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Create
@company_session_required
@login_required(login_url='/')
@check_permission('orderrequestchild_create')
def orderrequestchild_create(request):
    """
    Handles the creation of a new OrderRequestChild record.

    - If the request method is POST, the form data is validated and, if valid, the new record is saved.
    - If the request method is GET, an empty form is displayed.
    - Upon successful creation, redirects to the list view.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        if request.method == "POST":
            form = OrderRequestChildForm(request.POST)
            if form.is_valid():
                obj = form.save(commit=False)

                obj.company_id=company.id
                obj.save()
                  # Save the form data as a new record
                return redirect('orderrequestchild_list')
        else:
            form = OrderRequestChildForm()  # Display an empty form
        context = {
            'form': form, 'screen_name': 'OrderRequestChild'
        }
        return render(request, 'create.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Read - List View
@company_session_required
@login_required(login_url='/')
@check_permission('orderrequestchild_view')
def orderrequestchild_list(request):
    """
    Displays a list of all OrderRequestChild records.

    - Fetches all records from the OrderRequestChild model.
    - Passes the records to the template for rendering.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        records = OrderRequestChild.objects.filter(company_id=company.id)
        context = {
            'records': records, 'screen_name': 'OrderRequestChild'
        }
        return render(request, 'orderrequestchild_list.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Read - Detail View
@company_session_required
@login_required(login_url='/')
@check_permission('orderrequestchild_view')
def orderrequestchild_detail(request, pk):
    """
    Displays the details of a specific OrderRequestChild record.

    - Fetches the record based on the primary key (pk).
    - Passes the record to the form for viewing.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        record = get_object_or_404(OrderRequestChild, pk=pk,company_id=company.id)
        form = OrderRequestChildForm(instance=record)
        context = {
            'screen_name': 'OrderRequestChild', 'view': True, 'form': form
        }
        return render(request, 'create.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Update
@company_session_required
@login_required(login_url='/')
@check_permission('orderrequestchild_update')
def orderrequestchild_update(request, pk):
    """
    Handles the updating of an existing OrderRequestChild record.

    - If the request method is POST, the form data is validated and, if valid, the record is updated.
    - If the request method is GET, the existing record is displayed in the form.
    - Upon successful update, redirects to the list view.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        orderrequestchild = get_object_or_404(OrderRequestChild, pk=pk,company_id=company.id)
        if request.method == "POST":
            form = OrderRequestChildForm(request.POST, instance=orderrequestchild)
            if form.is_valid():
                obj = form.save(commit=False)

                obj.company_id=company.id
                obj.save()  # Save the updated record
                return redirect('orderrequestchild_list')
        else:
            form = OrderRequestChildForm(instance=orderrequestchild)  # Display the existing record in the form
        context = {
            'form': form, 'screen_name': 'OrderRequestChild'
        }
        return render(request, 'create.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Delete
@company_session_required
@login_required(login_url='/')
@check_permission('orderrequestchild_delete')
def orderrequestchild_delete(request, pk):
    """
    Handles the deletion of an existing OrderRequestChild record.

    - Fetches the record based on the primary key (pk).
    - Deletes the record from the database.
    - Upon successful deletion, redirects to the list view.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        record = get_object_or_404(OrderRequestChild, pk=pk,company_id=company.id)
        record.delete()  # Delete the record
        return redirect('orderrequestchild_list')
    except Exception as error:
        return render(request, '500.html', {'error': error})
# Create
@company_session_required
@login_required(login_url='/')
@check_permission('manualstockadjustment_create')
def manualstockadjustment_create(request):
    """
    Handles the creation of a new ManualStockAdjustment record.

    - If the request method is POST, the form data is validated and, if valid, the new record is saved.
    - If the request method is GET, an empty form is displayed.
    - Upon successful creation, redirects to the list view.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        if request.method == "POST":
            form = ManualStockAdjustmentForm(request.POST)
            if form.is_valid():
                obj = form.save(commit=False)

                obj.company_id=company.id
                obj.save()
                  # Save the form data as a new record
                return redirect('manualstockadjustment_list')
        else:
            form = ManualStockAdjustmentForm()  # Display an empty form
        context = {
            'form': form, 'screen_name': 'ManualStockAdjustment'
        }
        return render(request, 'SupplierPortal/create.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Read - List View
@company_session_required
@login_required(login_url='/')
@check_permission('manualstockadjustment_view')
def manualstockadjustment_list(request):
    """
    Displays a list of all ManualStockAdjustment records.

    - Fetches all records from the ManualStockAdjustment model.
    - Passes the records to the template for rendering.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        records = ManualStockAdjustment.objects.filter(company_id=company.id)
        context = {
            'records': records, 'screen_name': 'ManualStockAdjustment'
        }
        return render(request, 'SupplierPortal/manualstockadjustment_list.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Read - Detail View
@company_session_required
@login_required(login_url='/')
@check_permission('manualstockadjustment_view')
def manualstockadjustment_detail(request, pk):
    """
    Displays the details of a specific ManualStockAdjustment record.

    - Fetches the record based on the primary key (pk).
    - Passes the record to the form for viewing.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        record = get_object_or_404(ManualStockAdjustment, pk=pk,company_id=company.id)
        form = ManualStockAdjustmentForm(instance=record)
        context = {
            'screen_name': 'ManualStockAdjustment', 'view': True, 'form': form
        }
        return render(request, 'SupplierPortal/create.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Update
@company_session_required
@login_required(login_url='/')
@check_permission('manualstockadjustment_update')
def manualstockadjustment_update(request, pk):
    """
    Handles the updating of an existing ManualStockAdjustment record.

    - If the request method is POST, the form data is validated and, if valid, the record is updated.
    - If the request method is GET, the existing record is displayed in the form.
    - Upon successful update, redirects to the list view.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        manualstockadjustment = get_object_or_404(ManualStockAdjustment, pk=pk,company_id=company.id)
        if request.method == "POST":
            form = ManualStockAdjustmentForm(request.POST, instance=manualstockadjustment)
            if form.is_valid():
                obj = form.save(commit=False)

                obj.company_id=company.id
                obj.save()  # Save the updated record
                return redirect('manualstockadjustment_list')
        else:
            form = ManualStockAdjustmentForm(instance=manualstockadjustment)  # Display the existing record in the form
        context = {
            'form': form, 'screen_name': 'ManualStockAdjustment'
        }
        return render(request, 'SupplierPortal/create.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Delete
@company_session_required
@login_required(login_url='/')
@check_permission('manualstockadjustment_delete')
def manualstockadjustment_delete(request, pk):
    """
    Handles the deletion of an existing ManualStockAdjustment record.

    - Fetches the record based on the primary key (pk).
    - Deletes the record from the database.
    - Upon successful deletion, redirects to the list view.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        record = get_object_or_404(ManualStockAdjustment, pk=pk,company_id=company.id)
        record.delete()  # Delete the record
        return redirect('manualstockadjustment_list')
    except Exception as error:
        return render(request, '500.html', {'error': error})
# Create
@company_session_required
@login_required(login_url='/')
@check_permission('stocktransferchild_create')
def stocktransferchild_create(request):
    """
    Handles the creation of a new StockTransferChild record.

    - If the request method is POST, the form data is validated and, if valid, the new record is saved.
    - If the request method is GET, an empty form is displayed.
    - Upon successful creation, redirects to the list view.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        if request.method == "POST":
            form = StockTransferChildForm(request.POST)
            if form.is_valid():
                obj = form.save(commit=False)

                obj.company_id=company.id
                obj.save()
                  # Save the form data as a new record
                return redirect('stocktransferchild_list')
        else:
            form = StockTransferChildForm()  # Display an empty form
        context = {
            'form': form, 'screen_name': 'StockTransferChild'
        }
        return render(request, 'SupplierPortal/create.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Read - List View
@company_session_required
@login_required(login_url='/')
@check_permission('stocktransferchild_view')
def stocktransferchild_list(request):
    """
    Displays a list of all StockTransferChild records.

    - Fetches all records from the StockTransferChild model.
    - Passes the records to the template for rendering.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        records = StockTransferChild.objects.filter(company_id=company.id)
        context = {
            'records': records, 'screen_name': 'StockTransferChild'
        }
        return render(request, 'SupplierPortal/stocktransferchild_list.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Read - Detail View
@company_session_required
@login_required(login_url='/')
@check_permission('stocktransferchild_view')
def stocktransferchild_detail(request, pk):
    """
    Displays the details of a specific StockTransferChild record.

    - Fetches the record based on the primary key (pk).
    - Passes the record to the form for viewing.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        record = get_object_or_404(StockTransferChild, pk=pk,company_id=company.id)
        form = StockTransferChildForm(instance=record)
        context = {
            'screen_name': 'StockTransferChild', 'view': True, 'form': form
        }
        return render(request, 'SupplierPortal/create.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Update
@company_session_required
@login_required(login_url='/')
@check_permission('stocktransferchild_update')
def stocktransferchild_update(request, pk):
    """
    Handles the updating of an existing StockTransferChild record.

    - If the request method is POST, the form data is validated and, if valid, the record is updated.
    - If the request method is GET, the existing record is displayed in the form.
    - Upon successful update, redirects to the list view.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        stocktransferchild = get_object_or_404(StockTransferChild, pk=pk,company_id=company.id)
        if request.method == "POST":
            form = StockTransferChildForm(request.POST, instance=stocktransferchild)
            if form.is_valid():
                obj = form.save(commit=False)

                obj.company_id=company.id
                obj.save()  # Save the updated record
                return redirect('stocktransferchild_list')
        else:
            form = StockTransferChildForm(instance=stocktransferchild)  # Display the existing record in the form
        context = {
            'form': form, 'screen_name': 'StockTransferChild'
        }
        return render(request, 'SupplierPortal/create.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Delete
@company_session_required
@login_required(login_url='/')
@check_permission('stocktransferchild_delete')
def stocktransferchild_delete(request, pk):
    """
    Handles the deletion of an existing StockTransferChild record.

    - Fetches the record based on the primary key (pk).
    - Deletes the record from the database.
    - Upon successful deletion, redirects to the list view.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        record = get_object_or_404(StockTransferChild, pk=pk,company_id=company.id)
        record.delete()  # Delete the record
        return redirect('stocktransferchild_list')
    except Exception as error:
        return render(request, '500.html', {'error': error})


@company_session_required
def supplier_approval(request):
    try:
        company = Company.objects.get(id=request.company)
        suppliers=Supplier.objects.filter(company_id = company.id,verified_by_admin=False)
        return render(request,'AdminPortal/ApprovalProcess/supplier_approval.html',{'suppliers':suppliers})
    except Exception as error:
        return render(request, '500.html', {'error': error})

@company_session_required
def approval(request, id):
    try:
        company = Company.objects.get(id=request.company)
        supplier = Supplier.objects.get(pk=id)
        supplierstore = SupplierStore.objects.filter(supplier_id = supplier.id)
    
        supplier.status = 'Approved'
        supplier.verified_by_admin = True
        supplier.rejection_reason = 'Approved'
        supplier.save()

        user = User.objects.create(
            company_id=company.id,
            first_name=supplier.supplier_name,
            last_name=supplier.short_name,
            email=supplier.email,
            phone_number=supplier.phone,
            user_type = "Supplier",
            password = make_password("1234"),
            supplier_id = supplier.id,
            is_admin = True,
            buyer_id = request.user.buyer_id,
 
        )

  
        return redirect('supplier_list')

    except Exception as error:
        print("Error:", error)  
        return render(request, '500.html', {'error': error})
    
def rejection(request):
    try:
        
        supplier_id = request.POST.get("supplier_id")  
        print('supplier_id',supplier_id)
        supplier = get_object_or_404(Supplier, pk=supplier_id)

        if request.method == "POST":
            reason = request.POST.get("rejection_reason")
            supplier.status = "Rejected"
            supplier.verified_by_admin = False
            supplier.rejection_reason = reason  
            supplier.save()

        return redirect("supplier_list")

    except Exception as error:
        return render(request, "500.html", {"error": error})



def customer_approval(request):
    try:
        customers=CustomerRegistrations.objects.filter(verified_by_admin = False)
        return render(request,'AdminPortal/ApprovalProcess/customer_approval_list.html',{'customers':customers})
    except Exception as error:
        return render(request, '500.html', {'error': error})

@company_session_required
def customer_admin_approval(request, id):
    try:
        company = Company.objects.get(id=request.company)
        customer = CustomerRegistrations.objects.get(pk=id)
      
        customer.verified_by_admin = True
        customer.rejection_reason = 'Approved'
        customer.approved_by = request.user
        customer.save()

        user = User.objects.create(
            company_id=company.id,
            first_name=customer.name,
            email=customer.email,
            phone_number=customer.phone,
            password=make_password(customer.name),
            user_type = "Customer",
            customer_id = customer.id,
            maker=True,
            checker=True,
            is_admin = True,
            buyer_id = request.user.buyer_id,
        )
     
        return redirect('customerregistrations_list')
    except Exception as error:
        print("Error:", error)  
        return render(request, '500.html', {'error': error})
    
def customer_rejection(request):
    try:
        
        customer_id = request.POST.get("customer_id")  
        print('supplier_id',customer_id)
        customer = get_object_or_404(CustomerRegistrations, pk=customer_id)

        if request.method == "POST":
            reason = request.POST.get("rejection_reason")
            customer.status = "Rejected"
            customer.verified_by_admin = False
            customer.rejection_reason = reason  
            customer.save()

        return redirect("customerregistrations_list")

    except Exception as error:
        return render(request, "500.html", {"error": error})


def get_subcategories(request):
    category_id = request.GET.get('category_id')
    subcategories = ItemSubCategoryMaster.objects.filter(category_id=category_id).values('id', 'name')
    return JsonResponse({'subcategories': list(subcategories)})



@company_session_required
@login_required(login_url='/')
@check_permission('producttype_create')
def producttype_create(request):
    """
    Handles the creation of a new producttype record.

    - If the request method is POST, the form data is validated and, if valid, the new record is saved.
    - If the request method is GET, an empty form is displayed.
    - Upon successful creation, redirects to the list view.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        if request.method == "POST":
            form = ProductMasterForm(request.POST)
            if form.is_valid():
                obj = form.save(commit=False)

                obj.company_id=company.id
                obj.save()
                  # Save the form data as a new record
                return redirect('producttype_list')
        else:
            form = ProductMasterForm()  # Display an empty form
        context = {
            'form': form, 'screen_name': 'ProductType'
        }
        return render(request, 'create.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})


# Read - List View
@company_session_required
@login_required(login_url='/')
@check_permission('producttype_list')
def producttype_list(request):
    """
    Displays a list of all producttype records.

    - Fetches all records from the producttype model.
    - Passes the records to the template for rendering.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        records = ProductMaster.objects.filter(company_id=company.id)
        context = {
            'records': records, 'screen_name': 'ProductType'
        }
        return render(request, 'producttype_list.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Read - Detail View
@company_session_required
@login_required(login_url='/')
@check_permission('producttype_view')
def producttype_detail(request, pk):
    """
    Displays the details of a specific producttype record.

    - Fetches the record based on the primary key (pk).
    - Passes the record to the form for viewing.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        record = get_object_or_404(ProductMaster, pk=pk,company_id=company.id)
        form = ProductMasterForm(instance=record)
        context = {
            'screen_name': 'ProductType', 'view': True, 'form': form
        }
        return render(request, 'create.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Update
@company_session_required
@login_required(login_url='/')
@check_permission('producttype_update')
def producttype_update(request, pk):
    """
    Handles the updating of an existing Invoice record.

    - If the request method is POST, the form data is validated and, if valid, the record is updated.
    - If the request method is GET, the existing record is displayed in the form.
    - Upon successful update, redirects to the list view.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        product = get_object_or_404(ProductMaster, pk=pk,company_id=company.id)
        if request.method == "POST":
            form = ProductMasterForm(request.POST, instance=product)
            if form.is_valid():
                obj = form.save(commit=False)

                obj.company_id=company.id
                obj.save()  # Save the updated record
                return redirect('producttype_list')
        else:
            form = ProductMasterForm(instance=product)  # Display the existing record in the form
        context = {
            'form': form, 'screen_name': 'ProductType'
        }
        return render(request, 'create.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Delete
@company_session_required
@login_required(login_url='/')
@check_permission('invoice_delete')
def producttype_delete(request, pk):
    """
    Handles the deletion of an existing Invoice record.

    - Fetches the record based on the primary key (pk).
    - Deletes the record from the database.
    - Upon successful deletion, redirects to the list view.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        record = get_object_or_404(ProductMaster, pk=pk,company_id=company.id)
        record.delete()  # Delete the record
        return redirect('producttype_list')
    except Exception as error:
        return render(request, '500.html', {'error': error})

#================= Vendor creation ===============

@company_session_required
@login_required(login_url='/')
def Vendor_list(request):
    try:
        company = Company.objects.get(id=request.company)
        records = Vendor.objects.filter(company_id=company.id)
        context = {
            'records': records, 'screen_name': 'Supplier List'
        }
        return render(request, 'AdminPortal/vendor_list.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Read - Detail View
@company_session_required
@login_required(login_url='/')
@check_permission('vendor_view')
def vendor_detail(request, pk):
    """
    Displays the details of a specific vendor record.

    - Fetches the record based on the primary key (pk).
    - Passes the record to the form for viewing.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        record = get_object_or_404(Vendor, pk=pk,company_id=company.id)
        form = VendorForm(instance=record)
        context = {
            'screen_name': 'Supplier Details', 'view': True, 'form': form
        }
        return render(request, 'create.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Create
@company_session_required
@login_required(login_url='/')
@check_permission('vendor_create')
def vendor_create(request):
    """
    Handles the creation of a new vendor record.

    - If the request method is POST, the form data is validated and, if valid, the new record is saved.
    - If the request method is GET, an empty form is displayed.
    - Upon successful creation, redirects to the list view.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        if request.method == "POST":
            form = VendorForm(request.POST)
            if form.is_valid():
                obj = form.save(commit=False)

                obj.company_id=company.id
                obj.save()
                  # Save the form data as a new record
                return redirect('Vendor_list')
        else:
            form = VendorForm()  # Display an empty form
        context = {
            'form': form, 'screen_name': 'Supplier Registration'
        }
        return render(request, 'AdminPortal/create.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})
    
# Update
@company_session_required
@login_required(login_url='/')
@check_permission('vendor_update')
def vendor_update(request, pk):
    """
    Handles the updating of an existing Invoice record.

    - If the request method is POST, the form data is validated and, if valid, the record is updated.
    - If the request method is GET, the existing record is displayed in the form.
    - Upon successful update, redirects to the list view.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        product = get_object_or_404(Vendor, pk=pk,company_id=company.id)
        if request.method == "POST":
            form = VendorForm(request.POST, instance=product)
            if form.is_valid():
                obj = form.save(commit=False)

                obj.company_id=company.id
                obj.save()  # Save the updated record
                return redirect('vendor_list')
        else:
            form = VendorForm(instance=product)  # Display the existing record in the form
        context = {
            'form': form, 'screen_name': 'Update Supplier'
        }
        return render(request, 'create.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Delete
@company_session_required
@login_required(login_url='/')
@check_permission('invoice_delete')
def vendor_delete(request, pk):
    """
    Handles the deletion of an existing Invoice record.

    - Fetches the record based on the primary key (pk).
    - Deletes the record from the database.
    - Upon successful deletion, redirects to the list view.
    - In case of an error, renders a custom 500 error page.
    """
    try:
        company = Company.objects.get(id=request.company)
        record = get_object_or_404(Vendor, pk=pk,company_id=company.id)
        record.delete()  # Delete the record
        return redirect('vendor_list')
    except Exception as error:
        return render(request, '500.html', {'error': error})





#============== Roots Mapping ===================
@company_session_required 
def disply_allsupplier(request):
    try:
        suppliers = Supplier.objects.filter(company_id = request.company)
        context = {'suppliers':suppliers}
        return render(request,"AdminPortal/disply_allsupplier.html",context)
    except Exception as error:
        return render(request, "500.html", {"error": error})

@company_session_required 
def root_mapping(request,pk): # pk is a supplier id
    try:
        suppliers = Supplier.objects.get(company_id = request.company,id = pk)
        customers = SupplierCustomerMapping.objects.filter(supplier_id=suppliers.id)
        supplierstores = SupplierStore.objects.filter(supplier_id = suppliers.id)
        if request.method == "POST":
            selected_ids = request.POST.getlist('select[]')
            supplier_ids = request.POST.getlist('supplierstore[]')
            orders = request.POST.getlist('order[]')
            tostore = request.POST.get('distributorstore')
            routename = request.POST.get('routename', '').strip()

            if routename and tostore:
                routes = StockTransferRouteMain.objects.create(
                    company_id=request.company,
                    name=routename,
                    supplier_id=suppliers.id,
                    to_store_id=tostore,
                )

                for i in range(len(supplier_ids)):
                    if supplier_ids[i] in selected_ids:
                        try:
                            order_value = int(orders[i] or 0)
                        except ValueError:
                            order_value = 0

                        StockTransferRouteSub.objects.create(
                            company_id=request.company,
                            transfer_id=routes.id,
                            intermediate_store_id=supplier_ids[i],
                            sequence=order_value,
                        )
                
                child = StockTransferRouteSub.objects.filter(transfer_id=routes.id)
                if child.exists():
                    pass
                else:
                    routes.delete()

            
            return redirect('disply_allsupplier')



        context = {'suppliers':suppliers,'customers':customers,'supplierstores':supplierstores}
        return render(request,'AdminPortal/root_mapping.html',context)
    except Exception as error:
        return render(request, "500.html", {"error": error})

def get_mapped_customers(request):
    supplier_id = request.GET.get('supplier_id')
    if supplier_id:
        mappings = SupplierCustomerMapping.objects.filter(supplier_id=supplier_id)
        data = [{
            'id': m.id,
            'customer_name': m.customer.name  # or whatever fields you want
        } for m in mappings]
        return JsonResponse({'data': data})
    return JsonResponse({'data': []})

def get_customer_stores(request):
    distributor_id = request.GET.get('distributor_id')
    if distributor_id:
        stores = Customerstore.objects.filter(customer_id=distributor_id)
        data = [{
            'id': store.id,
            'store_name': store.name  # or however it's named in your model
        } for store in stores]
        print("data",data)
        return JsonResponse({'data': data})
    return JsonResponse({'data': []})

def disply_routes(request,pk): # pk is a supplier id
    try:
        mainrecords = StockTransferRouteMain.objects.filter(supplier_id = pk)

        context = {'mainrecords':mainrecords}
        return render(request,'AdminPortal/disply_routes.html',context) 
    except Exception as error:
        return render(request, "500.html", {"error": error})

def disply_routesdetailed(request,pk): # pk is a StockTransferRouteMain id
    try:
        mainrecords = StockTransferRouteMain.objects.get(id = pk)
        subrecords = StockTransferRouteSub.objects.filter(transfer_id = pk).order_by("sequence")
        
        # Fetching the Supplier and Customer Store information (for clarity)
        supplier_store = mainrecords.supplier 
        customer_store = mainrecords.to_store.name

        context = {'subrecords':subrecords,'mainrecords':mainrecords,'supplier_store': supplier_store,
            'customer_store': customer_store,}
        return render(request,'AdminPortal/disply_routesdetailed.html',context) 
    except Exception as error:
        return render(request, "500.html", {"error": error})
    


def distributor_apporovallist(request):
    try:
        customers=CustomerRegistrations.objects.all()
        return render(request,'AdminPortal/ApprovalProcess/customer_approval.html',{'customers':customers})
    except Exception as error:
        return render(request, '500.html', {'error': error})
    

@company_session_required
def create_distributor_branch(request,id):

    distributor=DistributorBranch.objects.filter(company_id=request.company,customer_id=id)

    if request.method == 'POST':
        # company_id = request.POST.get('company')
        # customer_id = request.POST.get('customer')
        name = request.POST.get('name')
        address = request.POST.get('address')
        phone_number = request.POST.get('phone_number')
        manager_name = request.POST.get('manager_name')
        country = request.POST.get('country')
        state = request.POST.get('state')
        city = request.POST.get('city')
        description = request.POST.get('description')
      

        company = Company.objects.get(id=request.company) if request.company else None
        customer = CustomerRegistrations.objects.get(id=id) 

        

        DistributorBranch.objects.create(
            company= company,
            customer=customer,
            name=name,
            address=address,
            phone_number=phone_number,
            manager_name=manager_name,
            country=country,
            state=state,
            city=city,
            description=description,
         
        )
        return redirect('distributor_apporovallist')  # Redirect to success page after saving

    return render(request, 'AdminPortal/ApprovalProcess/create_branch.html',{'distributor':distributor})


@company_session_required
def admin_dashboard(request):

    # try:
        company = Company.objects.get(id=request.company)
        suppliers = Supplier.objects.filter(company_id=company.id).count()
        customers = CustomerRegistrations.objects.filter(company_id=company.id).count()
        Customerstores = Customerstore.objects.filter(company_id=company.id).count()
        supplierstore= SupplierStore.objects.filter(company_id=company.id).order_by('id')[:10]
        supplier1= SupplierStore.objects.filter(company_id=company.id).count()
        queryset = (
        ProductMaster.objects.filter(company_id=company.id, ).annotate(month=TruncMonth('created_at')).values('month') .annotate(avg_price=Avg('price')).order_by('month') )
        
    # Prepare data for Chart.js
       
        
        labels = [item['month'].strftime('%b %Y') for item in queryset]
        data = [item['total_volume'] for item in queryset]

        print('labels',labels)
        products = ProductMaster.objects.filter(company_id=company.id).count()
        brand= BrandMaster.objects.filter(company_id=company.id).count()
        category= ItemCategoryMaster.objects.filter(company_id=company.id).count()
        subcategory= ItemSubCategoryMaster.objects.filter(company_id=company.id).count()
        item= ItemMaster.objects.filter(company_id=company.id).count()
         

        May_total = (
    ItemMaster.objects
    .filter(created_at__year=2025, created_at__month=5)
    .aggregate(total=Sum('amount'))
        
)       
        jan_total = (
    ItemMaster.objects
    .filter(created_at__year=2025, created_at__month=1)
    .aggregate(total=Sum('amount'))
        
)       

        feb_total = (
    ItemMaster.objects
    .filter(created_at__year=2025, created_at__month=2)
    .aggregate(total=Sum('amount'))
        
)       
        mar_total = (
    ItemMaster.objects
    .filter(created_at__year=2025, created_at__month=3)
    .aggregate(total=Sum('amount'))
        
)       
        apr_total = (
    ItemMaster.objects
    .filter(created_at__year=2025, created_at__month=4)
    .aggregate(total=Sum('amount'))
        
)       
        jun_total = (
    ItemMaster.objects
    .filter(created_at__year=2025, created_at__month=6)
    .aggregate(total=Sum('amount'))
        
)       
        
        feb_month=feb_total['total']
        mar_month=mar_total['total']
        apr_month=apr_total['total']
        jun_month=jun_total['total']
        may_month=May_total['total']

        print('feb_month',feb_month)

        jan_month=jan_total['total']
        if jan_month is None:
            jan_month = 0
        if May_total['total'] is None:
            may_month = 0
        if feb_total['total'] is None:
            feb_month = 0

        if mar_total['total'] is None:
            mar_month = 0

        if apr_total['total'] is None:
            apr_month= 0
        if jun_total['total'] is None:
            jun_month = 0           


        context = {
    'suppliers': suppliers,
    'customers': customers,
    'customer_stores': Customerstores,
    'supplier_stores': supplier1,
    'products': products,
    'brands': brand,
    'stores':supplierstore,
    'categories': category,
    'subcategories': subcategory,
    'items': item,
    'jan_month': jan_month,
    'feb_month': feb_month,
    'mar_month': mar_month,
    'apr_month': apr_month,
    'jun_month': jun_month,
    'may_month': may_month,
    # 'labels': labels,
    # 'data': data,
}

        return render(request, 'dashboard.html', context)
    # except Exception as error:
    #     return render(request, '500.html', {'error': error})

@company_session_required
@login_required(login_url='/')
def logistics_list(request):
    try: 
        company = Company.objects.get(id=request.company)
        records = LogisticsPartner.objects.filter(company_id=company.id)
        
        context = {
            'records': records, 'screen_name': 'LogisticsPartner List'
        }
        return render(request, 'AdminPortal/logistics_list.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error}) 

@company_session_required
@login_required(login_url='/')
def assign_logisticsvehicles(request,pk):
    try: 
        company = Company.objects.get(id=request.company)
        records = LogisticsPartner.objects.get(id = pk)
  
        if request.method == "POST":
            form = LogisticsVehicleForm(request.POST)
            if form.is_valid():
                vehicle = form.save(commit=False)
                company_id = company.id
                vehicle.partner_id = records.id  # force assign the selected partner
                vehicle.save()
                return redirect(f'/assign_logisticsvehicles/{pk}')
        else:
            form = LogisticsVehicleForm(initial = {'partner':records})
            vehicles = LogisticsVehicle.objects.filter(partner_id = records.id)
 
        context = {
            'records': records, 'screen_name': 'Assign Logistics Vehicle','form':form,'vehicles':vehicles
        }
        return render(request, 'AdminPortal/assign_logisticsvehicles.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error}) 

@company_session_required
@login_required(login_url='/')
def multiapproval_process(request):
    try:
        company = Company.objects.get(id=request.company)
        if request.method == 'POST':
            form = MultiApproverForm(request.POST)
            if form.is_valid():
                aa = form.save(commit=False)

                aa.company_id = company.id
                aa.save()
                return redirect('multiapprovalview')
        else:
            form = MultiApproverForm()

        context = {'form':form}
        return render(request, 'AdminPortal/create.html',context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

@company_session_required
@login_required(login_url='/')
def multiapproval_view(request):
    try:
        company = Company.objects.get(id=request.company)
        records = MultiApprover.objects.filter(company_id = company.id)
        context = {'records':records,'screen_name':"View Multiapprovels"}
        return render(request, 'AdminPortal/multiapproval_view.html',context)
    except Exception as error:
        return render(request, '500.html', {'error': error})


@company_session_required
@login_required(login_url='/')
def multiapproval_delete(request,pk):
    try:
        company = Company.objects.get(id=request.company)
        records = MultiApprover.objects.get(id=pk).delete()
        return redirect('multiapprovalview')
    except Exception as error:
        return render(request, '500.html', {'error': error})
    

