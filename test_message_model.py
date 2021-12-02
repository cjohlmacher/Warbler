"""Message model tests."""

# run these tests like:
#
#    python -m unittest test_message_model.py


import os
from unittest import TestCase
from datetime import datetime

from models import db, User, Message, Follows, Likes

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


class MessageModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        all_follows = Follows.query.all()
        for test_follow in all_follows:
            db.session.delete(test_follow)
        db.session.commit()
        
        all_messages = Message.query.all()
        for test_message in all_messages:
            db.session.delete(test_message)
        db.session.commit()

        all_likes = Likes.query.all()
        for test_like in all_likes:
            db.session.delete(test_like)
        db.session.commit()

        all_users = User.query.all()
        for test_user in all_users:
            db.session.delete(test_user)
        db.session.commit()

        user1 = User(username="testuser",email="testemail@test.com",password="HASHED_PASSWORD")
        db.session.add(user1)
        db.session.commit()

        self.client = app.test_client()
    
    def tearDown(self):
        db.session.rollback()

    def test_message_model(self):
        """Does basic model work?"""
        user1 = User.query.first()
        m = Message(
            text="Test Message",
            timestamp=datetime.utcnow(),
            user_id=user1.id
        )

        db.session.add(m)
        db.session.commit()

        # User data is stored in the database
        self.assertEqual(m.text,"Test Message")
        self.assertIsNotNone(m.timestamp)
        self.assertIsNotNone(m.id)
        self.assertEqual(m.user_id,user1.id)

        # User should have a user relationship
        self.assertEqual(m.user, user1)

    def test_missing_required_data(self):
        """ Does model throw error with missing required data """
        
        user1 = User.query.first()
        messages = [
            Message(text="Test Message",timestamp=datetime.utcnow()),
            Message(timestamp=datetime.utcnow(),user_id=user1.id),
            ]

        for m in messages:
            db.session.rollback()
            try:
                print('message: ',m)
                db.session.add(m)
                db.session.commit()
                exception = None
            except Exception:
                exception = "Error"
            # User data is not stored in the database
            self.assertEqual(exception,"Error")
    
    def test_missing_data_with_defaults(self):
        """ Does model populate default with missing data that has defaults """
        
        user1 = User.query.first()
        messages = [Message(text="Test Message",user_id=user1.id)]

        for m in messages:
            db.session.rollback()
            try:
                print('message: ',m)
                db.session.add(m)
                db.session.commit()
                exception = None
            except Exception:
                exception = "Error"
            # User data is not stored in the database
            self.assertIsNone(exception)
        