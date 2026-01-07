from django.shortcuts import render, redirect, get_object_or_404
from .models import *
from mainapp.models import *
from .forms import *
from user_management.decorators import company_session_required,supplier_store_session_required
from user_management.models import Role
@supplier_store_session_required
def supplierrole_list(request):
    try:
        supplierstore = SupplierStore.objects.get(id = request.supplier_store_id)
        supplier_roles = SupplierRole.objects.filter(supplier_id = supplierstore.supplier.id)
      
        return render(request, 'SupplierPortal/SupplierUsers/supplierrole_list.html', {'supplier_roles': supplier_roles})
    except Exception as error:
        return render(request, '500.html', {'error': error})

@company_session_required
@supplier_store_session_required
def supplierrole_create(request):
    try:
        supplierstore = SupplierStore.objects.get(id = request.supplier_store_id)
        if request.method == 'POST':
            form = SupplierRoleForm(request.POST)
            if form.is_valid():
                record = form.save(commit=False)
                record.company_id = request.company
                record.supplier_id = supplierstore.supplier.id
                record.save()

                return redirect('supplierrolelist')
        else:
            form = SupplierRoleForm()
        return render(request, 'SupplierPortal/create.html', {'form': form})
    except Exception as error:
        return render(request, '500.html', {'error': error})

def supplierrole_update(request, pk):
    supplier_role = get_object_or_404(SupplierRole, pk=pk)
    if request.method == 'POST':
        form = SupplierRoleForm(request.POST, instance=supplier_role)
        if form.is_valid():
            form.save()
            return redirect('supplierrole_list')
    else:
        form = SupplierRoleForm(instance=supplier_role)
    return render(request, 'supplierrole_form.html', {'form': form})

def supplierrole_delete(request, pk):
    supplier_role = get_object_or_404(SupplierRole, pk=pk)
    if request.method == 'POST':
        supplier_role.delete()
        return redirect('supplierrole_list')
    return render(request, 'supplierrole_confirm_delete.html', {'supplier_role': supplier_role})

# supplierrole permisstions
@company_session_required
def supplierpermission(request,pk): # pk is a supplierrole id
    try:
        company=Company.objects.get(id = request.company)
        # Fetch all Function objects
        records = SupplierFunction.objects.filter(company_id=company.id)
        role_obj = SupplierRole.objects.get(pk=pk,company_id=company.id)
        permission_records = role_obj.permissions.all()
        permission_id_list = [data.id for data in permission_records]
  
        if request.method == 'POST':
   
            
            # Fetch permissions from POST data
            permission_ids = request.POST.getlist('permission')
            if permission_ids:
                # Assuming permissions field is a ManyToManyField related to Function
                role_obj.permissions.set(permission_ids)  # Use set() instead of add() for a fresh list
            
            role_obj.save()
            return redirect('supplierrolelist')

        # Prepare the context for rendering
        context = {
            'roles': 'active', 
            'roles_show': 'show', 
            'screen_name': "Permission",
            'records': records,'permission_id_list':permission_id_list
        }
        return render(request, 'SupplierPortal/SupplierUsers/supplierpermission.html', context)
    
    except Exception as error:
        return render(request, '500.html', {'error': str(error)})

@company_session_required
@supplier_store_session_required
def supplieruser_list(request):
    company = Company.objects.get(id = request.company) 
    supplierstore = SupplierStore.objects.get(id = request.supplier_store_id)
    userlist = User.objects.filter(user_type='Supplier',is_active = True )
  
    context = {
        'user_list': 'active', 'user_list_show': 'show','records':userlist 
    }
    return render(request, 'SupplierPortal/SupplierUsers/supplieruser_list.html', context)

@company_session_required
@supplier_store_session_required
def supplieruser_create(request):
    try:
        company = Company.objects.get(id=request.company)
        supplierstore = SupplierStore.objects.get(id=request.supplier_store_id)
        filter_supplierrole = Role.objects.all()
        filter_supplierstore = SupplierStore.objects.filter(supplier_id=supplierstore.supplier.id)

        if request.method == "POST":
            form = UserSupplierCommonForm(request.POST)
            form.fields['role'].queryset = filter_supplierrole
            form.fields['supplierstore'].queryset = filter_supplierstore

            if form.is_valid():
        
                
                user_create = User.objects.create_user(
                    company_id=company.id,
                    first_name=form.cleaned_data['first_name'],
                    last_name=form.cleaned_data['last_name'],
                    email=form.cleaned_data['email'],
                    phone_number=form.cleaned_data['phone_number'],
                    password=form.cleaned_data['password'],  # create_user will hash password
                    user_type='Supplier',
                    is_staff=form.cleaned_data['is_staff'],
                    is_active=True,
                    is_admin=form.cleaned_data['is_admin'],
                )

                supplieruser = SupplierUser.objects.create(
                    user=user_create,
                    supplier_id=supplierstore.supplier.id,
                    role=form.cleaned_data['role'],
                    isadmin=form.cleaned_data['is_admin'],
                    is_staff=form.cleaned_data['is_staff'],
                )

                # After saving supplieruser, add many-to-many relationship
                supplieruser.store.set(form.cleaned_data['supplierstore'])

                print("IIIIIIIIIIIIIIIIIIIIIII",supplieruser)

                return redirect('supplieruser_list')

        else:
            form = UserSupplierCommonForm()
            form.fields['role'].queryset = filter_supplierrole
            form.fields['supplierstore'].queryset = filter_supplierstore

        context = {'form': form}
        return render(request, 'SupplierPortal/create.html', context)

    except Exception as error:
        return render(request, '500.html', {'error': str(error)})
