from django.db import models
from django.template.defaultfilters import slugify
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
# from batches.solutions import updateScoreSave

class User(models.Model):
    email = models.EmailField(unique=True)
    created_on = models.DateTimeField(auto_now_add=True)
