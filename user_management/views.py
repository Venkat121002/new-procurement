from django.shortcuts import render, redirect,get_object_or_404

from mainapp.models import Customerstore, SupplierStore,DistributorBranch,Supplier
from user_management.decorators import company_session_required,distributorbranch_session_required
from .forms import *
from django.contrib.auth.hashers import make_password
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import logout
from bb_id_gen_app.scripts import simple_unique_id_generation
import json
from SupplierPortal.models import SupplierUser,SupplierFunction
from .models import *
from urllib.parse import urlparse
import re


def dashboard(request):
    return render(request, 'dashboard.html')

@company_session_required
def user_registration(request):
    company=Company.objects.get(id = request.company) 
    roles = Role.objects.filter(company_id = company.id)

    user=request.session['is_superuser']
    # contact=Contacts.objects.filter(branch_id=request.branch_id)
    print('buyer-idddd',request.user.buyer_id)
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST,is_superuser=user)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.password = make_password(form.cleaned_data.get('password'))
            obj.company_id=company.id
            obj.buyer_id = request.user.buyer_id
            obj.is_superuser = form.cleaned_data.get('is_superadmin')
            obj.save()
            return redirect('user_list')  # Redirect to a success page after registration
        else:
            print("======",form.errors)
    else:
        form = UserRegistrationForm(is_superuser=user)

    context = {
        'form': form, 'user_registration': 'active', 'user_registration_show': 'show',
    }
    return render(request, 'UserManagement/user_registration.html', context)



@company_session_required
def user_list(request):
    company=Company.objects.get(id = request.company) 
    if request.user.is_superuser or request.user.is_company_admin:
        records = User.objects.filter(is_active=True,company_id=company.id)
        context = {
            'user_list': 'active', 'user_list_show': 'show', 'records': records
        }
        return render(request, 'UserManagement/user_list.html', context)
    else:
        user_type=request.user.user_type
        print('user_type',user_type)
        roles=Role.objects.filter(user_type=user_type)
        print('roles',roles)
        records = User.objects.filter(is_active=True,company_id=company.id,roles__in=roles)
        context = {
            'user_list': 'active', 'user_list_show': 'show', 'records': records
        }
        return render(request, 'UserManagement/user_list.html', context)


@company_session_required
def user_edit(request,pk):
    try:
 
        company=Company.objects.get(id = request.company) 
        record=User.objects.get(pk=pk,company_id=company.id)
        if request.method == 'POST':
            form = UserRegistrationForm(request.POST,instance=record)
            if form.is_valid():
                obj=form.save()
                return redirect('user_list') 
        else:
            form = UserRegistrationForm(instance=record)

        context = {
            'form': form, 'user_edit': 'active', 'user_edit_show': 'show',
        }
        return render(request,'SupplierPortal/create.html',context)
        
        #return render(request, 'UserManagement/user_edit.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

@company_session_required
def user_view(request,pk):
    try:
        company=Company.objects.get(id = request.company) 
        record=User.objects.get(pk=pk,company_id=company.id)
        form = UserRegistrationForm(instance=record)

        context = {
            'user_list': 'active', 'user_list_show': 'show', 'form': form,'screen_name':'User'
        }
        return render(request, 'UserManagement/user_view.html', context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

@company_session_required
def user_delete(request,pk):
    try:
        company=Company.objects.get(id = request.company) 
        obj=User.objects.get(pk=pk)
        obj.is_active=False
        obj.save()
        return redirect('user_list')          
        #records = User.objects.all()
    except Exception as error:
        return render(request, '500.html', {'error': error})

def user_logout(request):
    if request.user.is_authenticated:
        logout(request)
        return redirect('user_login')
    else:
        return redirect('user_login')

@company_session_required
def roles(request):
    try:
        company=Company.objects.get(id = request.company) 
        records=Role.objects.filter(company_id=company.id)
        context={
            'records':records,'roles': 'active', 'roles_show': 'show'
        }
        return render(request,'UserManagement/roles.html',context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

@company_session_required
def roles_create(request):
    try:
        form = RoleForm()
        # branch=request.session['branch_id']
        company=Company.objects.get(id = request.company) 

        if request.method=='POST':
            form = RoleForm(request.POST)
            if form.is_valid():
                obj = form.save(commit=False)
                obj.created_by = request.user
                obj.updated_by = request.user
                obj.company_id=company.id
                obj.save()
                return redirect('roles')
        context={
            'roles': 'active', 'roles_show': 'show','form':form,'screen_name':"Roles"
        }
        return render(request,'AdminPortal/create.html',context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

def roles_edit(request,pk):
    try:
        record = Role.objects.get(pk=pk)
        form = RoleForm(instance=record)
        if request.method=='POST':
            form = RoleForm(request.POST,instance=record)
            if form.is_valid():
                obj = form.save(commit=False)
                obj.updated_by = request.user
                obj.save()
                return redirect('roles')
        context={
            'roles': 'active', 'roles_show': 'show','form':form,'screen_name':"Roles"
        }
        return render(request,'AdminPortal/create.html',context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

def roles_delete(request,pk):
    try:
        Role.objects.get(pk=pk).delete()
        return redirect('roles')
    except Exception as error:
        return render(request, '500.html', {'error': error})
    

@company_session_required
def permission(request, pk):
    try:
        company=Company.objects.get(id = request.company)
        # Fetch all Function objects
        records = Function.objects.filter(company_id=company.id)
        role_obj = Role.objects.get(pk=pk,company_id=company.id)
        permission_records = role_obj.permissions.all()
        permission_id_list = [data.id for data in permission_records]
        print('permission_records',permission_id_list)
        if request.method == 'POST':
   
            
            # Fetch permissions from POST data
            permission_ids = request.POST.getlist('permission')
            if permission_ids:
                # Assuming permissions field is a ManyToManyField related to Function
                role_obj.permissions.set(permission_ids)  # Use set() instead of add() for a fresh list
            
            role_obj.save()
            return redirect('roles')

        # Prepare the context for rendering
        context = {
            'roles': 'active', 
            'roles_show': 'show', 
            'screen_name': "Permission",
            'records': records,'permission_id_list':permission_id_list
        }
        return render(request, 'UserManagement/permission.html', context)
    
    except Exception as error:
        return render(request, '500.html', {'error': str(error)})


# Load the function names from the configuration file
def load_function_names_from_config(config_path='config/function_config.json'):
    with open(config_path, 'r') as config_file:
        config = json.load(config_file)
        return config.get('functions', [])


# Example usage in a view:
@company_session_required
def function_setup(request):
    try:
        company=Company.objects.get(id = request.company)
        user = request.user  # Use the currently logged-in user
        function_names = load_function_names_from_config()  # Load from the configuration file
        records_list = []

        for function_name in function_names:
            # Check if the function already exists
            if not Function.objects.filter(function_name=function_name,company_id=company.id).exists():
                # Create a new function
                function = Function.objects.create(
                    company_id=company.id,
                    function_name=function_name,
                    description=None,  # You can modify this to add descriptions if needed
                    created_by=user
                )
                # Assign a unique ID to the function
                function.function_id = simple_unique_id_generation("FUN", function.id)
                function.save()  # Save only if it's a new record
                records_list.append(function.function_name)
            else:
                # Log if the function already exists
                print(f"Function '{function_name}' already exists.")

        # Return the success response and redirect
        print('Added functions:', records_list)
        return redirect(request.META.get('HTTP_REFERER', '/'))
    
    except Exception as error:
        # Render a 500 error page with the exception details
        return render(request, '500.html', {'error': str(error)})
    
    
#====================Company======================

def company_create(request):
    try:
        form = CompanyForm()
        if request.method=='POST':
            form = CompanyForm(request.POST)
            if form.is_valid():
                obj = form.save()
                obj.save()
                return redirect('company_list')
        context={
            'roles': 'active', 'roles_show': 'show','form':form,'screen_name':"Company"
        }
        return render(request,'company_create.html',context)
    except Exception as error:
        return render(request, '500.html', {'error': error})


def company_create_admin(request):
    try:
        
        if request.method == "POST":
            form = CompanyForm(request.POST,request.FILES)
            if form.is_valid():
                company= form.save(commit=False)
                company_logo=form.cleaned_data.get('company_logo')
                application_logo=form.cleaned_data.get('application_logo')
                if company_logo:
                    company.company_logo=company_logo.read()
                if application_logo:
                    company.application_logo=application_logo.read()
                company.created_by = request.user 
                company.save()
              
                return redirect('select_company')
        else:
            form = CompanyForm()
        return render(request, 'UserManagement/company_create.html', {'form': form})
    except Exception as error:
            return render(request,'500.html',{'error':str(error)})

def company_list(request):
    try:
        records=Company.objects.all()
        context={
            'records':records,'roles': 'active', 'roles_show': 'show'
        }
        return render(request,'UserManagement/company_list.html',context)
    except Exception as error:
        return render(request, '500.html', {'error': error})
    

def company_detail(request, pk):
    try:
        company=Company.objects.get(pk=pk)
        return render(request, 'UserManagement/company_detail.html', {'company': company})

    except Exception as error:
        return render(request,'500.html',{'error':str(error)})
    
# Update----------------------------------->
def company_update(request, pk):
    try:
        record = Company.objects.get(pk=pk)
        form = CompanyForm(instance=record)
        if request.method=='POST':
            form = CompanyForm(request.POST,instance=record)
            if form.is_valid():
                obj = form.save()
                return redirect('company_list')
        context={
            'roles': 'active', 'roles_show': 'show','form':form,'screen_name':"Company"
        }
        return render(request,'company_update.html',context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

# Delete----------------------------------------->
def company_delete(request, pk):
    try:
        Company.objects.get(pk=pk).delete()
        return redirect('company_list')
    except Exception as error:
        return render(request, '500.html', {'error': error})
    
def select_company(request):
    try:
        company_list = Company.objects.all()
        form = CompanyForm()
        if request.method == 'POST':
            company_id = request.POST.get('company')
            request.session['company'] = company_id

            return redirect('dashboard')
        context = {
             'company_list':company_list,'form':form
        }
        return render(request, 'UserManagement/select_company.html',context)
    except Exception as error:
    #     # Handle any errors that occur
        return render(request, '500.html', {'error': str(error)}) 

    
def select_supplier_store(request,pk): # pk is a user id
    # try:
        user = User.objects.get(id = pk)
        request.session['company'] = user.company.id
        if user.is_admin:
            supplier = Supplier.objects.get(id = user.supplier.id)
            store_list = SupplierStore.objects.filter(supplier_id = supplier.id)
        else:
            suppieruser = SupplierUser.objects.get(user_id = user.id)
            store_list = suppieruser.store.all()

        if request.method == 'POST':
            store_id = request.POST.get('store')
            request.session['supplier_store_id'] = store_id if store_id else None
          
            if request.user.is_admin :
                request.session['store_id']=store_id
                records = SupplierFunction.objects.all() 
                permission_id_list = [data.function_name for data in records]
                request.session['permission']=permission_id_list
                
                return redirect('supplierdashboard')
            else:
                return redirect('supplierdashboard')
        context ={
            'store_list':store_list,
        }
        return render(request, 'UserManagement/select_supplier_store.html',context)
    # except Exception as error:
    #     # Handle any errors that occur
    #     return render(request, '500.html', {'error': str(error)})
    
@company_session_required
def select_distributor_branches(request,pk): #pk is a userid
    try:
        user = User.objects.get(id = pk)
        company = Company.objects.get(pk=request.user.company.pk)
        request.session['company'] = user.company.id
        if request.method == "POST":
            branch = request.POST.get('branch')
            request.session['distributorbranch'] = branch
            return redirect(f'/user_management/select_customer_store/{user.id}')
        else:
            if user.is_admin:  
                customerbranch_list = DistributorBranch.objects.filter(customer_id = user.customer.id) 
                return render(request, 'UserManagement/select_distributor_branches.html',{'customerbranch_list':customerbranch_list}) 
            else:
                distributoruser = DistributorUser.objects.get(user_id = user.id)
                request.session['DistributorBranch'] = distributoruser.branch.id
                return redirect(f'/user_management/select_customer_store/{user.id}')
    
    except Exception as error:
        # Handle any errors that occur
        return render(request, '500.html', {'error': str(error)})

@company_session_required
@distributorbranch_session_required
def select_customer_store(request,pk): # user id
    try:
        user = User.objects.get(id = pk)
        company = Company.objects.get(pk=request.user.company.pk)
        branch = DistributorBranch.objects.get(id = request.branch)
        request.session['company'] = user.company.id
        
        if user.is_admin:  
            customer_list = Customerstore.objects.filter(branch_id = branch.id)  
        else:
            distributoruser = DistributorUser.objects.get(user_id = user.id)
            customer_list = distributoruser.store.all()

        if request.method == 'POST':
            store_id = request.POST.get('store')
            request.session['Distributorstore_id'] = store_id if store_id else None
    
            if request.user.is_admin :
                request.session['Distributorstore_id']=store_id
                return redirect('customer_dashboard')
            else:
                return redirect('customer_dashboard')
        context ={
            'store_list':customer_list,'company':company
        }
        return render(request, 'UserManagement/select_customer_store.html',context)
    except Exception as error:
        # Handle any errors that occur
        return render(request, '500.html', {'error': str(error)})
    



def feedback_create(request):
    print('hhshshhshs',request.META.get('HTTP_REFERER', '/'))

    referer = request.META.get('HTTP_REFERER', '/')
    path = urlparse(referer).path      # '/collect_fees'
    last_name = path.strip('/').split('/')[-1]
    print('last name',last_name)
    name = path.strip('/').split('/')[-1].replace('_', ' ').title()
    print(name,'nameeeeeeeeeeeeee')
    if re.search(r'/\d+/?$', path) and request.method == "GET":
        return redirect(path)
    if request.method == "POST":
        reason_id = request.POST.get("reason")
        feedback_text = request.POST.get("feedback")
        return_url = request.POST.get("last_name")
        print('return_url',return_url)
        print('reason_id',reason_id)
        print('yyyyyyyyyyy',request.POST)
        reason = get_object_or_404(Feedback_Reasons, id=reason_id)
        Feedback.objects.create(
            user=request.user,
            reason=reason,
            feedback=feedback_text,
            name=last_name,
            endpoint=referer
        )
        print('the request user type is ',request.user.user_type)
        # if request.user.user_type == 'Student':
        #     print('in student redirect')
        #     return redirect(f"student/{return_url}")
        # elif request.user.user_type == 'parent':
        #     print('in parent redirect')
        #     return redirect(f"parent/{return_url}")
        # else:
        print('return url',return_url)
        print('the request user type is ',request.user.is_superuser)
        if request.user.is_company_admin or request.user.is_superuser: 

            return redirect('admin_dashboard')
            # base_template = 'AdminPortal/base.html'
        elif request.user.user_type == 'Supplier':

            return redirect('supplierdashboard')

    reasons = Feedback_Reasons.objects.all()


    return render(
        request,
        "feedback_create.html",
        {
            "reasons": reasons,
            "last_name": last_name,
            "name": name,
        }
    )

def feedback_list(request):
    # POST → SAVE ONLY FEEDBACK REASON
    if request.method == "POST":
        reason_text = request.POST.get("reason")

        if reason_text:
            Feedback_Reasons.objects.create(
                reason=reason_text
            )

        return redirect("feedback_list")

    # GET → LIST ONLY FEEDBACK
    feedbacks = Feedback.objects.select_related("user", "reason").order_by("-created_at")


    return render(
        request,
        "feedback_list.html",
        {
            "feedbacks": feedbacks,
        }
    )

