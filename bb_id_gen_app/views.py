from django.shortcuts import render,redirect
import json
from .models import *

import os

def app_and_model_registration(request):
    try:
        config_path = os.path.join(os.path.dirname(_file_), '../config/model_config.json')

        with open(config_path, 'r') as config_file:
                config = yaml.safe_load(file)['transaction_type']
                config = json.load(config_file)
                app, model_instances = save_app_and_models(config)

        return redirect('dashboard')
    except Exception as errors:
        print('app_and_model_registration',errors)

def app_and_model_registration(request):
    try:
        config_path='config/model_config.json'
        with open(config_path, 'r') as config_file:
            config = json.load(config_file)
            app, model_instances = save_app_and_models(config)
        return redirect('dashboard')
    except Exception as errors:
        print('app_and_model_registration',errors)


def save_app_and_models(data):
    """
    Save AppRegistration and ModelRegistration from a dictionary.

    :param data: Dictionary containing app and model data
    :type data: dict
    :return: Tuple of (app_instance, list of model_instances)
    """
    # Extract and save AppRegistration
    app_data = data.get('app_registration', {})
    app_name = app_data.get('app_name')
    
    if not app_name:
        raise ValueError("App name is required in app_registration data")
    
    app, created = AppRegistration.objects.get_or_create(app_name=app_name)
    
    # Extract and save ModelRegistrations
    model_data_list = data.get('model_registrations', [])
    model_instances = []
    
    for model_data in model_data_list:
        model_name = model_data.get('model_name')
        self_authorized = model_data.get('self_authorized', False)
        same_user_authorized = model_data.get('same_user_authorized', False)

        if model_name:
            if not ModelRegistration.objects.filter(app_name=app,model_name=model_name).exists():
                model_instance = ModelRegistration(
                    app_name=app,
                    model_name=model_name,
                    self_authorized=self_authorized,
                    same_user_authorized=same_user_authorized
                )
                model_instance.save()
                model_instances.append(model_instance)
        else:
            raise ValueError("Model name is required in model_registrations data")

    return app, model_instances
