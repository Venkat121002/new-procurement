from django.shortcuts import get_object_or_404, render,redirect
from razorpay import Order

from SupplierPortal.forms import *
from user_management.decorators import company_session_required,supplier_store_session_required
from mainapp.models import *
from django.http import JsonResponse
from mainapp.forms import *
from django.utils.dateparse import parse_datetime
from datetime import date
from django.db.models import F, Sum, ExpressionWrapper, FloatField
from django.db.models import Q
from django.shortcuts import render
from django.db.models.functions import TruncMonth
from datetime import datetime
from user_management.models import Company
from django.contrib import messages
import qrcode
from io import BytesIO
from django.core.files.base import ContentFile

from django.utils import timezone
from SupplierPortal.models import *
from django.core.mail import send_mail
from django.urls import reverse
from django.conf import settings
from SupplierPortal.apicall import *
from django.db import transaction

def generate_unique_id(pre, suf):
    tot_rec_count = suf + 1

    # Format record count to 3 digits (e.g., 001, 012, 123)
    rec_str = str(tot_rec_count).zfill(3)

    # Get current date as YYMMDD
    date_str = datetime.now().strftime('%y%m%d')  # <-- 2-digit year

    # Construct ID: prefix + date + count (e.g., PO250516001)
    id = f"{pre}{date_str}{rec_str}"

    return id

def generate_unique_supplierbatch(Batch_name = None):
    count = SupplierInventoryBatchWise.objects.count()
    print("Gohila batch",type(Batch_name))
    if not Batch_name:
        Batch_name = "NilBat"
        
    while True:
        # Format: BATCH + YYMMDD + 3-digit count
        date_str = datetime.now().strftime('%y%m%d')
        count_str = str(count + 1)
        batch_no = f"{Batch_name}{date_str}{count_str}"
        
        if not SupplierInventoryBatchWise.objects.filter(batch_no=batch_no).exists():
            return batch_no
        count += 1

@company_session_required
@supplier_store_session_required
def supplierdashboard(request):
    try:
 
        company = Company.objects.get(id=request.company)
        customer_store = int(request.supplier_store_id)
        print("customer_store",customer_store)
        customerstore = SupplierStore.objects.get(id=customer_store)
        goods_recieved= GoodsReceived.objects.filter(company_id=request.company,store_to_id=customer_store).count()
        customer_inventory= SupplierInventoryBatchWise.objects.filter(company_id=company.id,store_to_id=customer_store).count()
        # distibutor_strore = Customerstore.objects.filter(company_id=request.company,customerstore_id=customer_store).count()
        # distributor_branch=DistributorBranch.objects.filter(company_id=request.company,customer_id=customer_store.customer.id).count()
        total_purchase = SupplierOrderMain.objects.filter(supplierstore_id=customer_store).count()
        total_invoice = SupplierInvoice.objects.filter(store_to_id=customer_store).count()
        invoices_pending = SupplierInvoice.objects.filter(store_to_id=customer_store,payment_status__in = ["Pending"]).count()
        invoices_partial = SupplierInvoice.objects.filter(store_to_id=customer_store,payment_status__in = ["PartiallyPaid"]).count()
        invoices_paid = SupplierInvoice.objects.filter(store_to_id=customer_store,payment_status__in = ["Paid"]).count()
        po_pending=SupplierOrderMain.objects.filter(supplierstore_id=customer_store,approval_status__in = ["Pending"]).count()
        po_approved= SupplierOrderMain.objects.filter(supplierstore_id=customer_store,approval_status__in = ["Approved"]).count()
        po_rejected= SupplierOrderMain.objects.filter(supplierstore_id=customer_store,approval_status__in = ["Rejected"]).count()
        po_completed=SupplierOrderMain.objects.filter(supplierstore_id=customer_store,approval_status__in = ["Completed"]).count()
        stock_return = StockReturnToManufacturerMain.objects.filter(store_id=customer_store).count()
        po_last=SupplierOrderItemSub.objects.filter(supplierstore_id=customer_store).order_by('-id')[:10]
        # store_stock_transfer = StockRequestToStoresMain.objects.filter(customerstore_id = customer_store).count()
        print('po_last',po_last)
     
        # recieve_stocks_pending= StockRequestToStoresMain.objects.filter(customerstore_id=customer_store,approval_status='Pending').count()
        total_purchase_sub = SupplierOrderItemSub.objects.filter(company_id=company.id,supplierstore_id=customer_store).count()
        total_inventory = SupplierInventoryBatchWise.objects.filter(store_to_id=customer_store).count()
        ss = SupplierPayment.objects.filter(supplier_id=customerstore.supplier.id)
        kk = ss.aggregate(total_amt=Sum('paid_amount'))
        total_paid_amount = kk['total_amt'] 
        print("total_paid_amount",total_paid_amount)
        pending_invoice = SupplierInvoice.objects.filter(store_to_id=customer_store)
        sk=pending_invoice.aggregate(total_amt=Sum('pending_amount'))
        pending_amount=sk['total_amt']

        inventory = SupplierInventoryBatchWise.objects.filter(store_to_id=customer_store)
        data = SupplierInventoryBatchWise.objects.filter(store_to_id=customer_store).values('item_unit__item__item_name').annotate(total=Sum('total_amount'))
    
        items = [d['item_unit__item__item_name'] for d in data]
        totals = [d['total'] for d in data]
        
        context = {'items':items,'totals':totals,
    'goods_recieved': goods_recieved,
    'customer_inventory': customer_inventory,
    'total_purchase': total_purchase,
    'total_invoice': total_invoice,
    'invoices_pending': invoices_pending,
    'invoices_partial': invoices_partial,
    'invoices_paid': invoices_paid,
    'po_pending': po_pending,
    'po_approved': po_approved,
    'po_rejected': po_rejected,
    'po_completed': po_completed,
    'stock_return': stock_return,
    'po_last': po_last,
    
    # 'store_stock_transfer': store_stock_transfer,
    # 'recieve_stocks_pending': recieve_stocks_pending,
    'total_purchase_sub': total_purchase_sub,
    'total_inventory': total_inventory,
    'total_paid_amount': total_paid_amount,
    'pending_amount': pending_amount,
}    
        print("context",context)

        return render(request,'SupplierPortal/supplierdashboard.html',context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

@company_session_required
@supplier_store_session_required
def supplierorder_view(request):
    try:
        company = Company.objects.get(id=request.company)
        supplier_store = request.supplier_store_id
        supplierstore = SupplierStore.objects.get(id = supplier_store)
        main = SupplierOrderMain.objects.filter(company_id = company.id,supplierstore_id = supplier_store,order_status__iexact = "Pending")
        context = {'records':main}
        return render(request,'SupplierPortal/supplierorder_view.html',context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

@company_session_required
@supplier_store_session_required
def orderapprovals_view(request,pk): # pk is a supplierorder main
    try:
        record = POApproval.objects.filter(po_details_id = pk)
        context = {'screen_name':"PO Approval Status",'record':record}
        return render(request,'SupplierPortal/orderapprovals_view.html',context)
    except Exception as error:
        return render(request, '500.html', {'error': error})



@company_session_required
@supplier_store_session_required
def supplierordersub_view(request,pk):
    try:  
        supplier_store = request.supplier_store_id
        supplierstore = SupplierStore.objects.get(id = supplier_store)
        main = SupplierOrderMain.objects.get(id=pk)
        subtable = SupplierOrderItemSub.objects.filter(order_id = main.id)
        context = {'records':main,'subtable':subtable}
        return render(request,'SupplierPortal/supplierordersub_view.html',context)
    except Exception as error:
        return render(request, '500.html', {'error': error})


def supplierorder_preview(request,pk): # SupplierOrderMain ID pass
    try:
        main = SupplierOrderMain.objects.get(id=pk)

        data_name = SupplierOrderItemSub.objects.filter(order_id = main.id)

        context = {'records':main,'subtable':data_name }
        return render(request,'SupplierPortal/supplierorder_preview.html',context)
    except Exception as error:
        return render(request, '500.html', {'error': error})


def notify_po_approvers(purchase_order, request):
    # Get all approvers for PurchaseOrder
    approvers = MultiApprover.objects.filter(process='PurchaseOrder', company_id=purchase_order.company.id)

        

    for approver in approvers:

        POApproval.objects.create(
            po_details_id = purchase_order.id,
            approver_id = approver.user.id,
            status = 'Pending',
            )
        
        user = approver.user
        email = user.email
        print("++++++++++++++++++",email)

        # Build the preview URL (assuming you have a view named 'po_preview' that takes pk)
        preview_url = f"https://procurementtest.pythonanywhere.com/"

        subject = f'New Purchase Order for Approval - PO#{purchase_order.id}'
        message = f'''
            Dear {approver.user},

            A new Purchase Order has been created and requires your approval.

            Purchase Order ID: {purchase_order.id}
            Description: {approver.description or 'No description'}

            Preview and approve/reject using the link below:
            {preview_url}

            Thank you,
            Your Procurement Team
            '''

            # send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])

@company_session_required
@supplier_store_session_required
def supplierorder(request):
    try:
       
        company = Company.objects.get(id=request.company)
        supplier_store = request.supplier_store_id
        supplierstore = SupplierStore.objects.get(id = supplier_store)
        itemtemp = SupplierOrderItemTemp.objects.filter(company_id = company.id,supplierstore_id = supplier_store)
        itemunit = ItemUnit.objects.filter(company_id = company.id)
        deliverystore = SupplierStore.objects.filter(company_id = company.id,supplier_id = supplierstore.supplier.id) 
    
        vendors = Vendor.objects.all()
        total_amount = itemtemp.aggregate(Sum('total_price'))['total_price__sum']
        if request.method == "POST":

            # Generate unique id
            def get_unique_poid():
                count = SupplierOrderMain.objects.count()
                
                while True:
                    POID = generate_unique_id('SPO', count)
                    if not SupplierOrderMain.objects.filter(po_number=POID).exists():
                        return POID  # Found a unique one, return it
                    count += 1  # Otherwise, try the next number

        
            POID = get_unique_poid()
    
            main = SupplierOrderMain.objects.create(
                company_id = company.id,
                supplier_id = supplierstore.supplier.id,
                supplierstore_id = supplierstore.id,
                po_number = POID,
                vendor_id = request.POST.get('vendor') if request.POST.get('vendor') != "None" else None,
                deliverystore_id = request.POST.get('deliverystore'),
                expected_delivery = request.POST.get('expecteddate'),
                approval_status = 'Pending',
                total_amount = total_amount,
       
            )
        
            for data in itemtemp:
            
                subtable = SupplierOrderItemSub(
                    company_id = company.id,
                    supplier_id = supplierstore.supplier.id,
                    supplierstore_id = supplierstore.id,
                    order_id = main.id,
                    item_unit_id = data.item_unit.id,  # Track the unit type
                    package_size_id = data.package_size.id if data.package_size else None,
                    ordertype = data.ordertype,
                    quantity = data.quantity,
                    pending_received_qty = data.quantity,
                    unit_price = data.unit_price,
                    total_price = data.total_price,
                    tax = data.tax,
                    discount = data.discount,
                    discount_type = data.discount_type,
                )
                subtable.save()

            #=============
            
            itemtemp.delete()
            notify_po_approvers(main, request)

            

            
            return redirect('supplierorder')
        context = {'itemunit':itemunit,'itemtemp':itemtemp,'vendors':vendors,'total_amount':total_amount,'deliverystore':deliverystore}
        return render(request,"SupplierPortal/supplierorder.html",context)
    except Exception as error:
        return render(request, '500.html', {'error': "Kindly Add the Item Details properly"})

@company_session_required
@supplier_store_session_required
def supplieroredr_itemstemp(request):
    try:
        company = Company.objects.get(id=request.company)
        supplier_store = request.supplier_store_id
        supplierstore = SupplierStore.objects.get(id = supplier_store)
    
        SupplierOrderItemTemp.objects.create(
            company_id = company.id,
            supplier_id = supplierstore.supplier.id,
            supplierstore_id = supplier_store,
            item_unit_id = request.POST.get("item_unit"),  # Track the unit type
            package_size_id = request.POST.get("item_package") if request.POST.get("item_package") != "None" else None, # Optional for bulk orders
            ordertype = request.POST.get("order_type"),
            quantity = request.POST.get("quantity_received"),
            unit_price = request.POST.get("amt"),
            total_price = request.POST.get("total_amt"),
            tax = request.POST.get("item_tax"),
            discount = request.POST.get("discount_value"),
            discount_type = request.POST.get("discount_type"),
        )
 
        return redirect("supplierorder")
    except Exception as error:
        return render(request, '500.html', {'error': error})

@company_session_required
@supplier_store_session_required
def delete_POtemp_details(request,pk):
    try:
        SupplierOrderItemTemp.objects.get(id=pk).delete()
        return redirect("supplierorder")
    except Exception as error:
        return render(request, '500.html', {'error': error})


# ajax function 
@company_session_required
# @supplier_store_session_required
def get_package_sizes(request):
    company = Company.objects.get(id=request.company)
    itemunit_id = request.GET.get('itemunit')  # Get itemunit_id from AJAX request
    packages = PackageSizeMaster.objects.filter(itemunit_id=itemunit_id,company_id = company.id)

    # Convert QuerySet to list of dictionaries
    package_list = [{"id": p.id, "package_name": p.package_name, 'quantity': p.quantity} for p in packages]

    return JsonResponse({"packages": package_list,})

# ajax function 

# @supplier_store_session_required
def get_item_price(request):
    item_unit_id = request.GET.get('item_unit_id')
    order_type = request.GET.get('order_type')
    Package = request.GET.get('package')
 

    item_unit = ItemUnit.objects.get(id=item_unit_id)
  
    try:
        if order_type == "Piece":
            
            amount = item_unit.price  # Assuming ItemUnit has a price field
        elif order_type == "Package":
            package = PackageSizeMaster.objects.get(id = Package)
            amount = package.pack_price
        else:
            return JsonResponse({"error": "Invalid order type"}, status=400)

        return JsonResponse({"amount": amount,'discount':item_unit.item.discount,'discounttype':item_unit.item.discount_type,'tax':item_unit.item.tax_rate})

    except ItemUnit.DoesNotExist:
        return JsonResponse({"error": "Item not found"}, status=404)
    except PackageSizeMaster.DoesNotExist:
        return JsonResponse({"error": "Package not found"}, status=404)



@company_session_required
@supplier_store_session_required
def po_edit(request, pk):
    try:
        company = Company.objects.get(id=request.company)
        supplier_store = request.supplier_store_id

        # Fetch order details
        order = get_object_or_404(SupplierOrderMain, id=pk, company_id=company.id, supplierstore_id=supplier_store)
        order.expected_delivery = order.expected_delivery.strftime("%m/%d/%Y")
  
        items = SupplierOrderItemSub.objects.filter(order_id=order.id)
        pack=PackageSizeMaster.objects.filter(company_id=company.id)

        kk= order.expected_delivery
 

        vendors = Vendor.objects.all()
        itemunits = ItemUnit.objects.filter(company_id=company.id)
        

        for item in itemunits:
           li= item.id
      

        ss= order.expected_delivery
        order.expected_delivery = request.POST.get('expecteddate')
        total=order.total_amount



        if request.method == "POST":
            # Update order details
            order.vendor_id = request.POST.get('vendor') if request.POST.get('vendor') != "None" else None
            order.expected_delivery = request.POST.get('expecteddate')

            print("expected_delivery",request.POST.get('expecteddate'))
            order.total_amount = request.POST.get('total_amount')

            order.save()

            # Update each item in the order
            for item in items:
            
                item.quantity = request.POST.get(f'quantity_{item.id}', item.quantity)
                item.unit_price = request.POST.get(f'unit_price_{item.id}', item.unit_price)
                item.total_price = float(item.quantity) * float(item.unit_price)
               
                item.tax = request.POST.get(f'item_tax_{item.id}', item.tax)
                item.discount = request.POST.get(f'discount_value_{item.id}', item.discount)
                item.discount_type = request.POST.get(f'discount_type_{item.id}', item.discount_type)
                item.package_size_id = request.POST.get(f'item_package_{item.id}') if request.POST.get(f'item_package_{item.id}') != "None" else None
                item.ordertype = request.POST.get(f'order_type_{item.id}', item.ordertype)
                item.save()

            return redirect('supplierorderview')

        # Context data for rendering template
        context = {
            'order': order,
            'items': items,
            'vendors': vendors,
            'itemunits': itemunits,
            'li':li,
            'date':kk,
            
             
        }
        return render(request, "SupplierPortal/po_edit.html", context)


    except Exception as error:
        return render(request, '500.html', {'error': error})
    

@company_session_required
@supplier_store_session_required
def po_delete(request, pk):
    try:
        company = Company.objects.get(id=request.company)
        supplier_store = request.supplier_store_id
        order = get_object_or_404(SupplierOrderMain, id=pk, company_id=company.id, supplierstore_id=supplier_store)
        items = SupplierOrderItemSub.objects.filter(order_id=order.id)
        items.delete() 
        order.delete()
        return redirect('supplierorderview')
    except Exception as error:
        return render(request, '500.html', {'error': error})


# Update with your actual model name

def delete_order_item(request):
    if request.method == "POST":
        item_id = request.POST.get("item_id")
        order_item = get_object_or_404(SupplierOrderItemSub, id=item_id)
        order_item.delete()
        return JsonResponse({"success": True})
    return JsonResponse({"success": False})

@company_session_required
@supplier_store_session_required

def pending_orders(request):
    pening_approval_po = POApproval.objects.filter(approver=request.user).values_list('po_details',flat=True)
    company = Company.objects.get(id=request.company)
    current_store = SupplierStore.objects.filter(id = request.supplier_store_id).last()
    pending_orders = SupplierOrderMain.objects.filter(id__in = pening_approval_po, approval_status__iexact='Pending',supplierstore_id=current_store.id,company_id=company.id)# Fetch only pending orders

    return render(request, 'SupplierPortal/supplier_order_form.html', {'orders': pending_orders})

@company_session_required
@supplier_store_session_required
def approved_orderslist(request):
    company = Company.objects.get(id=request.company)
    supplierstore = SupplierStore.objects.filter(id = request.supplier_store_id).last()
    pending_orders = SupplierOrderMain.objects.filter(approval_status__iexact='Approved',supplierstore_id=supplierstore.id)# Fetch only pending orders

    return render(request, 'SupplierPortal/approved_orderslist.html', {'orders': pending_orders})

@company_session_required
@supplier_store_session_required
def orderlist(request, id):
    try:
        print("++++++++++++++++++++++++++",request.user)
        company = Company.objects.get(id=request.company)
        receivedmain = SupplierOrderMain.objects.get(company_id = company.id,id = id)
        supplier = SupplierOrderItemSub.objects.filter(order_id=id,company_id=company.id)
        


       
        return render(request, 'SupplierPortal/supplierorder_list.html', {'supplier': supplier,'mainid': id,'receivedmain':receivedmain})
    except Exception as error:
        return render(request, '500.html', {'error': error})
    
@company_session_required
@supplier_store_session_required
def orderapproval(request,id):
    company = Company.objects.get(id=request.company)
    supplier= SupplierOrderMain.objects.get(pk=id,company_id=company.id)
    pening_approval_po = POApproval.objects.filter(po_details_id = supplier.id,approver_id = request.user.id).last()
    pening_approval_po.status = 'Approved'
    pening_approval_po.save()
    
    pening_approvalss = POApproval.objects.filter(po_details_id = supplier.id)
    pening_approvalss2  = pening_approvalss.filter(status = 'Approved')
    rejects_po = pening_approvalss.filter(status = 'Rejected')
    if pening_approvalss.count() == pening_approvalss2.count():
        supplier.approval_status = 'Approved'
    elif pening_approvalss.count() == rejects_po.count():
        supplier.approval_status = 'Rejected'
    supplier.save()
  

    return redirect("create_supplier_order")

@company_session_required 
@supplier_store_session_required
def order_rejections(request,id):
    try:
        company = Company.objects.get(id=request.company)
        supplier= SupplierOrderMain.objects.get(pk=id,company_id=company.id)

    

        if request.method == "POST":
            reason = request.POST.get("rejection_reason")
            supplier.approval_status = "Rejected"
            supplier.verified_by_admin = False
            supplier.rejection_reason = reason  
            supplier.save()
            pening_approval_po = POApproval.objects.filter(po_details_id = supplier.id,approver_id = request.user.id).last()
            pening_approval_po.status = 'Rejected'
            pening_approval_po.reject_reason = reason
            pening_approval_po.save()

            pening_approvalss = POApproval.objects.filter(po_details_id = supplier.id)
            pening_approvalss2  = pening_approvalss.filter(status = 'Approved')
            rejects_po = pening_approvalss.filter(status = 'Rejected')
            if pening_approvalss.count() == pening_approvalss2.count():
                supplier.approval_status = 'Approved'
            elif pening_approvalss.count() == rejects_po.count():
                supplier.approval_status = 'Rejected'
            supplier.save()

        return redirect("create_supplier_order")

    except Exception as error:
        return render(request, "500.html", {"error": error})
    
#======================== Goods Received ========================
@company_session_required
@supplier_store_session_required
def goodsreceivedfromvendor(request):
    try:
        company = Company.objects.get(id=request.company)
        supplier_store = request.supplier_store_id
        supplierstore = SupplierStore.objects.get(id = supplier_store)
        print("++++++++company_id",company.id)
        print("++++++++deliverystore_id",supplierstore.id)

        main = SupplierOrderMain.objects.filter(company_id = company.id,deliverystore_id = supplierstore.id,approval_status__iexact = "Approved",order_status__in = ['Pending','PartiallyDelivered']).order_by('-id')
        print("main",main)
        context = {'records':main}
        return render(request,"SupplierPortal/goodsreceivemain.html",context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

def call_token_api(request):
    url = "https://kasaccounts.pythonanywhere.com/token/"
    post_data = {
        "email": "test1@gmail.com",
        "password": "1234"
    }
    return post_method_without_token(request, url, post_data)

@transaction.atomic
@company_session_required
@supplier_store_session_required
def goodsreceivedfromvendorSub(request,pk):
    try:
        company = Company.objects.get(id=request.company)
        supplier_store = int(request.supplier_store_id)

        supplierstore = SupplierStore.objects.get(id = supplier_store)
        main = SupplierOrderMain.objects.get(id = pk)
        sub = SupplierOrderItemSub.objects.filter(company_id = company.id,pending_received_qty__gt = 0,order_status__in = ['Pending','PartiallyDelivered'],order_id = main.id )

        for data in sub:
            data.total_grn = data.pending_received_qty * data.unit_price
     
        if request.method == "POST":
            received_by = request.POST.get('Receivedby')
            childid = request.POST.getlist('childid')
            delivered_qty = request.POST.getlist('delivered_qty')
            batchnumber = request.POST.getlist('batchnumber')
            manufacturerdate = request.POST.getlist('manufacturerdate')
            expirydate = request.POST.getlist('expirydate')
         

            today = date.today()
      

            def get_unique_poid6():
                count = GoodsReceived.objects.count()
                
                while True:
                    POID = generate_unique_id('GRN', count)
                    if not GoodsReceived.objects.filter(GRN_number=POID).exists():
                        return POID  # Found a unique one, return it
                    count += 1  # Otherwise, try the next number

        
            GRNID = get_unique_poid6()
            
            goodsmain = GoodsReceived.objects.create(
                company_id = company.id,
                supplier_id = main.supplier.id,
                store_to_id = supplierstore.id,
                vendor_id = main.vendor.id,
                po_number_id = main.id,
                GRN_number = GRNID,
                received_by = received_by,
               
                received_date = today,

            )
       
            for index,data in enumerate(childid):
                if isinstance(expirydate[index], datetime):
                    expiry_date_str = expirydate[index].date().isoformat()
                elif isinstance(expirydate[index], str) and expirydate[index].strip():
                    try:
                        # Try to parse the string to a date
                        parsed_date = datetime.strptime(expirydate[index], "%Y-%m-%d")
                        expiry_date_str = parsed_date.date().isoformat()
                    except ValueError:
                        expiry_date_str = None  # or handle error accordingly
                else:
                    expiry_date_str = None  # or handle error accordingly
                
                
                if delivered_qty[index] != 0:


      
                    itemdetails = sub.get(id = childid[index])
                    inhand_package1 = delivered_qty[index] if itemdetails.ordertype == "Package" else 0
                    inhand_pieces1 = delivered_qty[index] if itemdetails.ordertype == "Piece" else 0
                    
                    # received quantity amount calculation
               
                    totalamount = float(itemdetails.unit_price) * int(delivered_qty[index])
                    

                    SupplierInventoryBatchWise.objects.create(
                        
                        company_id = company.id,
                        supplier_id = main.supplier.id,
                        store_to_id = supplierstore.id,
                        receiveddetails_id = goodsmain.id,
                        item_unit_id = itemdetails.item_unit.id,
                        expiry_date = expiry_date_str,
                        receivetype = itemdetails.ordertype,
                        batch_no = generate_unique_supplierbatch(batchnumber[index]),
                        packsize_id = itemdetails.package_size.id if itemdetails.package_size else None,
                        inhand_package = inhand_package1,
                        inhand_pieces = inhand_pieces1,
                        total_amount = totalamount,
                        tax = itemdetails.tax,
                        discount_type = 'Fixed',
                        stock_balance = f"{inhand_package1}W{inhand_pieces1}P",
                        received_date = today,
                        received_qty = delivered_qty[index],
                        manufacture_date = None,

                        )
                    
                    itemdetails.received_qty += int(delivered_qty[index])
                    itemdetails.pending_received_qty -= int(delivered_qty[index])
                    itemdetails.save()
                    if itemdetails.received_qty >= itemdetails.quantity:
                        itemdetails.order_status = "Delivered"
                    elif itemdetails.received_qty < itemdetails.quantity and itemdetails.received_qty != 0:
                        itemdetails.order_status = "PartiallyDelivered"
                    else:
                        itemdetails.order_status = "Pending"
                    itemdetails.save()




            # calculate GRN amount and update it to GoodsReceived 
            get_reateddetails = SupplierInventoryBatchWise.objects.filter(receiveddetails_id = goodsmain.id)        
            grn_amount = get_reateddetails.aggregate(total_amount_sum = Sum('total_amount'))['total_amount_sum']
            goodsmain.GRN_amount = grn_amount
            goodsmain.save()

            # generate invoice for received goods
    
            def get_unique_poid6():
                count = SupplierInvoice.objects.count()
                
                while True:
                    POID = generate_unique_id('INV', count)
                    if not SupplierInvoice.objects.filter(invoice=POID).exists():
                        return POID  # Found a unique one, return it
                    count += 1  # Otherwise, try the next number

        
            invoicess = get_unique_poid6()


            #======== call finance API for get refference type ===========

  
            SupplierInvoice.objects.create(
                company_id = company.id,
                supplier_id = main.supplier.id,
                store_to_id = supplierstore.id,
                po_number_id = main.id,
                GRN_number_id = goodsmain.id,
                received_by = received_by,
                GRN_amount = grn_amount,
                paid_amount = 0.0,
                pending_amount = grn_amount,
                invoice = invoicess,
                received_date = today,
            )

            subtable_count = SupplierOrderItemSub.objects.filter(order_id = main.id ).count()
            completed_count = SupplierOrderItemSub.objects.filter(company_id = company.id,order_status__iexact = "Delivered",order_id = main.id ).count()
            if completed_count == subtable_count:
                main.order_status = "Delivered"
            else:
                main.order_status = "PartiallyDelivered"
            main.save()

            return redirect('goodsreceivedfromvendor')
        
        context = {'ordermain':main,'ordersub':sub}
        return render(request,"SupplierPortal/goodsreceiveSub.html",context)
    except Exception as error:
        return render(request, '500.html', {'error': "Kindly Give received details Properly"})
 

#================= Received goods Details ======================
@company_session_required
@supplier_store_session_required
def received_goodsmain_details(request):
    try:
        company = Company.objects.get(id=request.company)
        supplier_store = int(request.supplier_store_id)
        received = GoodsReceived.objects.filter(company_id = company.id,store_to_id = supplier_store).order_by('-id')
        context = {'records':received}
        return render(request,"SupplierPortal/received_goodsmain_details.html",context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

@company_session_required
@supplier_store_session_required
def received_goodssub_details(request,pk):
    try:
        company = Company.objects.get(id=request.company)
        supplier_store = int(request.supplier_store_id)
        receivedmain = GoodsReceived.objects.get(company_id = company.id,store_to_id = supplier_store,id = pk)
        receivedsub = SupplierInventoryBatchWise.objects.filter(company_id = company.id,store_to_id = supplier_store,receiveddetails_id = receivedmain)
        context = {'recordssub':receivedsub,'receivedmain':receivedmain}
        return render(request,"SupplierPortal/received_goodssub_details.html",context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

@company_session_required
@supplier_store_session_required
def supplier_grminvoice(request, pk):
    try:
        company = Company.objects.get(id=request.company)
        supplier_store = int(request.supplier_store_id)

        invoice = SupplierInvoice.objects.filter(id=pk).last()
        receivedmain = None
        receivedsub = None
        
        if invoice and invoice.GRN_number:
            receivedmain = GoodsReceived.objects.filter(
                company_id=company.id,
                store_to_id=supplier_store,
                id=invoice.GRN_number.id
            ).last()
            
            if receivedmain:
                receivedsub = SupplierInventoryBatchWise.objects.filter(
                    company_id=company.id,
                    store_to_id=supplier_store,
                    receiveddetails_id=receivedmain.id
                )

        context = {
            'invoice': invoice,
            'receivedmain': receivedmain,
            'receivedsub': receivedsub
        }
        return render(request, "SupplierPortal/supplier_grminvoice.html", context)
    
    except Company.DoesNotExist:
        return render(request, '500.html', {'error': 'Company not found'})
    except Exception as error:
        return render(request, '500.html', {'error': str(error)})

@company_session_required
@supplier_store_session_required
def pending_invoices(request):
    try:
        company = Company.objects.get(id=request.company)
        supplier_store = int(request.supplier_store_id)
        pendinginvoice = SupplierInvoice.objects.filter(store_to_id = supplier_store)
        context = {'pendinginvoice':pendinginvoice}
        return render(request,"SupplierPortal/pending_invoices.html",context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

@company_session_required
@supplier_store_session_required
def create_invoice(request):
    try:
        company = Company.objects.get(id=request.company)
        supplierstore = SupplierStore.objects.get(id = request.supplier_store_id)
        if request.method == 'POST':
            form = SupplierInvoiceForm(request.POST)
            if form.is_valid():
                aa = form.save(commit=False)

                def get_unique_poid6():
                    count = SupplierInvoice.objects.count()
                    
                    while True:
                        POID = generate_unique_id('TG', count)
                        if not SupplierInvoice.objects.filter(invoice=POID).exists():
                            return POID  # Found a unique one, return it
                        count += 1  # Otherwise, try the next number

        
                invoicess = get_unique_poid6()

                aa.company_id = company.id
                aa.supplier_id = supplierstore.supplier.id
                aa.store_to_id = supplierstore.id
                aa.invoice = invoicess
                aa.save()
                return redirect('pendinginvoices')  # Replace with your list page
        else:
            form = SupplierInvoiceForm()

        context = {'form':form,'screen_name':'Create Invoice'}
        return render(request,"SupplierPortal/create.html",context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

@company_session_required
@supplier_store_session_required
def supplier_invoice_edit(request, pk):
    invoice = get_object_or_404(SupplierInvoice, pk=pk)
    if request.method == 'POST':
        form = SupplierInvoiceForm(request.POST, instance=invoice)
        if form.is_valid():
            form.save()
            return redirect('pendinginvoices')  # Replace with your list page
    else:
        form = SupplierInvoiceForm(instance=invoice)
    context = {'form':form,'screen_name':'Create Invoice'}
    return render(request,"SupplierPortal/create.html",context)

#=============== Payments screens======================
@company_session_required
@supplier_store_session_required
def all_goods(request):
    try:
        supplier_store = int(request.supplier_store_id)
        invoices = SupplierInvoice.objects.filter(store_to_id = supplier_store,payment_status__in = ["Pending","PartiallyPaid"])
        return render(request, 'SupplierPortal/pendingpayments.html', {'GoodsReceiveds': invoices})
    except Exception as error:
        return render(request, '500.html', {'error': error})

@company_session_required
@supplier_store_session_required
def paymentdetails(request):
    try:
        supplier_store = int(request.supplier_store_id)
        invoices = SupplierInvoice.objects.filter(store_to_id = supplier_store,payment_status__in = ["Paid","PartiallyPaid"])
        return render(request, 'SupplierPortal/paymentdetails.html', {'GoodsReceiveds': invoices})
    except Exception as error:
        return render(request, '500.html', {'error': error})

@company_session_required
@supplier_store_session_required
def paiddetails(request,pk): 
    try:
        supplier_store = int(request.supplier_store_id)
        invoices = SupplierInvoice.objects.filter(id = pk).last()
        payments = SupplierPayment.objects.filter(invoice_id = invoices.id)
        return render(request, 'SupplierPortal/paiddetails.html', {'GoodsReceiveds': invoices,"payments":payments})
    except Exception as error:
        return render(request, '500.html', {'error': error})

@company_session_required
@supplier_store_session_required
def paymentprocess(request, pk):
    try:
        company = Company.objects.get(id=request.company)
        invoice = SupplierInvoice.objects.get(id=pk)
        
        # current_branch = request.branch_id
        if request.method == "POST":
            payment_mode = request.POST.get("payment_mode")
            paid_by = request.POST.get("paid_by")
            pay_amount = request.POST.get("pay_amount")
            ref_no = request.POST.get("ref_no")
            bank_no = request.POST.get("bank_no")
            card_holder_name = request.POST.get("card_holder_name")
            mobile_number = request.POST.get("mobilenumber")
      

            SupplierPayment.objects.create(
                company_id = company.id,
                supplier_id = invoice.supplier.id,
                invoice_id = invoice.id,
                paid_by = paid_by,
                payment_method = payment_mode,
                bank_no = bank_no,
                transaction_reference = ref_no,
                holder_name = card_holder_name,
                mobile_number = None if mobile_number == "" else mobile_number,
                paid_amount = float(pay_amount),
            )
            invoice.paid_amount += float(pay_amount)
            invoice.pending_amount -= float(pay_amount)
            invoice.save()

            if float(invoice.paid_amount) == float(invoice.GRN_amount):
                invoice.payment_status = "Paid"
            elif float(invoice.paid_amount) < float(invoice.GRN_amount) and invoice.paid_amount != 0:
                invoice.payment_status = "PartiallyPaid"
            else:
                invoice.payment_status = "Pending"

            invoice.save()
            return redirect('all_goods')
            
        context = {"invoice":invoice}
        return render(request, 'SupplierPortal/payments.html',context)
    except Exception as error:
        return render(request, '500.html', {'error': error})
   
#============= Stock Return to Manufacturer or Vendor =============
@company_session_required
@supplier_store_session_required
def item_return_to_manufacturer(request):
    try:
        suppliers_store_id = request.supplier_store_id
        supplier = SupplierStore.objects.get(id = request.supplier_store_id)
        
        if request.method == "POST":
            manufacturer_id = request.POST.get('manufacturer')
            return redirect(f"/stockreturnto-manufacturer/{manufacturer_id}")
        else:
            subcategory = ItemSubCategoryMaster.objects.filter(company_id = request.company)
            product = ItemUnit.objects.filter(company_id = request.company)
            manufacturer = Vendor.objects.filter(company_id = request.company)
        context = {'supplier':supplier,'subcategory':subcategory,'product':product,'manufacturer':manufacturer}
        return render(request, 'SupplierPortal/item_return_to_manufacturer.html',context)
    except Exception as error:
        return render(request, '500.html', {'error': error})


@company_session_required
@supplier_store_session_required
def stockreturnto_manufacturer(request,pk): # pk is a manufacturer id
    try: 
        suppliers_store_id = request.supplier_store_id
        supplier = SupplierStore.objects.get(id = request.supplier_store_id)
        records = SupplierInventoryBatchWise.objects.filter(supplier_id = supplier.supplier.id,store_to_id = suppliers_store_id,receiveddetails__vendor_id = pk)
        subcategory = ItemSubCategoryMaster.objects.filter(company_id = request.company)
        product = ItemUnit.objects.filter(company_id = request.company)
        manufacture = Vendor.objects.get(id=pk)
        if request.method == "POST":
            search_btn = request.POST.get("return_btn")
            if search_btn == "return_btn":

       
                today = date.today()
            

                selected_ids = request.POST.getlist('active_products')

                def get_unique_poid():
                    count = StockReturnToManufacturerMain.objects.count()
                    
                    while True:
                        POID = generate_unique_id('RN', count)
                        if not StockReturnToManufacturerMain.objects.filter(return_id=POID).exists():
                            return POID  # Found a unique one, return it
                        count += 1  # Otherwise, try the next number

            
                RNID = get_unique_poid()
            
                returns = StockReturnToManufacturerMain.objects.create(
                    company_id = request.company,
                    supplier_id = supplier.supplier.id,
                    store_id = supplier.id, # return from
                    manufacturer_id = manufacture.id, # return to
                    return_id = RNID,
                    return_by = None,
                )


                for data in selected_ids:
                    instockrecords = SupplierInventoryBatchWise.objects.get(id=data)
                    return_qty = request.POST.get(f'returnqty_{data}')
                    return_type = request.POST.get(f'returntype_{data}')
                    reason = request.POST.get(f'reason_{data}')
                    
                    

                    amt = instockrecords.item_unit.price if return_type == 'Piece' else instockrecords.packsize.pack_price
                   
                    if return_qty and return_type:
                        StockReturnToManufacturerSub.objects.create(
                            company_id = request.company,
                            returnmain_id = returns.id,
                            item_unit_id = instockrecords.item_unit.id,
                            returntype = return_type,
                            batch_id =data,
                            quantity = return_qty,
                            amount =  int(return_qty) * float(amt),
                            reason = reason,
                        )
                        
                        if return_type == 'Piece':
                            total_amt = float(instockrecords.item_unit.price) * int(return_qty)
                            instockrecords.inhand_pieces -= int(return_qty)
                            instockrecords.total_amount -=total_amt
                            instockrecords.stock_balance = str(instockrecords.inhand_package)+ 'W' + str(instockrecords.inhand_pieces) + 'P'
                        else:
                            total_amt = float(instockrecords.item_unit.price) * int(return_qty)
                            instockrecords.inhand_pieces -= int(return_qty)
                            instockrecords.total_amount -=total_amt
                            instockrecords.stock_balance = str(instockrecords.inhand_package)+ 'W' + str(instockrecords.inhand_pieces) + 'P'
                        instockrecords.save()
                    fortotalamt = StockReturnToManufacturerSub.objects.filter(returnmain_id = returns.id).aggregate(total_amt = Sum("amount"))
                    fortotalamt = fortotalamt['total_amt'] or 0.0
                    returns.total_amount = fortotalamt
                    returns.save()
                return redirect('itemreturn_to_manufacturer')


        context = {"records":records,'supplier':supplier,'subcategory':subcategory,'product':product,'manufacture':manufacture}
        return render(request, 'SupplierPortal/stockreturnto_manufacturer.html',context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

@company_session_required
@supplier_store_session_required
def view_returntomanufacturermain(request):
    try:
        suppliers_store_id = request.supplier_store_id
        supplier = SupplierStore.objects.get(id = request.supplier_store_id)
        records = StockReturnToManufacturerMain.objects.filter(supplier_id=supplier.supplier.id,store_id = supplier.id)
        context = {'records':records,'supplier':supplier}
        return render(request, 'SupplierPortal/view_returntomanufacturermain.html',context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

@company_session_required
@supplier_store_session_required
def view_returntomanufacturersub(request,pk):
    try:
        suppliers_store_id = request.supplier_store_id
        supplier = SupplierStore.objects.get(id = request.supplier_store_id)
        recordsmain = StockReturnToManufacturerMain.objects.get(id = pk)
        records = StockReturnToManufacturerSub.objects.filter(returnmain_id = pk)
        context = {'records':records,'recordsmain':recordsmain,'supplier':supplier}
        return render(request, 'SupplierPortal/view_returntomanufacturersub.html',context)
    except Exception as error:
        return render(request, '500.html', {'error': error})


#============== Wastage managemnent =====================
@company_session_required
@supplier_store_session_required
def search_instock_forwastage(request):
    try:
        supplier = SupplierStore.objects.get(id = request.supplier_store_id)
        category = ItemCategoryMaster.objects.filter(company_id = request.company)
        sub_category = ItemSubCategoryMaster.objects.filter(company_id = request.company)
        product = ItemUnit.objects.filter(company_id = request.company)
        instockrecords = SupplierInventoryBatchWise.objects.filter(Q(inhand_package__gt = 0)|Q(inhand_pieces__gt = 0),supplier_id=supplier.supplier.id,store_to_id = supplier.id)
        if request.method == "POST":
            
            category_id = request.POST.get("category")
            subcategory_id = request.POST.get("sub_category")
            product_id = request.POST.get("product")
        
            if category_id or subcategory_id or product_id:
                
                filters = Q()
                if category_id:
                    filters &= Q(item_unit__item__category_id=category_id)
                if subcategory_id:
                    filters &= Q(item_unit__item__subcategory_id=subcategory_id)
                if product_id:
                    filters &= Q(item_unit_id=product_id)

                filters = Q(
                    supplier_id=supplier.supplier.id,
                    store_to_id=supplier.id
                ) & (
                    Q(inhand_package__gt=0) | Q(inhand_pieces__gt=0)
                )                
                instockrecords = SupplierInventoryBatchWise.objects.filter(filters)
            else:
                messages.warning(request, "Please select at least one filter.")
                

        context = {'category':category,'sub_category':sub_category,'product':product,'instockrecords':instockrecords}
        return render(request, 'SupplierPortal/search_instock_forwastage.html',context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

@supplier_store_session_required
def save_wastage_stocks(request,pk): # batchid
    try:
        supplier = SupplierStore.objects.get(id = request.supplier_store_id)
        instockrecords = SupplierInventoryBatchWise.objects.get(id = pk)
        if request.method == "POST":
            form = SupplierInventoryWastageForm(request.POST)
            if form.is_valid():
                wastage = form.save(commit=False)
                if wastage.wastage_type == "Piece":
                    total_amt = float(instockrecords.item_unit.price) * int(wastage.wastage_qty)
                    instockrecords.inhand_pieces -= int(wastage.wastage_qty)
                else:
                    total_amt = float(instockrecords.packsize.pack_price) * int(wastage.wastage_qty)
                    instockrecords.inhand_package -= int(wastage.wastage_qty)
                wastage.amount = total_amt
                wastage.inventory_batch_id = instockrecords.id
                wastage.supplier_id = supplier.supplier.id
                wastage.store_id = supplier.id

                wastage.save()
                instockrecords.save()
                messages.success(request, "Wastage recorded successfully.")
                return redirect('search_instock_forwastage')
            else:
                messages.error(request, "Error in wastage form.")
        else:
            form = SupplierInventoryWastageForm()

        context = {'form':form,'instockrecords':instockrecords}
        return render(request, 'SupplierPortal/save_wastage_stocks.html',context)
    except Exception as error:
        return render(request, '500.html', {'error': error})


@company_session_required
@supplier_store_session_required
def disply_forwastage(request):
    try:
        supplier = SupplierStore.objects.get(id = request.supplier_store_id)
        category = ItemCategoryMaster.objects.filter(company_id = request.company)
        sub_category = ItemSubCategoryMaster.objects.filter(company_id = request.company)
        product = ItemUnit.objects.filter(company_id = request.company)
        instockrecords = SupplierInventoryWastage.objects.filter(supplier_id=supplier.supplier.id,
                    store_id=supplier.id)
        if request.method == "POST":
            
            category_id = request.POST.get("category")
            subcategory_id = request.POST.get("sub_category")
            product_id = request.POST.get("product")
        
            if category_id or subcategory_id or product_id:
                
                filters = Q()
                if category_id:
                    filters &= Q(inventory_batch__item_unit__item__category_id=category_id)
                if subcategory_id:
                    filters &= Q(inventory_batch__item_unit__item__subcategory_id=subcategory_id)
                if product_id:
                    filters &= Q(inventory_batch__item_unit_id=product_id)

                filters = Q(
                    supplier_id=supplier.supplier.id,
                    store_id=supplier.id
                )  
                instockrecords = SupplierInventoryWastage.objects.filter(filters)
                
            else:
                messages.warning(request, "Please select at least one filter.")

        context = {'category':category,'sub_category':sub_category,'product':product,'instockrecords':instockrecords}
        return render(request, 'SupplierPortal/disply_forwastage.html',context)
    except Exception as error:
        return render(request, '500.html', {'error': error})



def stocktransfer_dashboard(request):
    try:
  
        return render(request, 'SupplierPortal/stocktransfer_dashboard.html')
    except Exception as error:
        return render(request, '500.html', {'error': error})


@company_session_required
@supplier_store_session_required
def Stock_details(request):
    try:
        suppliers_store_id = request.supplier_store_id
        supplier = SupplierStore.objects.get(id = request.supplier_store_id)
        records = SupplierInventoryBatchWise.objects.filter(supplier_id = supplier.supplier.id,store_to_id = suppliers_store_id).filter(Q(inhand_package__gt = 0)|Q(inhand_pieces__gt = 0))
        
        context = {"records":records,'supplier':supplier}
        return render(request, 'SupplierPortal/stockdetails.html',context)
    except Exception as error:
        return render(request, '500.html', {'error': error})
    

@company_session_required
@supplier_store_session_required
def supplier_dashboard(request):
    
        company = Company.objects.get(id=request.company)
        customer_store = int(request.supplier_store_id)
        print("customer_store",customer_store)
        customerstore = SupplierStore.objects.get(id=customer_store)
        goods_recieved= GoodsReceived.objects.filter(company_id=request.company,store_to_id=customer_store).count()
        customer_inventory= SupplierInventoryBatchWise.objects.filter(company_id=company.id,store_to_id=customer_store).count()
        # distibutor_strore = Customerstore.objects.filter(company_id=request.company,customerstore_id=customer_store).count()
        # distributor_branch=DistributorBranch.objects.filter(company_id=request.company,customer_id=customer_store.customer.id).count()
        total_purchase = SupplierOrderMain.objects.filter(supplierstore_id=customer_store).count()
        total_invoice = SupplierInvoice.objects.filter(store_to_id=customer_store).count()
        invoices_pending = SupplierInvoice.objects.filter(store_to_id=customer_store,payment_status__in = ["Pending"]).count()
        invoices_partial = SupplierInvoice.objects.filter(store_to_id=customer_store,payment_status__in = ["Partially Paid"]).count()
        invoices_paid = SupplierInvoice.objects.filter(store_to_id=customer_store,payment_status__in = ["Paid"]).count()
        po_pending=SupplierOrderMain.objects.filter(supplierstore_id=customer_store,approval_status__in = ["Pending"]).count()
        po_approved= SupplierOrderMain.objects.filter(supplierstore_id=customer_store,approval_status__in = ["Approved"]).count()
        po_rejected= SupplierOrderMain.objects.filter(supplierstore_id=customer_store,approval_status__in = ["Rejected"]).count()
        po_completed=SupplierOrderMain.objects.filter(supplierstore_id=customer_store,approval_status__in = ["Completed"]).count()
        stock_return = StockReturnToManufacturerMain.objects.filter(store_id=customer_store).count()
        # store_stock_transfer = StockRequestToStoresMain.objects.filter(customerstore_id = customer_store).count()
        # recieve_stocks_pending= StockRequestToStoresMain.objects.filter(customerstore_id=customer_store,approval_status='Pending').count()
        total_purchase_sub = SupplierOrderItemSub.objects.filter(company_id=company.id,supplierstore_id=customer_store).count()
        total_inventory = SupplierInventoryBatchWise.objects.filter(store_to_id=customer_store).count()
        ss = SupplierPayment.objects.filter(store_to_id=customer_store)
        kk = ss.aggregate(total_amt=Sum('paid_amount'))
        total_paid_amount = kk['total_amt'] 
        pending_invoice = SupplierInvoice.objects.filter(store_to_id=customer_store)
        sk=pending_invoice.aggregate(total_amt=Sum('pending_amount'))
        pending_amount=sk['total_amt']
        context = {
    'goods_recieved': goods_recieved,
    'customer_inventory': customer_inventory,
    'total_purchase': total_purchase,
    'total_invoice': total_invoice,
    'invoices_pending': invoices_pending,
    'invoices_partial': invoices_partial,
    'invoices_paid': invoices_paid,
    'po_pending': po_pending,
    'po_approved': po_approved,
    'po_rejected': po_rejected,
    'po_completed': po_completed,
    'stock_return': stock_return,
    # 'store_stock_transfer': store_stock_transfer,
    # 'recieve_stocks_pending': recieve_stocks_pending,
    'total_purchase_sub': total_purchase_sub,
    'total_inventory': total_inventory,
    'total_paid_amount': total_paid_amount,
    'pending_amount': pending_amount,
}
        return render(request, 'SupplierPortal/dashboard.html',context)    

# ===================== Stock transfer to another store ==================


@company_session_required
@supplier_store_session_required
def stocktransfer_tostore(request):
    try:
        suppliers_store_id = request.supplier_store_id
        supplier = SupplierStore.objects.get(id = request.supplier_store_id)
        destination_store = SupplierStore.objects.filter(supplier_id = supplier.supplier.id).exclude(id = supplier.id)
        records = SupplierInventoryBatchWise.objects.filter(supplier_id = supplier.supplier.id,store_to_id = suppliers_store_id).filter(Q(inhand_package__gt = 0)|Q(inhand_pieces__gt = 0))
        if request.method == "POST":
            search_btn = request.POST.get("transfer_btn")
            if search_btn == "transfer_btn":
                selected_ids = request.POST.getlist('active_products')
                destinationstore = request.POST.get('destination_store')
                expected_delivery_date = request.POST.get('expected_delivery_date')


                def get_unique_poid6():
                    count = StockTransferMain.objects.count()
                    
                    while True:
                        POID = generate_unique_id('TG', count)
                        if not StockTransferMain.objects.filter(transfer_id=POID).exists():
                            return POID  # Found a unique one, return it
                        count += 1  # Otherwise, try the next number

            
                TNID = get_unique_poid6()

                if selected_ids:

                    returns = StockTransferMain.objects.create(
                        company_id = request.company,
                        supplier_id = supplier.supplier.id,
                        storefrom_id = supplier.id, # return from
                        destinationstore_id = destinationstore,
                        transfertype = "Direct",
                        transfer_id = TNID,
                        delivery_date = expected_delivery_date,
                        approval_status = "Approved",
                        tracking_status = "Delivered",

                    )

                   

                for data in selected_ids:

                    instockrecords = SupplierInventoryBatchWise.objects.get(id=data)
                    transferqty = request.POST.get(f'transferqty_{data}')
                    transfertype = request.POST.get(f'transfertype_{data}')
                    
                    amt = instockrecords.item_unit.price if transfertype == 'Piece' else instockrecords.packsize.pack_price

                    if transferqty != 0 and transfertype:
                        StockTransferSub.objects.create(
                            company_id = request.company,
                            transfermain_id = returns.id,
                            item_unit_id = instockrecords.item_unit.id,
                            transfertype = transfertype,
                            batch_id =instockrecords.id,
                            quantity = transferqty,
                            amount =  int(transferqty) * float(amt),
                      
                        )
                        
                    fortotalamt = StockTransferSub.objects.filter(transfermain_id = returns.id).aggregate(total_amt = Sum("amount"))
                    fortotalamt = fortotalamt['total_amt'] or 0.0
                    returns.total_amount = fortotalamt
                    returns.save()
                    if transfertype == 'Piece':
                        instockrecords.inhand_pieces -= int(transferqty)
                    else:
                        instockrecords.inhand_package -= int(transferqty)
                    instockrecords.save()
                    
                checking = update_transferedstock_torequested(returns.id)
                print("checkingcheckingchecking",checking)
                return redirect('stocktransfertostore')

        context = {'supplier':supplier,'destination_store':destination_store,'records':records}
        return render(request, 'SupplierPortal/stocktransfer_tostore.html',context)
    except Exception as error:
        return render(request, '500.html', {'error': error})


@company_session_required
@supplier_store_session_required
def disply_transferdetails(request):
    try:
        suppliers_store_id = request.supplier_store_id
        supplier = SupplierStore.objects.get(id = request.supplier_store_id)
        records = StockTransferMain.objects.filter(storefrom_id = supplier.id,tracking_status = 'Pending' ).order_by('-id')
        context = {'records':records}
        return render(request, 'SupplierPortal/disply_transferdetails.html',context) 
    except Exception as error:
        return render(request, '500.html', {'error': error})

@company_session_required
@supplier_store_session_required
def transfer_confirmation(request,pk):
    try:
        suppliers_store_id = request.supplier_store_id
        supplier = SupplierStore.objects.get(id = request.supplier_store_id)
        recordsmain = StockTransferMain.objects.get(id = pk)
        recordssub = StockTransferSub.objects.filter(transfermain_id = recordsmain.id)
        if request.method == "POST":
            recordsmain.approval_status = 'Approved'
            recordsmain.tracking_status = 'Confirmed'
            recordsmain.confirmed_date = datetime.today().now()
            recordsmain.save()
            return redirect('displytransferdetails')

        context = {'records':recordsmain,'recordssub':recordssub,'currentdate':datetime.today().now()}
        return render(request, 'SupplierPortal/transfer_confirmation.html',context) 
    except Exception as error:
        return render(request, '500.html', {'error': error})

@company_session_required
@supplier_store_session_required
def disply_transfer(request):
    try:
        suppliers_store_id = request.supplier_store_id
        supplier = SupplierStore.objects.get(id = request.supplier_store_id)
        records = StockTransferMain.objects.filter(storefrom_id = supplier.id,tracking_status = 'Confirmed' )
        context = {'records':records}
        return render(request, 'SupplierPortal/disply_transfer.html',context) 
    except Exception as error:
        return render(request, '500.html', {'error': error})

@company_session_required
@supplier_store_session_required
def assign_logisticstransfer(request,pk):
    try:
        suppliers_store_id = request.supplier_store_id
        supplier = SupplierStore.objects.get(id = request.supplier_store_id)
        recordsmain = StockTransferMain.objects.get(id = pk)
        recordssub = StockTransferSub.objects.filter(transfermain_id = recordsmain.id)
        logistics = LogisticsPartner.objects.filter(company_id = request.company)
        added_logistics = TransferLogisticsDetails.objects.filter(stock_transfer_id = recordsmain.id).last()
        supplierstore = SupplierStore.objects.filter(supplier_id = supplier.supplier.id).exclude(id__in = [supplier.id,recordsmain.destinationstore.id])
        if request.method == "POST":
            logistics = request.POST.get('logistics')
            transfertype = request.POST.get('transfertype')
          
            vehiclenumber = request.POST.get('vehiclenumber')
            transportmode = request.POST.get('transportmode')
            driver_name = request.POST.get('driver_name')
            driver_contact = request.POST.get('driver_contact')
            departure_time = request.POST.get('departure_time')
            arrival_estimate = request.POST.get('arrival_estimate')
            notes = request.POST.get('notes')
            intermediatestores = request.POST.getlist('intermediatestores')
            driver_signature = request.FILES.get('driver_signature')

            logis = TransferLogisticsDetails.objects.create(
                stock_transfer_id = recordsmain.id,
                supplier_id = supplier.supplier.id,
                currentstore_id = supplier.id,
                logistics_id = logistics,
                vehicle_number = vehiclenumber,
                transfertype = transfertype,
                transport_mode = transportmode,
                driver_name = driver_name,
                driver_contact = driver_contact,
                departure_time = parse_datetime(departure_time),
                arrival_estimate = parse_datetime(arrival_estimate),
                notes = notes,
                driver_signature = driver_signature,
            )
            if transfertype == "Direct":
                TransferLogisticsStores.objects.create(
                    supplier_id = supplier.supplier.id,
                    currentstore_id = supplier.id,
                    stock_transfer_id = logis.id,
                    stores_id = recordsmain.destinationstore.id,
                    status = 'Pending',
                    reached = False
                    )
            else:
                for data in intermediatestores:
                    TransferLogisticsStores.objects.create(
                        supplier_id = supplier.supplier.id,
                        currentstore_id = supplier.id,
                        stock_transfer_id = logis.id,
                        stores_id = data,
                        status = 'Pending',
                        reached = False
                        )
                    # saving destination store
                TransferLogisticsStores.objects.create(
                supplier_id = supplier.supplier.id,
                currentstore_id = supplier.id,
                stock_transfer_id = logis.id,
                stores_id = recordsmain.destinationstore.id,
                status = 'Pending',
                reached = False
                )
            
             # Generate and save QR code in recordsmain
            qr_data = f"Transfer ID: {recordsmain.id}\nVehicle: {transfertype}\nDriver: {vehiclenumber}"
            qr = qrcode.make(qr_data)
            buffer = BytesIO()
            qr.save(buffer, format='PNG')
            file_name = f"qr_transfer_{recordsmain.id}.png"
            recordsmain.qr_code.save(file_name, ContentFile(buffer.getvalue()), save=True)
            recordsmain.tracking_status = "OrderShipped"
            recordsmain.save()
            return redirect(f'displytransfer')

        context = {'records':recordsmain,'recordssub':recordssub,'logistics':logistics,'supplierstore':supplierstore,'added_logistics':added_logistics}
        return render(request, 'SupplierPortal/assign_logisticstransfer.html',context) 
    except Exception as error:
        return render(request, '500.html', {'error': error})

    
#============ this function for show over all details of stock transfer ===============
@company_session_required
@supplier_store_session_required
def supplierstock_transferdetails(request):
    try:
        suppliers_store_id = request.supplier_store_id
        supplier = SupplierStore.objects.get(id = request.supplier_store_id)
        recordsmain = StockTransferMain.objects.filter(storefrom_id = supplier.id).order_by('-id')

        context = {'records':recordsmain}
        return render(request, 'SupplierPortal/supplierstock_transferdetails.html',context) 
    except Exception as error:
        return render(request, '500.html', {'error': error})
    
@company_session_required
@supplier_store_session_required
def stocktransfer_status(request,pk): # pknis a StockTransferMain id
    try:
        suppliers_store_id = request.supplier_store_id
        supplier = SupplierStore.objects.get(id = request.supplier_store_id)
        recordsmain = StockTransferMain.objects.get(id = pk)
        logistic = TransferLogisticsDetails.objects.filter(stock_transfer = recordsmain.id).last()
        intermediate_stores = []
        if logistic:
            intermediate_stores = TransferLogisticsStores.objects.filter(stock_transfer_id = logistic.id)
        context = {'records':recordsmain,'logistic':logistic,'intermediate_stores':intermediate_stores}
        return render(request, 'SupplierPortal/stocktransfer_status.html',context) 
    except Exception as error:
        return render(request, '500.html', {'error': error})

#=================== delivered stock confirmation ===================
@company_session_required
@supplier_store_session_required
def delivered_stocks(request):
    try:
        suppliers_store_id = request.supplier_store_id
        supplier = SupplierStore.objects.get(id = request.supplier_store_id)
        recordsmain = StockTransferMain.objects.filter(destinationstore_id = supplier.id).order_by('-id')
    
        context = {'records':recordsmain}
        return render(request, 'SupplierPortal/delivered_stocks.html',context) 
    except Exception as error:
        return render(request, '500.html', {'error': error})

@company_session_required
@supplier_store_session_required
def Stockdelivered_confirmation(request,pk):
    try:
        company = Company.objects.get(id = request.company)
        suppliers_store_id = request.supplier_store_id
        supplier = SupplierStore.objects.get(id = request.supplier_store_id)
        recordsmain = StockTransferMain.objects.get(id = pk)
        recordssub = StockTransferSub.objects.filter(transfermain_id = recordsmain.id)
        logistics = TransferLogisticsDetails.objects.filter(stock_transfer_id = recordsmain.id).last()
        if request.method == "POST":
            if supplier.id == recordsmain.destinationstore.id:
                recordsmain.approval_status = 'Approved'
                recordsmain.tracking_status = 'Delivered'
                recordsmain.delivery_date = datetime.today().now()
              
                recordsmain.save()

                #=================== Add stoct to store inventary =================
                for transfer in recordssub:
                    for batch in transfer.batch.all():  # because it's now ManyToMany
                        # Determine quantities based on transfer type
                        inhand_package1 = transfer.quantity if transfer.transfertype == "Package" else 0
                        inhand_pieces1 = transfer.quantity if transfer.transfertype == "Piece" else 0

                        # Try to find matching batch in SupplierInventoryBatchWise
                        existing_record = SupplierInventoryBatchWise.objects.filter(
                            store_to_id=supplier.id,
                            item_unit_id=batch.item_unit.id,
                            batch_no=batch.batch_no
                        ).last()

                        if existing_record:
                        
                            amount = batch.item_unit.price if transfer.transfertype == "Piece" else batch.packsize.pack_price
                            existing_record.inhand_package += inhand_package1
                            existing_record.inhand_pieces += inhand_pieces1
                            existing_record.stock_balance = f"{existing_record.inhand_package}W{existing_record.inhand_pieces}P"
                            existing_record.total_amount = float(amount) * int(transfer.quantity)
                            existing_record.save()

                        else:
                            # Create a new batch record (with a unique batch_no if needed)
                            SupplierInventoryBatchWise.objects.create(
                                company_id=company.id,
                                supplier_id=supplier.supplier.id,
                                store_to_id=supplier.id,
                                item_unit_id=batch.item_unit.id,
                                expiry_date=batch.expiry_date,
                                receivetype=batch.receivetype,
                                batch_no=generate_unique_supplierbatch(batch.batch_no),
                                packsize_id=batch.packsize_id,
                                inhand_package=inhand_package1,
                                inhand_pieces=inhand_pieces1,
                                total_amount=transfer.amount,
                                tax=batch.tax,
                                discount_type='Fixed',
                                stock_balance=f"{inhand_package1}W{inhand_pieces1}P",
                                received_date=datetime.today().date(),
                                received_qty=transfer.quantity,
                            )


            # intermediatestore = TransferLogisticsStores.objects.filter(stock_transfer_id = logistics.id).last()
            # intermediatestore.reached_date = datetime.today().date()
            # intermediatestore.reached = True
            # intermediatestore.save()

            #========== update status and quantity to stock request table ==========
            if recordsmain.request:
                stock_request = SupplierStoreToStoreRequestMain.objects.get(id = recordsmain.request.id)
                for data in recordssub:
                    transfersub = StockTransferSub.objects.get(id = data.id)
                    stock_request = SupplierStoreToStoreRequestSub.objects.get(id = transfersub.request_sub.id)
                    stock_request.received_qty += transfersub.quantity
                    stock_request.received_qty -= transfersub.quantity
                    stock_request.save()

                    update_stockrequest_status(stock_request.id)


            return redirect('delivered_stocks')
        


        context = {'records':recordsmain,'recordssub':recordssub,'currentdate':datetime.today().now()}
        return render(request, 'SupplierPortal/Stockdelivered_confirmation.html',context) 
    except Exception as error:
        return render(request, '500.html', {'error': error})


def update_stockrequest_status(maintable_id): # maintable_id is a SupplierStoreToStoreRequestMain table id 
    try:
        stock_request = SupplierStoreToStoreRequestMain.objects.get(id = maintable_id)
        stock_subtable = SupplierStoreToStoreRequestSub.objects.filter(order_id = stock_request.id)
        for data in stock_subtable:
            if data.quantity <= data.received_qty:
                data.order_status = "Delivered"
            elif data.quantity >= data.received_qty:
                data.order_status = "PartiallyDelivered"
            data.save()
        delivered_stock = SupplierStoreToStoreRequestSub.objects.filter(order_id = stock_request.id,order_status__iexact = "Delivered")
        if stock_subtable.count() == delivered_stock.count():
            stock_request.order_status = "Delivered"
        else:
            stock_request.order_status = "PartiallyDelivered"
        stock_request.save()
    
        return True
    except Exception as error:
        return False


# =========================== Supplier store to store request ======================
@company_session_required
@supplier_store_session_required
def supplierstoretostorerequest_view(request):
    try:
        company = Company.objects.get(id=request.company)
        supplier_store = request.supplier_store_id
        supplierstore = SupplierStore.objects.get(id = supplier_store)
        main = SupplierStoreToStoreRequestMain.objects.filter(company_id = company.id,supplierstore_from_id = supplier_store,order_status__iexact = "Pending").order_by('-id')
        context = {'records':main}
        return render(request,'SupplierPortal/supplierstoretostorerequest_view.html',context)
    except Exception as error:
        return render(request, '500.html', {'error': error})


@company_session_required
@supplier_store_session_required
def supplierstoretostorerequestsub_view(request,pk): # pk is a SupplierStoreToStoreRequestMain id
    try:  
        supplier_store = request.supplier_store_id
        supplierstore = SupplierStore.objects.get(id = supplier_store)
        main = SupplierStoreToStoreRequestMain.objects.get(id=pk)
        subtable = SupplierStoreToStoreRequestSub.objects.filter(order_id = main.id)
        context = {'records':main,'subtable':subtable}
        return render(request,'SupplierPortal/supplierstoretostorerequestsub_view.html',context)
    except Exception as error:
        return render(request, '500.html', {'error': error})


@company_session_required
@supplier_store_session_required
def stock_request_tostore(request):
    try:
        company = Company.objects.get(id=request.company)
        supplier_store = request.supplier_store_id
        supplierstore = SupplierStore.objects.get(id = supplier_store)
        destination_store = SupplierStore.objects.filter(supplier_id = supplierstore.supplier.id).exclude(id = supplierstore.id)
        itemtemp = SupplierStoreToStoreRequestTemp.objects.filter(company_id = company.id,supplierstore_id = supplier_store)
        itemunit = ItemUnit.objects.filter(company_id = company.id)
    
        vendors = Vendor.objects.all()
        total_amount = itemtemp.aggregate(Sum('total_price'))['total_price__sum']
        if request.method == "POST":

            today = date.today()
        
            def get_unique_poid6():
                    count = SupplierStoreToStoreRequestMain.objects.count()
                    
                    while True:
                        POID = generate_unique_id('STSID', count)
                        if not SupplierStoreToStoreRequestMain.objects.filter(request_number=POID).exists():
                            return POID  # Found a unique one, return it
                        count += 1  # Otherwise, try the next number

            
            POID = get_unique_poid6()
            
            main = SupplierStoreToStoreRequestMain.objects.create(
              
                company_id = company.id,
                supplier_id = supplierstore.supplier.id,
                supplierstore_from_id = supplierstore.id,
                supplierstore_destination_id = request.POST.get('destination_store') if request.POST.get('destination_store') != "None" else None,
                request_number = POID,
                expected_delivery = request.POST.get('expecteddate'),
                approval_status = 'Pending',
                total_amount = total_amount,
       
            )
        
            for data in itemtemp:
            
                subtable = SupplierStoreToStoreRequestSub(
                    company_id = company.id,
                    supplier_id = supplierstore.supplier.id,
                    supplierstore_id = supplierstore.id,
                    order_id = main.id,
                    item_unit_id = data.item_unit.id,  # Track the unit type
                    package_size_id = data.package_size.id if data.package_size else None,
                    ordertype = data.ordertype,
                    quantity = data.quantity,
                    pending_received_qty = data.quantity,
                    unit_price = data.unit_price,
                    total_price = data.total_price,
                    tax = data.tax,
                    discount = data.discount,
                    discount_type = data.discount_type,
                )
                subtable.save()

            #=============
            
            itemtemp.delete()
            
            return redirect('supplierstoretostorerequest_view')
        context = {'itemunit':itemunit,'itemtemp':itemtemp,'destination_store':destination_store,'total_amount':total_amount,'supplierstore':supplierstore}
        return render(request,"SupplierPortal/stock_request_tostore.html",context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

@company_session_required
@supplier_store_session_required
def supplierstorerequest_itemstemp(request):
    try:
        company = Company.objects.get(id=request.company)
        supplier_store = request.supplier_store_id
        supplierstore = SupplierStore.objects.get(id = supplier_store)
    
        SupplierStoreToStoreRequestTemp.objects.create(
            company_id = company.id,
            supplier_id = supplierstore.supplier.id,
            supplierstore_id = supplier_store,
            item_unit_id = request.POST.get("item_unit"),  # Track the unit type
            package_size_id = request.POST.get("item_package") if request.POST.get("item_package") != "None" else None, # Optional for bulk orders
            ordertype = request.POST.get("order_type"),
            quantity = request.POST.get("quantity_received"),
            unit_price = request.POST.get("amt"),
            total_price = request.POST.get("total_amt"),
            tax = request.POST.get("item_tax"),
            discount = request.POST.get("discount_value"),
            discount_type = request.POST.get("discount_type"),
        )
 
        return redirect("stock_request_tostore")
    except Exception as error:
        return render(request, '500.html', {'error': error})

def supplierstorerequest_itemsdelete(request,pk): # SupplierStoreToStoreRequestTemp id
    try:
        SupplierStoreToStoreRequestTemp.objects.get(id = pk).delete()
        return redirect('stock_request_tostore')
    except Exception as error:
        return render(request, '500.html', {'error': error})

@company_session_required
@supplier_store_session_required
def supplierstorerequestapproval(request,pk):
    company = Company.objects.get(id=request.company)
    supplier= SupplierStoreToStoreRequestMain.objects.get(id=pk)
    supplier.approval_status = 'Approved'
    supplier.save()
  
    return redirect("supplierstoretostorerequest_view")

@company_session_required 
@supplier_store_session_required
def supplierstorerequestrejection(request,pk):
    try:
        company = Company.objects.get(id=request.company)
        supplier= SupplierStoreToStoreRequestMain.objects.get(id = pk,company_id=company.id)


        if request.method == "POST":
            reason = request.POST.get("rejection_reason")
            supplier.approval_status = "Rejected"
            supplier.verified_by_admin = False
            supplier.rejection_reason = reason  
            supplier.save()

        return redirect("supplierstoretostorerequest_view")

    except Exception as error:
        return render(request, "500.html", {"error": error})

def supplierstorerequest_preview(request,pk): # SupplierOrderMain ID pass
    try:
        main = SupplierStoreToStoreRequestMain.objects.get(id=pk)

        data_name = SupplierStoreToStoreRequestSub.objects.filter(order_id = main.id)
        current_date = datetime.today().date()
        context = {'records':main,'subtable':data_name,'current_date':current_date }
        return render(request,'SupplierPortal/supplierstorerequest_preview.html',context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

@company_session_required 
@supplier_store_session_required
def approved_supplierstorerequest(request): # SupplierOrderMain ID pass
    try:
        company = Company.objects.get(id=request.company)
        supplier_store = request.supplier_store_id
        supplierstore = SupplierStore.objects.get(id = supplier_store)

        main = SupplierStoreToStoreRequestMain.objects.filter(supplierstore_destination_id = supplierstore.id,approval_status__iexact = "Approved",order_status__in = ['Pending','PartiallyDispatched']).order_by('-id')
        context = {'records':main}
        return render(request,'SupplierPortal/approved_supplierstorerequest.html',context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

@company_session_required 
@supplier_store_session_required
def approved_supplierstorerequest_view(request): # SupplierOrderMain ID pass
    try:
        company = Company.objects.get(id=request.company)
        supplier_store = request.supplier_store_id
        supplierstore = SupplierStore.objects.get(id = supplier_store)

        main = SupplierStoreToStoreRequestMain.objects.filter(supplierstore_destination_id = supplierstore.id,approval_status__iexact = "Approved",order_status__in = ['Pending','PartiallyDispatched']).order_by('-id')
        context = {'records':main}
        return render(request,'SupplierPortal/approved_supplierstorerequest.html',context)
    except Exception as error:
        return render(request, '500.html', {'error': error})




def update_transferedstock_torequested(transferedmain_id):
    transfer = StockTransferMain.objects.filter(id = transferedmain_id).last()
    transfersub = StockTransferSub.objects.filter(transfermain_id = transfer.id)

    for data in transfersub:
        instore = SupplierInventoryBatchWise.objects.filter(id = data.batch.id).last() # transfer store batch details
        existing_record = SupplierInventoryBatchWise.objects.filter(store_to_id=transfer.destinationstore.id,
        item_unit_id=data.item_unit.id,batch_no=instore.batch_no).last() # requested store 

        if existing_record:
            existing_record.inhand_pieces += int(data.quantity)
            existing_record.total_amount = float(instore.item_unit.price) * int(data.quantity)
            existing_record.save()
        else:
        # Create a new batch record (with a unique batch_no if needed)

            SupplierInventoryBatchWise.objects.create(
                company_id=instore.company.id,
                supplier_id=instore.supplier.id,
                store_to_id=transfer.destinationstore.id,
                item_unit_id=data.item_unit.id,
                expiry_date=instore.expiry_date,
                receivetype= 'Piece',
                batch_no=instore.batch_no,
                
                inhand_pieces=int(data.quantity),
                total_amount=float(instore.item_unit.price) * int(data.quantity),
                tax=instore.tax,
                discount_type='Fixed',
                received_date=datetime.today().date(),
                received_qty=int(data.quantity),
            )




    return True
 


@company_session_required
@supplier_store_session_required
def supplierstorerequest_transfer(request,pk):
    try:
        company = Company.objects.get(id=request.company)
        suppliers_store_id = request.supplier_store_id
        supplier = SupplierStore.objects.get(id = request.supplier_store_id) # current store
        destination_store = SupplierStore.objects.filter(supplier_id = supplier.supplier.id).exclude(id = supplier.id)
        requestmain = SupplierStoreToStoreRequestMain.objects.get(id = pk)
        recordssub = SupplierStoreToStoreRequestSub.objects.filter(order_id = requestmain.id,order_status__in = ['PartiallyDispatched','Pending'])

        # ================ display pending sending stocks ====================
        lists = []
        for data in recordssub:
            instore = SupplierInventoryBatchWise.objects.filter(
                store_to_id=supplier.id,
                item_unit_id=data.item_unit.id
            ).filter(
                Q(inhand_package__gt=0) | Q(inhand_pieces__gt=0)
            )

            instore_qty = sum(batch.inhand_pieces for batch in instore)

            dicts = {
                'recordssub': data,
                'instore_qty': instore_qty,
                'pending_qty': int(data.quantity) - int(data.received_qty),
            
            }

            lists.append(dicts)
        
        if request.method == "POST":
            search_btn = request.POST.get("transfer_btn")
            if search_btn == "transfer_btn":
                def get_unique_poid6():
                    count = StockTransferMain.objects.count()
                    
                    while True:
                        POID = generate_unique_id('TG', count)
                        if not StockTransferMain.objects.filter(transfer_id=POID).exists():
                            return POID  # Found a unique one, return it
                        count += 1  # Otherwise, try the next number
                TNID = get_unique_poid6()

                selected_ids = request.POST.getlist('active_products') # request sub table id
                expected_delivery_date = request.POST.get('expected_delivery_date')
                returns = StockTransferMain.objects.create(
                    company_id = request.company,
                    supplier_id = supplier.supplier.id,
                    storefrom_id = supplier.id, # return from
                    destinationstore_id = requestmain.supplierstore_from.id,
                    request_id = requestmain.id,
                    transfertype = 'Requested',
                    transfer_id = TNID,
                    delivery_date = expected_delivery_date,
                    approval_status = "Approved",
                    tracking_status = "Delivered",
                    
                )

                for data in selected_ids:
                    subtable = SupplierStoreToStoreRequestSub.objects.get(id=data)
                    dispatchqty = request.POST.get(f'dispatchqty_{data}')
                    transfertype = request.POST.get(f'transfertype_{data}')
                    product = request.POST.get(f'itemunit_{data}')

                    #========== current store product batchh ====================
                    if transfertype == "Piece":
                        instockrecords = SupplierInventoryBatchWise.objects.filter(
                            item_unit_id=subtable.item_unit.id,store_to_id=supplier.id
                        ).filter(Q(inhand_package__gt=0) | Q(inhand_pieces__gt=0)).order_by('id')  # FIFO

                        qty_needed = dispatchqty

                        for batch in instockrecords:
                            if int(qty_needed) <= 0:
                                break

                            available_qty = batch.inhand_pieces
                            used_qty = min(int(qty_needed), int(available_qty)) # iss how much quantity will reduce from that batch
                            batch.inhand_pieces -= int(used_qty)
                            batch.save()
                            qty_needed = int(qty_needed) - int(used_qty)

                            # Save transfer sub entry for this batch
                            StockTransferSub.objects.create(
                                company_id=request.company,
                                transfermain_id=returns.id,
                                item_unit_id=product,
                                request_sub_id=subtable.id,
                                transfertype=transfertype,
                                quantity=used_qty,
                                batch_id=batch.id,
                                amount=used_qty * float(subtable.item_unit.price)
                            )
                            subtable.received_qty += used_qty
                            subtable.pending_received_qty -= used_qty
                            subtable.save()

                            # Update dispatched qty and status in request sub table
                            if subtable.quantity <= (subtable.received_qty or 0) + int(used_qty):
                                subtable.order_status = "Delivered"
                            else:
                                subtable.order_status = "PartiallyDelivered"
                            subtable.save()
                            update_stockrequest_status(subtable.id)

                checking = update_transferedstock_torequested(returns.id)
                print("checkingcheckingchecking",checking)

    
                #Update total amount in transfer main
                fortotalamt = StockTransferSub.objects.filter(transfermain_id=returns.id).aggregate(
                    total_amt=Sum("amount")
                )
                returns.total_amount = fortotalamt['total_amt'] or 0.0
                returns.save()

                # Update request main status
                all_subs = SupplierStoreToStoreRequestSub.objects.filter(order_id=requestmain.id)
                dispatched_subs = all_subs.filter(order_status__iexact='Delivered')

                if all_subs.count() == dispatched_subs.count():
                    requestmain.order_status = 'Delivered'
                else:
                    requestmain.order_status = 'PartiallyDelivered'
                requestmain.save()
            return redirect('approvedsupplierstorerequest')
                
        context = {'supplier':supplier,'destination_store':destination_store,'records':recordssub,'requestmain':requestmain,'lists':lists}
        return render(request, 'SupplierPortal/supplierstorerequest_transfer.html',context)
    except Exception as error:
        return render(request, '500.html', {'error': error})







@company_session_required
@supplier_store_session_required
def get_batch_data(request):

    suppliers_store_id = request.supplier_store_id
    supplier = SupplierStore.objects.get(id = request.supplier_store_id)
    batch_no = request.GET.get('batch_id')
    item_unit_id = request.GET.get('item_unit_id')
    transferType = request.GET.get('transferType')

    try:
        batch_data = SupplierInventoryBatchWise.objects.filter(id=batch_no, item_unit_id=item_unit_id,store_to_id = supplier.id ).last()


        data = {
            'instoreqty': batch_data.stock_balance,
            'expirydate': batch_data.expiry_date.strftime('%Y-%m-%d') if batch_data.expiry_date else '',
            'package': batch_data.packsize,
            'price': batch_data.item_unit.price,
    
        }
        return JsonResponse(data)
    except SupplierInventoryBatchWise.DoesNotExist:
        return JsonResponse({'error': 'Batch not found'}, status=404)

#=================================== Stock Transfer to Distributor =======================

def stocktransferdistributor_dashboard(request):
    try:
        return render(request,'SupplierPortal/stocktransferdistributor_dashboard.html')
    except Exception as error:
        return render(request, '500.html', {'error': error})

@company_session_required 
@supplier_store_session_required
def distributor_request(request):
    try:
        company = Company.objects.get(id=request.company)
        supplier_store = request.supplier_store_id
        supplierstore = SupplierStore.objects.get(id = supplier_store)
        if supplierstore.is_mainstore == True:
            main = PurchaseOrderMain.objects.filter(supplier_id = supplierstore.supplier.id,approval_status__iexact = "Approved",order_status__in = ['Pending','PartiallyDispatched'])
        else:
            main = []
        context = {'records':main}
        return render(request,'SupplierPortal/distributor_request.html',context)
    except Exception as error:
        return render(request, '500.html', {'error': error})



@company_session_required
@supplier_store_session_required
def distributorrequest_transfer(request,pk): # PurchaseOrderMain id
    try:
        suppliers_store_id = request.supplier_store_id
        supplier = SupplierStore.objects.get(id = request.supplier_store_id) # current store
        
        requestmain = PurchaseOrderMain.objects.get(id = pk)
        recordssub = PurchaseOrderItemSub.objects.filter(order_id = requestmain.id,order_status__in = ['PartiallyDispatched','Pending'])
        destination_store = Customerstore.objects.get(id = requestmain.customerstore.id)
        lists = []
        for data in recordssub:
            instore = SupplierInventoryBatchWise.objects.filter(
                store_to_id=supplier.id,
                item_unit_id=data.item_unit.id
            ).filter(
                Q(inhand_package__gt=0) | Q(inhand_pieces__gt=0)
            )            
            dicts  = {
                'recordssub':data,
                'batch': [{'batch_no':data.batch_no,'batch_id':data.id} for data in instore],  
                'pending_qty': int(data.quantity) - int(data.dispatched_qty)
            }
            lists.append(dicts)

        search_btn = request.POST.get("transfer_btn")
        if search_btn == "transfer_btn":


                def getunique_poid():
                    count = DistributorStockTransferMain.objects.count()
                    
                    while True:
                        GID = generate_unique_id('STD', count)
                        if not DistributorStockTransferMain.objects.filter(transfer_id=GID).exists():
                            return GID  # Found a unique one, return it
                        count += 1  # Otherwise, try the next number

        
                GID = getunique_poid()
         

                selected_ids = request.POST.getlist('active_products') # request sub table id
           
                expected_delivery_date = request.POST.get('expected_delivery_date')

                returns = DistributorStockTransferMain.objects.create(
                        company_id = request.company,
                        supplier_id = supplier.supplier.id,
                        storefrom_id = supplier.id, # return from
                        distributorstore_id = destination_store.id,
                        request_id = requestmain.id,
                        transfertype = 'Requested',
                        transfer_id = GID,
                        delivery_date = expected_delivery_date,
                        approval_status = "Pending",
                        tracking_status = "Pending",

                    )

                for data in selected_ids:
                    subtable = PurchaseOrderItemSub.objects.get(id = data)
                    dispatchqty = request.POST.get(f'dispatchqty_{data}')
                    transfertype = request.POST.get(f'transfertype_{data}')
                    batch_no = request.POST.get(f'batch_no_{data}')
                    instockrecords = SupplierInventoryBatchWise.objects.get(id=batch_no,store_to_id = supplier.id)

                    amt = instockrecords.item_unit.price if transfertype == 'Piece' else instockrecords.packsize.pack_price
                   
                    if dispatchqty and transfertype:
                        DistributorStockTransferSub.objects.create(
                            company_id = request.company,
                            transfermain_id = returns.id,
                            distributorstore_id = destination_store.id,
                            item_unit_id = instockrecords.item_unit.id,
                            request_sub_id = subtable.id,
                            transfertype = transfertype,
                            batch_id = instockrecords.id,
                            quantity = dispatchqty,
                            amount =  int(dispatchqty) * float(amt),
                      
                        )
                        
                    fortotalamt = DistributorStockTransferSub.objects.filter(transfermain_id = returns.id).aggregate(total_amt = Sum("amount"))
                    fortotalamt = fortotalamt['total_amt'] or 0.0
                    returns.total_amount = fortotalamt
                    returns.save()

                    # = update status to request sub table 
                    subtable.dispatched_qty = int(int(subtable.dispatched_qty) + int(dispatchqty))
                    if subtable.quantity <= int(int(subtable.received_qty) + int(dispatchqty)):
                        subtable.order_status = "Dispatched"
                    elif subtable.quantity <= int(int(subtable.received_qty) + int(dispatchqty)):
                        subtable.order_status = "PartiallyDispatched"
                    subtable.save()

                    # = update status to request main table 
                    fortotalamtaa = PurchaseOrderItemSub.objects.filter(order_id = requestmain.id)
                    dispatched_records = PurchaseOrderItemSub.objects.filter(order_id = requestmain.id,order_status__iexact = 'Dispatched')
                    
                    if fortotalamtaa.count() == dispatched_records.count():
                        requestmain.order_status = 'Dispatched'
                    elif fortotalamtaa.count() > dispatched_records.count():
                        requestmain.order_status = 'PartiallyDispatched'
                    requestmain.save()

                    #============= deduct the disbatched qty ==========
                    
                    if instockrecords.receivetype == 'Piece':
                        instockrecords.inhand_pieces -= int(dispatchqty)
                    else:
                        instockrecords.inhand_package -= int(dispatchqty)
                    instockrecords.save()

                return redirect('distributor_request')

        context = {'supplier':supplier,'destination_store':destination_store,'records':recordssub,'requestmain':requestmain,'lists':lists}
        return render(request, 'SupplierPortal/distributor_transfer.html',context)
    except Exception as error:
        return render(request, '500.html', {'error': error})
  
@company_session_required
@supplier_store_session_required
def distributor_transfered_view(request):
    try:
        suppliers_store_id = request.supplier_store_id
        supplier = SupplierStore.objects.get(id = request.supplier_store_id) # current store

        maintable = DistributorStockTransferMain.objects.filter(storefrom_id = supplier.id)
        context = {'records':maintable}
        return render(request, 'SupplierPortal/distributor_transfered_view.html',context)
    except Exception as error:
        return render(request, '500.html', {'error': error})
    
@company_session_required
@supplier_store_session_required
def distributor_transfered_sub(request,pk):
    try:
        suppliers_store_id = request.supplier_store_id
        supplier = SupplierStore.objects.get(id = request.supplier_store_id) # current store

        maintable = DistributorStockTransferMain.objects.get(id = pk)
        subtable = DistributorStockTransferSub.objects.filter(transfermain_id = maintable.id)
        context = {'records':maintable,'subtable':subtable}
        return render(request, 'SupplierPortal/distributor_transfered_sub.html',context)
    except Exception as error:
        return render(request, '500.html', {'error': error})


@company_session_required
@supplier_store_session_required
def disply_distributortransfer(request):
    try:
        suppliers_store_id = request.supplier_store_id
        supplier = SupplierStore.objects.get(id = request.supplier_store_id) # current store

        maintable = DistributorStockTransferMain.objects.filter(storefrom_id = supplier.id,tracking_status__iexact = 'Pending')
       
        context = {'records':maintable}
        return render(request, 'SupplierPortal/disply_distributortransfer.html',context) 
    except Exception as error:
        return render(request, '500.html', {'error': error})

@company_session_required
@supplier_store_session_required
def distributortransfer_confirmation(request,pk):
    try:
        suppliers_store_id = request.supplier_store_id
        supplier = SupplierStore.objects.get(id = request.supplier_store_id)
        maintable = DistributorStockTransferMain.objects.get(id = pk)
        subtable = DistributorStockTransferSub.objects.filter(transfermain_id = maintable.id)
        if request.method == "POST":
            maintable.approval_status = 'Approved'
            maintable.tracking_status = 'Confirmed'
            maintable.confirmed_date = datetime.today().now()
            maintable.save()
            return redirect('disply_distributor_transfer')

        context = {'records':maintable,'recordssub':subtable,'currentdate':datetime.today().now()}
        return render(request, 'SupplierPortal/distributortransfer_confirmation.html',context) 
    except Exception as error:
        return render(request, '500.html', {'error': error})

@company_session_required
@supplier_store_session_required
def confirmeddistributor_transfered(request):
    try:
        suppliers_store_id = request.supplier_store_id
        supplier = SupplierStore.objects.get(id = request.supplier_store_id) # current store

        maintable = DistributorStockTransferMain.objects.filter(storefrom_id = supplier.id,tracking_status__in = ["Confirmed",'OrderShipped','InTransit','Delivered'])
        context = {'records':maintable}
        return render(request, 'SupplierPortal/confirmeddistributor_transfered.html',context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

@company_session_required
@supplier_store_session_required
def assignlogistic_distributortransfer(request):
    try:
        suppliers_store_id = request.supplier_store_id
        supplier = SupplierStore.objects.get(id = request.supplier_store_id) # current store

        maintable = DistributorStockTransferMain.objects.filter(storefrom_id = supplier.id,tracking_status__iexact = "Confirmed")
        context = {'records':maintable}
        return render(request, 'SupplierPortal/assignlogistic_distributortransfer.html',context)
    except Exception as error:
        return render(request, '500.html', {'error': error})



@company_session_required
@supplier_store_session_required
def reorder_stocks(request):
    try:
        company = Company.objects.get(id = request.company)
        vendors = Vendor.objects.all()
        supplierstore = SupplierStore.objects.get(id = request.supplier_store_id)
        deliverystore = SupplierStore.objects.filter(company_id = company.id)
        today = timezone.now()
        start_month = today.replace(day=1)
        end_month = (start_month + timezone.timedelta(days=32)).replace(day=1)
        # 1. Delivered orders this month (group by item_unit)
        order_items = SupplierOrderItemSub.objects.filter(
            created_at__gte=start_month,
            created_at__lt=end_month,
            order_status="Delivered",
            supplierstore_id=supplierstore.id,
        )
        order_totals = order_items.values(
            'item_unit__id',
            'item_unit__brand__name',
            'item_unit__conversion_factor_to_base',
            'item_unit__unit__symbol',
            'item_unit__item__item_name',
            'item_unit__price'
        ).annotate(total_ordered=Sum('received_qty'))
        # 2. Current inventory
        inventory = SupplierInventoryBatchWise.objects.filter(store_to_id=supplierstore.id)
        stock_totals = inventory.values(
            'item_unit__id',
            'item_unit__brand__name',
            'item_unit__conversion_factor_to_base',
            'item_unit__unit__symbol',
            'item_unit__item__item_name',
            'item_unit__price'
        ).annotate(total_inhand=Sum('inhand_pieces'))

        stock_dict = {entry['item_unit__id']: entry['total_inhand'] for entry in stock_totals}

        # 3. Set reorder threshold
        REORDER_THRESHOLD = 10

        # 4. Final report
        report = []
        for order in order_totals:
            unit_id = order['item_unit__id']
            item_name = order['item_unit__item__item_name']
            brand = order['item_unit__brand__name']
            unit = order['item_unit__conversion_factor_to_base']
            symbol = order['item_unit__unit__symbol']
            amount = order['item_unit__price']
            total_received = order['total_ordered']
            current_stock = stock_dict.get(unit_id, 0)
            consumed = total_received - current_stock
            reorder_needed = current_stock < REORDER_THRESHOLD
            reorder_qty = REORDER_THRESHOLD - current_stock if reorder_needed else 0
            if reorder_qty <= current_stock:
                reorder_qty = 0
                reorder_needed = 0
            if reorder_qty != 0:
                report.append({
                    'unit_id':unit_id,
                    'item_name': f'{item_name}/{unit}{symbol}',
                    'brand' : brand,
                    'amount' : amount,
                    'total_received': total_received,
                    'current_stock': current_stock,
                    'consumed': consumed,
                    'reorder_needed': reorder_needed,
                    'reorder_qty': reorder_qty,
                    'totalAmountss': float(amount)*int(reorder_qty),
                })
        itemunit = ItemUnit.objects.filter(company_id = company.id )

        

        if request.method == "POST":
            manufacture = request.POST.get('vendor')
            expected_date = request.POST.get('expecteddate')
            itemunit = request.POST.getlist('selected')
            def get_unique_poid():
                count = SupplierOrderMain.objects.count()
                
                while True:
                    POID = generate_unique_id('SPO', count)
                    if not SupplierOrderMain.objects.filter(po_number=POID).exists():
                        return POID  # Found a unique one, return it
                    count += 1  # Otherwise, try the next number

            # Generate unique id
            POID = get_unique_poid()
            
            main = SupplierOrderMain.objects.create(
                
                company_id = company.id,
                supplier_id = supplierstore.supplier.id,
                supplierstore_id = supplierstore.id,
                deliverystore_id = request.POST.get('deliverystore'),
                po_number = POID,
                vendor_id = request.POST.get('vendor') if request.POST.get('vendor') != "None" else None,
                expected_delivery = request.POST.get('expecteddate'),
                approval_status = 'Pending',
                
        
            )

            for data in itemunit:
                ordertype = request.POST.get(f'order_type_{data}')
                package = request.POST.get(f'item_package_{data}')
                qty = request.POST.get(f'quantity_received_{data}')
                discount = request.POST.get(f'discount_value_{data}')
                discounttype = request.POST.get(f'discount_type_{data}')
                tax = request.POST.get(f'item_tax_{data}')

            
                subtable = SupplierOrderItemSub(
                    company_id = company.id,
                    supplier_id = supplierstore.supplier.id,
                    supplierstore_id = supplierstore.id,
                    order_id = main.id,
                    item_unit_id = data.item_unit.id,  # Track the unit type
                    package_size_id = package if package else None,
                    ordertype = ordertype,
                    quantity = qty,
                    pending_received_qty = data.quantity,
                    unit_price = data.unit_price,
                    total_price = data.total_price,
                    tax = tax,
                    discount = discount,
                    discount_type = discounttype,
                )
                subtable.save()
            return redirect('reorder_stocks')

        
        context = {'report': report,'itemunit':itemunit,'deliverystore':deliverystore,'vendors':vendors}
        return render(request, 'SupplierPortal/reorder_stocks.html',context)
    except Exception as error:
        return render(request, '500.html', {'error': error})



# =============================== Stock Convertion &&& Stock Production =============================
@company_session_required
@supplier_store_session_required
def displyownproduct(request):
    try:
        records = ItemUnit.objects.filter(company_id = request.company,ownproduct = True)
        context = {'records':records}
        return render(request, 'SupplierPortal/StockConvertion/ownproductions.html',context)
    except Exception as error:
        return render(request, '500.html', {'error': error})
    
@company_session_required
@supplier_store_session_required
def billofmaterial(request,pk): # pk is item unit id
    try:
        company = Company.objects.get(id = request.company)

        supplierstore = SupplierStore.objects.filter(id = request.supplier_store_id).last()
        itemunit = ItemUnit.objects.filter(company_id = request.company)
        records = ItemUnit.objects.filter(id = pk).last()
        allrecords = BOMMapping.objects.filter(supplierstore_id = supplierstore.id)
        if request.method == "POST":
            itemsofadd = request.POST.get('item_unit')
            quantity = request.POST.get('quantity_received')
            description = request.POST.get('Description')

            BOMMapping.objects.create(
                company_id = company.id,
                supplier_id = supplierstore.supplier.id,
                supplierstore_id = supplierstore.id, 
                own_product_id = pk,
                product_id = itemsofadd,
                quantity_required = quantity,
                description = description,
            )
            return redirect(f'/billofmaterial/{pk}')
       
        context = {'records':records,'itemunit':itemunit,'allrecords':allrecords}
        return render(request, 'SupplierPortal/StockConvertion/billofmaterial.html',context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

def get_itemunitdetails_js(request):
    itemid = request.POST.get('itemunit')
    packages = ItemUnit.objects.filter(id = itemid).last()

    return JsonResponse({"price": packages.price})

@company_session_required
@supplier_store_session_required
def multiapproval_view(request):
    try:
        supplierstore = SupplierStore.objects.get(id = request.supplier_store_id)
        records = MultiApprover.objects.filter(supplierstore_id = supplierstore.id)
        context = {'records':records}
        return render(request, 'SupplierPortal/multiapproval_view.html',context)
    except Exception as error:
        return render(request, '500.html', {'error': error})


