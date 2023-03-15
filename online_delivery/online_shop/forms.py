from django import forms
from django.contrib.auth.forms import AuthenticationForm


class CustomAuthForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'autofocus': True}))


# class OrderForm(forms.ModelForm):
#     class Meta:
#         model = Order
#         fields = ['shipping_address', 'billing_address', 'payment_method']
#
#         widgets = {
#             'shipping_address': forms.TextInput(attrs={'class': 'form-control'}),
#             'billing_address': forms.TextInput(attrs={'class': 'form-control'}),
#             'payment_method': forms.Select(attrs={'class': 'form-control'}),
#         }
#
#         labels = {
#             'shipping_address': 'Shipping Address',
#             'billing_address': 'Billing Address',
#             'payment_method': 'Payment Method',
#         }
#
#     # Add validation for the billing_address field to make sure it's not empty
#     def clean_billing_address(self):
#         billing_address = self.cleaned_data['billing_address']
#         if not billing_address:
#             raise forms.ValidationError("Billing Address is required.")
#         return billing_address
