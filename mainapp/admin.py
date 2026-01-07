from django.contrib import admin
from .models import *


@admin.register(CustomerRegistrations)
class CustomerRegistrationsAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'phone', 'customer_type', 'registration_method', 'verified_by_admin', 'rejection_reason', 'approved_by', 'approval_date']
    search_fields = ['name', 'email', 'phone']
@admin.register(ItemCategoryMaster)
class ItemCategoryMasterAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']

@admin.register(UnitOfMeasure)
class UnitOfMeasureAdmin(admin.ModelAdmin):
    list_display = ['name', 'symbol']

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ['supplier_name', 'short_name', 'contact_person', 'kas_membership_number',  'address', 'city', 'district', 'pincode', 'phone', 'email', 'website']
    search_fields = ['supplier_name', 'short_name', 'contact_person', 'phone', 'email'] 
@admin.register(CountryMaster)
class CountryMasterAdmin(admin.ModelAdmin):
    list_display = ['country_name']

@admin.register(LogisticsPartner)
class LogisticsPartnerAdmin(admin.ModelAdmin):
    list_display = ['name', 'contact_person', 'phone', 'email', 'description']

@admin.register(BrandMaster)
class BrandMasterAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']

@admin.register(StoreTypeMaster)
class StoreTypeMasterAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']

@admin.register(Customerstore)
class CustomerstoreAdmin(admin.ModelAdmin):
    list_display = ['customer', 'name', 'location', 'contact_number', 'manager_name', 'description']
    search_fields = ['name', 'location', 'contact_number'] 

@admin.register(ItemSubCategoryMaster)
class ItemSubCategoryMasterAdmin(admin.ModelAdmin):
    list_display = ['category', 'name', 'description']

@admin.register(SupplierCustomerMapping)
class SupplierCustomerMappingAdmin(admin.ModelAdmin):
    list_display = ['supplier', 'customer', 'description']

@admin.register(Manufacturer)
class ManufacturerAdmin(admin.ModelAdmin):
    list_display = ['name', 'country', 'sub_country', 'contact_person', 'email', 'phone']

@admin.register(SubCountryMaster)
class SubCountryMasterAdmin(admin.ModelAdmin):
    list_display = ['country', 'sub_country']

@admin.register(SupplierStore)
class SupplierStoreAdmin(admin.ModelAdmin):
    list_display = ['supplier', 'storetype', 'name', 'location', 'contact_number', 'manager_name']

@admin.register(ItemMaster)
class ItemMasterAdmin(admin.ModelAdmin):
    list_display = ['item_name', 
                    # 'category', 'subcategory', 
                    'description', 'reorder_level', 'amount', 'tax_rate', 'discount', 'discount_type', 'barcode']

@admin.register(OrderRequestParent)
class OrderRequestParentAdmin(admin.ModelAdmin):
    list_display = ['po_datetime', 'supplier', 'customer', 'net_amount', 'basic_amt', 'po_status', 'purpose', 'invoice_no', 'delivery_instruction', 'deliver_date', 'payment_terms']

@admin.register(StockTransferRouteMain)
class StockTransferRouteMainAdmin(admin.ModelAdmin):
    list_display = ['name', 'supplier', 'to_store',  'tracking_id']

@admin.register(ItemUnit)
class ItemUnitAdmin(admin.ModelAdmin):
    list_display = ['item', 'unit', 'conversion_factor_to_base', 'price']

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_no', 'po', 'customer', 'issue_date', 'due_date', 'total_amount', 'tax_amount', 'discount_amount', 'net_amount', 'payment_status', 'payment_terms', 'payment_method', 'payment_reference', 'remarks']

@admin.register(StockTransferParent)
class StockTransferParentAdmin(admin.ModelAdmin):
    list_display = ['from_store', 'to_store', 'requests', 'transfer_date', 'delivery_date']

@admin.register(StockTransferRouteSub)
class StockTransferRouteSubAdmin(admin.ModelAdmin):
    list_display = ['transfer', 'intermediate_store', 'sequence', 'description']

@admin.register(PackageSizeMaster)
class PackageSizeMasterAdmin(admin.ModelAdmin):
    list_display = ['itemunit', 'quantity', 'pack_price', 'brand']

@admin.register(PackageAssignment)
class PackageAssignmentAdmin(admin.ModelAdmin):
    list_display = ['logistics_partner', 'stock', 'roots', 'currentlocation', 'assigned_at', 'status']


@admin.register(OrderRequestChild)
class OrderRequestChildAdmin(admin.ModelAdmin):
    list_display = ['poid', 'po_datetime', 'item_name', 'packsize', 'request_type', 'packs_qty', 'pieces_qty', 'piece_amt', 'pack_amount', 'received_qty', 'outstanding_qty', 'selling_pack_rate', 'selling_pieces_rate', 'tax', 'total_amt', 'discount', 'discount_type', 'stock_balance', 'manually_confirm', 'supplier_approval_status']


@admin.register(StockTransferChild)
class StockTransferChildAdmin(admin.ModelAdmin):
    list_display = ['requests', 'item_name', 'packsize', 'request_type', 'quantity']

@admin.register(MultiApprover)
class MultiApproverAdmin(admin.ModelAdmin):
    list_display = ['id', 'created_at', 'process', 'user']

# @admin.register(Role)
# class RoleAdmin(admin.ModelAdmin):
#     list_display = ['user_type', 'name', 'description']
