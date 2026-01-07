# your_app/decorators.py
from functools import wraps
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse

def check_permission(permission_codename):
    """
    Custom decorator to check if the user has a specific permission.
    
    :param permission_codename: The codename of the permission to check (e.g., 'app_name.permission_codename').
    """
    def decorator(view_func):
        @wraps(view_func)  # This helps to keep the original view function's metadata
        @login_required    # Ensures that the user is logged in before checking permissions
        def _wrapped_view(request, *args, **kwargs):
            # Check if the user has the required permission
            if request.user.is_superuser or request.user.is_company_admin or request.user.roles.permissions.filter(function_name=permission_codename):
                # If the user has the permission, call the original view
                return view_func(request, *args, **kwargs)
            else:
                # If the user does not have permission, raise PermissionDenied
                return render(request,'500.html')

        return _wrapped_view

    return decorator

def company_session_required(view_func):
    """
    Decorator to ensure the branch ID is available in the session.
    Passes the branch ID to the view if it exists.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Check if the branch ID is present in the session
        company = request.session.get('company')
        if company:
            # Attach company to the request object to pass to the view
            request.company = company
        else:
            # Handle case where branch ID is missing, e.g., redirect to select_branch
            return redirect('select_company')  # Adjust as necessary
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def supplier_store_session_required(view_func):
    """
    Decorator to ensure the branch ID is available in the session.
    Passes the branch ID to the view if it exists.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Check if the branch ID is present in the session
        supplier_store_id = request.session.get('supplier_store_id')
        
        if supplier_store_id:
            # Attach branch_id to the request object to pass to the view
            request.supplier_store_id = supplier_store_id
        
        else:
            # Handle case where branch ID is missing, e.g., redirect to select_branch
            return redirect('select_supplier_store', pk=request.user.pk)  # Adjust as necessary
        
        return view_func(request, *args, **kwargs)
    
    return wrapper

def customer_store_session_required(view_func):
    """
    Decorator to ensure the customer store ID is available in the session.
    Passes the customer store ID to the view if it exists.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        customer_store_id = request.session.get('Distributorstore_id')
        if customer_store_id:
            request.customer_store_id = customer_store_id
        else:
            # Redirect to the view where user selects a store
            return redirect(reverse('select_customer_store', kwargs={'pk': request.user.pk}))
        
        return view_func(request, *args, **kwargs)
    
    return wrapper

def distributorbranch_session_required(view_func):
    """
    Decorator to ensure the branch ID is available in the session.
    Passes the branch ID to the view if it exists.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Check if the branch ID is present in the session
        branch_id = request.session.get('distributorbranch')
        if branch_id:
            # Attach branch_id to the request object to pass to the view
            request.branch = branch_id
        else:
            # Handle case where branch ID is missing, e.g., redirect to select_branch
            return redirect('select_distributor_branches', pk=request.user.pk)  # Adjust as necessary
        
        return view_func(request, *args, **kwargs)
    
    return wrapper
