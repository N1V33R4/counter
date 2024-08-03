from django.db import models
from django.utils import timezone
from django.conf import settings


class Expense(models.Model):
    day = models.DateField(default=timezone.now)
    category = models.ForeignKey("Category", models.RESTRICT)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.ForeignKey("Currency", models.RESTRICT)
    label = models.CharField(max_length=200, blank=True)
    note = models.TextField(blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, models.CASCADE)

    def __str__(self) -> str:
        return f"{self.amount}{self.currency.symbol} {self.label} {self.day}"

    class Meta:
        ordering = ["-day", "-amount"]


class Category(models.Model):
    name = models.CharField(max_length=200)
    note = models.TextField(blank=True)

    def __str__(self) -> str:
        return self.name

    class Meta:
        verbose_name_plural = "categories"


class Currency(models.Model):
    name = models.CharField(max_length=200)
    symbol = models.CharField(max_length=1)
    country = models.CharField(max_length=100)
    amount_equal_usd = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self) -> str:
        return f"{self.name} {self.symbol}"

    class Meta:
        verbose_name_plural = "currenies"
