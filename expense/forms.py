from django import forms
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
            "amount": forms.NumberInput(attrs={"placeholder": "Amount", 'required': False}),
            "currency": forms.Select(attrs={"placeholder": "Currency"}),
            "note": forms.Textarea(
                attrs={"placeholder": "Write a memorable note... (optional)", "rows": 3}
            ),
        }


class ExpenseFilter(forms.Form):
    from_day = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}), label='From', required=False)
    to_day = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}), label="To", required=False)
    category = forms.ModelChoiceField(Category.objects.all(), empty_label="All", required=False)
    
    def is_empty(self):
        for _, value in self.data.items():
            if value:
                return False
        return True
    
    def filter_query(self, query):
        if self.is_valid():
            category = self.cleaned_data['category']
            if category:
                query = query.filter(category=category)

            from_day = self.cleaned_data['from_day']
            to_day = self.cleaned_data['to_day']
            if to_day is None or from_day > to_day: 
                to_day = from_day
            if from_day:
                query = query.filter(day__gte=from_day, day__lte=to_day)

        return query
