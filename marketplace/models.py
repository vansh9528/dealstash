from django.db import models
from django.conf import settings
from decimal import Decimal


class Company(models.Model):
    # one user -> one company
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="company"
    )
    name = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    website = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Companies"


class Product(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="products")
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to="product_images/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Order(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("shipped", "Shipped"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="orders")
    buyer_name = models.CharField(max_length=200)
    buyer_email = models.EmailField()
    quantity = models.PositiveIntegerField(default=1)

    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    commission = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # calculate totals and commission
        self.total_price = self.product.price * self.quantity
        commission_rate = getattr(settings, "COMMISSION_RATE", Decimal("0.10"))
        self.commission = self.total_price * Decimal(commission_rate)
        super().save(*args, **kwargs)

    def seller_earnings(self):
        return self.total_price - self.commission

    def __str__(self):
        return f"Order #{self.pk} - {self.product.name}"
