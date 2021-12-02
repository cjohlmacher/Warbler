"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


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


class UserModelTestCase(TestCase):
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

        self.client = app.test_client()
    
    def tearDown(self):
        db.session.rollback()

    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD",
            image_url="test_image.png",
            header_image_url="test_header_image.png",
            bio="test bio",
            location="testlocale"
        )

        db.session.add(u)
        db.session.commit()

        # User data is stored in the database
        self.assertEqual(u.email, "test@test.com")
        self.assertEqual(u.username, "testuser")
        self.assertEqual(u.image_url, "test_image.png")
        self.assertEqual(u.header_image_url, "test_header_image.png")
        self.assertEqual(u.bio, "test bio")
        self.assertEqual(u.location,"testlocale")
        self.assertIsNotNone(u.id)

        # User should have no messages & no followers & no likes
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)
        self.assertEqual(len(u.likes), 0)
    
    def test_missing_nullable_data(self):
        """ Does model work with missing nullable data """

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD",
        )

        db.session.add(u)
        db.session.commit()

        # User data is stored in the database
        self.assertEqual(u.email, "test@test.com")
        self.assertEqual(u.username, "testuser")
        self.assertIsNotNone(u.id)

    def test_missing_required_data(self):
        """ Does model work with missing required data """

        users = [
            User(email="test1@test.com",username="testuser1"),
            User(username="testuser2",password="HASHED_PASSWORD"), 
            User(email="test3@test.com",password="HASHED_PASSWORD"),
            ]

        for u in users:
            db.session.rollback()
            try:
                db.session.add(u)
                db.session.commit()
                exception = None
            except Exception:
                exception = "Error"
            # User data is not stored in the database
            self.assertEqual(exception,"Error")
    
    def test_missing_nullable_data(self):
        """ Does model work with missing nullable data """

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD",
        )

        db.session.add(u)
        db.session.commit()

        # User data is stored in the database
        self.assertEqual(u.email, "test@test.com")
        self.assertEqual(u.username, "testuser")
        self.assertIsNotNone(u.id)

    def test_duplicate_unique_data(self):
        """ Does model catch duplicates for unique fields """

        user1 = User(email="test1@test.com",username="testuser1",password="HASHED_PASSWORD")
        user2 = User(email="test2@test.com",username="testuser1",password="HASHED_PASSWORD") 
        user3 = User(email="test1@test.com",username="testuser3",password="HASHED_PASSWORD")

        combinations=[[user1,user2], [user1,user3]]

        for combination in combinations:
            db.session.rollback()
            try:
                for user in combination:
                    db.session.add(user)
                db.session.commit()
                exception = None
            except Exception:
                exception = "Error"
            # User data is not stored in the database
            self.assertEqual(exception,"Error")
        
    def test_repr__user(self):
        """ Does user model represent itself correctly """

        user = User(email="test@test.com",username="testuser",password="HASHED_PASSWORD")
        db.session.add(user)
        db.session.commit()
        self.assertEqual(repr(user),f"<User #{user.id}: testuser, test@test.com>")
    
    def test_is_followed_by(self):
        """ Does is-followed-by function works correctly """

        user1 = User(email="test1@test.com",username="testuser1",password="HASHED_PASSWORD")
        user2 = User(email="test2@test.com",username="testuser2",password="HASHED_PASSWORD")
        db.session.add(user1)
        db.session.add(user2)
        db.session.commit()
        follow1 = Follows(user_being_followed_id=user1.id, user_following_id=user2.id)
        db.session.add(follow1)
        db.session.commit()

        self.assertTrue(user1.is_followed_by(user2))
        self.assertFalse(user2.is_followed_by(user1))
    
    def test_is_following(self):
        """ Does is-following function work correctly """

        user1 = User(email="test1@test.com",username="testuser1",password="HASHED_PASSWORD")
        user2 = User(email="test2@test.com",username="testuser2",password="HASHED_PASSWORD")
        db.session.add(user1)
        db.session.add(user2)
        db.session.commit()
        follow1 = Follows(user_being_followed_id=user1.id, user_following_id=user2.id)
        db.session.add(follow1)
        db.session.commit()

        self.assertTrue(user2.is_following(user1))
        self.assertFalse(user1.is_following(user2))
    
    def test_sign_up(self):
        """ Does is-following function work correctly """

        user1 = User.signup("testuser","testuser@test.com","HASHED_PASSWORD","test_image.png","test_header_image.png","test bio")
        db.session.commit()
        self.assertEqual(user1.username,"testuser")
        self.assertEqual(user1.email,"testuser@test.com")
        self.assertEqual(user1.image_url,"test_image.png")
        self.assertEqual(user1.header_image_url,"test_header_image.png")
        self.assertEqual(user1.bio,"test bio")
        self.assertIsNotNone(user1.id)
    
    def test_authenticate(self):
        """ Does authenticating user with correct crediantials work """

        user1 = User.signup("testuser","testuser@test.com","HASHED_PASSWORD","test_image.png","test_header_image.png","test bio")
        db.session.commit()
        resulting_user = User.authenticate("testuser","HASHED_PASSWORD")
        self.assertEqual(user1,resulting_user)
    
    def test_bad_authentication(self):
        """ Does authenticating user with incorrect credentials fail """

        user1 = User.signup("testuser","testuser@test.com","HASHED_PASSWORD","test_image.png","test_header_image.png","test bio")
        db.session.commit()
        resulting_user = User.authenticate("testuser","BAD_PASSWORD")
        self.assertFalse(resulting_user)
    
    def test_likes_relationship(self):
        """ Does the .likes relationship work """

        user1 = User(email="test1@test.com",username="testuser1",password="HASHED_PASSWORD")
        db.session.add(user1)
        db.session.commit()
        message1 = Message(text="Test Message",timestamp=datetime.utcnow(),user_id=user1.id)
        message2 = Message(text="Test Message 2",timestamp=datetime.utcnow(),user_id=user1.id)
        db.session.add(message1)
        db.session.add(message2)
        db.session.commit()
        like1 = Likes(user_id=user1.id, message_id=message1.id)
        like2 = Likes(user_id=user1.id, message_id=message2.id)
        db.session.add(like1)
        db.session.add(like2)
        db.session.commit()
        self.assertEqual(len(user1.likes),2)
    
    def test_followers_relationship(self):
        """ Does the .followers relationship work """

        user1 = User(email="test1@test.com",username="testuser1",password="HASHED_PASSWORD")
        user2 = User(email="test2@test.com",username="testuser2",password="HASHED_PASSWORD")
        user3 = User(email="test3@test.com",username="testuser3",password="HASHED_PASSWORD")
        db.session.add(user1)
        db.session.add(user2)
        db.session.add(user3)
        db.session.commit()
        follow1 = Follows(user_being_followed_id=user1.id, user_following_id=user2.id)
        follow2 = Follows(user_being_followed_id=user1.id, user_following_id=user3.id)
        db.session.add(follow1)
        db.session.add(follow2)
        db.session.commit()
        self.assertEqual(len(user1.followers),2)
    
    def test_following_relationship(self):
        """ Does the .following relationship work """

        user1 = User(email="test1@test.com",username="testuser1",password="HASHED_PASSWORD")
        user2 = User(email="test2@test.com",username="testuser2",password="HASHED_PASSWORD")
        user3 = User(email="test3@test.com",username="testuser3",password="HASHED_PASSWORD")
        db.session.add(user1)
        db.session.add(user2)
        db.session.add(user3)
        db.session.commit()
        follow1 = Follows(user_being_followed_id=user2.id, user_following_id=user1.id)
        follow2 = Follows(user_being_followed_id=user3.id, user_following_id=user1.id)
        db.session.add(follow1)
        db.session.add(follow2)
        db.session.commit()
        self.assertEqual(len(user1.following),2)
    



    

    

        

        

        