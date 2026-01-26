from django.db import models
from django.contrib.auth.models import User # ユーザー認証を使う場合
from django.contrib.auth import get_user_model
from django.db.models.fields.related import OneToOneField

# Create your models here.
class mst_shop(models.Model):
    shop_id = models.CharField('Shop_ID',max_length=6,primary_key=True)
    shop_name = models.CharField('Shop_Name',max_length=10)
    shop_addres = models.CharField('Shop_Address',max_length=100)
    shop_tel = models.CharField('Shop_Tel',max_length=11)

class mst_employee(models.Model):
    employee = models.CharField('Employee',max_length=6,primary_key=True)
    user = OneToOneField(User, on_delete=models.CASCADE)    
    emp_name = models.CharField('Emp_Name',max_length=30)
    emp_age = models.IntegerField('Emp_Age')
    emp_email = models.CharField('Emp_Email',max_length=50,unique=True)
    affiliated_store = models.ForeignKey(mst_shop,on_delete=models.PROTECT)
    emp_status = models.CharField("Emp_Status",max_length=1)
    hire_date = models.DateField("Hire_Date")
    def __str__(self):
        return self.emp_name
