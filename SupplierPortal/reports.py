from SupplierPortal.models import *
from mainapp.models import *
from django.shortcuts import render,redirect
from user_management.decorators import company_session_required,supplier_store_session_required
from django.utils import timezone
from django.db.models import Sum
def supplierreport_dashboard(request):
    try:
        return render(request,'SupplierPortal/Reports/supplierreport_dashboard.html')
    except Exception as error:
        return render(request, '500.html', {'error': error})

@company_session_required
@supplier_store_session_required
def supplierorder_report(request):
    try:
        maintable = SupplierOrderMain.objects.filter(supplierstore_id=request.supplier_store_id)
        
        supplier = Vendor.objects.all()

        # Filter inputs
        po_id = request.GET.get('po_id')
        supplier_id = request.GET.get('supplier_id')
        start_date = request.GET.get('startdate')
        end_date = request.GET.get('enddate')

        if po_id:
            maintable = maintable.filter(id=po_id)
        if supplier_id:
            maintable = maintable.filter(supplier_id=supplier_id)
        if start_date and end_date:
            maintable = maintable.filter(order_date__range=[start_date, end_date])

        records = []
        for data in maintable:
            subtable = SupplierOrderItemSub.objects.filter(order_id=data.id)
            records.append({
                'main': data,
                'items': subtable
            })
        return render(request, 'SupplierPortal/Reports/supplierorder_report.html', {'records': records,'maintable':maintable,'supplier':supplier})
    except Exception as error:
        return render(request, '500.html', {'error': error})


@company_session_required
@supplier_store_session_required
def supplierorder_approval_report(request):
    try:
        maintable = SupplierOrderMain.objects.filter(supplierstore_id=request.supplier_store_id)
        supplier = Vendor.objects.all()

        # Filter inputs
        po_id = request.GET.get('po_id')
        supplier_id = request.GET.get('supplier_id')
        start_date = request.GET.get('startdate')
        end_date = request.GET.get('enddate')

        if po_id:
            maintable = maintable.filter(id=po_id)
        if supplier_id:
            maintable = maintable.filter(supplier_id=supplier_id)
        if start_date and end_date:
            maintable = maintable.filter(order_date__range=[start_date, end_date])
        records = []
        for data in maintable:
            subtable = SupplierOrderItemSub.objects.filter(order_id=data.id)
            records.append({
                'main': data,
                'items': subtable
            })
        return render(request, 'SupplierPortal/Reports/supplierorder_approval_report.html', {'records': records,'maintable':maintable,'supplier':supplier})
    except Exception as error:
        return render(request, '500.html', {'error': error})


@company_session_required
@supplier_store_session_required
def goodsreceive_report(request):
    # try:
        maintable1 = SupplierOrderMain.objects.filter(supplierstore_id=request.supplier_store_id)
        receivetable = GoodsReceived.objects.filter(store_to_id=request.supplier_store_id)
        supplier = Vendor.objects.all()
        
        records = []
        

        if request.method == "POST":
            # Filter inputs
            po_id = request.POST.get('POnumber')
            supplier_id = request.POST.get('vendorsss')
            grnnumber = request.POST.get('GRNnumber')
            start_date = request.POST.get('startdate')
            end_date = request.POST.get('enddate')
            maintable = []
            print("++++++++++++++++===",po_id)
            if po_id:
                maintable = receivetable.filter(po_number_id=int(po_id))
            if grnnumber:
                
                maintable = receivetable.filter(id=int(grnnumber))
            if supplier_id:
                maintable = receivetable.filter(vendor_id=int(supplier_id))
        
            if start_date and end_date:
                maintable = receivetable.filter(received_date__range=[start_date, end_date])
            
            for data in maintable:
             
                subtable = SupplierInventoryBatchWise.objects.filter(store_to_id=request.supplier_store_id,receiveddetails_id = data.id)
                records.append({
                    'ordermain': data,
                    'items': subtable,
                })
        else:
            for data in receivetable:
                subtable = SupplierInventoryBatchWise.objects.filter(store_to_id=request.supplier_store_id,receiveddetails_id = data.id)
                records.append({
                    'ordermain': data,
                    'items': subtable,
                })
        
        return render(request, 'SupplierPortal/Reports/goodsreceive_report.html', {'records': records,'maintable':maintable1,'supplier':supplier,'receivetable':receivetable})
    # except Exception as error:
    #     return render(request, '500.html', {'error': error})


@company_session_required
@supplier_store_session_required
def supplierstock_report(request):
    try:
        product = ItemUnit.objects.filter(company_id = request.company)
        subtable = SupplierInventoryBatchWise.objects.filter(store_to_id=request.supplier_store_id)
        if request.method == "POST":
            product = request.POST.get('productss')
            subtable = SupplierInventoryBatchWise.objects.filter(store_to_id=request.supplier_store_id,item_unit_id =product )
             
        return render(request, 'SupplierPortal/Reports/supplierstock_report.html', {'records': subtable,'product':product})
    except Exception as error:
        return render(request, '500.html', {'error': error})


@company_session_required
@supplier_store_session_required
def invoices_reports(request):
    try:
        company = Company.objects.get(id=request.company)
        supplier_store = int(request.supplier_store_id)
        pendinginvoice = SupplierInvoice.objects.filter(store_to_id = supplier_store)
        if request.method == "POST":
            invoice = request.POST.get('invoice')
            paymentstatus = request.POST.get('paymentstatus')
            if invoice:
                pendinginvoice = SupplierInvoice.objects.filter(store_to_id = supplier_store,id = invoice)
            if paymentstatus:
                pendinginvoice = SupplierInvoice.objects.filter(store_to_id = supplier_store,payment_status__iexact = paymentstatus)

            
        context = {'records':pendinginvoice}
        return render(request,"SupplierPortal/Reports/invoices_reports.html",context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

@company_session_required
@supplier_store_session_required
def stock_transferreport(request):
    try:
        company = Company.objects.get(id=request.company)
        supplier_store = int(request.supplier_store_id)
        current_store = SupplierStore.objects.get(id = supplier_store)
        stores = SupplierStore.objects.filter(supplier_id = current_store.supplier.id)
        if request.method == "POST":
            storefrom = request.POST.get('storefrom')
            startdate = request.POST.get('startdate')
            enddate = request.POST.get('enddate')
            maintable = []
            if storefrom:
                maintable = StockTransferMain.objects.filter(storefrom_id = storefrom)
            if startdate and enddate:
                maintable = StockTransferMain.objects.filter(storefrom_id=request.supplier_store_id,transfer_date__range = [startdate,enddate])
            records = []
            for data in maintable:
                subtable = StockTransferSub.objects.filter(transfermain_id=data.id)
                records.append({
                    'main': data,
                    'items': subtable
                })
           

        else:
            maintable = StockTransferMain.objects.filter(storefrom_id=request.supplier_store_id)
            
            records = []
            for data in maintable:
                subtable = StockTransferSub.objects.filter(transfermain_id=data.id)
                records.append({
                    'main': data,
                    'items': subtable
                })
        
        context = {'records':records,'stores':stores}
        return render(request,"SupplierPortal/Reports/stock_transferreport.html",context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

@company_session_required
@supplier_store_session_required
def stock_returnreport(request):
    try:
        company = Company.objects.get(id=request.company)
        supplier_store = int(request.supplier_store_id)
        current_store = SupplierStore.objects.get(id = supplier_store)
        maintable = StockReturnToManufacturerMain.objects.filter(store_id=request.supplier_store_id)
        stores = Vendor.objects.all()
        if request.method == "POST":
            manufacturer = request.POST.get('manufacturer')
            startdate = request.POST.get('startdate')
            enddate = request.POST.get('enddate')
            subtable = []
            if manufacturer:
                subtable = StockReturnToManufacturerMain.objects.filter(manufacturer_id=manufacturer)
            if startdate and enddate:
                subtable = StockReturnToManufacturerMain.objects.filter(storefrom_id=request.supplier_store_id,return_date__range = [startdate,enddate])
            records = []
            for data in maintable:
                subtable = StockReturnToManufacturerSub.objects.filter(returnmain_id=data.id)
                records.append({
                    'main': data,
                    'items': subtable
                })
        else:
            records = []
            for data in maintable:
                subtable = StockReturnToManufacturerSub.objects.filter(returnmain_id=data.id)
                records.append({
                    'main': data,
                    'items': subtable
                })
        context = {'records':records,'stores':stores}
        return render(request,"SupplierPortal/Reports/stock_returnreport.html",context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

@company_session_required
@supplier_store_session_required
def stock_wastagereport(request):
    try:
        company = Company.objects.get(id=request.company)
        supplier_store = int(request.supplier_store_id)
        maintable = SupplierInventoryWastage.objects.filter(store_id=request.supplier_store_id)
        product = ItemUnit.objects.filter(company_id = company.id)
        if request.method == "POST":
            productss = request.POST.get('productss')
            maintable = SupplierInventoryWastage.objects.filter(store_id=request.supplier_store_id,inventory_batch__item_unit_id = productss)
        context = {'records':maintable,'product':product}
        return render(request,"SupplierPortal/Reports/stock_wastagereport.html",context)
    except Exception as error:
        return render(request, '500.html', {'error': error})
    

    
@company_session_required
@supplier_store_session_required
def manualstock_report(request):
    try:
        supplier_store = int(request.supplier_store_id)
        current_store = SupplierStore.objects.get(id = supplier_store)
        stores = SupplierStore.objects.filter(supplier_id = current_store.supplier.id)
        
        if request.method == "POST":
            storefrom = request.POST.get('storefrom')
            startdate = request.POST.get('startdate')
            enddate = request.POST.get('enddate')
            maintable = []
            if storefrom:
                maintable = SupplierStockAdjustMain.objects.filter(supplierstore_id=storefrom)
            if startdate and enddate:
                maintable = SupplierStockAdjustMain.objects.filter(supplierstore_id=request.supplier_store_id,return_date__range = [startdate,enddate] )
            records = []
            for data in maintable:
                subtable = SupplierStockAdjustmentSub.objects.filter(returnmain=data.id)
                records.append({
                    'main': data,
                    'items': subtable
                })
        else:
            maintable = SupplierStockAdjustMain.objects.filter(supplierstore_id=request.supplier_store_id)
            records = []
            for data in maintable:
                subtable = SupplierStockAdjustmentSub.objects.filter(returnmain=data.id)
                records.append({
                    'main': data,
                    'items': subtable
                })


        return render(request, 'SupplierPortal/Reports/manualstock_report.html', {'records': records,'stores':stores})

    except Exception as error:
        return render(request, '500.html', {'error': error})

@company_session_required
@supplier_store_session_required
def stockreorder_report(request):
    try:
        company = Company.objects.get(id=request.company)
        supplier_store_id = request.supplier_store_id
        supplierstore = SupplierStore.objects.get(id=supplier_store_id)

        today = timezone.now()
        start_month = today.replace(day=1)
        end_month = (start_month + timezone.timedelta(days=32)).replace(day=1)

        
        # 1. Delivered orders this month (group by item_unit)
        order_items = SupplierOrderItemSub.objects.filter(
            created_at__gte=start_month,
            created_at__lt=end_month,
            order_status="Delivered",
            supplierstore=supplierstore
        )

        order_totals = order_items.values(
            'item_unit__id',
            'item_unit__brand__name',
            'item_unit__conversion_factor_to_base',
            'item_unit__unit__symbol',
            'item_unit__item__item_name'
        ).annotate(
            total_ordered=Sum('received_qty')
        )

        # 2. Current inventory
        inventory = SupplierInventoryBatchWise.objects.filter(
            received_date__lte=end_month,
            store_to_id=supplierstore.id
        )

        stock_totals = inventory.values(
            'item_unit__id',
            'item_unit__brand__name',
            'item_unit__conversion_factor_to_base',
            'item_unit__unit__symbol',
            'item_unit__item__item_name'
        ).annotate(
            total_inhand=Sum('inhand_pieces')
        )

        stock_dict = {
            entry['item_unit__id']: entry['total_inhand'] for entry in stock_totals
        }

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
            total_received = order['total_ordered']
            current_stock = stock_dict.get(unit_id, 0)
            consumed = total_received - current_stock
            reorder_needed = current_stock < REORDER_THRESHOLD
            reorder_qty = REORDER_THRESHOLD - current_stock if reorder_needed else 0
            if reorder_qty <= current_stock:
                reorder_qty = 0
                reorder_needed = 0

            report.append({
                'item_unit_id':unit_id,
                'item_name': f'{item_name}/{unit}{symbol}',
                'brand' : brand,
                'total_received': total_received,
                'current_stock': current_stock,
                'consumed': consumed,
                'reorder_needed': reorder_needed,
                'reorder_qty': reorder_qty,
            })

        context = {
            'report': report,
            'supplierstore': supplierstore,
            'start_month': start_month,
            'end_month': end_month
        }

        return render(request, "SupplierPortal/Reports/stockreorder_report.html", context)

    except Exception as error:
        return render(request, '500.html', {'error': error})