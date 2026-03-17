from user_management.models import *
from SupplierPortal.models import *


def check_branch_limit(request):
    if not request.user.is_authenticated:
        return False
    
    try:
        print('------------------------------------')
        print('user company',request.user.company_id)
        company_id = request.user.company_id
        if company_id:
            company = company_id
            user_sub = UserSubscription.objects.get(company=company)
            print('User Subscription:', user_sub)
            plan_name = str(user_sub.plan_name).lower()
            print('Plan Name:', plan_name)

        else:
            return False
        branch_count = Branch.objects.filter(company_name=company).count()
        print('Branch Count:', branch_count)

        plan_limits = {
            'free': 1,
            'basic': 4,
            'standard': 10,
            'premium': 5,
            'entrepreneur': 10,
            'unlimited': None,
        }

        limit = plan_limits.get(plan_name)

        if limit is None:
            print('unlimited plan -> Allowed')
            return True

        if branch_count < limit:
            print('Within limit -> Allowed')
            return True

        print('Limit reached -> Not Allowed')
        return False
    
    except Exception as e:
        print('Branch Error:',e)
        return False




def check_pr_limit(request):
    if not request.user.is_authenticated:
        return False
    supplier_store = request.supplier_store_id
    try:
        print('------------------------------------')
        print('user company',request.user.company_name_id)
        company_id = request.user.company_name_id
        if company_id:
            company = company_id
            user_sub = UserSubscription.objects.get(company=company)
            print('User Subscription:', user_sub)
            plan_name = str(user_sub.plan_name).lower()
            print('Plan Name:', plan_name)

        else:
            return False
        employee_count = main = SupplierOrderMain.objects.filter(company_id = company.id,supplierstore_id = supplier_store,order_status__iexact = "Pending").count()
        print('Employee Count:', employee_count)

        plan_limits = {
            'free': 1,
            'basic': 1,
            'standard': 10,
            'premium': 5,
            'entrepreneur': 10,
            'unlimited': None,
        }

        limit = plan_limits.get(plan_name)

        if limit is None:
            print('unlimited plan -> Allowed')
            return True

        if employee_count < limit:
            print('Within limit -> Allowed')
            return True

        print('Limit reached -> Not Allowed')
        return False
    
    except Exception as e:
        print('Branch Error:',e)
        return False

def check_pr_limit(request):
    if not request.user.is_authenticated:
        return False
    supplier_store = request.supplier_store_id
    try:
        print('------------------------------------')
        print('user company',request.user.company_name_id)
        company_id = request.user.company_name_id
        if company_id:
            company = company_id
            user_sub = UserSubscription.objects.get(company=company)
            print('User Subscription:', user_sub)
            plan_name = str(user_sub.plan_name).lower()
            print('Plan Name:', plan_name)

        else:
            return False
        supplier_count = main = SupplierOrderMain.objects.filter(company_id = company.id,supplierstore_id = supplier_store,order_status__iexact = "Pending").count()
        print('supplier Count:', supplier_count)

        plan_limits = {
            'free': 1,
            'basic': 1,
            'standard': 10,
            'premium': 5,
            'entrepreneur': 10,
            'unlimited': None,
        }

        limit = plan_limits.get(plan_name)

        if limit is None:
            print('unlimited plan -> Allowed')
            return True

        if supplier_count < limit:
            print('Within limit -> Allowed')
            return True

        print('Limit reached -> Not Allowed')
        return False
    
    except Exception as e:
        print('Branch Error:',e)
        return False

def check_invoice_limit(request):
    if not request.user.is_authenticated:
        return False
    supplier_store = request.supplier_store_id
    try:
        supplier_store = int(request.supplier_store_id)
        print('------------------------------------')
        print('user company',request.user.company_name_id)
        company_id = request.user.company_name_id
        if company_id:
            company = company_id
            user_sub = UserSubscription.objects.get(company=company)
            print('User Subscription:', user_sub)
            plan_name = str(user_sub.plan_name).lower()
            print('Plan Name:', plan_name)

        else:
            return False
        invoice_count = SupplierInvoice.objects.filter(store_to_id = supplier_store).count()
        print('invoice Count:', invoice_count)

        plan_limits = {
            'free': 1,
            'basic': 1,
            'standard': 10,
            'premium': 5,
            'entrepreneur': 10,
            'unlimited': None,
        }

        limit = plan_limits.get(plan_name)

        if limit is None:
            print('unlimited plan -> Allowed')
            return True

        if invoice_count < limit:
            print('Within limit -> Allowed')
            return True

        print('Limit reached -> Not Allowed')
        return False
    
    except Exception as e:
        print('Branch Error:',e)
        return False


def check_approval_limit(request):
    if not request.user.is_authenticated:
        return False
    supplier_store = request.supplier_store_id
    try:
        supplier_store = int(request.supplier_store_id)
        print('------------------------------------')
        print('user company',request.user.company_name_id)
        company_id = request.user.company_name_id
        if company_id:
            company = company_id
            user_sub = UserSubscription.objects.get(company=company)
            print('User Subscription:', user_sub)
            plan_name = str(user_sub.plan_name).lower()
            print('Plan Name:', plan_name)

        else:
            return False
        approval_count= SupplierInvoice.objects.filter(store_to_id = supplier_store).count()
        print('approval Count:', approval_count)

        plan_limits = {
            'free': 1,
            'basic': 1,
            'standard': 10,
            'premium': 5,
            'entrepreneur': 10,
            'unlimited': None,
        }

        limit = plan_limits.get(plan_name)

        if limit is None:
            print('unlimited plan -> Allowed')
            return True

        if approval_count < limit:
            print('Within limit -> Allowed')
            return True

        print('Limit reached -> Not Allowed')
        return False
    
    except Exception as e:
        print('Branch Error:',e)
        return False
