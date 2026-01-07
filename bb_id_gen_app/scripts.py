import string
import random
from django.db import transaction
from .models import IdGenSetUp, IdGeneration


def generate_suffix(suffix_type, suffix_length):
    if suffix_type == 'alpha_numeric':
        return ''.join(random.choices(string.ascii_letters + string.digits, k=suffix_length)).upper()
    elif suffix_type == 'alpha':
        return ''.join(random.choices(string.ascii_letters, k=suffix_length)).upper()
    elif suffix_type == 'numeric':
        return ''.join(random.choices(string.digits, k=suffix_length))
    return ''


@transaction.atomic
def generate_id(app_name_id, model_name_id):
    try:
        # Fetch the setup configuration
        
        setup = IdGenSetUp.objects.get(app_name_id=app_name_id, model_name_id=model_name_id)

        # Get or create IdGeneration entry
        id_gen, created = IdGeneration.objects.get_or_create(app_name_id=app_name_id, model_name_id=model_name_id)

        # Initialize prefix variable
        prefix = setup.prefix

        if created or not id_gen.current_id:
            # If it's a new entry or no current_id, initialize the next ID number and suffix
            next_id_number = 1
            suffix = generate_suffix(setup.suffix_type, setup.suffix_length)
        else:
            if id_gen.next_id:
                # Use the next_id for current_id
                next_id = id_gen.next_id
                # Extract the number part of the next ID
                current_number_str = next_id[len(prefix):-setup.suffix_length]
                next_id_number = int(current_number_str)
                suffix = next_id[-setup.suffix_length:]
            else:
                # Extract the number part of the current ID
                current_number_str = id_gen.current_id[len(prefix):len(prefix) + setup.id_padding]
                next_id_number = int(current_number_str) + 1
                suffix = generate_suffix(setup.suffix_type, setup.suffix_length)

        # Generate the next ID
        next_id = f"{prefix}{str(next_id_number).zfill(setup.id_padding)}{suffix}"

        # Update IdGeneration model
        id_gen.previous_id = id_gen.current_id if id_gen.current_id else ''
        id_gen.current_id = next_id
        id_gen.next_id = f"{prefix}{str(next_id_number + 1).zfill(setup.id_padding)}{generate_suffix(setup.suffix_type, setup.suffix_length)}"
        id_gen.save()

        return next_id
    except IdGenSetUp.DoesNotExist:
        print("Setup configuration not found for the given app_name and model_name.")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


def simple_unique_id_generation(pre,obj):
    # Calculating the total number of* records and incrementing by 1
    if obj:
        tot_rec_count=obj + 1
    else:
        tot_rec_count=1
     # Creating a unique ID b   ased on the total record count and the provided prefix
    if len(str(tot_rec_count)) == 1:
        id=pre+'000'+str(tot_rec_count)
    elif  len(str(tot_rec_count)) == 2:
        id=pre+'00'+str(tot_rec_count)
    else: 
        id=pre+str(tot_rec_count)
    return id