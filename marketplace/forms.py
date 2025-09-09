from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Product, Company, Order

# Product form (you already had this)
class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'price', 'description', 'image']  # removed 'company'



# Seller signup form — creates a User and a Company
class SellerSignUpForm(UserCreationForm):
    # extra fields for the company
    email = forms.EmailField(required=True)
    company_name = forms.CharField(max_length=200, label="Company name")
    website = forms.URLField(required=False)

    class Meta:
        model = User
        # username, password1, password2 come from UserCreationForm
        fields = ("username", "email", "password1", "password2")

    def save(self, commit=True):
        # create the user first
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
            # then create the company linked to this user
            Company.objects.create(
                user=user,
                name=self.cleaned_data["company_name"],
                email=self.cleaned_data["email"],
                website=self.cleaned_data.get("website") or ""
            )
        return user
    


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['buyer_name', 'buyer_email', 'quantity']
        widgets = {
            'buyer_name': forms.TextInput(attrs={'class':'form-control'}),
            'buyer_email': forms.EmailInput(attrs={'class':'form-control'}),
            'quantity': forms.NumberInput(attrs={'class':'form-control', 'min':1}),
        }

