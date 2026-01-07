from django.contrib import admin
from .models import *
# Register your models here.
admin.site.register(User)
admin.site.register(Role)
admin.site.register(Company)
admin.site.register(UserSubscription)
admin.site.register(Notification)
admin.site.register(Feedback)
admin.site.register(Feedback_Reasons)

@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ('name', 'company', 'phone_number', 'manager_name', 'city', 'country', 'created_at')
    list_filter = ('country', 'state', 'city', 'company')
    search_fields = ('name', 'manager_name', 'city', 'state', 'country')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'update_at')

    fieldsets = (
        ("Branch Details", {
            'fields': ('company', 'name', 'address', 'phone_number', 'manager_name', 
                       'country', 'state', 'city', 'local_currency', 'description', 'branch_api_id')
        }),
        ("Audit Information", {
            'fields': ('created_by', 'update_by', 'created_at', 'update_at')
        }),
    )