import datetime

from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView
from django.db import models
from django.utils.timezone import now
from django.views.generic import CreateView

from .forms import CustomAuthForm


class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=200)
    email = models.EmailField()

    def __str__(self):
        return self.name


class Cart(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    date_added = models.DateTimeField(default=datetime.datetime.now, blank=True)


class Product(models.Model):
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=7, decimal_places=2)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(null=True, blank=True)

    def __str__(self):
        return self.name


class Feature(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    feature = models.CharField(max_length=1000, null=True, blank=True)

    def __str__(self):
        return str(self.product) + " Feature: " + self.feature


class Review(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    content = models.TextField()
    datetime = models.DateTimeField(default=now)

    def __str__(self):
        return str(self.customer) + " Review: " + self.content


class Order(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, verbose_name='Customer')
    date_ordered = models.DateTimeField(auto_now_add=True, verbose_name='Date Ordered')
    complete = models.BooleanField(default=False, verbose_name='Order Complete')
    transaction_id = models.CharField(max_length=100, verbose_name='Transaction ID')
    shipping_address = models.CharField(max_length=200, default=None, verbose_name='Shipping Address')
    billing_address = models.CharField(max_length=200, default='', verbose_name='Billing Address')
    payment_method = models.CharField(max_length=100, default=None, verbose_name='Payment Method')

    def __str__(self):
        return str(self.customer), self.transaction_id

    @property
    def get_cart_total(self):
        orderitems = self.orderitem_set.all()
        total = sum([item.get_total for item in orderitems])
        return total

    @property
    def get_cart_items(self):
        """
        Return the total number of items in the order
        """
        order_items = self.orderitem_set.all()
        total_items = sum(item.quantity for item in order_items)
        return total_items, sum(item.quantity for item in self.orderitem_set.all())


# class OrderCreateView(CreateView):
#     model = Order
#     form_class = OrderForm
#     template_name = 'order_form.html'
#
#     def form_valid(self, form):
#         # Add custom logic here if needed
#         return super().form_valid(form)
#
#     def form_invalid(self, form):
#         # Add custom logic here if needed
#         return super().form_invalid(form)


class OrderItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True)
    quantity = models.IntegerField(default=0)
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.order)

    @property
    def get_total(self):
        total = self.product.price * self.quantity
        return total


class CheckoutDetail(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True)
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True)
    phone_number = models.CharField(max_length=10, blank=True, null=True)
    total_amount = models.CharField(max_length=10, blank=True, null=True)
    address = models.CharField(max_length=300)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zipcode = models.CharField(max_length=100)
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.address


class Contact(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone_number = models.CharField(max_length=10, null=True, blank=True)
    message = models.TextField()

    def __str__(self):
        return self.name


class CustomLoginView(LoginView):
    authentication_form = CustomAuthForm
    template_name = 'login.html'


class CartItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=0)
    date_added = models.DateTimeField(auto_now_add=True)
