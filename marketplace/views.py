import logging

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.conf import settings
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives

from .models import Product, Company, Order
from .forms import ProductForm, SellerSignUpForm, OrderForm

logger = logging.getLogger(__name__)


def product_list(request):
    """Homepage: list all products (public)."""
    products = Product.objects.all().order_by("-created_at")
    return render(request, "marketplace/product_list.html", {"products": products})


def product_detail(request, pk):
    """Show product details (public)."""
    product = get_object_or_404(Product, pk=pk)
    return render(request, "marketplace/product_detail.html", {"product": product})


@login_required
def product_create(request):
    """
    Create a new product. Only allowed for logged-in sellers (users with a linked Company).
    Product.company is set automatically from request.user.company.
    """
    company = getattr(request.user, "company", None)
    if not company:
        messages.error(request, "You must complete seller signup before adding products.")
        return redirect("seller_signup")

    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.company = company
            product.save()
            messages.success(request, "✅ Product added successfully.")
            return redirect("seller_dashboard")
    else:
        form = ProductForm()

    return render(request, "marketplace/product_form.html", {"form": form})


@login_required
def product_edit(request, pk):
    """Edit a product — only the owning seller may edit."""
    product = get_object_or_404(Product, pk=pk)

    # Permission check: logged-in user must own the product's company
    if not hasattr(request.user, "company") or request.user.company != product.company:
        raise PermissionDenied()

    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ Product updated.")
            return redirect("seller_dashboard")
    else:
        form = ProductForm(instance=product)

    return render(request, "marketplace/product_form.html", {"form": form, "edit": True})


@login_required
def product_delete(request, pk):
    """
    Delete a product — owner only.
    GET shows confirmation page, POST performs delete.
    """
    product = get_object_or_404(Product, pk=pk)

    if not hasattr(request.user, "company") or request.user.company != product.company:
        raise PermissionDenied()

    if request.method == "POST":
        name = product.name
        product.delete()
        messages.success(request, f"🗑️ Product '{name}' deleted.")
        return redirect("seller_dashboard")

    return render(request, "marketplace/product_confirm_delete.html", {"product": product})


def seller_signup(request):
    """
    Seller signup view: creates a User + Company (handled by SellerSignUpForm),
    logs the user in, and redirects to seller_dashboard.
    """
    if request.method == "POST":
        form = SellerSignUpForm(request.POST)
        if form.is_valid():
            user = form.save()  # form should create User and Company and link them
            login(request, user)
            messages.success(request, "🎉 Seller account created. Welcome!")
            return redirect("seller_dashboard")
    else:
        form = SellerSignUpForm()

    return render(request, "marketplace/seller_signup.html", {"form": form})


@login_required
def seller_dashboard(request):
    """Seller dashboard: show products for the logged-in seller's company."""
    company = getattr(request.user, "company", None)
    if not company:
        messages.info(request, "Please complete seller signup to manage your products.")
        return redirect("seller_signup")

    products = company.products.all().order_by("-created_at")
    return render(request, "marketplace/seller_dashboard.html", {"products": products})


@login_required
def seller_orders(request):
    """List orders for products belonging to the logged-in seller's company."""
    company = getattr(request.user, "company", None)
    if not company:
        messages.info(request, "Please complete seller signup to view your orders.")
        return redirect("seller_signup")

    orders = Order.objects.filter(product__company=company).select_related("product").order_by("-created_at")
    return render(request, "marketplace/seller_orders.html", {"orders": orders})


def _send_order_emails(order):
    """
    Helper to send seller & admin emails for a newly created order.
    Uses HTML + text templates and EmailMultiAlternatives.
    """
    product = order.product
    company = product.company
    admin_emails = [a[1] for a in getattr(settings, "ADMINS", []) if a[1]]

    # Context for templates
    context = {"company": company, "product": product, "order": order}

    # SELLER: send multipart email if company has an email
    if company and company.email:
        subject_seller = f"New order for your product: {product.name}"
        text_seller = render_to_string("emails/order_seller.txt", context)
        html_seller = render_to_string("emails/order_seller.html", context)

        msg = EmailMultiAlternatives(subject_seller, text_seller, settings.DEFAULT_FROM_EMAIL, [company.email])
        msg.attach_alternative(html_seller, "text/html")
        msg.send(fail_silently=False)

    # ADMIN: notify admins
    if admin_emails:
        admin_context = {**context, "admin_url": f"/admin/marketplace/order/{order.pk}/change/"}
        subject_admin = f"New order placed — {product.name} (Order #{order.pk})"
        text_admin = render_to_string("emails/order_admin.txt", admin_context)
        html_admin = render_to_string("emails/order_admin.html", admin_context)

        msg_admin = EmailMultiAlternatives(subject_admin, text_admin, settings.DEFAULT_FROM_EMAIL, admin_emails)
        msg_admin.attach_alternative(html_admin, "text/html")
        msg_admin.send(fail_silently=False)


def order_create(request, pk):
    """
    Create an Order for the given product. Public (no login needed).
    On success: save order, send emails (seller + admin), show success message and redirect to detail.
    """
    product = get_object_or_404(Product, pk=pk)

    if request.method == "POST":
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.product = product
            order.save()

            # Try to send notification emails, but if they fail, log and show clear message
            try:
                _send_order_emails(order)
            except Exception as e:
                logger.exception("Failed to send order emails")
                messages.warning(request, f"Order created but sending notification failed: {e}")
            else:
                messages.success(request, f"✅ Order placed. We will contact you at {order.buyer_email}")

            return redirect("product_detail", pk=product.pk)
    else:
        form = OrderForm(initial={"quantity": 1})

    return render(request, "marketplace/order_form.html", {"form": form, "product": product})


# --- Staff-only delete pages (for superuser/staff to remove any product/company) ---


@staff_member_required
def product_delete_confirm_staff(request, pk):
    """Staff-only confirmation & deletion of any product (admin-like action)."""
    product = get_object_or_404(Product, pk=pk)

    if request.method == "POST":
        name = product.name
        product.delete()
        messages.success(request, f"Product '{name}' deleted by staff.")
        return redirect("product_list")

    return render(request, "marketplace/product_confirm_delete.html", {"product": product})


@staff_member_required
def company_delete_confirm_staff(request, pk):
    """Staff-only confirmation & deletion of a company (cascades products)."""
    company = get_object_or_404(Company, pk=pk)

    if request.method == "POST":
        company_name = company.name
        company.delete()
        messages.success(request, f"Company '{company_name}' and its products were deleted.")
        return redirect("product_list")

    return render(request, "marketplace/company_confirm_delete.html", {"company": company})
