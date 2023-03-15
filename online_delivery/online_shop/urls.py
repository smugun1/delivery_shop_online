from django.urls import path, include
from . import views
from django.views.generic.base import RedirectView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("", views.index, name="index"),
    path("cart/", views.cart, name="cart"),
    path('checkout/', views.checkout, name='checkout'),
    path("my_account/", views.my_account, name="my_account"),
    path("update_item/", views.update_item, name="update_item"),
    path("product/<int:id>/", views.product_view, name="product_view"),
    path("not_found/<int:id>/", views.product_not_found, name="product_not_found"),
    path("search/", views.search, name="search"),
    path("contact/", views.contact, name="contact"),
    path("logged_contact/", views.Logged_contact, name="logged_contact"),
    path("register/", views.register, name="register"),
    path("change_password/", views.change_password, name="change_password"),
    path("login/", views.Login, name="login"),
    path("logout/", views.Logout, name="logout"),
    path("social-auth/", include("social_django.urls", namespace="social")),
    path("favicon.ico", RedirectView.as_view(url="/static/favicon.ico", permanent=True)),
]
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

