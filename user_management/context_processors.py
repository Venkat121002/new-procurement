from user_management.models import Company
from .models import Function
from user_management.models import Notification
def custom_permissions(request):
    user = request.user
    if user.is_authenticated:
        if user.is_superuser:
            return {
                'user_permissions': [data.function_name for data in Function.objects.all()], 
            }
        else:
            return {
                'user_permissions': [data.function_name for data in user.roles.permissions.all()] if user.roles else [], 
            }
    return {}


def companylogin_details(request):
    company = None
    print("usermanagement context process--------------------------------")
    if hasattr(request, 'company'):
        try:
            company = Company.objects.get(id=request.company)
        except Company.DoesNotExist:
            company = None

    return {
        'current_company': company
    }

def alert_messages(request):
    message = None

    if request.user.is_authenticated:
        print('request.user in context processor', request.user)
        message = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).last()
        print('messages in context processor', message)

    return {'alert_messages': message}