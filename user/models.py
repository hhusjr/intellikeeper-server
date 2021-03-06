from django.contrib.auth.models import AbstractBaseUser
from django.contrib.auth.models import BaseUserManager
from django.core.validators import RegexValidator
from django.db import models

phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$',
                             message="Mobile number must be entered in the format:"
                                     " '+999999999'. Up to 15 digits allowed.")


class User(AbstractBaseUser):
    mobile = models.CharField(validators=[phone_regex], max_length=15, unique=True, blank=True, null=True)
    mobile_verified = models.BooleanField(default=False)

    objects = BaseUserManager()

    USERNAME_FIELD = 'mobile'
