from django.urls import path,include
from .views import *

urlpatterns = [
    path('app_and_models_reg/', app_and_model_registration, name='app_and_models_reg'),

]