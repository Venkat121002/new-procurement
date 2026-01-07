from django.db import models


# Create your models here.
class AppRegistration(models.Model):
    app_name = models.CharField(max_length=50, unique=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.app_name)


class ModelRegistration(models.Model):
    app_name = models.ForeignKey(AppRegistration, on_delete=models.CASCADE, related_name='app_name_model_reg')
    model_name = models.CharField(max_length=100, )
    self_authorized = models.BooleanField(default=False)
    same_user_authorized = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.model_name)


class IdGenSetUp(models.Model):
    app_name = models.ForeignKey(AppRegistration, on_delete=models.CASCADE, related_name='app_name_registration')
    model_name = models.OneToOneField(ModelRegistration, on_delete=models.CASCADE, related_name='model_name_idgsu')
    prefix = models.CharField(max_length=10, )
    id_padding = models.PositiveIntegerField()
    SUFFIX_TYPE = (
        ('alpha_numeric', 'Alpha Numeric'),
        ('alpha', 'Alpha'),
        ('numeric', 'Numeric')
    )
    suffix_type = models.CharField(max_length=15, choices=SUFFIX_TYPE)
    suffix_length = models.PositiveIntegerField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.prefix)


class IdGeneration(models.Model):
    app_name = models.ForeignKey(AppRegistration, on_delete=models.CASCADE, related_name='app_name_ig')
    model_name = models.ForeignKey(ModelRegistration, on_delete=models.CASCADE, related_name='model_name_ig')
    next_id = models.CharField(max_length=100, )
    current_id = models.CharField(max_length=100, )
    previous_id = models.CharField(max_length=100, )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Next Id {self.next_id} | Current Id {self.current_id} | Previous Id {self.previous_id}'
