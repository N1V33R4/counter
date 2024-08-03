from django.contrib import admin
from .models import Expense, Category, Currency

# Register your models here.
@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ['day', 'category', 'amount', 'currency', 'label']
    list_filter = ['day', 'category']

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    ...
@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    ...