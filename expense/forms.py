import calendar
from django import forms
from django.db import models
from django.db.models import Sum, F, CharField
from django.db.models.functions import Concat
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from datetime import date, timedelta
from .models import Expense, Category


class ExpenseForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["currency"].empty_label = None
        self.fields["category"].empty_label = None

    class Meta:
        model = Expense
        fields = ["day", "label", "amount", "currency", "category", "note"]
        widgets = {
            "day": forms.DateInput(attrs={"type": "date"}),
            "label": forms.TextInput(
                attrs={"placeholder": "Label (optional)", "class": "align-s-e"}
            ),
            "amount": forms.NumberInput(
                attrs={"placeholder": "Amount", "required": False}
            ),
            "currency": forms.Select(attrs={"placeholder": "Currency"}),
            "note": forms.Textarea(
                attrs={"placeholder": "Write a memorable note... (optional)", "rows": 3}
            ),
        }


class ExpenseFilter(forms.Form):
    from_day = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"}), label="From", required=False
    )
    to_day = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"}), label="To", required=False
    )
    category = forms.ModelChoiceField(
        Category.objects.all(), empty_label="All", required=False
    )
    page = forms.IntegerField(min_value=1, initial=1, required=False)
    per_page = forms.IntegerField(min_value=10, initial=10, required=False)

    def is_empty(self):
        for _, value in self.data.items():
            if value:
                return False
        return True

    def filter_query(self, query):
        if self.is_valid():
            category = self.cleaned_data["category"]
            if category:
                query = query.filter(category=category)

            from_day = self.cleaned_data["from_day"]
            to_day = self.cleaned_data["to_day"]
            if from_day:
                query = query.filter(day__gte=from_day)
            if to_day:
                query = query.filter(day__lte=to_day)

            page = self.cleaned_data["page"] or 1
            per_page = self.cleaned_data["per_page"] or 10
            paginator = Paginator(query, per_page)
            try:
                query = paginator.page(page)
            except EmptyPage:
                query = paginator.page(paginator.num_pages)
            except PageNotAnInteger:
                query = paginator.page(1)

        return query
    
    def querystring(self):
        copy = self.data.copy()
        copy.pop('page', True)
        return copy.urlencode()



class Group(models.TextChoices):
    DAY = "D", "Day"
    MONTH = "M", "Month"
    YEAR = "Y", "Year"


class ExpenseSummary(forms.Form):
    from_day = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"}), label="From"
    )
    to_day = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}), label="To")
    category = forms.ModelChoiceField(
        Category.objects.all(), empty_label="All", required=False
    )
    group = forms.ChoiceField(choices=Group.choices, label="Group by")

    def clean(self):
        cd = super().clean()
        if self.is_valid():
            if cd["from_day"] > cd["to_day"]:
                self.add_error("to_day", "This date must come AFTER from.")
        return cd
    
    def filter_group(self, query):
        if self.is_valid():
            category = self.cleaned_data["category"]
            if category:
                query = query.filter(category=category)

            from_day = self.cleaned_data["from_day"]
            to_day = self.cleaned_data["to_day"]
            group = self.cleaned_data["group"]
            match group:
                case Group.DAY:
                    group_filter = ["day"]
                case Group.MONTH:
                    group_filter = ["day__year", "day__month"]
                case Group.YEAR:
                    group_filter = ["day__year"]

            query = (
                query.filter(day__gte=from_day, day__lte=to_day)
                .values(*group_filter, symbol=F("currency__symbol"))
                .annotate(total_amount=Sum("amount"))
                .order_by(*group_filter, "-total_amount")
            )
            # add a concatenated field to group the results by
            if group == Group.MONTH:
                query = query.annotate(
                    year_month=Concat(
                        "day__year", "day__month", output_field=CharField()
                    )
                )
            return query

    def filter_sum(self, query):
        if self.is_valid():
            category = self.cleaned_data["category"]
            if category:
                query = query.filter(category=category)

            from_day = self.cleaned_data["from_day"]
            to_day = self.cleaned_data["to_day"]

            return (
                query
                .filter(day__gte=from_day, day__lte=to_day)
                .values('currency__amount_equal_usd', symbol=F("currency__symbol"))
                .annotate(total_amount=Sum("amount"))
                .order_by("-total_amount")
            )

    def prev_month_qs(self):
        if self.is_valid():
            from_day: date = self.cleaned_data['from_day']
            prev_month_last = from_day.replace(day=1) - timedelta(days=1)
            prev_month_first = prev_month_last.replace(day=1)
            return f'?from_day={prev_month_first.strftime('%Y-%m-%d')}&to_day={prev_month_last.strftime('%Y-%m-%d')}&group=D'
        
    def next_month_qs(self):
        if self.is_valid():
            from_day: date = self.cleaned_data['from_day']
            next_month_first = (from_day.replace(day=1) + timedelta(days=32)).replace(day=1)
            last = calendar.monthrange(next_month_first.year, next_month_first.month)[1]
            next_month_last = next_month_first.replace(day=last)
            return f'?from_day={next_month_first.strftime('%Y-%m-%d')}&to_day={next_month_last.strftime('%Y-%m-%d')}&group=D'
