from django.shortcuts import render

from SupplierPortal.models import StockTransferMain, StockTransferSub, SupplierStoreToStoreRequestMain
from mainapp.models import Customerstore, SupplierStore
from user_management.decorators import company_session_required, customer_store_session_required, supplier_store_session_required
from user_management.models import Company


@company_session_required 
@supplier_store_session_required
def view_supplierstorerequest(request): # SupplierOrderMain ID pass
    try:
        company = Company.objects.get(id=request.company)
        supplier_store = request.supplier_store_id
        supplierstore = SupplierStore.objects.get(id = supplier_store)

        main = StockTransferMain.objects.filter(storefrom_id = supplierstore.id )
        context = {'records':main}
        return render(request,'SupplierPortal/view_supplierstorerequest.html',context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

@company_session_required 
@supplier_store_session_required  
def view_suppliertransfer_sub(request,pk): # SupplierOrderMain ID pass
    try:
        company = Company.objects.get(id=request.company)
        supplier_store = request.supplier_store_id
        supplierstore = SupplierStore.objects.get(id = supplier_store)

        main = StockTransferMain.objects.get(id = pk)
        subtable = StockTransferSub.objects.filter(transfermain_id = main.id)
        context = {'records':main,'recordssub':subtable}
        return render(request,'SupplierPortal/view_suppliertransfer_sub.html',context)
    except Exception as error:
        return render(request, '500.html', {'error': error})

@company_session_required
@supplier_store_session_required
def direct_suppliertransferdetails(request):
    try:
        suppliers_store_id = request.supplier_store_id
        print("suppliers_store_id",suppliers_store_id)
        supplier = SupplierStore.objects.get(id = suppliers_store_id)
        records = StockTransferMain.objects.filter(storefrom = suppliers_store_id ).order_by('-id')
        context = {'records':records}
        print("records",records)
        return render(request, 'SupplierPortal/supplier_transferdetails.html',context) 
    except Exception as error:
        return render(request, '500.html', {'error': error})  


@company_session_required
@supplier_store_session_required
def direct_suppliertransferdetailssub(request,id):
    try:
        suppliers_store_id = request.supplier_store_id
        print("suppliers_store_id",suppliers_store_id)
        recordsmain = StockTransferMain.objects.filter(id=id)
      
        records = StockTransferSub.objects.filter(transfermain_id=id)
        context = {'records':records,'recordsmain':recordsmain}
        return render(request, 'SupplierPortal/suppliertransfer_sub.html',context) 
    except Exception as error:
        return render(request, '500.html', {'error': error})          



@company_session_required
@supplier_store_session_required
def view_disply_transfer(request):
    try:
        suppliers_store_id = request.supplier_store_id
        supplier = SupplierStore.objects.get(id = suppliers_store_id)
        records = StockTransferMain.objects.filter(storefrom_id = supplier.id,tracking_status__in = ['OrderShipped','InTransit','Delivered']  )
        context = {'records':records}
        return render(request, 'SupplierPortal/view_display_transfer.html',context) 
    except Exception as error:
        return render(request, '500.html', {'error': error})    


@company_session_required
@supplier_store_session_required
def view_delivered_stocks(request):
    try:
        suppliers_store_id = request.supplier_store_id
        supplier = SupplierStore.objects.get(id = request.supplier_store_id)
        recordsmain = StockTransferMain.objects.filter(destinationstore_id = supplier.id,transfertype__iexact = 'Direct').order_by('-id')
    
        context = {'records':recordsmain}
        return render(request, 'SupplierPortal/view_delivered_stocks.html',context) 
    except Exception as error:
        return render(request, '500.html', {'error': error})       
    

@company_session_required
@supplier_store_session_required
def view_supplierdisply_transferdetails(request):
    try:
        suppliers_store_id = request.supplier_store_id
        supplier = SupplierStore.objects.get(id = request.supplier_store_id)
        records = StockTransferMain.objects.filter(storefrom_id = supplier.id,tracking_status__in = ['Confirmed','OrderShipped','InTransit','Delivered'] )
        context = {'records':records}
        return render(request, 'SupplierPortal/view_suppliertransferdetails.html',context) 
    except Exception as error:
        return render(request, '500.html', {'error': error})    
    


@company_session_required
@supplier_store_session_required
def supplier_view_returntomanufacturermain(request):
    try:
        suppliers_store_id = request.supplier_store_id
        supplier = SupplierStore.objects.get(id = request.supplier_store_id)
        records = CustomerStockReturnToManufacturerMain.objects.filter(supplier_id=supplier.supplier.id)
        context = {'records':records,'supplier':supplier}
        return render(request, 'SupplierPortal/supplier_view_returntomanufacturemain.html',context)
    except Exception as error:
        return render(request, '500.html', {'error': error})
    
@company_session_required
@supplier_store_session_required
def supplier_returntomanufacturersub(request,pk):
    try:
        supplier = SupplierStore.objects.get(id = request.supplier_store_id)
        recordsmain = CustomerStockReturnToManufacturerMain.objects.get(id = pk)
        records = CustomerStockReturnToManufacturerSub.objects.filter(returnmain_id = pk)
        context = {'records':records,'recordsmain':recordsmain,'supplier':supplier}
        return render(request, 'SupplierPortal/supplier_return_to_manufacture.html',context)
    except Exception as error:
        return render(request, '500.html', {'error': error})    