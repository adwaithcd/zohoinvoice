"""
Contains URL patterns for web app
"""
from django.conf.urls import url
from django.urls import path
from .views import userdetails, user_detail_update_delete_view, index
# from .views import user_detail_update_delete_view
# from .views import user_login

urlpatterns = [
    path("user/", userdetails, name="home"),
    path("user/<int:id>/", user_detail_update_delete_view, name="home"),
    # path("accounts/<int:id>/", user_detail_update_delete_view, name="home"),
    # path("yellowantredirecturl/register/",UserLogin,name="home"),
    url(r'^(?P<path>.*)$', index, name="index"),

]
