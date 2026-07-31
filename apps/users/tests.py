from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from django.urls import reverse

User = get_user_model()

class UserAuthenticationTests(TestCase):
    def setUp(self):
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
        """Test user signup automatically initializes profile with approved KYC status."""
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
        self.assertEqual(new_user.profile.kyc_status, 'APPROVED')

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
