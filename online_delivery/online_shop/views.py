from django.contrib import messages
from django.core.mail import send_mail
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models.signals import post_save
from django.views.generic import CreateView
from django.http import JsonResponse
from django.dispatch import receiver
from django.urls import reverse
# from .forms import OrderForm
from .models import *

import json


@receiver(post_save, sender=User)
def create_customer(sender, instance, created, **kwargs):
    if created:
        Customer.objects.create(user=instance)


def index(request):
    order = None
    name = request.user.username  # retrieve the current user's username
    cart_items = 0  # set default value for cart_items
    if request.user.is_authenticated:
        user = User.objects.get(username=name)
        customer = None
        if request.user.is_authenticated:
            customer, created = Customer.objects.get_or_create(
                user=request.user)  # get the customer associated with the user
            order, created = Order.objects.get_or_create(
                customer=customer,
                complete=False,
                defaults={
                    'billing_address': '',
                    'shipping_address': '',
                    'payment_method': '',
                }
            )

        # calculate the number of cart items
        cart_items = sum(item.quantity for item in order.orderitem_set.all())

    products = Product.objects.all()

    context = {
        'products': products,
        'cart_items': cart_items,
        'order': order,
    }

    return render(request, "online_shop/index.html", context)


def place_order(request):
    order = None
    if request.user.is_authenticated:
        user = request.user
        customer, created = Customer.objects.get_or_create(user=user)
        order, created = Order.objects.get_or_create(
            customer=customer,
            complete=False,
            defaults={'complete': False}
        )

        if request.method == 'POST':
            form = OrderForm(request.POST, instance=order)
            if form.is_valid():
                form.save()
                return redirect('online_shop:index')
        else:
            form = OrderForm(instance=order)

        context = {
            'form': form,
            'order': order,
        }
        return render(request, 'online_shop/place_order.html', context)
    else:
        return redirect('login')


def search(request):
    queryset = Product.objects.all()
    query = request.GET.get('q')
    if query:
        queryset = queryset.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query)
        ).distinct()

    data = cartData(request)
    cart_items = data['cart_items']

    context = {
        'queryset': queryset,
        'cart_items': cart_items,
    }

    return render(request, "online_shop/search.html", context)


def product_view(request, id):
    product = Product.objects.filter(id=id).first()
    if not product:
        return redirect('product_not_found', id=id)
    feature = Feature.objects.filter(product=product)
    reviews = Review.objects.filter(product=product)

    data = cartData(request)
    items = data['items']
    order = data['order']
    cartItems = data['cartItems']

    if request.method == "POST":
        customer = request.user.customer
        content = request.POST['content']
        review = Review(customer=customer, content=content, product=product)
        review.save()
        return redirect('product_view', id=product.id)

    return render(request, "online_shop/product_view.html", {
        'product': product,
        'cartItems': cartItems,
        'feature': feature,
        'reviews': reviews,
        'product_id': product.id if product else None,  # add this line to pass product ID to template
    })


def product_not_found(request, id):
    return render(request, "online_shop/product_not_found.html", {'id': id})


def cart(request, cart_items=None):
    data = cartData(request)
    items = data.get('items', [])
    order = data.get('order')
    cart_items = data.get('cartItems')

    if not items:
        items = []

    if not order:
        order = {}

    try:
        cart = json.loads(request.COOKIES['cart'])
    except:
        cart = {}

    for i in cart:
        try:
            cart_items += cart[i]["quantity"]

            product = Product.objects.get(id=i)
            total = (product.price * cart[i]["quantity"])

            order["get_cart_total"] += total
            order["get_cart_items"] += cart[i]["quantity"]

            item = {
                'product': {
                    'id': product.id,
                    'name': product.name,
                    'price': product.price,
                    'image': product.image,
                },
                'quantity': cart[i]["quantity"],
                'get_total': total
            }
            items.append(item)
        except:
            pass

    return render(request, "online_shop/cart.html", {'items': items, 'order': order, 'cart_items': cart_items})


def update_item(request):
    data = None
    if 'cart' in request.COOKIES:
        cart = request.COOKIES['cart']
        data = cartData(request)
    if request.body:
        data = json.loads(request.body)
    else:
        # handle case where request body is empty
        pass

    # Check for missing or incorrect data
    if not data or not data.get('productId') or not data.get('action'):
        return JsonResponse({'error': 'Missing or invalid data'})

    product = get_object_or_404(Product, id=data['productId'])
    action = data['action']
    customer = request.user.customer
    order, created = Order.objects.get_or_create(customer=customer, complete=False)
    order_item, created = OrderItem.objects.get_or_create(order=order, product=product)

    if action == 'add':
        order_item.quantity += 1
    elif action == 'remove':
        order_item.quantity -= 1

    order_item.save()

    if order_item.quantity <= 0:
        order_item.delete()

    cart_items = order.get_cart_items()
    return JsonResponse({'cart_items': cart_items})



# function to view user profile page, if user is logged in
@login_required
def my_account(request):
    # get logged in user
    user_id = request.user.id

    # get users previous purchased products
    previous_orders = OrderItem.objects.filter(shopper=user_id)

    # get order numbers of the purchased products
    order_numbers = sorted(list(set(order.order_id for order in previous_orders)), reverse=True)

    # get a list of the customers previous orders
    customer_orders = [Order.objects.filter(id=number).first() for number in order_numbers]

    return render(request, 'online_shop/my-account.html', {'customer_orders': customer_orders})


def change_password(request):
    if not request.user.is_authenticated:
        return redirect('/login')

    data = cartData(request)
    items = data['items']
    order = data['order']
    cartItems = data['cartItems']

    if request.method == "POST":
        current_password = request.POST['current_password']
        new_password = request.POST['new_password']
        try:
            u = User.objects.get(id=request.user.id)
            if u.check_password(current_password):
                u.set_password(new_password)
                u.save()
                alert = True
                return render(request, "change_password.html", {'alert': alert})
            else:
                currpasswrong = True
                return render(request, "change_password.html", {'currpasswrong': currpasswrong})
        except:
            pass

    return render(request, "online_shop/change_password.html", {'cartItems': cartItems})


# def contact(request):
#     if request.method == "POST":
#         name = request.POST['name']
#         email = request.POST['email']
#         phone = request.POST['phone']
#         desc = request.POST['desc']
#         contact = Contact(name=name, email=email, phone=phone, desc=desc)
#         contact.save()
#         alert = True
#         return render(request, 'online_shop/contact.html', {'alert': alert})
#     else:
#         return render(request, "online_shop/contact.html")


def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')
        send_mail(
            'Contact Form Submission',
            f'Name: {name}\nEmail: {email}\n\nMessage: {message}',
            email,
            ['admin@example.com'],
            fail_silently=False,
        )
        messages.success(request, 'Your message has been sent!')
        return redirect('contact')

    # Add the following check for id
    if request.GET.get('id'):
        id = request.GET.get('id')
        return redirect(reverse('product_view', kwargs={'id': id}))

    return render(request, "online_shop/contact.html")


def UpdateOrder(request):
    data = json.loads(request.body)
    productId = data['productId']
    action = data['action']

    customer = request.user.customer
    product = Product.objects.get(id=productId)
    order, created = Order.objects.get_or_create(customer=customer, complete=False)

    orderItem, created = OrderItem.objects.get_or_create(order=order, product=product)

    if action == 'add':
        orderItem.quantity += 1
    elif action == 'remove':
        orderItem.quantity -= 1

    orderItem.save()

    if orderItem.quantity <= 0:
        orderItem.delete()

    return JsonResponse('Item was added', safe=False)


def cartData(request):
    if request.user.is_authenticated:
        customer = request.user.customer  # retrieve the customer associated with the user
        order, created = Order.objects.get_or_create(customer=customer, complete=False)

        items = order.orderitem_set.all()
        cart_items = order.get_cart_items
    else:
        try:
            cart = json.loads(request.COOKIES['cart'])
        except:
            cart = {}

        items = []
        order = {'get_cart_total': 0, 'get_cart_items': 0, 'shipping': False}
        cart_items = 0

        for i in cart:
            try:
                cart_items += cart[i]['quantity']

                product = Product.objects.get(id=i)
                total = (product.price * cart[i]['quantity'])

                order['get_cart_total'] += total
                order['get_cart_items'] += cart[i]['quantity']

                if not product.digital:
                    order['shipping'] = True

                item = {
                    'id': product.id,
                    'product': {
                        'id': product.id,
                        'name': product.name,
                        'price': product.price,
                        'imageURL': product.imageURL
                    },
                    'quantity': cart[i]['quantity'],
                    'digital': product.digital,
                    'get_total': total,
                }
                items.append(item)

            except:
                pass

    return {'items': items, 'order': order, 'cart_items': cart_items}


@login_required(login_url='login')
def checkout(request):
    try:
        cart = Cart.objects.get(customer=request.user.customer)
    except Cart.DoesNotExist:
        cart = Cart.objects.create(customer=request.user.customer)

    customer = request.user.customer
    order, created = Order.objects.get_or_create(customer=customer, complete=False)
    items = OrderItem.objects.filter(order=order)

    if request.method == 'POST':
        address = request.POST.get('address')
        city = request.POST.get('city')
        state = request.POST.get('state')
        zipcode = request.POST.get('zipcode')
        phone_number = request.POST.get('phone_number')

        order.address = address
        order.city = city
        order.state = state
        order.zipcode = zipcode
        order.phone_number = phone_number
        order.complete = True
        order.save()

        # clear cart items
        cart_items = cart.cartitem_set.all()
        for item in cart_items:
            item.delete()

        return redirect('index')

    context = {
        'items': items,
        'order': order,
    }
    return render(request, 'online_shop/checkout.html', context)



def tracker(request):
    if not request.user.is_authenticated:
        return redirect('/login')
    data = cartData(request)
    items = data['items']
    order = data['order']
    cartItems = data['cartItems']
    if request.method == "POST":
        order_id = request.POST['order_id']
        order = Order.objects.filter(id=order_id).first()
        order_items = OrderItem.objects.filter(order=order)
        update_order = UpdateOrder.objects.filter(order_id=order_id)
        print(update_order)
        return render(request, "online_shop/tracker.html", {'order_items': order_items, 'update_order': update_order})
    return render(request, "online_shop/tracker.html", {'cartItems': cartItems})


def Login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('index')
        else:
            error_message = 'Invalid login'
            return render(request, 'online_shop/login.html', {'error_message': error_message})
    else:
        return render(request, 'online_shop/login.html')


def Logout(request):
    logout(request)
    return redirect('index')


def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        user = User.objects.create_user(username, email, password)
        login(request, user)
        return redirect('index')
    else:
        return render(request, 'online_shop/register.html')


def Logged_contact(request):
    if request.user.is_authenticated:
        if request.method == 'POST':
            name = request.POST['name']
            email = request.POST['email']
            message = request.POST['message']
            contact = Contact(name=name, email=email, message=message)
            contact.save()
            return redirect('index')
        else:
            return render(request, 'online_shop/loggedin_contact.html')
    else:
        return redirect('login')
