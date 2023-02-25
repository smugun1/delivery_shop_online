import json

from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import render, redirect

from .models import Product, Feature, Review, CheckoutDetail, Order, OrderItem, Contact


# Create your views here.
def index(request):
    order = None
    cart_items = 0  # set default value for cart_items
    if request.user.is_authenticated:
        customer = request.user.customer
        order, created = Order.objects.get_or_create(customer=customer, complete=False)

        # update the value of cart_items
        cart_items = order.get_cart_items

    products = Product.objects.all()

    context = {
        'products': products,
        'cart_items': cart_items,
        'order': order,
    }

    return render(request, "online_shop/index.html", context)


def search(request):
    data = cartData(request)
    if data is None:
        data = {'items': [], 'order': {'get_cart_total': 0, 'get_cart_items': 0}, 'cartItems': 0}

    items = data['items']
    order = data['order']
    cartItems = data['cartItems']

    if request.method == "POST":
        search = request.POST['search']
        products = Product.objects.filter(name__contains=search)
        return render(request, "online_shop/search.html",
                      {'search': search, 'products': products, 'cartItems': cartItems})

    return render(request, "online_shop/search.html", {'cartItems': cartItems})


def product_view(request, id):
    product = Product.objects.filter(id=id).first()
    if not product:
        # handle case where product does not exist
        pass
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

    return render(request, "online_shop/product_view.html",
                  {'product': product, 'cartItems': cartItems, 'feature': feature, 'reviews': reviews})


def cart(request, cart_items=None):
    data = cartData(request)
    items = data['items']
    order = data['order']
    cartItems = data['cartItems']

    try:
        cart = json.loads(request.COOKIES['cart'])
    except:
        cart = {}

    for i in cart:
        try:
            cartItems += cart[i]["quantity"]

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


def updateItem(request):
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

    cart_items = order.get_cart_items()
    return JsonResponse({'cart_items': cart_items})


@login_required
def checkout(request):
    data = cartData(request)
    items = data['items']
    order = data['order']
    cartItems = data['cartItems']
    total = 0

    customer = request.user.customer
    if request.method == "POST":
        address = request.POST['address']
        city = request.POST['city']
        state = request.POST['state']
        zipcode = request.POST['zipcode']
        phone_number = request.POST['phone_number']
        payment = request.POST['payment']

        shipping_address = CheckoutDetail.objects.create(
            address=address,
            city=city,
            phone_number=phone_number,
            state=state,
            zipcode=zipcode,
            customer=customer,
            total_amount=total,
            order=order,
            payment=payment
        )
        shipping_address.save()

        if order is not None:
            total = order.get_cart_total() if order else 0
            if total == order.get_cart_total() and order:
                order.complete = True
                order.save()
        alert = True
        return render(request, "checkout.html", {'alert': alert})

    return render(request, "online_shop/checkout.html", {'items': items, 'order': order, 'cartItems': cartItems})


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


def contact(request):
    if request.method == "POST":
        name = request.POST['name']
        email = request.POST['email']
        phone = request.POST['phone']
        desc = request.POST['desc']
        contact = Contact(name=name, email=email, phone=phone, desc=desc)
        contact.save()
        alert = True
        return render(request, 'online_shop/contact.html', {'alert': alert})
    else:
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
        customer = request.user.customer
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

    return {'cartItems': cart_items, 'order': order, 'items': items}


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


def loggedin_contact(request):
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
