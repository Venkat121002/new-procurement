
import csv
import io
from pyexpat.errors import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.db.models import Sum
from SupplierPortal.models import SupplierInventoryBatchWise, SupplierStockAdjustMain, SupplierStockAdjustmentSub, SupplierStoreToStoreRequestMain, SupplierStoreToStoreRequestSub
from mainapp.models import CustomerRegistrations, ItemSubCategoryMaster, ItemUnit, PackageSizeMaster, Supplier, SupplierStore
from user_management.decorators import company_session_required, supplier_store_session_required
from user_management.models import Company
from datetime import date, datetime

def generateunique_id(pre, suf):
    tot_rec_count = suf + 1

    # Format record count to 3 digits (e.g., 001, 012, 123)
    rec_str = str(tot_rec_count).zfill(3)

    # Get current date as YYMMDD
    date_str = datetime.now().strftime('%y%m%d')  # <-- 2-digit year

    # Construct ID: prefix + date + count (e.g., PO250516001)
    id = f"{pre}{date_str}{rec_str}"

    return id

@company_session_required
@supplier_store_session_required
def supplier_stockadjustment(request): # pk is a manufacturer id
    try: 

        sk= request.GET.get('manufacturer')
        print("sk",sk)
        suppliers_store_id = request.supplier_store_id
        supplier = SupplierStore.objects.get(id = request.supplier_store_id)
        # manufacture = SupplierCustomerMapping.objects.get(id = pk,company_id = request.company)
        # kk=manufacture.supplier.id
        records = SupplierInventoryBatchWise.objects.filter(company_id=request.company,store_to_id=suppliers_store_id)
        subcategory = ItemSubCategoryMaster.objects.filter(company_id = request.company)
        product = ItemUnit.objects.filter(company_id = request.company)
        
        if request.method == "POST":
            search_btn = request.POST.get("return_btn")
            if search_btn == "return_btn":
                selected_ids = request.POST.getlist('active_products')
                def get_unique_poid1():
                    count = SupplierStockAdjustMain.objects.count()
                    
                    while True:
                        POID = generateunique_id('MA', count)
                        if not SupplierStockAdjustMain.objects.filter(return_id=POID).exists():
                            return POID  # Found a unique one, return it
                        count += 1  # Otherwise, try the next number

            
                RNID = get_unique_poid1()


                # Generate unique id
                def get_unique_poid():
                    count = SupplierStockAdjustMain.objects.count()
                    
                    while True:
                        POID = generateunique_id('MA', count)
                        if not SupplierStockAdjustMain.objects.filter(return_id=POID).exists():
                            return POID  # Found a unique one, return it
                        count += 1  # Otherwise, try the next number

            
                TNID = get_unique_poid()
            
                returns = SupplierStockAdjustMain.objects.create(
                    company_id = request.company,
                    supplier_id = supplier.supplier.id,
                    supplierstore_id = supplier.id, # return from
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
                        SupplierStockAdjustmentSub.objects.create(
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
                            instockrecords.inhand_pieces += int(return_qty)
                            instockrecords.total_amount +=total_amt
                            instockrecords.stock_balance = str(instockrecords.inhand_package)+ 'W' + str(instockrecords.inhand_pieces) + 'P'
                        else:
                            total_amt = float(instockrecords.item_unit.price) * int(return_qty)
                            instockrecords.inhand_pieces += int(return_qty)
                            instockrecords.total_amount +=total_amt
                            instockrecords.stock_balance = str(instockrecords.inhand_package)+ 'W' + str(instockrecords.inhand_pieces) + 'P'
                        instockrecords.save()
                    # ss+=int(return_qty) * float(amt)

                    # print('total',ss)


                    fortotalamt = SupplierStockAdjustmentSub.objects.filter(returnmain_id = returns.id).aggregate(total_amt = Sum("amount"))
                    fortotalamt = fortotalamt['total_amt'] or 0.0
                    returns.total_amount = fortotalamt
                    returns.save()
                return redirect('supplier_viewstockadjust')


        context = {"records":records,'supplier':supplier,'subcategory':subcategory,'product':product,}
        return render(request, 'SupplierPortal/supplier_stockadjust.html',context)
    except Exception as error:
        return render(request, '500.html', {'error': error})




@company_session_required
@supplier_store_session_required
def supplier_viewstockadjust(request):
    try:
        records=SupplierStockAdjustMain.objects.filter(company_id=request.company,supplierstore_id=request.supplier_store_id).order_by("-id")
        context={'records':records}
        return render(request,'SupplierPortal/supplier_viewstockadjust.html',context)
    except Exception as error:
        return render(request, '500.html', {'error': error})


@company_session_required
@supplier_store_session_required
def supplier_viewstockadjustsub(request,id):
   records=SupplierStockAdjustmentSub.objects.filter(company_id=request.company,returnmain=id)
   context={'records':records}
   return render(request,'SupplierPortal/supplier_viewstockadjustsub.html',context)



@company_session_required
@supplier_store_session_required
def upload_supplierinventory_csv(request):
    supplier = SupplierStore.objects.get(id = request.supplier_store_id)
    if request.method == 'POST':
        csv_file = request.FILES['csv_file']
        if not csv_file.name.endswith('.csv'):
            messages.error(request, 'This is not a CSV file.')
            return redirect('upload_inventory_csv')

        data_set = csv_file.read().decode('UTF-8')
        io_string = io.StringIO(data_set)
        reader = csv.DictReader(io_string)

        for row in reader:
           
                # customer = CustomerRegistrations.objects.get(name=row['customer_id']) if row['customer_id'] else None
                # customerstore = SupplierStore.objects.get(name=row['customerstore_id']) if row['customerstore_id'] else None
                # company = Company.objects.get(name=row['company_id'])
                # print('company',company)
                # print('company_id',company.id)
                # receiveddetails = CustomerGoodsReceived.objects.get(id=row['receiveddetails_id']) if row['receiveddetails_id'] else None
                item_unit = ItemUnit.objects.get(item__item_name=row['item_unit_id'])
                print('item_unit',item_unit)
                receivetype = row['receivetype']
                expiry_date = row['expiry_date']
                print('expiry date',expiry_date)
                batch_no = row['batch_no']
                print('batch_no',batch_no)


                # Skip if already exists (define your uniqueness criteria)
                if SupplierInventoryBatchWise.objects.filter(
                    supplier_id=supplier.supplier.id,
                    item_unit_id=item_unit.id,
                    batch_no=batch_no,
                ).exists():
                    continue

                SupplierInventoryBatchWise.objects.create(
                    supplier_id=supplier.supplier.id,
                    store_to_id=request.supplier_store_id,
                    # customerstore_id=supplier.id,
                    company_id=request.company,
                    # receiveddetails=receiveddetails,
                    item_unit_id=item_unit.id,
                    receivetype=receivetype,
                    expiry_date=expiry_date,
                    batch_no=batch_no,
                    packsize=PackageSizeMaster.objects.get(package_name=row['packsize_id']) if row['packsize_id'] else None,
                    inhand_package=int(row['inhand_package']),
                    inhand_pieces=int(row['inhand_pieces']),
                    total_amount=float(row['total_amount']),
                    piece_amt=float(row['piece_amt']),
                    package_amount=float(row['package_amount']),
                    package_selling_rate=float(row['package_selling_rate']),
                    piece_selling_rate=float(row['piece_selling_rate']),
                    tax=float(row['tax']),
                    discount=float(row['discount']),
                    discount_type=row['discount_type'],
                    stock_balance=row['stock_balance'],
                    received_date=row['received_date'],
                    manufacture_date=row['manufacture_date']
                )

        # messages.success(request, 'CSV imported successfully!')
        return redirect('upload_supplierinventory_csv')

    return render(request, 'SupplierPortal/upload_supplier_csv.html')



@company_session_required
@supplier_store_session_required
def supplier_stockrequest_edit(request, pk):
    # try:
        company = Company.objects.get(id = request.company)
        customer_store = request.supplier_store_id
        customerstore = SupplierStore.objects.get(id=customer_store)
        vendors = SupplierStore.objects.filter(supplier_id=customerstore.supplier.id, company_id=company.id).exclude(id=customer_store)

        # Fetch order details
        order = get_object_or_404(SupplierStoreToStoreRequestMain, id=pk, company_id=company.id, supplierstore_from=customer_store)

        kk=order.expected_delivery

        print('kk',kk)

        # orders = get_object_or_404(SupplierStoreToStoreRequestSub, id=pk, company_id=company.id, supplierstore=customer_store)

        orders=SupplierStoreToStoreRequestSub.objects.filter(order_id=pk).last()

        items = SupplierStoreToStoreRequestSub.objects.filter(order_id=pk)

        pack=PackageSizeMaster.objects.filter(company_id=company.id)

        itemunits = ItemUnit.objects.filter(company_id=company.id)
        for item in itemunits:
           li= item.item


        
        order.expected_delivery = request.POST.get('expecteddate')
        # order.extra_charges=request.POST.get('extra_charges')



        if request.method == "POST":
            # Update order details
            v2=request.POST.get('vendor')
            print("vendor===",v2)
            # order.supplier_id = request.POST.get('vendor') if request.POST.get('vendor') != "None" else None
            order.expected_delivery = request.POST.get('expected_delivery')

            order.total_amount = request.POST.get('total_amount')

            order.save()

            # Update each item in the order
            for item in items:
                print('dicount',request.POST.get(f'discount_value_{item.id}', item.discount))
                item.quantity = request.POST.get(f'quantity_{item.id}', item.quantity)
                item.unit_price = request.POST.get(f'unit_price_{item.id}', item.unit_price)
                item.total_price = float(item.quantity) * float(item.unit_price)
                print("total_price",item.total_price)   
                item.tax = request.POST.get(f'item_tax_{item.id}', item.tax)
                item.discount = request.POST.get(f'discount_value_{item.id}', item.discount)
                item.discount_type = request.POST.get(f'discount_type_{item.id}', item.discount_type)
                item.package_size_id = request.POST.get(f'item_package_{item.id}') if request.POST.get(f'item_package_{item.id}') != "None" else None
                item.ordertype = request.POST.get(f'order_type_{item.id}', item.ordertype)
                item.save()

            return redirect('supplierstoretostorerequest_view')

        # Context data for rendering template
        context = {
            'order': orders,
            'items': items,
            'vendors': vendors,
            'itemunits': itemunits,
            'li':li,
            'kk':kk
             
        }
        return render(request, "SupplierPortal/supplierstockrequest_edit.html", context)


    # except Exception as error:
    #     return render(request, '500.html', {'error': error})