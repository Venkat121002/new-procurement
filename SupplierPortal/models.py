from django.db import models
from django.core.exceptions import ValidationError
from mainapp.models import SupplierStore

class SupplierFunction(models.Model):
    company = models.ForeignKey("user_management.Company", on_delete=models.CASCADE, related_name='%(class)s_companies')
    function_name=models.CharField(max_length=100)
    function_id=models.CharField(max_length=100, unique=True,blank=True,null=True)
    description = models.TextField(max_length=800,blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.function_name 
    
class SupplierRole(models.Model):
    company = models.ForeignKey("user_management.Company", on_delete=models.CASCADE, related_name='%(class)s_companies')
    supplier = models.ForeignKey('mainapp.Supplier',on_delete=models.CASCADE, related_name='%(class)s_companies')
    name = models.CharField(max_length=200)
    permissions = models.ManyToManyField(SupplierFunction)
    description = models.TextField(max_length=800,blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class SupplierUser(models.Model):
    user = models.ForeignKey("user_management.User", on_delete=models.CASCADE, related_name='%(class)s_supplieruser')
    supplier = models.ForeignKey("mainapp.Supplier", on_delete=models.CASCADE, related_name='%(class)s_supplierrole')
    role = models.ForeignKey("user_management.Role", on_delete=models.CASCADE, related_name='%(class)s_supplierrole')
    store = models.ManyToManyField(SupplierStore)
    isadmin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)



class SupplierOrderMain(models.Model):
    ORDER_STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('PartiallyDelivered', 'PartiallyDelivered'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
    ]
    company = models.ForeignKey("user_management.Company", on_delete=models.CASCADE, related_name='%(class)s_companies')
    supplier = models.ForeignKey('mainapp.Supplier',on_delete=models.CASCADE,)
    supplierstore = models.ForeignKey('mainapp.SupplierStore',on_delete=models.CASCADE, related_name='%(class)s_currentstore')
    deliverystore = models.ForeignKey('mainapp.SupplierStore',on_delete=models.CASCADE, related_name='%(class)s_deliverystore')
    po_number = models.CharField(max_length=50, unique=True)
    vendor = models.ForeignKey('mainapp.Vendor', on_delete=models.CASCADE)
    order_date = models.DateTimeField(auto_now_add=True)
    expected_delivery = models.DateField()
    approval_status = models.CharField(max_length=20, choices=[('Pending', 'Pending'), ('Approved', 'Approved'),('Rejected','Rejected')], default='Pending')
    order_status = models.CharField(max_length=20,choices=ORDER_STATUS_CHOICES, default='Pending')
    total_amount = models.FloatField(default=0.0)
    tracking_number = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    rejection_reason = models.TextField(blank=True, null=True,)

    def __str__(self):
        return self.po_number

class SupplierOrderItemSub(models.Model):
    ORDER_STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('PartiallyDelivered', 'PartiallyDelivered'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
    ]
    company = models.ForeignKey("user_management.Company", on_delete=models.CASCADE, related_name='%(class)s_companies')
    OrderType = [("Piece","Piece"),("Package","Package")]
    DiscountType = [("Fixed","Fixed"),("Percentage","Percentage")]
    supplier = models.ForeignKey('mainapp.Supplier',on_delete=models.CASCADE)
    supplierstore = models.ForeignKey('mainapp.SupplierStore',on_delete=models.CASCADE)
    order = models.ForeignKey(SupplierOrderMain, on_delete=models.CASCADE, related_name="order_items")
    item_unit = models.ForeignKey('mainapp.ItemUnit', on_delete=models.CASCADE)  # Track the unit type
    package_size = models.ForeignKey('mainapp.PackageSizeMaster', on_delete=models.SET_NULL, null=True, blank=True)  # Optional for bulk orders
    ordertype = models.CharField(max_length= 50,choices=OrderType)
    quantity = models.IntegerField(default=0)
    received_qty = models.IntegerField(default = 0)
    pending_received_qty = models.IntegerField(default = 0)
    unit_price = models.FloatField(default=0.0) # its not unit price its actual price based on package or unit
    total_price = models.FloatField(default=0.0)
    tax = models.FloatField(default=0.0)
    discount = models.FloatField(default=0.0)
    discount_type = models.CharField(max_length= 50, choices=DiscountType)
    order_status = models.CharField(max_length=20,choices=ORDER_STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)


class POApproval(models.Model):
    po_details = models.ForeignKey(SupplierOrderMain, on_delete=models.CASCADE, related_name="%(class)s_order_items")
    approver = models.ForeignKey("user_management.User", on_delete=models.CASCADE, related_name='%(class)s_supplieruser')
    status = models.CharField(max_length=20, choices=[('Pending', 'Pending'), ('Approved', 'Approved'),('Rejected','Rejected')], default='Pending')
    reject_reason = models.TextField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)

class SupplierOrderItemTemp(models.Model):
    company = models.ForeignKey("user_management.Company", on_delete=models.CASCADE, related_name='%(class)s_companies')
    OrderType = [("Piece","Piece"),("Package","Package")]
    DiscountType = [("Fixed","Fixed"),("Percentage","Percentage")]
    supplier = models.ForeignKey('mainapp.Supplier',on_delete=models.CASCADE)
    supplierstore = models.ForeignKey('mainapp.SupplierStore',on_delete=models.CASCADE)
    item_unit = models.ForeignKey('mainapp.ItemUnit', on_delete=models.CASCADE)  # Track the unit type
    package_size = models.ForeignKey('mainapp.PackageSizeMaster', on_delete=models.SET_NULL, null=True, blank=True)  # Optional for bulk orders
    ordertype = models.CharField(max_length= 50,choices=OrderType)
    quantity = models.IntegerField(default=0.0)
    unit_price = models.FloatField(default=0.0)
    total_price = models.FloatField(default=0.0)
    tax = models.FloatField(default=0.0)
    discount = models.FloatField(default=0.0)
    discount_type = models.CharField(max_length= 50, choices=DiscountType)
    created_at = models.DateTimeField(auto_now_add=True)

class GoodsReceived(models.Model):
    company = models.ForeignKey("user_management.Company", on_delete=models.CASCADE, related_name='%(class)s_companies')
    supplier = models.ForeignKey('mainapp.Supplier',on_delete=models.CASCADE)
    store_to = models.ForeignKey('mainapp.SupplierStore', on_delete=models.CASCADE, related_name='%(class)s_store_to')
    vendor = models.ForeignKey('mainapp.Vendor', on_delete=models.CASCADE)
    po_number = models.ForeignKey('SupplierPortal.SupplierOrderMain', on_delete=models.CASCADE, related_name='%(class)s_orderdetails')
    GRN_number = models.CharField(max_length=50, unique=True)
    received_by = models.CharField(max_length=50,blank=True, null=True)
    GRN_amount = models.FloatField(default=0.0)
    received_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

class SupplierInventoryBatchWise(models.Model):
    DiscountType = [("Fixed","Fixed"),("Percentage","Percentage")]
    ReceiveType = [("Piece","Piece"),("Package","Package")]
    company = models.ForeignKey("user_management.Company", on_delete=models.CASCADE, related_name='%(class)s_companies')
    supplier = models.ForeignKey('mainapp.Supplier',on_delete=models.CASCADE,blank=True, null=True)
    store_to = models.ForeignKey('mainapp.SupplierStore', on_delete=models.CASCADE, related_name='%(class)s_store_to')
    receiveddetails = models.ForeignKey(GoodsReceived,on_delete=models.CASCADE, related_name='%(class)s_item',blank=True, null=True)
    item_unit = models.ForeignKey('mainapp.ItemUnit', on_delete=models.CASCADE, related_name='%(class)s_item_unit')
    receivetype = models.CharField(max_length=100,choices=ReceiveType)
    expiry_date = models.DateField(blank=True, null=True)
    batch_no = models.CharField(max_length=100,blank=True, null=True)
    packsize = models.ForeignKey('mainapp.PackageSizeMaster', on_delete=models.CASCADE, related_name='%(class)s_packsize',blank=True, null=True)
    inhand_package = models.IntegerField(default=0) # if package then save here or
    inhand_pieces = models.IntegerField(default=0) # if piece then save here or
    total_amount = models.FloatField(default=0.0)
    piece_amt = models.FloatField(default=0.0)
    package_amount = models.FloatField(default=0.0)
    package_selling_rate = models.FloatField(default=0.0)
    piece_selling_rate = models.FloatField(default=0.0)
    tax = models.FloatField(default=0.0)
    discount = models.FloatField(default=0.0)
    discount_type = models.CharField(max_length= 50, choices=DiscountType)
    stock_balance = models.CharField(max_length=50,blank=True, null=True)
    received_qty = models.IntegerField(default=0)
    received_date = models.DateField()
    manufacture_date = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self,*args,**kwargs):
        self.stock_balance = f"{self.inhand_package}W{self.inhand_pieces}P"
        super().save(*args,**kwargs)  # Call the real save() method

    def __str__(self):
        return f'{self.pk}'

class SupplierInventory(models.Model):
    company = models.ForeignKey("user_management.Company", on_delete=models.CASCADE, related_name='%(class)s_companies')
    supplier = models.ForeignKey('mainapp.Supplier',on_delete=models.CASCADE,blank=True, null=True)
    store_to = models.ForeignKey('mainapp.SupplierStore', on_delete=models.CASCADE, related_name='%(class)s_store_to')
    item_unit = models.ForeignKey('mainapp.ItemUnit', on_delete=models.CASCADE, related_name='%(class)s_item_unit')
    packsize = models.ForeignKey('mainapp.PackageSizeMaster', on_delete=models.CASCADE, blank=True, null=True,related_name='%(class)s_packsize')
    inhand_package = models.IntegerField(default=0.0)
    inhand_pieces = models.IntegerField(default=0.0)
    piece_amt = models.FloatField(default=0.0)
    package_amount = models.FloatField(default=0.0)
    package_selling_rate = models.FloatField(default=0.0)
    piece_selling_rate = models.FloatField(default=0.0)
    tax = models.FloatField(default=0.0)
    stock_balance = models.CharField(max_length=50,blank=True, null=True)
    def __str__(self):
        return f'{self.pk}'

class SupplierInvoice(models.Model):
    company = models.ForeignKey("user_management.Company", on_delete=models.CASCADE, related_name='%(class)s_companies')
    supplier = models.ForeignKey('mainapp.Supplier',on_delete=models.CASCADE)
    store_to = models.ForeignKey('mainapp.SupplierStore', on_delete=models.CASCADE, related_name='%(class)s_store_to')
    po_number = models.ForeignKey('SupplierPortal.SupplierOrderMain', on_delete=models.CASCADE, related_name='%(class)s_orderdetails',blank=True, null=True)
    GRN_number = models.ForeignKey('SupplierPortal.GoodsReceived', on_delete=models.CASCADE, related_name='%(class)s_orderdetails',blank=True, null=True)
    received_by = models.CharField(max_length=50,blank=True, null=True)
    GRN_amount = models.FloatField(default=0.0)
    paid_amount = models.FloatField(default=0.0)
    pending_amount = models.FloatField(default=0.0)
    refference_number = models.CharField(max_length=50,blank=True, null=True)
    refference_type = models.CharField(max_length=50,blank=True, null=True)
    currency = models.CharField(max_length=50,blank=True, null=True)
    payment_complexity = models.CharField(max_length=50,blank=True, null=True)
    payment_status = models.CharField(max_length=20, choices=[('Pending', 'Pending'), ('PartiallyPaid', 'PartiallyPaid'),('Paid','Paid')], default='Pending')
    invoice = models.CharField(max_length=50,unique=True)
    received_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)

    def save(self, *args, **kwargs):
        # Calculate pending amount
        self.pending_amount = self.GRN_amount - self.paid_amount

        # Update payment_status based on amounts
        if self.paid_amount == 0.0:
            self.payment_status = 'Pending'
        elif self.pending_amount == 0.0:
            self.payment_status = 'Paid'
        else:
            self.payment_status = 'PartiallyPaid'

        super().save(*args, **kwargs)

class SupplierPayment(models.Model):
    company = models.ForeignKey("user_management.Company", on_delete=models.CASCADE, related_name='%(class)s_companies')
    supplier = models.ForeignKey('mainapp.Supplier', on_delete=models.CASCADE)
    store_to = models.ForeignKey('mainapp.SupplierStore', on_delete=models.CASCADE, related_name='%(class)s_store_to_ok', blank=True, null=True)
    invoice = models.ForeignKey('SupplierInvoice', on_delete=models.CASCADE, related_name='payments')
    payment_date = models.DateField(auto_now_add=True)
    paid_by = models.CharField(max_length=50,blank=True, null=True) 
    payment_method = models.CharField(max_length=50, choices=[
        ('Card', 'Card'),
        ('Cash', 'Cash'),
        ('Mpesa', 'Mpesa'),
    ])
    bank_no = models.CharField(max_length=50,blank=True, null=True) 
    transaction_reference = models.CharField(max_length=100, blank=True, null=True)
    holder_name = models.CharField(max_length=100, blank=True, null=True)
    mobile_number = models.IntegerField(blank=True, null=True)
    paid_amount = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)


class StockReturnToManufacturerMain(models.Model):
    company = models.ForeignKey("user_management.Company", on_delete=models.CASCADE, related_name='%(class)s_companies')
    supplier = models.ForeignKey('mainapp.Supplier', on_delete=models.CASCADE, related_name='%(class)s_supplier')
    store = models.ForeignKey('mainapp.SupplierStore', on_delete=models.CASCADE, related_name='%(class)s_store') # return from
    manufacturer = models.ForeignKey('mainapp.Vendor', on_delete=models.CASCADE, related_name='%(class)s_manufacturer') # return to
    return_id = models.CharField(max_length=50,unique=True)
    return_by = models.CharField(max_length=50,blank=True,null=True)
    return_date = models.DateField(auto_now_add=True)
    total_amount = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)

class StockReturnToManufacturerSub(models.Model):
    ReturnType = [("Piece","Piece"),("Package","Package")]
    company = models.ForeignKey("user_management.Company", on_delete=models.CASCADE, related_name='%(class)s_companies')
    returnmain = models.ForeignKey("StockReturnToManufacturerMain", on_delete=models.CASCADE, related_name='%(class)s_main')
    item_unit = models.ForeignKey('mainapp.ItemUnit', on_delete=models.CASCADE, related_name='%(class)s_item_unit')
    returntype = models.CharField(max_length=100,choices=ReturnType)
    batch = models.ForeignKey('SupplierInventoryBatchWise', on_delete=models.CASCADE, related_name='%(class)s_batch')
    quantity = models.IntegerField(default=0)
    amount = models.FloatField(default=0.0)
    reason = models.TextField(blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True)

class SupplierInventoryWastage(models.Model):
    WASTAGE_REASON_CHOICES = [
        ("Expired", "Expired"),
        ("Damaged", "Damaged"),
        ("Spoiled", "Spoiled"),
        ("Lost", "Lost"),
        ("Other", "Other")
    ]
    WastageType = [("Piece","Piece"),("Package","Package")]
    company = models.ForeignKey("user_management.Company", on_delete=models.CASCADE, related_name='%(class)s_companies',blank=True,null=True)
    supplier = models.ForeignKey('mainapp.Supplier', on_delete=models.CASCADE, related_name='%(class)s_supplier',blank=True,null=True)
    store = models.ForeignKey('mainapp.SupplierStore', on_delete=models.CASCADE, related_name='%(class)s_store',blank=True,null=True) # return from
    inventory_batch = models.ForeignKey('SupplierInventoryBatchWise',on_delete=models.CASCADE,related_name="wastages")
    wastage_date = models.DateField(auto_now_add=True)
    reason = models.CharField(max_length=50, choices=WASTAGE_REASON_CHOICES)
    wastage_type = models.CharField(max_length=50, choices=WastageType)
    wastage_qty = models.IntegerField(default=0)
    amount = models.FloatField(default=0.0)
    remarks = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

class SupplierStoreToStoreRequestMain(models.Model):
    ORDER_STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('PartiallyDelivered', 'PartiallyDelivered'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
    ]
    company = models.ForeignKey("user_management.Company", on_delete=models.CASCADE, related_name='%(class)s_companies')
    supplier = models.ForeignKey('mainapp.Supplier',on_delete=models.CASCADE,related_name='%(class)s_requestfromstore')
    supplierstore_from = models.ForeignKey('mainapp.SupplierStore',on_delete=models.CASCADE,related_name='%(class)s_requesttostore')
    supplierstore_destination = models.ForeignKey('mainapp.SupplierStore',on_delete=models.CASCADE)
    request_number = models.CharField(max_length=50, unique=True)
    request_date = models.DateTimeField(auto_now_add=True)
    expected_delivery = models.DateField()
    approval_status = models.CharField(max_length=20, choices=[('Pending', 'Pending'), ('Approved', 'Approved'),('Rejected','Rejected')], default='Pending')
    order_status = models.CharField(max_length=20,choices=ORDER_STATUS_CHOICES, default='Pending')
    total_amount = models.FloatField(default=0.0)
    tracking_number = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    rejection_reason = models.TextField(blank=True, null=True,)

    def __str__(self):
        return f'{self.request_number}'

class SupplierStoreToStoreRequestSub(models.Model):
    ORDER_STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('PartiallyDelivered', 'PartiallyDelivered'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
    ]
    company = models.ForeignKey("user_management.Company", on_delete=models.CASCADE, related_name='%(class)s_companies')
    OrderType = [("Piece","Piece"),("Package","Package")]
    DiscountType = [("Fixed","Fixed"),("Percentage","Percentage")]
    supplier = models.ForeignKey('mainapp.Supplier',on_delete=models.CASCADE)
    supplierstore = models.ForeignKey('mainapp.SupplierStore',on_delete=models.CASCADE)
    order = models.ForeignKey(SupplierStoreToStoreRequestMain, on_delete=models.CASCADE, related_name="%(class)s_order_itemsa")
    item_unit = models.ForeignKey('mainapp.ItemUnit', on_delete=models.CASCADE)  # Track the unit type
    package_size = models.ForeignKey('mainapp.PackageSizeMaster', on_delete=models.SET_NULL, null=True, blank=True)  # Optional for bulk orders
    ordertype = models.CharField(max_length= 50,choices=OrderType)
    quantity = models.IntegerField(default=0)
    received_qty = models.IntegerField(default = 0) # totally how much receive to item requested store
    pending_received_qty = models.IntegerField(default = 0)
    unit_price = models.FloatField(default=0.0) # its not unit price its actual price based on package or unit
    total_price = models.FloatField(default=0.0)
    tax = models.FloatField(default=0.0)
    discount = models.FloatField(default=0.0)
    discount_type = models.CharField(max_length= 50, choices=DiscountType,default="Percentage")
    order_status = models.CharField(max_length=20,choices=ORDER_STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)

class SupplierStoreToStoreRequestTemp(models.Model):
    company = models.ForeignKey("user_management.Company", on_delete=models.CASCADE, related_name='%(class)s_companies')
    OrderType = [("Piece","Piece"),("Package","Package")]
    DiscountType = [("Fixed","Fixed"),("Percentage","Percentage")]
    supplier = models.ForeignKey('mainapp.Supplier',on_delete=models.CASCADE)
    supplierstore = models.ForeignKey('mainapp.SupplierStore',on_delete=models.CASCADE)
    item_unit = models.ForeignKey('mainapp.ItemUnit', on_delete=models.CASCADE)  # Track the unit type
    package_size = models.ForeignKey('mainapp.PackageSizeMaster', on_delete=models.SET_NULL, null=True, blank=True)  # Optional for bulk orders
    ordertype = models.CharField(max_length= 50,choices=OrderType)
    quantity = models.IntegerField(default=0.0)
    unit_price = models.FloatField(default=0.0)
    total_price = models.FloatField(default=0.0)
    tax = models.FloatField(default=0.0)
    discount = models.FloatField(default=0.0)
    discount_type = models.CharField(max_length= 50, choices=DiscountType,default="Percentage")
    created_at = models.DateTimeField(auto_now_add=True)

class StockTransferMain(models.Model):
    ApprovalStatus = [('Pending','Pending'),('Approved','Approved'),('Reject','Reject')]
    TrackingStatus = [('Pending','Pending'),('Delivered','Delivered')]
    TransferType = [('Direct','Direct'),('Requested','Requested')]
    company = models.ForeignKey("user_management.Company", on_delete=models.CASCADE, related_name='%(class)s_companies')
    supplier = models.ForeignKey('mainapp.Supplier', on_delete=models.CASCADE, related_name='%(class)s_supplier')
    storefrom = models.ForeignKey('mainapp.SupplierStore', on_delete=models.CASCADE, related_name='%(class)s_store') # return from
    destinationstore = models.ForeignKey('mainapp.SupplierStore', on_delete=models.CASCADE, related_name='%(class)s_destinationstore') # return to
    request = models.ForeignKey('SupplierPortal.SupplierStoreToStoreRequestMain',on_delete=models.CASCADE, related_name='%(class)s_storerequest',blank=True,null=True)
    transfer_id = models.CharField(max_length=50,unique=True)
    transfer_date = models.DateField(auto_now_add=True)
    transfertype = models.CharField(max_length=50,choices=TransferType)
    total_amount = models.FloatField(default = 0.0)
    delivery_date = models.DateField(blank=True, null=True)
    approval_status = models.CharField(max_length=50,choices=ApprovalStatus,default="Pending")
    tracking_status = models.CharField(max_length=50,choices=TrackingStatus,default="Pending")
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True, null=True)
    confirmed_date = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.transfer_id}'


class StockTransferSub(models.Model):
    TransferType = [("Piece","Piece"),("Package","Package")]
    company = models.ForeignKey("user_management.Company", on_delete=models.CASCADE, related_name='%(class)s_companies')
    supplier = models.ForeignKey('mainapp.Supplier', on_delete=models.CASCADE, related_name='%(class)s_supplier',blank=True, null=True)
    storefrom = models.ForeignKey('mainapp.SupplierStore', on_delete=models.CASCADE, related_name='%(class)s_store',blank=True,null=True) # return from
    destinationstore = models.ForeignKey('mainapp.SupplierStore', on_delete=models.CASCADE, related_name='%(class)s_destinationstore',blank=True,null=True) # return to
    transfermain = models.ForeignKey("StockTransferMain", on_delete=models.CASCADE, related_name='%(class)s_main')
    item_unit = models.ForeignKey('mainapp.ItemUnit', on_delete=models.CASCADE, related_name='%(class)s_item_unit')
    request_sub = models.ForeignKey('SupplierPortal.SupplierStoreToStoreRequestSub', on_delete=models.CASCADE, related_name='%(class)s_item_requres6t',blank=True,null=True)
    transfertype = models.CharField(max_length=100,choices=TransferType)
    batch = models.ForeignKey('SupplierInventoryBatchWise',on_delete=models.CASCADE, related_name='%(class)s_batches')
    quantity = models.IntegerField(default=0)
    amount = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)

class TransferLogisticsDetails(models.Model):
    TRANSPORT_MODE_CHOICES = [
    ('truck', 'Truck'),
    ('van', 'Van'),
    ('air', 'Air Cargo'),
    ]

    stock_transfer = models.ForeignKey('StockTransferMain', on_delete=models.CASCADE, related_name='%(class)s_logistics_details')
    supplier = models.ForeignKey('mainapp.Supplier', on_delete=models.CASCADE, related_name='%(class)s_supplier',blank=True,null=True)
    currentstore = models.ForeignKey('mainapp.SupplierStore', on_delete=models.CASCADE, related_name='%(class)s_storefromsd',blank=True,null=True) # return from
    transfertype = models.CharField(max_length=20, choices=[('Direct','Direct'),('IntermediateStores','IntermediateStores')])
    logistics = models.ForeignKey('mainapp.LogisticsPartner',on_delete=models.CASCADE,blank=True, null=True)
    vehicle_number = models.CharField(max_length=50)
    type = models.CharField(max_length=50 )
    transport_mode = models.CharField(max_length=20, choices=TRANSPORT_MODE_CHOICES)
    driver_name = models.CharField(max_length=100,null=True, blank=True)
    driver_contact = models.CharField(max_length=20,null=True, blank=True)
    departure_time = models.DateTimeField(null=True, blank=True)
    arrival_estimate = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    sender_signature = models.ImageField(upload_to='signatures/sender/', null=True, blank=True)
    driver_signature = models.ImageField(upload_to='signatures/driver/', null=True, blank=True)
   

class TransferLogisticsStores(models.Model):
    supplier = models.ForeignKey('mainapp.Supplier', on_delete=models.CASCADE, related_name='%(class)s_supplier',blank=True,null=True)
    currentstore = models.ForeignKey('mainapp.SupplierStore', on_delete=models.CASCADE, related_name='%(class)s_storeasd',blank=True,null=True) # return from
    stock_transfer = models.ForeignKey('TransferLogisticsDetails', on_delete=models.CASCADE, related_name='%(class)slogistics_details')
    stores = models.ForeignKey('mainapp.SupplierStore', on_delete=models.CASCADE, related_name='%(class)s_store')
    status = models.CharField(max_length=20, choices=[('Pending','Pending'),('Reached','Reached')])
    reached_date = models.DateField(blank=True,null=True)
    reached = models.BooleanField(default=False)



class ManualStockAdjustment(models.Model):
    company = models.ForeignKey("user_management.Company", on_delete=models.CASCADE, related_name='%(class)s_companies')
    supplier = models.ForeignKey('mainapp.Supplier', on_delete=models.CASCADE, related_name='%(class)s_supplier')
    store = models.ForeignKey('mainapp.SupplierStore', on_delete=models.CASCADE, related_name='%(class)s_store')
    adjustment_date = models.DateTimeField(auto_now_add=True,)
    item_name = models.ForeignKey('mainapp.ItemUnit', on_delete=models.CASCADE, related_name='%(class)s_item_names')
    packsize = models.ForeignKey('mainapp.PackageSizeMaster', on_delete=models.CASCADE, related_name='%(class)s_packsize')
    batch_no = models.ForeignKey(SupplierInventoryBatchWise, on_delete=models.CASCADE, related_name='%(class)s_batch_no')
    expiry_date = models.DateField(blank=True, null=True)
    amount = models.FloatField(default="0.0")
    remark = models.TextField(blank=True, null=True,)
	



class SupplierStockAdjustMain(models.Model):
    company = models.ForeignKey("user_management.Company", on_delete=models.CASCADE, related_name='%(class)s_companies_kk_supplier')
    supplier = models.ForeignKey('mainapp.Supplier', on_delete=models.CASCADE, related_name='%(class)s_supplier_on')
    supplierstore = models.ForeignKey('mainapp.SupplierStore', on_delete=models.CASCADE, related_name='%(class)s_store_supplier') # return from
    return_id = models.CharField(max_length=50,unique=True)
    return_by = models.CharField(max_length=50,blank=True,null=True)
    return_date = models.DateField(auto_now_add=True)
    total_amount = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)    

class SupplierStockAdjustmentSub(models.Model):
    ReturnType = [("Piece","Piece"),("Package","Package")]
    company = models.ForeignKey("user_management.Company", on_delete=models.CASCADE, related_name='%(class)s_companies_pp_supplier')
    returnmain = models.ForeignKey("SupplierStockAdjustMain", on_delete=models.CASCADE, related_name='%(class)s_returnmainw_kk')
    item_unit = models.ForeignKey('mainapp.ItemUnit', on_delete=models.CASCADE, related_name='%(class)s_item_unit_oo_kk')
    returntype = models.CharField(max_length=100,choices=ReturnType)
    batch = models.ForeignKey('SupplierInventoryBatchWise', on_delete=models.CASCADE, related_name='%(class)s_batch_oo_jj')
    quantity = models.IntegerField(default=0)
    amount = models.FloatField(default=0.0)
    reason = models.TextField(blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True)    



class BOMMapping(models.Model):
    company = models.ForeignKey("user_management.Company", on_delete=models.CASCADE, related_name='%(class)s_companies_kk_supplier')
    supplier = models.ForeignKey('mainapp.Supplier', on_delete=models.CASCADE, related_name='%(class)s_supplier_on')
    supplierstore = models.ForeignKey('mainapp.SupplierStore', on_delete=models.CASCADE, related_name='%(class)s_store_supplier') # return from
    own_product = models.ForeignKey('mainapp.ItemUnit', on_delete=models.CASCADE,related_name='%(class)s_ownproduct')
    product = models.ForeignKey('mainapp.ItemUnit', on_delete=models.CASCADE,related_name='%(class)s_usingproduct')
    quantity_required = models.FloatField(default=0.0)
    wastage_percent = models.FloatField(default=0.0, help_text="Enter wastage percentage if any.")
    description = models.TextField(blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.own_product}"

