from django.urls import path, include
from . import views
from django.contrib.auth import views as auth_views


urlpatterns = [
    path('', views.main, name='main'),
    path('upload/', views.upload, name='upload'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register, name='register'),
    path('profile/update_profile_image/', views.update_profile_image, name='profile_image_update'),
    path('profile/<str:username>/', views.profile_view, name='profile'),
    path('stitcher/', views.stitcher, name='stitcher'),
    path('stitch_images/', views.stitch_images, name='stitch_images'),

]