from datetime import timezone
from django.db import models
# from bb_id_gen_app.models import ModelRegistration
from user_management.models import Company, User
from django.core.validators import FileExtensionValidator
import barcode
from barcode.writer import ImageWriter
from io import BytesIO
from django.core.files import File
from django.db import models
from barcode import Code128

class CustomerRegistrations(models.Model):
	company = models.ForeignKey("user_management.Company", on_delete=models.CASCADE, related_name='%(class)s_companies')
	name = models.CharField(max_length=255,)
	email = models.EmailField(unique=False ,)
	phone = models.CharField(max_length=20,)
	customer_type = models.CharField(max_length=20,choices=[('retailer', 'Retailer'), ('distributor', 'Distributor'), ('direct_customer', 'Direct_customer')],)
	registration_method = models.CharField(max_length=20,choices=[('invitation', 'Invitation'), ('direct', 'Direct')],)
	verified_by_admin = models.BooleanField(default=False, )
	rejection_reason = models.TextField(blank=True, null=True,)
	approved_by = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True, related_name="%(class)s_approved_by")
	approval_date = models.DateTimeField(auto_now_add=True,)
	def __str__(self):
		return f'{self.name}'

class ItemCategoryMaster(models.Model):
	company = models.ForeignKey("user_management.Company", on_delete=models.CASCADE, related_name='%(class)s_companies')
	name = models.CharField(max_length=255,unique=False ,)
	description = models.TextField(blank=True, null=True,)
	created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)	
	def __str__(self):
		return f'{self.name}'

class UnitOfMeasure(models.Model):
	company = models.ForeignKey("user_management.Company", on_delete=models.CASCADE, related_name='%(class)s_companies')
	name = models.CharField(max_length=100,)
	symbol = models.CharField(max_length=10,)
	def __str__(self):
		return f'{self.name}'

class Supplier(models.Model):
	company = models.ForeignKey("user_management.Company", on_delete=models.CASCADE, related_name='%(class)s_companies')
	supplier_name = models.CharField(max_length=100)
	short_name = models.CharField(max_length=100,)
	contact_person = models.CharField(max_length=100,)
	kas_membership_number = models.CharField(max_length=50,unique=True ,)
	# business_registration_certificate = models.FileField(upload_to="documents/", validators=[FileExtensionValidator(allowed_extensions=["pdf", "doc", "docx"])], )
	# tax_compliance_documents = models.FileField(upload_to="documents/", validators=[FileExtensionValidator(allowed_extensions=["pdf", "doc", "docx"])], blank=True, null=True)
	address = models.CharField(max_length=100,)
	city = models.CharField(max_length=100,blank=True, null=True ,)
	district = models.CharField(max_length=100,blank=True, null=True ,)
	pincode = models.CharField(max_length=100,blank=True, null=True ,)
	phone = models.CharField(max_length=100,blank=True, null=True ,)
	email = models.EmailField(("emailaddress"), unique=True)
	website = models.CharField(max_length=100,blank=True, null=True ,)
	verified_by_admin = models.BooleanField(default=False, )

	status = models.CharField(max_length=20,choices=[('pending', 'pending'), ('Accepted', 'Accepted'),('Rejected','Rejected')],default='pending')
	rejection_reason = models.TextField(blank=True, null=True,)

	def __str__(self):
		return f'{self.supplier_name}'

class CountryMaster(models.Model):
	company = models.ForeignKey("user_management.Company", on_delete=models.CASCADE, related_name='%(class)s_companies_on' )
	country_name = models.CharField(max_length=100,)
	def __str__(self):
		return f'{self.country_name}'

class LogisticsPartner(models.Model):
    company = models.ForeignKey(
        "user_management.Company", 
        on_delete=models.CASCADE, 
        related_name='%(class)s_companies'
    )
    name = models.CharField(max_length=255)
    contact_person = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    address = models.TextField(blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    services_offered = models.TextField(blank=True, null=True, help_text="List of logistics services like shipping, warehousing, etc.")
    license_number = models.CharField(max_length=100, blank=True, null=True)
    contract_start_date = models.DateField(blank=True, null=True)
    contract_end_date = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    rating = models.DecimalField(max_digits=3, decimal_places=2, blank=True, null=True, help_text="Average rating out of 5.00")
    description = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)

    def __str__(self):
        return f'{self.name} ({self.contact_person})'


class BrandMaster(models.Model):
	company = models.ForeignKey("user_management.Company", on_delete=models.CASCADE, related_name='%(class)s_companies')
	name = models.CharField(max_length=255,)
	description = models.TextField(blank=True, null=True,)
	def __str__(self):
		return f'{self.name}'

class StoreTypeMaster(models.Model):
	company = models.ForeignKey("user_management.Company", on_delete=models.CASCADE, related_name='%(class)s_companies')
	name = models.CharField(max_length=50,unique=False ,)
	description = models.TextField(blank=True, null=True,)
	def __str__(self):
		return f'{self.name}'

class Customerstore(models.Model):
	company = models.ForeignKey("user_management.Company", on_delete=models.CASCADE, related_name='%(class)s_companies')
	branch = models.ForeignKey('DistributorBranch', on_delete=models.CASCADE, related_name='%(class)s_companies_one_news_sky', blank=True, null=True)
	customer = models.ForeignKey('CustomerRegistrations', on_delete=models.CASCADE, related_name='%(class)s_customer')
	name = models.CharField(max_length=255,)
	location = models.CharField(max_length=255,)
	contact_number = models.CharField(max_length=50,)
	manager_name = models.CharField(max_length=100,)
	description = models.TextField(blank=True, null=True,)
	purchase_access = models.BooleanField(default=False)
	def __str__(self):
		return f'{self.name}'

class ItemSubCategoryMaster(models.Model):
	company = models.ForeignKey("user_management.Company", on_delete=models.CASCADE, related_name='%(class)s_companies')
	category = models.ForeignKey('ItemCategoryMaster', on_delete=models.CASCADE, related_name='%(class)s_category')
	name = models.CharField(max_length=255,)
	description = models.TextField(blank=True, null=True,)
	def __str__(self):
		return f'{self.name}'

class SupplierCustomerMapping(models.Model):
	company = models.ForeignKey("user_management.Company", on_delete=models.CASCADE, related_name='%(class)s_companies')
	customer = models.ForeignKey('CustomerRegistrations', on_delete=models.CASCADE, related_name='%(class)s_customer')
	supplier = models.ForeignKey('Supplier', on_delete=models.CASCADE, related_name='%(class)s_supplier')
	description = models.TextField(blank=True, null=True,)
	def __str__(self):
		return f'{self.pk}'

class Manufacturer(models.Model):
	company = models.ForeignKey("user_management.Company", on_delete=models.CASCADE, related_name='%(class)s_companies')
	name = models.CharField(max_length=255,)
	country = models.ForeignKey('CountryMaster', on_delete=models.CASCADE, related_name='%(class)s_country')
	sub_country = models.ForeignKey('CountryMaster', on_delete=models.CASCADE, related_name='%(class)s_sub_country')
	contact_person = models.CharField(max_length=255,)
	email = models.EmailField()
	phone = models.CharField(max_length=20,)
	def __str__(self):
		return f'{self.name}'

class SubCountryMaster(models.Model):
	company = models.ForeignKey("user_management.Company", on_delete=models.CASCADE, related_name='%(class)s_companies')
	country = models.ForeignKey('CountryMaster', on_delete=models.CASCADE, related_name='%(class)s_country')
	sub_country = models.CharField(max_length=100,)
	def __str__(self):
		return f'{self.pk}'

class SupplierStore(models.Model):
	company = models.ForeignKey("user_management.Company", on_delete=models.CASCADE, related_name='%(class)s_companies')
	supplier = models.ForeignKey('Supplier', on_delete=models.CASCADE, related_name='%(class)s_supplier')
	storetype = models.ForeignKey('StoreTypeMaster', on_delete=models.CASCADE, related_name='%(class)s_storetype')
	name = models.CharField(max_length=255,)
	location = models.CharField(max_length=255,)
	contact_number = models.CharField(max_length=50,)
	manager_name = models.CharField(max_length=100,)
	is_mainstore = models.BooleanField(default=False)
	is_active = models.BooleanField(default=False)
	def __str__(self):
		return f'{self.name}'

class ItemMaster(models.Model):
	company = models.ForeignKey("user_management.Company", on_delete=models.CASCADE, related_name='%(class)s_companies')
	category = models.ForeignKey('ItemCategoryMaster', on_delete=models.CASCADE, related_name='%(class)s_category')
	subcategory = models.ForeignKey('ItemSubCategoryMaster', on_delete=models.CASCADE, blank=True, null=True,related_name='%(class)s_subcategory')
	item_name = models.CharField(max_length=255,)
	description = models.TextField(blank=True, null=True,)
	reorder_level = models.FloatField(default=0.0)
	amount = models.FloatField(default=0.0)
	tax_rate = models.FloatField(default=0.0)
	discount = models.FloatField(default=0.0)
	discount_type = models.CharField(max_length=100,choices=[('Percentage', 'Percentage'), ('Fixed', 'Fixed')],)
	barcode = models.CharField(max_length=100,blank=True, null=True ,unique=False ,)
	created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)	
	def __str__(self):
		return self.item_name

class StockTransferRouteMain(models.Model):
	company = models.ForeignKey("user_management.Company", on_delete=models.CASCADE, related_name='%(class)s_companies')
	name = models.CharField(max_length=100,)
	supplier = models.ForeignKey('Supplier', on_delete=models.CASCADE, related_name='%(class)s_from_store',blank=True, null=True)
	to_store = models.ForeignKey('Customerstore', on_delete=models.CASCADE, related_name='%(class)s_to_store')
	tracking_id = models.CharField(max_length=100,blank=True, null=True ,unique=False ,)
	def __str__(self):
		return f'{self.name}'

class StockTransferRouteSub(models.Model):
	company = models.ForeignKey("user_management.Company", on_delete=models.CASCADE, related_name='%(class)s_companies')
	transfer = models.ForeignKey('StockTransferRouteMain', on_delete=models.CASCADE, related_name='%(class)s_transfer')
	intermediate_store = models.ForeignKey('SupplierStore', on_delete=models.CASCADE, related_name='%(class)s_intermediate_store')
	sequence = models.IntegerField()
	description = models.TextField(blank=True, null=True,)
	def __str__(self):
		return f'{self.pk}'

class OrderRequestParent(models.Model):
	company = models.ForeignKey("user_management.Company", on_delete=models.CASCADE, related_name='%(class)s_companies')
	po_datetime = models.DateField()
	supplier = models.ForeignKey('Customerstore', on_delete=models.CASCADE, related_name='%(class)s_supplier')
	customer = models.ForeignKey('SupplierStore', on_delete=models.CASCADE, related_name='%(class)s_customer')
	net_amount = models.FloatField(default="0.0", )
	basic_amt = models.FloatField(default="0.0", )
	po_status = models.CharField(max_length=50,choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected'), ('shipped', 'Shipped'), ('delivered', 'Delivered'), ('cancelled', 'Cancelled')],)
	purpose = models.CharField(max_length=50,blank=True, null=True ,)
	invoice_no = models.CharField(max_length=50,)
	delivery_instruction = models.CharField(max_length=255,blank=True, null=True ,)
	deliver_date = models.DateField(blank=True, null=True,)
	payment_terms = models.CharField(max_length=20,blank=True, null=True ,choices=[('prepaid', 'Prepaid'), ('postpaid', 'Postpaid')],)
	def __str__(self):
		return f'{self.po_datetime}'
	
class ItemUnit(models.Model):
    company = models.ForeignKey(
        "user_management.Company",
        on_delete=models.CASCADE,
        related_name='%(class)s_companies'
    )
    item = models.ForeignKey(
        'ItemMaster',
        on_delete=models.CASCADE,
        related_name='%(class)s_item'
    )
    itemname = models.CharField(max_length=50, blank=True, null=True)
    brand = models.ForeignKey(
        'BrandMaster',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='%(class)s_brand'
    )
    unit = models.ForeignKey(
        'UnitOfMeasure',
        on_delete=models.CASCADE,
        related_name='%(class)s_unit'
    )
    conversion_factor_to_base = models.FloatField(default=0.0)
    price = models.FloatField(default=0.0)
    ownproduct = models.BooleanField(default=False)

    barcode_image = models.ImageField(upload_to='barcodes/', blank=True, null=True)
    barcode_value = models.CharField(
        max_length=100,
        unique=True,
        blank=True,
        null=True
    )

    def __str__(self):
        return f'{self.item} {self.unit} {self.brand}'

    def save(self, *args, **kwargs):
        is_new = self.pk is None

        # First save → get PK
        super().save(*args, **kwargs)

        # Generate barcode value only once
        if is_new and not self.barcode_value:
            self.barcode_value = f'ITEMUNIT{self.pk:06}'
            super().save(update_fields=['barcode_value'])

        # Generate barcode image if not exists
        if self.barcode_value and not self.barcode_image:
            self.generate_barcode()

    def generate_barcode(self):
        EAN = barcode.get_barcode_class('code128')
        ean = EAN(self.barcode_value, writer=ImageWriter())

        buffer = BytesIO()
        ean.write(buffer)

        filename = f'barcode_{self.barcode_value}.png'
        self.barcode_image.save(filename, File(buffer), save=False)

        super().save(update_fields=['barcode_image'])

class Invoice(models.Model):
	company = models.ForeignKey("user_management.Company", on_delete=models.CASCADE, related_name='%(class)s_companies')
	invoice_no = models.CharField(max_length=50,unique=False ,)
	po = models.ForeignKey('OrderRequestParent', on_delete=models.CASCADE, related_name='%(class)s_po')
	customer = models.ForeignKey('Customerstore', on_delete=models.CASCADE, related_name='%(class)s_customer')
	issue_date = models.DateField()
	due_date = models.DateField()
	total_amount = models.FloatField(default="0.0", )
	tax_amount = models.FloatField(default="0.0", )
	discount_amount = models.FloatField(default="0.0", )
	net_amount = models.FloatField(default="0.0", )
	payment_status = models.CharField(max_length=20,choices=[('pending', 'Pending'), ('partially_paid', 'Partially_paid'), ('paid', 'Paid'), ('overdue', 'Overdue'), ('cancelled', 'Cancelled')],default="pending", )
	payment_terms = models.CharField(max_length=20,blank=True, null=True ,choices=[('prepaid', 'Prepaid'), ('postpaid', 'Postpaid')],)
	payment_method = models.CharField(max_length=20,blank=True, null=True ,choices=[('bank_transfer', 'Bank_transfer'), ('mpesa', 'Mpesa'), ('online_payment', 'Online_payment'), ('cash', 'Cash')],)
	payment_reference = models.CharField(max_length=100,blank=True, null=True ,)
	remarks = models.TextField(blank=True, null=True,)
	def __str__(self):
		return f'{self.invoice_no}'

class StockTransferParent(models.Model):
	company = models.ForeignKey("user_management.Company", on_delete=models.CASCADE, related_name='%(class)s_companies')
	from_store = models.ForeignKey('SupplierStore', on_delete=models.CASCADE, related_name='%(class)s_from_store')
	to_store = models.ForeignKey('Customerstore', on_delete=models.CASCADE, related_name='%(class)s_to_store')
	requests = models.ForeignKey('OrderRequestParent', on_delete=models.CASCADE, related_name='%(class)s_requests')
	transfer_date = models.DateTimeField(auto_now_add=True,)
	delivery_date = models.DateTimeField(blank=True, null=True,)
	def __str__(self):
		return f'{self.pk}'



class PackageSizeMaster(models.Model):
	company = models.ForeignKey("user_management.Company", on_delete=models.CASCADE, related_name='%(class)s_companies')
	itemunit = models.ForeignKey('ItemUnit', on_delete=models.CASCADE, related_name='%(class)s_itemunit')
	package_name = models.CharField(max_length=100)
	quantity = models.PositiveIntegerField()
	pack_price = models.FloatField(default=0.0)
	brand = models.ForeignKey('BrandMaster', on_delete=models.CASCADE, blank=True, null=True, related_name='%(class)s_brand')
	barcode_image = models.ImageField(upload_to='package_barcodes/', blank=True, null=True)
	barcode_value = models.CharField(max_length=100, unique=True, blank=True, null=True)


	def __str__(self):
		return f'{self.package_name} {self.quantity}'

	def save(self, *args, **kwargs):
		# Generate barcode_value if empty
		if not self.barcode_value:
			# Example format: package_name-quantity-random4chars
			import random
			import string
			rand_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
			self.barcode_value = f"{self.package_name}-{self.quantity}-{rand_str}"

		super().save(*args, **kwargs)

		# Generate barcode image if not exists
		if not self.barcode_image:
			buffer = BytesIO()
			barcode = Code128(self.barcode_value, writer=ImageWriter())
			barcode.write(buffer)
			file_name = f"{self.barcode_value}.png"
			self.barcode_image.save(file_name, File(buffer), save=False)

			super().save(update_fields=['barcode_image'])

class PackageAssignment(models.Model):
	company = models.ForeignKey("user_management.Company", on_delete=models.CASCADE, related_name='%(class)s_companies')
	logistics_partner = models.ForeignKey('LogisticsPartner', on_delete=models.CASCADE, related_name='%(class)s_logistics_partner')
	stock = models.ForeignKey('StockTransferParent', on_delete=models.CASCADE, related_name='%(class)s_stock')
	roots = models.ForeignKey('StockTransferRouteMain', on_delete=models.CASCADE, related_name='%(class)s_roots')
	currentlocation = models.CharField(max_length=20,blank=True, null=True ,)
	assigned_at = models.DateTimeField(auto_now_add=True,)
	status = models.CharField(max_length=20,choices=[('assigned', 'Assigned'), ('in_transit', 'In_transit'), ('delivered', 'Delivered')],)
	def __str__(self):
		return f'{self.pk}'

#===== Supplier Inventory===============


class OrderRequestChild(models.Model):
	company = models.ForeignKey("user_management.Company", on_delete=models.CASCADE, related_name='%(class)s_companies')
	poid = models.ForeignKey('OrderRequestParent', on_delete=models.CASCADE, related_name='%(class)s_poid')
	po_datetime = models.DateField()
	item_name = models.ForeignKey('ItemUnit', on_delete=models.CASCADE, related_name='%(class)s_item_name')
	packsize = models.ForeignKey('PackageSizeMaster', on_delete=models.CASCADE, related_name='%(class)s_packsize')
	request_type = models.CharField(max_length=50,choices=[('Whole', 'Whole'), ('Pieces', 'Pieces')],)
	packs_qty = models.IntegerField(default="0", )
	pieces_qty = models.IntegerField(default="0", )
	piece_amt = models.FloatField(default="0.0", )
	pack_amount = models.FloatField(default="0.0", )
	received_qty = models.IntegerField(default="0", )
	outstanding_qty = models.IntegerField(default="0", )
	selling_pack_rate = models.FloatField(default="0.0", )
	selling_pieces_rate = models.FloatField(default="0.0", )
	tax = models.FloatField(default="0.0", )
	total_amt = models.FloatField(default="0.0", )
	discount = models.FloatField(default="0.0", )
	discount_type = models.CharField(max_length=50,choices=[('Percentage', 'Percentage'), ('Fixed', 'Fixed')],)
	stock_balance = models.CharField(max_length=50,blank=True, null=True ,)
	manually_confirm = models.BooleanField(default=False, )
	supplier_approval_status = models.CharField(max_length=50,choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')],default="pending", )
	def __str__(self):
		return f'{self.pk}'



class StockTransferChild(models.Model):
	company = models.ForeignKey("user_management.Company", on_delete=models.CASCADE, related_name='%(class)s_companies')
	requests = models.ForeignKey('OrderRequestChild', on_delete=models.CASCADE, related_name='%(class)s_requests')
	item_name = models.ForeignKey('ItemUnit', on_delete=models.CASCADE, related_name='%(class)s_item_name')
	packsize = models.ForeignKey('PackageSizeMaster', on_delete=models.CASCADE, related_name='%(class)s_packsize')
	request_type = models.CharField(max_length=50,choices=[('Whole', 'Whole'), ('Pieces', 'Pieces')],)
	quantity = models.IntegerField(default="0.0", )
	def __str__(self):
		return f'{self.pk}'



class Invite(models.Model):
    email = models.EmailField(unique=True)  # Email field with unique constraint
    def __str__(self):
        return self.name



class ProductMaster(models.Model):
	company = models.ForeignKey("user_management.Company", on_delete=models.CASCADE, related_name='%(class)s_companies')
	name = models.CharField(max_length=255)
	subcategory = models.ForeignKey('ItemSubCategoryMaster', on_delete=models.CASCADE, related_name='products')
	brand = models.ForeignKey('BrandMaster', on_delete=models.CASCADE, related_name='products')
	description = models.TextField(blank=True, null=True)
	price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)  
	created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)	
	
	def __str__(self):
		return f"{self.brand.name} {self.name} ({self.subcategory.name})"

class Vendor(models.Model):
    SUPPLIER_TYPE_CHOICES = [
        ('wholesaler', 'Wholesaler'),
        ('importer', 'Importer'),
        ('dropshipper', 'Dropshipper'),
    ]

    company = models.ForeignKey("user_management.Company", on_delete=models.CASCADE, related_name='%(class)s_companies')
    name = models.CharField(max_length=255, unique=True)
    supplier_type = models.CharField(max_length=20, choices=SUPPLIER_TYPE_CHOICES)
    contact_person = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    address = models.TextField()
    country = models.CharField(max_length=100)
    tax_id = models.CharField(max_length=50, blank=True, null=True)  # GST/VAT etc.
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name}"
	

class DistributorBranch(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='branches_on_ss',blank=True,null=True)
    customer = models.ForeignKey('mainapp.CustomerRegistrations',related_name='branches_on_ssk',on_delete=models.CASCADE,blank=True,null=True)
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=255)
    phone_number = models.PositiveBigIntegerField()
    manager_name = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    state = models.CharField(max_length=100)    
    city = models.CharField(max_length=100)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    def _str_(self):
        return f"{self.name} - {self.company.name}"


class LogisticsVehicle(models.Model):
	TRANSPORT_MODE_CHOICES = [
		('truck', 'Truck'),
		('van', 'Van'),
		('air', 'Air Cargo')]
	company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='%(class)s_branches',blank=True,null=True)
	partner = models.ForeignKey(LogisticsPartner, on_delete=models.CASCADE, related_name='vehicles')
	vehicle_number = models.CharField(max_length=50)
	transport_mode = models.CharField(max_length=20, choices=TRANSPORT_MODE_CHOICES)
	capacity = models.FloatField(help_text="In tons or as per unit")
	is_active = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)
	update_at = models.DateTimeField(auto_now=True)

class MultiApprover(models.Model):
	PROCESS_CHOICES = [
		('PurchaseOrder', 'PurchaseOrder'),('IntenalRequest', 'Intenal Request')
	]
	company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='%(class)s_branches',blank=True,null=True)
	process = models.CharField(max_length=50,choices=PROCESS_CHOICES)
	user = models.ForeignKey("user_management.User", on_delete=models.CASCADE, related_name='%(class)s_supplieruser')
	description = models.TextField(blank=True,null=True)
	created_at = models.DateTimeField(auto_now_add=True)
	update_at = models.DateTimeField(auto_now=True)