from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from django.urls import reverse

User = get_user_model()

@override_settings(REST_FRAMEWORK={
    'DEFAULT_THROTTLE_CLASSES': [],
    'DEFAULT_THROTTLE_RATES': {},
})
class UserAuthenticationTests(TestCase):
    def setUp(self):
        from unittest.mock import patch
        self.throttle_patcher = patch('rest_framework.views.APIView.check_throttles', lambda self, request: None)
        self.throttle_patcher.start()

        self.client = APIClient()
        self.login_url = reverse('auth_login')
        self.register_url = reverse('auth_register')
        self.user = User.objects.create_user(
            email='testuser@flyorago.com',
            password='Password123!',
            first_name='Test',
            last_name='User',
            role='sender'
        )

    def tearDown(self):
        self.throttle_patcher.stop()

    def test_login_success_lowercase(self):
        """Test login with exact email matching."""
        response = self.client.post(self.login_url, {
            'email': 'testuser@flyorago.com',
            'password': 'Password123!'
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        self.assertIn('tokens', response.json()['data'])

    def test_login_success_case_insensitive(self):
        """Test case-insensitive login email handling."""
        response = self.client.post(self.login_url, {
            'email': 'TestUser@FlyoraGo.com ',
            'password': 'Password123!'
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        self.assertEqual(response.json()['data']['userId'], str(self.user.id))

    def test_login_wrong_password(self):
        """Test login with incorrect password returns WRONG_PASSWORD error code."""
        response = self.client.post(self.login_url, {
            'email': 'testuser@flyorago.com',
            'password': 'WrongPassword123!'
        }, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()['success'])
        self.assertEqual(response.json()['errors']['error_code'], 'WRONG_PASSWORD')

    def test_user_registration_auto_profile(self):
        """Test user signup automatically initializes profile with NOT_SUBMITTED KYC status."""
        response = self.client.post(self.register_url, {
            'email': 'newmember@flyorago.com',
            'password': 'NewPassword123!',
            'first_name': 'New',
            'last_name': 'Member',
            'role': 'traveler'
        }, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.json()['success'])
        
        new_user = User.objects.get(email='newmember@flyorago.com')
        self.assertTrue(hasattr(new_user, 'profile'))
        self.assertEqual(new_user.profile.kyc_status, 'NOT_SUBMITTED')

    def test_block_unblock_password_retention(self):
        """Verify that blocking and unblocking a user in Admin panel preserves original password."""
        # 1. Block user
        self.user.is_active = False
        self.user.save(update_fields=['is_active'])
        self.assertFalse(self.user.is_active)
        self.assertTrue(self.user.check_password('Password123!'))

        # 2. Unblock user
        self.user.is_active = True
        self.user.save(update_fields=['is_active'])
        self.assertTrue(self.user.is_active)

        # 3. Login with original password after unblocking
        response = self.client.post(self.login_url, {
            'email': 'testuser@flyorago.com',
            'password': 'Password123!'
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])

    def test_registration_weak_password_rejected(self):
        """Test weak passwords are rejected during registration."""
        response = self.client.post(self.register_url, {
            'email': 'weakpassworduser@flyorago.com',
            'password': '123',
            'first_name': 'Weak',
            'last_name': 'User',
            'role': 'sender'
        }, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()['success'])

    def test_otp_omitted_in_production(self):
        """Verify test_otp is absent from registration response in production mode."""
        from django.test import override_settings
        with override_settings(DEBUG=False):
            response = self.client.post(self.register_url, {
                'email': 'prodmember@flyorago.com',
                'password': 'Password123!',
                'first_name': 'Prod',
                'last_name': 'Member',
                'role': 'sender'
            }, format='json')
            self.assertEqual(response.status_code, 201)
            self.assertNotIn('test_otp', response.json()['data'])

    def test_booking_idor_restriction(self):
        """Verify standard user cannot view another user's booking details."""
        # Create other user
        other_user = User.objects.create_user(
            email='otheruser@flyorago.com',
            password='Password123!',
            first_name='Other',
            last_name='User',
            role='sender'
        )
        # Create a booking between other_user and user
        from bookings.models import Booking
        booking = Booking.objects.create(
            sender=other_user,
            traveler=other_user,
            package_name='Secret Box',
            weight=5.0,
            reward=100.0,
            status='REQUEST_SENT'
        )
        
        # Authenticate client as self.user
        self.client.force_authenticate(user=self.user)
        
        detail_url = reverse('booking_detail', kwargs={'pk': booking.id})
        response = self.client.get(detail_url)
        # Since get_queryset restricts to sender/traveler, this should return 404 (Not Found)
        self.assertEqual(response.status_code, 404)

    def test_luggage_booking_action_idor_protection(self):
        """Verify user C cannot accept or pay for a luggage booking between user A and B."""
        from luggage_sharing.models import LuggageListing, LuggageBooking
        
        user_a = self.user # traveler/owner
        user_b = User.objects.create_user(email='booker@flyorago.com', password='Password123!', role='sender')
        user_c = User.objects.create_user(email='stranger@flyorago.com', password='Password123!', role='sender')
        
        from decimal import Decimal
        listing = LuggageListing.objects.create(
            owner=user_a,
            airline='Delta',
            flight_number='DL100',
            departure_airport='JFK',
            arrival_airport='LAX',
            departure_date='2026-09-01',
            departure_time='12:00:00',
            price_per_kg=10.0,
            max_airline_allowance=Decimal('20.00'),
            currently_used_weight=Decimal('0.00'),
            available_weight=Decimal('20.00'),
            max_kg=Decimal('20.00'),
            status='ACTIVE'
        )
        
        booking = LuggageBooking.objects.create(
            listing=listing,
            booker=user_b,
            owner=user_a,
            booked_weight=5.0,
            price_per_kg=10.0,
            total_price=50.0,
            status='REQUESTED'
        )
        
        action_url = reverse('luggage_booking_action', kwargs={'pk': booking.id})
        
        # 1. User C tries to accept (Access Denied)
        self.client.force_authenticate(user=user_c)
        response = self.client.post(action_url, {'action': 'accept'}, format='json')
        self.assertEqual(response.status_code, 403)
        
        # 2. User C tries to pay (Access Denied)
        response = self.client.post(action_url, {'action': 'pay'}, format='json')
        self.assertEqual(response.status_code, 403)

    def test_payment_intent_idor_protection(self):
        """Verify standard user cannot initiate/confirm payments for another user's booking."""
        from bookings.models import Booking
        
        user_a = self.user
        user_b = User.objects.create_user(email='buyer@flyorago.com', password='Password123!', role='sender')
        
        booking = Booking.objects.create(
            sender=user_b,
            traveler=user_b,
            package_name='Valuable cargo',
            weight=5.0,
            reward=100.0,
            status='ACCEPTED'
        )
        
        # User A tries to create a payment intent for User B's booking
        self.client.force_authenticate(user=user_a)
        intent_url = reverse('payment_intent_create')
        response = self.client.post(intent_url, {'booking_id': booking.id}, format='json')
        self.assertEqual(response.status_code, 403)
