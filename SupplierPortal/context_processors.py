from SupplierPortal.models import SupplierStore
from user_management.decorators import *

def supplier_store_details(request):
    store = None
    print("context process--------------------------------")
    if hasattr(request, 'supplier_store_id'):
        try:
            store = SupplierStore.objects.get(id=request.supplier_store_id)
        except SupplierStore.DoesNotExist:
            store = None

    return {
        'current_store': store
    }