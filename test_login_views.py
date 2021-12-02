"""Login View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_login_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User
from datetime import datetime

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class LoginViewTestCase(TestCase):
    """Test views for login."""

    def setUp(self):
        """Create test client, add sample data."""

        self.client = app.test_client()

        #Seed initial users
        all_messages = Message.query.all()
        for test_message in all_messages:
            db.session.delete(test_message)
        db.session.commit()

        all_users = User.query.all()
        for test_user in all_users:
            db.session.delete(test_user)
        db.session.commit()

        testuser1 = User.signup(username="testuser1",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None,
                                    header_image_url=None,
                                    bio=None)
        testuser2 = User.signup(username="testuser2", 
                                    email="test2@test.com",
                                    password="testuser2",
                                    image_url=None,
                                    header_image_url=None,
                                    bio=None)
        db.session.add(testuser1)
        db.session.add(testuser2)
        db.session.commit()
        
        #Seed initial messages 
        message_1 = Message(text="Test Message 1",
        timestamp=datetime.utcnow(),
        user_id=testuser1.id)
        message_2 = Message(text="Test Message 2",
        timestamp=datetime.utcnow(),
        user_id=testuser2.id)
        message_3 = Message(text="Test Message 3",
        timestamp=datetime.utcnow(),
        user_id=testuser2.id)
        for msg in [message_1, message_2, message_3]:
            db.session.add(msg)
        db.session.commit()

    def tearDown(self):
        """Tear down"""
        db.session.rollback()

    def test_signup_form(self):
        """Can a new user see the sign up form? """
        with self.client as c:

            resp = c.get("/signup")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Username",html)
            self.assertIn("E-mail",html)
            self.assertIn("Password",html)
            self.assertIn("Image URL",html)
            self.assertIn("Header Image URL",html)
            self.assertIn("Bio",html)
    
    def test_signup_user(self):
        """Can a new user sign up? """
        with self.client as c:
            resp = c.post("/signup",data={
                "username":"testuser3",
                "password":"password",
                "email": "testuser3@test.com",
                "image_url": "test_image.png",
                "header_image_url": "test_header_image.png",
                "bio": "test bio"
                }, follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("testuser3",html)
            self.assertIn("test_image.png",html)
            self.assertIn("test_header_image.png",html)