from django.urls import path
from .views import ProfileMeView, AddressListCreateView, AddressDestroyView

urlpatterns = [
    path('me', ProfileMeView.as_view(), name='profile_me'),
    path('me/', ProfileMeView.as_view(), name='profile_me_slash'),
    path('addresses', AddressListCreateView.as_view(), name='address_list_create'),
    path('addresses/', AddressListCreateView.as_view(), name='address_list_create_slash'),
    path('addresses/<int:pk>', AddressDestroyView.as_view(), name='address_destroy'),
    path('addresses/<int:pk>/', AddressDestroyView.as_view(), name='address_destroy_slash'),
]
