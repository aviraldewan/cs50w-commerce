from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("auction", views.create_listing, name="createlisting"),
    path("auction/<str:title>", views.listing, name="listing"),
    path("auction/<str:title>/watch", views.watch_auction, name="watch_auction"),
    path("auction/<str:title>/place_bid", views.place_bid, name="place_bid"),
    path("auction/<str:title>/comment", views.comment, name="comment"),
    path("auction/<str:title>/end_auction", views.end_auction, name="end_auction"),
    path("archives", views.archives, name="archives"),
    path("watchlist", views.watchlist, name="watchlist"),
    path("categories", views.categories, name="categories"),
    path("category/<str:name>", views.category, name="category")
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
