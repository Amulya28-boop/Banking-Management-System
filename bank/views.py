import json
from datetime import datetime
from decimal import Decimal

from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

from django.http import HttpResponse
from reportlab.pdfgen import canvas

from .models import Customer, Transaction


# ================= AUTH =================

def user_login(request):
    error = None

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            print("LOGIN SUCCESS")
            login(request, user)
            return redirect("dashboard")
        else:
            print("LOGIN FAILED")
            error = "Invalid username or password"

    return render(request, "login.html", {"error": error})

# ================= HOMEPAGE =================

def homepage(request):
    return render(request, "homepage.html")


def user_logout(request):
    logout(request)
    return redirect("homepage")


def user_signup(request):
    error = None

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        if password != confirm_password:
            error = "Passwords do not match"

        elif User.objects.filter(username=username).exists():
            error = "Username already exists"

        else:
            User.objects.create_user(username=username, password=password)
            return redirect("login")

    return render(request, "signup.html", {"error": error})

from django.shortcuts import render

def homepage(request):
    return render(request, "homepage.html")

# ================= DASHBOARD =================

@login_required
def dashboard(request):

    total_customers = Customer.objects.count()

    total_balance = Customer.objects.aggregate(total=Sum("balance"))["total"] or 0

    total_deposit = Transaction.objects.filter(
        transaction_type="DEPOSIT"
    ).aggregate(total=Sum("amount"))["total"] or 0

    total_withdraw = Transaction.objects.filter(
        transaction_type="WITHDRAW"
    ).aggregate(total=Sum("amount"))["total"] or 0

    customers = Customer.objects.all()

    year = datetime.now().year

    months = []
    deposit_data = []
    withdraw_data = []

    for m in range(1, 13):
        months.append(m)

        dep = Transaction.objects.filter(
            transaction_type="DEPOSIT",
            date__year=year,
            date__month=m
        ).aggregate(total=Sum("amount"))["total"] or 0

        wit = Transaction.objects.filter(
            transaction_type="WITHDRAW",
            date__year=year,
            date__month=m
        ).aggregate(total=Sum("amount"))["total"] or 0

        deposit_data.append(float(dep))
        withdraw_data.append(float(wit))

    return render(request, "dashboard.html", {
        "total_customers": total_customers,
        "total_balance": total_balance,
        "total_deposit": total_deposit,
        "total_withdraw": total_withdraw,

        "customers": customers,

        "months": json.dumps(months),
        "deposit_data": json.dumps(deposit_data),
        "withdraw_data": json.dumps(withdraw_data),
    })


# ================= CUSTOMER =================

@login_required
def customer_list(request):
    customers = Customer.objects.all()
    return render(request, "customer_list.html", {"customers": customers})


@login_required
def add_customer(request):
    if request.method == "POST":
        Customer.objects.create(
            name=request.POST["name"],
            email=request.POST["email"],
            phone=request.POST["phone"],
            account_number=request.POST["account_number"],
            balance=Decimal(request.POST.get("balance", 0))
        )
        return redirect("customer_list")

    return render(request, "add_customer.html")


@login_required
def edit_customer(request, customer_id):
    customer = get_object_or_404(Customer, id=customer_id)

    if request.method == "POST":
        customer.name = request.POST["name"]
        customer.email = request.POST["email"]
        customer.phone = request.POST["phone"]
        customer.account_number = request.POST["account_number"]
        customer.save()
        return redirect("customer_list")

    return render(request, "edit_customer.html", {"customer": customer})


@login_required
def delete_customer(request, customer_id):
    customer = get_object_or_404(Customer, id=customer_id)
    customer.delete()
    return redirect("customer_list")


# ================= TRANSACTIONS =================

@login_required
def deposit(request, customer_id):
    customer = get_object_or_404(Customer, id=customer_id)

    if request.method == "POST":
        amount = Decimal(request.POST["amount"])

        if amount > 0:
            customer.balance += amount
            customer.save()

            Transaction.objects.create(
                customer=customer,
                transaction_type="DEPOSIT",
                amount=amount
            )

        return redirect("customer_list")

    return render(request, "deposit.html", {"customer": customer})


@login_required
def withdraw(request, customer_id):
    customer = get_object_or_404(Customer, id=customer_id)

    if request.method == "POST":
        amount = Decimal(request.POST["amount"])

        if amount <= customer.balance:
            customer.balance -= amount
            customer.save()

            Transaction.objects.create(
                customer=customer,
                transaction_type="WITHDRAW",
                amount=amount
            )

        return redirect("customer_list")

    return render(request, "withdraw.html", {"customer": customer})


@login_required
def transfer(request, customer_id):
    sender = get_object_or_404(Customer, id=customer_id)

    if request.method == "POST":
        receiver_acc = request.POST["receiver_account"]
        amount = Decimal(request.POST["amount"])

        receiver = Customer.objects.filter(account_number=receiver_acc).first()

        if receiver and amount > 0 and amount <= sender.balance:
            sender.balance -= amount
            receiver.balance += amount

            sender.save()
            receiver.save()

            Transaction.objects.create(
                customer=sender,
                transaction_type="TRANSFER_OUT",
                amount=amount
            )

            Transaction.objects.create(
                customer=receiver,
                transaction_type="TRANSFER_IN",
                amount=amount
            )

        return redirect("customer_list")

    return render(request, "transfer.html", {"sender": sender})


# ================= TRANSACTION HISTORY =================

@login_required
def transaction_history(request, customer_id):
    customer = get_object_or_404(Customer, id=customer_id)

    transactions = Transaction.objects.filter(customer=customer).order_by("-date")

    return render(request, "transaction_history.html", {
        "customer": customer,
        "transactions": transactions
    })


# ================= PDF DOWNLOAD =================

@login_required
def download_statement(request, customer_id):
    customer = get_object_or_404(Customer, id=customer_id)

    transactions = Transaction.objects.filter(customer=customer).order_by("-date")

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{customer.name}_statement.pdf"'

    p = canvas.Canvas(response)

    p.setFont("Helvetica-Bold", 14)
    p.drawString(200, 800, "BANK STATEMENT")

    p.setFont("Helvetica", 11)
    p.drawString(50, 770, f"Customer: {customer.name}")
    p.drawString(50, 750, f"Account: {customer.account_number}")
    p.drawString(50, 730, f"Balance: {customer.balance}")

    y = 700
    for t in transactions:
        p.drawString(50, y, f"{t.date} | {t.transaction_type} | {t.amount}")
        y -= 20

        if y < 50:
            p.showPage()
            y = 800

    p.save()
    return response


# ================= MONTHLY TRANSACTIONS PAGE =================

@login_required
def monthly_transactions(request):

    year = datetime.now().year

    months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

    deposit_data = [1200,1500,1000,1800,2000,1600,1400,1700,2100,1900,2200,2500]
    withdraw_data = [800,900,700,1000,1100,950,1000,1200,1300,1250,1400,1500]

    total_deposit = sum(deposit_data)
    total_withdraw = sum(withdraw_data)

    return render(request, "monthly_transactions.html", {
        "months": json.dumps(months),
        "deposit_data": json.dumps(deposit_data),
        "withdraw_data": json.dumps(withdraw_data),
        "total_deposit": total_deposit,
        "total_withdraw": total_withdraw,
        "year": year,
    })


@login_required
def customer_profile(request, customer_id):

    customer = get_object_or_404(Customer, id=customer_id)

    transactions = Transaction.objects.filter(customer=customer).order_by("-date")

    return render(request, "customer_profile.html", {
        "customer": customer,
        "transactions": transactions,
    })

# ================= ABOUT =================

@login_required
def about(request):
    return render(request, "about.html")