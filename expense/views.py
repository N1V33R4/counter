from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, F
from django.utils import timezone
from datetime import date
import calendar
from .models import Expense
from .forms import ExpenseFilter, ExpenseForm, ExpenseSummary


@login_required
def expense_list(request):
    if request.method == "POST":
        form = ExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save(False)
            expense.user = request.user
            expense.save()
            request.session["prev_day"] = expense.day.strftime("%Y-%m-%d")
            request.session["prev_currency"] = expense.currency.id
            request.session["prev_category"] = expense.category.id
            messages.success(request, "You spent it!")
            return redirect(request.META.get("HTTP_REFERER", "expense_list"))
    else:
        form = ExpenseForm(
            initial={
                "day": request.session.pop("prev_day", date.today()),
                "currency": request.session.pop("prev_currency", 0),
                "category": request.session.pop("prev_category", 0),
            }
        )
    filters = ExpenseFilter(request.GET)
    expenses = filters.filter_query(Expense.objects.filter(user=request.user))
    today = timezone.now().date()
    last = calendar.monthrange(today.year, today.month)[1]
    data = {
        "expenses": expenses,
        "form": form,
        "filters": filters,
        "today_total": (
            Expense.objects.values(symbol=F("currency__symbol"))
            .filter(day=today)
            .annotate(total_amount=Sum("amount"))
            .order_by("-total_amount")
        ),
        'month_start': today.replace(day=1),
        'month_end': today.replace(day=last),
        'year_start': today.replace(day=1, month=1),
        'year_end': today.replace(day=31, month=12),
    }
    return render(request, "expense/list.html", data)


@login_required
def expense_update(request, expense_id):
    expense = get_object_or_404(Expense, id=expense_id)
    if request.user != expense.user:
        return HttpResponseForbidden()
    form = ExpenseForm(request.POST or None, instance=expense)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "You updated an expense!")
        return redirect(request.session.get("return_url", "expense_list"))
    else:
        return_url = request.META.get("HTTP_REFERER", None)
        request.session["return_url"] = return_url
        return render(
            request,
            "expense/update.html",
            {"form": form, "id": expense_id, "return_url": return_url},
        )


@login_required
@require_POST
def expense_delete(request, expense_id):
    expense = get_object_or_404(Expense, id=expense_id)
    if request.user != expense.user:
        return HttpResponseForbidden()
    expense.delete()
    messages.success(request, "You erased an expense!")
    return redirect(request.META.get("HTTP_REFERER", "expense_list"))


@login_required
@require_POST
def expense_clone(request, expense_id):
    expense = get_object_or_404(Expense, id=expense_id)
    if request.user != expense.user:
        return HttpResponseForbidden()
    expense.id = None
    expense.day = date.today()
    expense.save()
    messages.success(request, "You spent it again!")
    return redirect(request.META.get("HTTP_REFERER", "expense_list"))


@login_required
def summary(request):
    filters = ExpenseSummary(request.GET)
    user_expenses = Expense.objects.filter(user=request.user)
    total_sum = filters.filter_sum(user_expenses)
    total_usd = 0
    if total_sum:
        for i in total_sum:
            total_usd += i['total_amount'] / i['currency__amount_equal_usd'] 
    data = {
        "filters": filters,
        "total_sum": total_sum,
        "total_with_items": filters.filter_group(user_expenses),
        "total_usd": total_usd,
    }
    return render(request, "expense/summary.html", data)


def home(request):
    return render(request, "expense/home.html", {})
