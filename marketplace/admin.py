from django.contrib import admin
from django.utils.html import format_html
from django.templatetags.static import static

from .models import Company, Product, Order


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "website")
    search_fields = ("name", "email")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("image_tag", "name", "company", "price", "created_at")
    list_filter = ("company",)
    search_fields = ("name", "description", "company__name")
    readonly_fields = ("image_preview",)

    def image_tag(self, obj):
        """Small thumbnail for list display."""
        if obj and obj.image:
            return format_html(
                '<img src="{}" style="width:60px;height:60px;object-fit:cover;border-radius:6px;" />',
                obj.image.url
            )
        # fallback to a placeholder in your static files (or an external placeholder)
        placeholder = static("marketplace/img/placeholder.png")
        return format_html(
            '<img src="{}" style="width:60px;height:60px;object-fit:cover;border-radius:6px;opacity:0.6" />',
            placeholder
        )
    image_tag.short_description = "Image"
    image_tag.allow_tags = True

    def image_preview(self, obj):
        """Larger preview in the change form."""
        if obj and obj.image:
            return format_html(
                '<img src="{}" style="max-width:300px;display:block;margin:6px 0;border-radius:6px;" />',
                obj.image.url
            )
        placeholder = static("marketplace/img/placeholder.png")
        return format_html(
            '<img src="{}" style="max-width:300px;display:block;margin:6px 0;border-radius:6px;opacity:0.6" />',
            placeholder
        )
    image_preview.short_description = "Image preview"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "product", "buyer_name", "buyer_email", "quantity", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("buyer_name", "buyer_email", "product__name")
    readonly_fields = ("created_at",)
