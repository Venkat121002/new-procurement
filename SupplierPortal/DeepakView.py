from django.shortcuts import get_object_or_404, redirect, render
# from CustomerPortal.forms import CreatestoreMasterForm
from SupplierPortal.models import GoodsReceived, SupplierInventoryBatchWise, SupplierInvoice
from user_management.decorators import company_session_required, customer_store_session_required, distributorbranch_session_required, supplier_store_session_required
import pandas as pd
from django.shortcuts import render, redirect
from django.contrib import messages

from user_management.forms import BranchForm
from user_management.models import Branch, Company
from .forms import FileUploadForm
from mainapp.models import CountryMaster, Customerstore, DistributorBranch, ItemMaster, ItemCategoryMaster, ItemSubCategoryMaster, BrandMaster, ItemUnit, PackageSizeMaster, StoreTypeMaster, SubCountryMaster, UnitOfMeasure


@company_session_required
def pay(request,id):
    company = Company.objects.get(id=request.company)
    obj=GoodsReceived.objects.get(id=id)
    current_store  =  obj.store_to
    # current_branch = request.branch_id
    

    supplier= get_object_or_404(SupplierInvoice,company_id=company.id,store_to_id=current_store)

    return render(request, 'SupplierPortal/pay.html',{'supplier': supplier},)


@company_session_required
def bulk_upload_items(request):
    company = Company.objects.get(id = request.company)
    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['file']
            try:
                # Detect file type and read data
                if file.name.endswith('.csv'):
                    df = pd.read_csv(file)
                elif file.name.endswith('.xlsx'):
                    df = pd.read_excel(file)
                else:
                    messages.error(request, "Unsupported file format. Please upload a CSV or Excel file.")
                    return redirect('bulk_upload_items')

                created_count = 0
                skipped_count = 0

                # Process each row
                for _, row in df.iterrows():
                    category = ItemCategoryMaster.objects.get(name=row['category'])
                    subcategory = ItemSubCategoryMaster.objects.get(name=row['subcategory']) if 'subcategory' in row and not pd.isna(row['subcategory']) else None
                    brand = BrandMaster.objects.get(id=row['brand_id']) if 'brand_id' in row and not pd.isna(row['brand_id']) else None

                    # Check for duplicates (based on item_name + branch + category + subcategory + brand)
                    if ItemMaster.objects.filter(
                        company_id=company.id,
                        item_name=row['item_name'],
                        category=category,
                        subcategory=subcategory,
                        brand=brand
                    ).exists():
                        skipped_count += 1
                        continue  # Skip duplicate

                    # Create new item
                    ItemMaster.objects.create(
                        company_id=company.id,
                        category=category,
                        subcategory=subcategory,
                        brand=brand,
                        item_name=row['item_name'],
                        description=row.get('description', ''),
                        reorder_level=row.get('reorder_level', 0.0),
                        amount=row.get('amount', 0.0),
                        tax_rate=row.get('tax_rate', 0.0),
                        discount=row.get('discount', 0.0),
                        discount_type=row['discount_type'],
                        barcode=row.get('barcode', '')
                    )
                    created_count += 1

                messages.success(request, f"{created_count} item(s) uploaded successfully. {skipped_count} duplicate(s) skipped.")
                return redirect('itemcategorymaster_list')

            except Exception as e:
                messages.error(request, f"Error: {e}")
                return redirect('bulk_upload_items')
    else:
        form = FileUploadForm()

    return render(request, 'Data_import/bulk_upload.html', {'form': form})


@company_session_required
def bulk_upload_itemcategory_master(request):
    company = Company.objects.get(id = request.company)
    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['file']
            print("file",file)
            print("file format",type(file))
            try:
                # Detect file type and read data
                if file.name.endswith('.csv'):
                    df = pd.read_csv(file)
                elif file.name.endswith('.xlsx'):
                    df = pd.read_excel(file)
                else:
                    messages.error(request, "Unsupported file format. Please upload a CSV or Excel file.")
                    return redirect('bulk_upload_items')
                created_count = 0
                skipped_count = 0
                # Process each row
                for _, row in df.iterrows():
                   
                    if ItemCategoryMaster.objects.filter(
                        company_id=company.id,
                        name=row['name'],
                    ).exists():
                        skipped_count += 1
                        continue  # Skip duplicate
                       
                    # Create new item   
                    ItemCategoryMaster.objects.create(
                        company_id=company.id,
                        
                       
                        name=row['name'],
                        description=row.get('description', ''),
                    
                    )
                    print("ss--------",ItemCategoryMaster)


                    created_count += 1

                messages.success(request, "Items uploaded successfully!")
                return redirect('bulk_upload_items')

            except Exception as e:
                messages.error(request, f"Error: {e}")
                return redirect('bulk_upload_items')
    else:
        form = FileUploadForm()
    
    return render(request, 'Data_import/bulk_upload.html', {'form': form})

@company_session_required
def bulk_upload_subcategory_master(request):
    company = Company.objects.get(id = request.company)
    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['file']
            try:
                # Detect file type and read data
                if file.name.endswith('.csv'):
                    df = pd.read_csv(file)
                elif file.name.endswith('.xlsx'):
                    df = pd.read_excel(file)
                else:
                    messages.error(request, "Unsupported file format. Please upload a CSV or Excel file.")
                    return redirect('itemsubcategorymaster_list')
                created_count = 0
                skipped_count = 0
                # Process each row
                for _, row in df.iterrows():
                    category = ItemCategoryMaster.objects.get(name=row['category_id'])

                    # subcategory = ItemSubCategoryMaster.objects.get(name=row['subcategory_id']) if 'subcategory_id' in row and not pd.isna(row['subcategory_id']) else None
                    # brand = BrandMaster.objects.get(id=row['brand_id']) if 'brand_id' in row and not pd.isna(row['brand_id']) else None
                    if ItemSubCategoryMaster.objects.filter(
                        company=company.id,
                        category=category,
                        name=row['name'],
                    ).exists():
                        skipped_count += 1
                        continue
                    ItemSubCategoryMaster.objects.create(
                        company_id=company.id,
                        category=category,
                       
                        name=row['name'],
                        description=row.get('description', ''),
                      
                    )
                    created_count += 1
                messages.success(request, "Items uploaded successfully!")
                return redirect('itemsubcategorymaster_list')

            except Exception as e:
                messages.error(request, f"Error: {e}")
                return redirect('bulk_upload_subcategory_master')
    else:
        form = FileUploadForm()
    
    return render(request, 'Data_import/bulk_upload.html', {'form': form})

@company_session_required
def bulk_upload_brand_master(request):
    company = Company.objects.get(id = request.company)
    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['file']
            try:
                # Detect file type and read data
                if file.name.endswith('.csv'):
                    df = pd.read_csv(file)
                elif file.name.endswith('.xlsx'):
                    df = pd.read_excel(file)
                else:
                    messages.error(request, "Unsupported file format. Please upload a CSV or Excel file.")
                    return redirect('bulk_upload_items')
                created_count = 0
                skipped_count = 0
                # Process each row
                for _, row in df.iterrows():
                    
                    if BrandMaster.objects.filter(
                        company_id=company.id,
                        name=row['name'],
                    ).exists():
                        skipped_count += 1
                        continue
                    
                    BrandMaster.objects.create(
                        company_id=company.id,
                        name=row['name'],
                        description=row.get('description', ''),
                     
                    )   
                    created_count

                messages.success(request, "Items uploaded successfully!")
                return redirect('brandmaster_list')

            except Exception as e:
                messages.error(request, f"Error: {e}")
                return redirect('bulk_upload_brand_master')
    else:
        form = FileUploadForm()
    
    return render(request, 'Data_import/bulk_upload.html', {'form': form})

@company_session_required
def bulk_upload_unitofmeasure(request):
    company = Company.objects.get(id = request.company)
    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['file']
            try:
                # Detect file type and read data
                if file.name.endswith('.csv'):
                    df = pd.read_csv(file)
                elif file.name.endswith('.xlsx'):
                    df = pd.read_excel(file)
                else:
                    messages.error(request, "Unsupported file format. Please upload a CSV or Excel file.")
                    return redirect('itemsubcategorymaster_list')
                created_count = 0
                skipped_count = 0
                # Process each row
                for _, row in df.iterrows():
                    # category = ItemCategoryMaster.objects.get(name=row['category_id'])
                    # subcategory = ItemSubCategoryMaster.objects.get(name=row['subcategory_id']) if 'subcategory_id' in row and not pd.isna(row['subcategory_id']) else None
                    # brand = BrandMaster.objects.get(id=row['brand_id']) if 'brand_id' in row and not pd.isna(row['brand_id']) else None
                    if UnitOfMeasure.objects.filter(
                        company_id=company.id,
                        name=row['name'],
                    ).exists():
                        skipped_count += 1
                        continue
                    UnitOfMeasure.objects.create(
                        company_id=company.id,
                      
                        name=row['name'],
                        symbol=row.get('symbol', ''),
                \
                    )
                    created_count += 1

                messages.success(request, "Items uploaded successfully!")
                return redirect('unitofmeasure_list')

            except Exception as e:
                messages.error(request, f"Error: {e}")
                return redirect('bulk_upload_unitofmeasure')
    else:
        form = FileUploadForm()
    
    return render(request, 'Data_import/bulk_upload.html', {'form': form})

@company_session_required
def bulk_upload_itemunit(request):
    company = Company.objects.get(id = request.company)
    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['file']

            print("file------------------->", file)
            try:
                # Detect file type and read data
                if file.name.endswith('.csv'):
                    df = pd.read_csv(file)
                elif file.name.endswith('.xlsx'):
                    df = pd.read_excel(file)
                else:
                    messages.error(request, "Unsupported file format. Please upload a CSV or Excel file.")
                    return redirect('itemsubcategorymaster_list')
                created_count = 0
                skipped_count = 0
                # Process each row
                for _, row in df.iterrows():
                    item = ItemMaster.objects.get(item_name=row['item'])
                    unit = UnitOfMeasure.objects.get(name=row['unit'])

                    # subcategory = ItemSubCategoryMaster.objects.get(name=row['subcategory_id']) if 'subcategory_id' in row and not pd.isna(row['subcategory_id']) else None
                    # brand = BrandMaster.objects.get(id=row['brand_id']) if 'brand_id' in row and not pd.isna(row['brand_id']) else None
                    if ItemUnit.objects.filter(
                        company_id=company.id,
                        item=item,
                        unit=unit,
                    ).exists():
                        skipped_count += 1
                        continue
                    ItemUnit.objects.create(
                        company_id=company.id,
                        item=item,
                        unit=unit,
                    
                        conversion_factor_to_base=row.get('conversion_factor_to_base'),
                        price=row.get('price'),
                     
                    )
                    created_count += 1

                messages.success(request, "Items uploaded successfully!")
                return redirect('itemunit_list')

            except Exception as e:
                messages.error(request, f"Error: {e}")
                return redirect('bulk_upload_itemunit')
    else:
        form = FileUploadForm()
    
    return render(request, 'Data_import/bulk_upload.html', {'form': form})


@company_session_required
def bulk_upload_packagesizemaster(request):
    company = Company.objects.get(id = request.company)
    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['file']
            try:
                # Detect file type and read data
                if file.name.endswith('.csv'):
                    df = pd.read_csv(file)
                elif file.name.endswith('.xlsx'):
                    df = pd.read_excel(file)
                else:
                    messages.error(request, "Unsupported file format. Please upload a CSV or Excel file.")
                    return redirect('itemsubcategorymaster_list')
                created_count = 0
                skipped_count = 0
                # Process each row
                for _, row in df.iterrows():


                    print(row['item'])
                    item = ItemUnit.objects.get(item__item_name=row['item'])

                    print("item------------------->", item)
                    name = BrandMaster.objects.get(name=row['name'])
                    print("name------------------->", name)
                    if PackageSizeMaster.objects.filter(
                        company_id=company.id,
                        itemunit=item,
                        brand=name,
                        package_name=row['package_name'],
                    ).exists():
                        skipped_count += 1
                        continue
                  
                    
                    PackageSizeMaster.objects.create(
                        company_id=company.id,
                        itemunit=item,
                        brand=name,
                        package_name=row.get('package_name', ''),
                        quantity=row.get('quantity', 0),
                        pack_price=row.get('pack_price'),
                     
                    )
                    created_count += 1

                messages.success(request, "Items uploaded successfully!")
                return redirect('packagesizemaster_list')

            except Exception as e:
                messages.error(request, f"Error: {e}")
                return redirect('bulk_upload_packagesizemaster')
    else:
        form = FileUploadForm()
    
    return render(request, 'Data_import/bulk_upload.html', {'form': form})


@company_session_required
def bulk_upload_countrymaster(request):
    company = Company.objects.get(id = request.company)
    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['file']
            try:
                # Detect file type and read data
                if file.name.endswith('.csv'):
                    df = pd.read_csv(file)
                elif file.name.endswith('.xlsx'):
                    df = pd.read_excel(file)
                else:
                    messages.error(request, "Unsupported file format. Please upload a CSV or Excel file.")
                    return redirect('itemsubcategorymaster_list')
                created_count = 0       
                skipped_count = 0
                # Process each row
                for _, row in df.iterrows():
                    # category = ItemCategoryMaster.objects.get(name=row['category_id'])
                    # subcategory = ItemSubCategoryMaster.objects.get(name=row['subcategory_id']) if 'subcategory_id' in row and not pd.isna(row['subcategory_id']) else None
                    # brand = BrandMaster.objects.get(id=row['brand_id']) if 'brand_id' in row and not pd.isna(row['brand_id']) else None
                    if CountryMaster.objects.filter(
                        # branch_id=request.branch_id,
                        company_id=company.id,
                        country_name=row['country_name'],
                    ).exists():
                        skipped_count += 1
                        continue
                    CountryMaster.objects.create(
                        company_id=company.id,
                        # branch_id=request.branch_id,
                      
                        country_name=row['country_name'],
                    
                    )
                    created_count += 1

                messages.success(request, "Items uploaded successfully!")
                return redirect('countrymaster_list')

            except Exception as e:
                messages.error(request, f"Error: {e}")
                return redirect('bulk_upload_countrymaster')
    else:
        form = FileUploadForm()
    
    return render(request, 'Data_import/bulk_upload.html', {'form': form})


@company_session_required
def bulk_upload_subcountrymaster(request):
    company = Company.objects.get(id = request.company)
    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['file']
            try:
                # Detect file type and read data
                if file.name.endswith('.csv'):
                    df = pd.read_csv(file)
                elif file.name.endswith('.xlsx'):
                    df = pd.read_excel(file)
                else:
                    messages.error(request, "Unsupported file format. Please upload a CSV or Excel file.")
                    return redirect('itemsubcategorymaster_list')
                created_count = 0
                skipped_count = 0
                # Process each row
                for _, row in df.iterrows():
                    country = CountryMaster.objects.get(country_name=row['country_id'])
                    # subcategory = ItemSubCategoryMaster.objects.get(name=row['subcategory_id']) if 'subcategory_id' in row and not pd.isna(row['subcategory_id']) else None
                    # brand = BrandMaster.objects.get(id=row['brand_id']) if 'brand_id' in row and not pd.isna(row['brand_id']) else None
                    if SubCountryMaster.objects.filter(
                        company_id=company.id,
                        country=country,
                        sub_country=row['sub_country'],
                    ).exists():
                        skipped_count += 1
                        continue
                    SubCountryMaster.objects.create(
                        company_id=company.id,
                        country=country,
                      
                        sub_country=row['sub_country'],
                    
                    )
                    created_count += 1
                messages.success(request, "Items uploaded successfully!")
                return redirect('subcountrymaster_list')

            except Exception as e:
                messages.error(request, f"Error: {e}")
                return redirect('bulk_upload_subcountrymaster')
    else:
        form = FileUploadForm()
    
    return render(request, 'Data_import/bulk_upload.html', {'form': form})
@company_session_required
def bulk_upload_storetypemaster(request):
    company = Company.objects.get(id = request.company)
    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['file']
            try:
                # Detect file type and read data
                if file.name.endswith('.csv'):
                    df = pd.read_csv(file)
                elif file.name.endswith('.xlsx'):
                    df = pd.read_excel(file)
                else:
                    messages.error(request, "Unsupported file format. Please upload a CSV or Excel file.")
                    return redirect('itemsubcategorymaster_list')
                created_count = 0
                skipped_count = 0
                # Process each rowgit
                for _, row in df.iterrows():
                   
                    if StoreTypeMaster.objects.filter(
                        company_id=company.id,
                        name=row['name'],
                    ).exists():
                        skipped_count += 1
                        continue
                    StoreTypeMaster.objects.create(
                        company_id=company.id,
                        name=row['name'],
                        description=row.get('description', ''),
                       
                    
                    )
                    created_count += 1

                messages.success(request, "Items uploaded successfully!")
                return redirect('storetypemaster_list')

            except Exception as e:
                messages.error(request, f"Error: {e}")
                return redirect('bulk_upload_storetypemaster')
    else:
        form = FileUploadForm()
    
    return render(request, 'Data_import/bulk_upload.html', {'form': form})
@company_session_required
@distributorbranch_session_required
@customer_store_session_required
def create_branch(request):
    try:
        customer_store = int(request.customer_store_id)
        customer=Customerstore.objects.get(id=customer_store)
        records=DistributorBranch.objects.filter(company_id=request.company,customer_id=customer.customer,id=customer.branch.id)
        context={
            'records':records,'roles': 'active', 'roles_show': 'show'
        }
        return render(request,'SupplierPortal/branches_listview.html',context)
    except Exception as error:
        return render(request, '500.html', {'error': error})
    

def new_branch_create(request):
    # try:
        if request.method == "POST":
            form = BranchForm(request.POST,files = request.FILES) 
            print('form.is_valid()',form.is_valid())
            if form.is_valid():
                obj=form.save(commit=False)
                obj.save()
               
                return redirect('create_branch')
            else:
                print('=====form',form.errors)
        else:
            form = BranchForm()
        return render(request, 'SupplierPortal/branches_create_new.html', {'form': form,'branch_list':True})
    # except Exception as error:
            # return render(request,'500.html',{'error':str(error)})

@company_session_required
@customer_store_session_required
def create_storemaster(request):
    # try:

        customer_store = int(request.customer_store_id)
        customer=Customerstore.objects.get(id=customer_store)
        records=Customerstore.objects.filter(company_id=request.company,id=customer.id)
        context={
            'records':records,'roles': 'active', 'roles_show': 'show'
        }
        return render(request,'SupplierPortal/store_listview.html',context)
@company_session_required
def new_storemaster_create(request):

    records=Branch.objects.filter(company_id=request.company)
    if request.method == "POST":
        # Manually extract fields from request.POST and request.FILES
        store_name = request.POST.get('store_name')
        branch = request.POST.get('branch')
        store_manager = request.POST.get('store_manager')
        store_address = request.POST.get('store_address')
        contact_number = request.POST.get('contact_number')
        # store_image = request.FILES.get('store_image')  # Example for file upload

        # You can print to debug if needed
        print('store_name:', store_name)

        # Create object manually
        new_store = CreatestoreMaster(
            name=store_name,
            branch_id=branch,  # Assuming branch is a foreign key, use *_id
            manager_name=store_manager,
            location=store_address,
            contact_number=contact_number,
            # store_image=store_image
        )
        new_store.save()

        return redirect('create_storemaster')
    else:
        # If GET request
        return render(request, 'SupplierPortal/storemaster_new.html',{"branch_list":records,})
    # except Exception as error:
            # return render(request,'500.html',{'error':str(error)})