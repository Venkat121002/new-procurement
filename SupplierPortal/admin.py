from django.contrib import admin
from SupplierPortal.models import *
# Register your models here.
@admin.register(SupplierInventory)
class SupplierInventoryAdmin(admin.ModelAdmin):
    list_display = ['store_to', 'item_unit', 'packsize', 'inhand_package', 'inhand_pieces', 'piece_amt', 'package_amount', 'package_selling_rate', 'piece_selling_rate', 'tax', 'stock_balance']


@admin.register(ManualStockAdjustment)
class ManualStockAdjustmentAdmin(admin.ModelAdmin):
    list_display = ['supplier', 'store', 'adjustment_date', 'item_name', 'packsize', 'batch_no', 'expiry_date', 'amount', 'remark']

    
@admin.register(SupplierOrderItemTemp)
class SupplierOrderItemTempAdmin(admin.ModelAdmin):
    list_display = ['supplier','item_unit']

@admin.register(SupplierOrderMain)
class SupplierOrderMainAdmin(admin.ModelAdmin):
    list_display = ['supplier','po_number']

@admin.register(SupplierOrderItemSub)
class SupplierOrderItemSubAdmin(admin.ModelAdmin):
    list_display = ['OrderType','item_unit']


@admin.register(SupplierInvoice)
class SupplierInvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice', 'supplier', 'store_to', 'GRN_number', 'GRN_amount', 'paid_amount', 'pending_amount', 'payment_status', 'received_date', 'created_at')
    list_filter = ('payment_status', 'supplier',)
    search_fields = ('invoice', 'supplier__name', 'po_number__id', 'GRN_number__id')
    ordering = ('-received_date',) 

from django.contrib import admin
from .models import GoodsReceived

@admin.register(GoodsReceived)
class GoodsReceivedAdmin(admin.ModelAdmin):
    list_display = ('GRN_number', 'supplier', 'store_to', 'po_number', 'received_by', 'GRN_amount', 'received_date', 'created_at')
    list_filter = ( 'supplier', 'received_date')
    search_fields = ('GRN_number', 'received_by', 'supplier__name', 'po_number__id')
    ordering = ('-created_at',)
    date_hierarchy = 'received_date'


# @admin.register(GoodsReceived)
# class GoodsReceivedAdmin(admin.ModelAdmin):
#     list_display = ['supplier','vendor','po_number']

@admin.register(SupplierInventoryBatchWise)
class SupplierInventoryBatchWiseAdmin(admin.ModelAdmin):
    list_display = ['supplier','batch_no']

admin.site.register(StockReturnToManufacturerMain)
admin.site.register(StockReturnToManufacturerSub)
admin.site.register(SupplierFunction)
admin.site.register(SupplierRole)
admin.site.register(SupplierUser)
admin.site.register(StockTransferMain)
admin.site.register(StockTransferSub)
admin.site.register(TransferLogisticsDetails)
admin.site.register(TransferLogisticsStores)
admin.site.register(SupplierStoreToStoreRequestMain)
admin.site.register(SupplierStoreToStoreRequestSub)

