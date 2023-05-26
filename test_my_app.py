from flask import url_for
from flask_testing import TestCase
from app import app
import unittest

class MyTestCase(TestCase):
    def create_app(self):
        return app

    def test_protected_captcha_solved(self):
        response = self.client.get(url_for('protected', captcha='solved'))
        assert response.status_code == 302

    def test_protected_captcha_not_solved(self):
        response = self.client.get(url_for('protected', captcha='unsolved'))
        self.assertEqual(response.data, b'Captcha not succed')

if __name__ == '__main__':
    unittest.main()