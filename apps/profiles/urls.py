from django.urls import path
from .views import ProfileMeView, AddressListCreateView, AddressDestroyView

urlpatterns = [
    path('me', ProfileMeView.as_view(), name='profile_me'),
    path('addresses', AddressListCreateView.as_view(), name='address_list_create'),
    path('addresses/<int:pk>', AddressDestroyView.as_view(), name='address_destroy'),
]
