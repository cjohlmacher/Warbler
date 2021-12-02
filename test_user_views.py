"""User View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_user_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User, Follows, Likes
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


class UserViewTestCase(TestCase):
    """Test views for users."""

    def setUp(self):
        """Create test client, add sample data."""

        self.client = app.test_client()

        #Seed initial users
        all_messages = Message.query.all()
        for test_message in all_messages:
            db.session.delete(test_message)
        db.session.commit()

        all_follows = Follows.query.all()
        for test_follow in all_follows:
            db.session.delete(test_follow)
        db.session.commit()

        all_likes = Likes.query.all()
        for test_like in all_likes:
            db.session.delete(test_like)
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
        testuser3 = User.signup(username="testuser3", 
                                    email="test3@test.com",
                                    password="testuser3",
                                    image_url=None,
                                    header_image_url=None,
                                    bio=None)
        db.session.add(testuser1)
        db.session.add(testuser2)
        db.session.add(testuser3)
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

    def test_list_users(self):
        """ Are users listed """
        with self.client as c:
            resp = c.get("/users")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("testuser1",html)
            self.assertIn("testuser2",html)

    def test_view_user(self):
        """ Can a user's profile be viewed? """
        with self.client as c:
            testuser2 = User.query.filter_by(username="testuser2").first()
            
            resp = c.get(f"/users/{testuser2.id}")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("testuser2",html)

            self.assertNotIn("Test Message 1", html)
            self.assertIn("Test Message 2",html)
            self.assertIn("Test Message 3",html)
    
    def test_view_nonexistent_user(self):
        """ Is a non-existent user's profile handled? """
        with self.client as c:
            user1 = User.query.get(999)
            if user1:
                raise Exception("Test error: Need user id 999 to be unused")
            resp = c.get(f"/users/999")
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 404)

    def test_view_user_following(self):
        """ View users a user is following """
        with self.client as c:
            testuser1 = User.query.filter_by(username="testuser1").first()
            testuser2 = User.query.filter_by(username="testuser2").first()
            testuser3 = User.query.filter_by(username="testuser3").first()
            follow1 = Follows(user_being_followed_id=testuser2.id, user_following_id=testuser1.id)
            follow2 = Follows(user_being_followed_id=testuser3.id, user_following_id=testuser1.id)
            db.session.add(follow1)
            db.session.add(follow2)
            db.session.commit()
            testuser1 = User.query.filter_by(username="testuser1").first()
            testuser2 = User.query.filter_by(username="testuser2").first()
            testuser3 = User.query.filter_by(username="testuser3").first()
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = testuser2.id

            resp = c.get(f"/users/{testuser1.id}/following")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn(testuser2.username,html)
            self.assertIn(testuser3.username,html)

    def test_unathorized_view_user_following(self):
        """ Unauthorized request to view user's following """
        with self.client as c:
            testuser1 = User.query.filter_by(username="testuser1").first()
            testuser2 = User.query.filter_by(username="testuser2").first()
            testuser3 = User.query.filter_by(username="testuser3").first()
            follow1 = Follows(user_being_followed_id=testuser2.id, user_following_id=testuser1.id)
            follow2 = Follows(user_being_followed_id=testuser3.id, user_following_id=testuser1.id)
            db.session.add(follow1)
            db.session.add(follow2)
            db.session.commit()
            testuser1 = User.query.filter_by(username="testuser1").first()
            testuser2 = User.query.filter_by(username="testuser2").first()
            testuser3 = User.query.filter_by(username="testuser3").first()

            resp = c.get(f"/users/{testuser1.id}/following", follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized",html)
            self.assertNotIn(testuser3.username,html)
    
    def test_view_user_followers(self):
        """ View users that follow a user """
        with self.client as c:
            testuser1 = User.query.filter_by(username="testuser1").first()
            testuser2 = User.query.filter_by(username="testuser2").first()
            testuser3 = User.query.filter_by(username="testuser3").first()
            follow1 = Follows(user_being_followed_id=testuser1.id, user_following_id=testuser2.id)
            follow2 = Follows(user_being_followed_id=testuser1.id, user_following_id=testuser3.id)
            db.session.add(follow1)
            db.session.add(follow2)
            db.session.commit()
            testuser1 = User.query.filter_by(username="testuser1").first()
            testuser2 = User.query.filter_by(username="testuser2").first()
            testuser3 = User.query.filter_by(username="testuser3").first()
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = testuser2.id

            resp = c.get(f"/users/{testuser1.id}/followers")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn(testuser2.username,html)
            self.assertIn(testuser3.username,html)

    def test_unathorized_view_user_followers(self):
        """ Unauthorized request to view user's following """
        with self.client as c:
            testuser1 = User.query.filter_by(username="testuser1").first()
            testuser2 = User.query.filter_by(username="testuser2").first()
            testuser3 = User.query.filter_by(username="testuser3").first()
            follow1 = Follows(user_being_followed_id=testuser1.id, user_following_id=testuser2.id)
            follow2 = Follows(user_being_followed_id=testuser1.id, user_following_id=testuser3.id)
            db.session.add(follow1)
            db.session.add(follow2)
            db.session.commit()
            testuser1 = User.query.filter_by(username="testuser1").first()
            testuser2 = User.query.filter_by(username="testuser2").first()
            testuser3 = User.query.filter_by(username="testuser3").first()

            resp = c.get(f"/users/{testuser1.id}/followers", follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized",html)
            self.assertNotIn(testuser3.username,html)

    def test_view_user_likes(self):
            """ View messages that a user likes """
            with self.client as c:
                testuser1 = User.query.filter_by(username="testuser1").first()
                testuser2 = User.query.filter_by(username="testuser2").first()
                message1 = Message.query.filter_by(text="Test Message 1").first()
                message2 = Message.query.filter_by(text="Test Message 2").first()
                message3 = Message.query.filter_by(text="Test Message 3").first()
                like1 = Likes(user_id=testuser1.id,message_id=message1.id)
                like2 = Likes(user_id=testuser1.id,message_id=message2.id)
                db.session.add(like1)
                db.session.add(like2)
                db.session.commit()
                testuser1 = User.query.filter_by(username="testuser1").first()
                testuser2 = User.query.filter_by(username="testuser2").first()
                message1 = Message.query.filter_by(text="Test Message 1").first()
                message2 = Message.query.filter_by(text="Test Message 2").first()
                message3 = Message.query.filter_by(text="Test Message 3").first()
                with c.session_transaction() as sess:
                    sess[CURR_USER_KEY] = testuser2.id

                resp = c.get(f"/users/{testuser1.id}/likes")
                html = resp.get_data(as_text=True)

                self.assertEqual(resp.status_code, 200)
                self.assertIn(message1.text,html)
                self.assertIn(message2.text,html)
                self.assertNotIn(message3.text,html)

    def test_unathorized_view_user_likes(self):
        """ Unauthorized request to view user's following """
        with self.client as c:
            testuser1 = User.query.filter_by(username="testuser1").first()
            message1 = Message.query.filter_by(text="Test Message 1").first()
            message2 = Message.query.filter_by(text="Test Message 2").first()
            message3 = Message.query.filter_by(text="Test Message 3").first()
            like1 = Likes(user_id=testuser1.id,message_id=message1.id)
            like2 = Likes(user_id=testuser1.id,message_id=message2.id)
            db.session.add(like1)
            db.session.add(like2)
            db.session.commit()
            testuser1 = User.query.filter_by(username="testuser1").first()
            message3 = Message.query.filter_by(text="Test Message 3").first()

            resp = c.get(f"/users/{testuser1.id}/likes", follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized",html)
            self.assertNotIn(message3.text,html)

    def test_follow(self):
        """Can a user follow another user"""
        with self.client as c:
            testuser1 = User.query.filter_by(username="testuser1").first()
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = testuser1.id
            
            testuser2 = User.query.filter_by(username="testuser2").first()
            resp = c.post(f"/users/follow/{testuser2.id}", data={}, follow_redirects=True)

            self.assertEqual(resp.status_code, 200)

            testuser1 = User.query.filter_by(username="testuser1").first()
            testuser2 = User.query.filter_by(username="testuser2").first()
            resp = c.get(f"/users/{testuser1.id}/following")
            html = resp.get_data(as_text=True)
            self.assertIn(testuser2.username,html)
    
    def test_unauthorized_follow(self):
        """Can a user follow another user"""
        with self.client as c:
            testuser1 = User.query.filter_by(username="testuser1").first()
            testuser2 = User.query.filter_by(username="testuser2").first()
            
            resp = c.post(f"/users/follow/{testuser2.id}", data={}, follow_redirects=True)
            html = resp.get_data(as_text=True)
            
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized",html)

            testuser1 = User.query.filter_by(username="testuser1").first()
            testuser2 = User.query.filter_by(username="testuser2").first()
            resp = c.get(f"/users/{testuser1.id}/following")
            html = resp.get_data(as_text=True)
            self.assertNotIn(testuser2.username,html)

    def test_stop_follow(self):
            """Can a user stop following another user"""
            with self.client as c:
                testuser1 = User.query.filter_by(username="testuser1").first()
                testuser2 = User.query.filter_by(username="testuser2").first()
                testuser3 = User.query.filter_by(username="testuser3").first()
                follow1 = Follows(user_being_followed_id=testuser2.id, user_following_id=testuser1.id)
                follow2 = Follows(user_being_followed_id=testuser3.id, user_following_id=testuser1.id)
                db.session.add(follow1)
                db.session.add(follow2)
                db.session.commit()
                with c.session_transaction() as sess:
                    sess[CURR_USER_KEY] = testuser1.id
                
                testuser1 = User.query.filter_by(username="testuser1").first()
                testuser2 = User.query.filter_by(username="testuser2").first()
                
                resp = c.get(f"/users/{testuser1.id}/following")
                html = resp.get_data(as_text=True)
                self.assertIn(testuser2.username,html)

                resp = c.post(f"/users/stop-following/{testuser2.id}", data={}, follow_redirects=True)

                self.assertEqual(resp.status_code, 200)

                testuser1 = User.query.filter_by(username="testuser1").first()
                testuser2 = User.query.filter_by(username="testuser2").first()
                resp = c.get(f"/users/{testuser1.id}/following")
                html = resp.get_data(as_text=True)
                self.assertNotIn(testuser2.username,html)

    def test_unauthorized_stop_follow(self):
            """Can an anonymous user stop following another user"""
            with self.client as c:
                testuser1 = User.query.filter_by(username="testuser1").first()
                testuser2 = User.query.filter_by(username="testuser2").first()
                testuser3 = User.query.filter_by(username="testuser3").first()
                follow1 = Follows(user_being_followed_id=testuser2.id, user_following_id=testuser1.id)
                follow2 = Follows(user_being_followed_id=testuser3.id, user_following_id=testuser1.id)
                db.session.add(follow1)
                db.session.add(follow2)
                db.session.commit()
                
                testuser1 = User.query.filter_by(username="testuser1").first()
                testuser2 = User.query.filter_by(username="testuser2").first()

                resp = c.post(f"/users/stop-following/{testuser2.id}", data={}, follow_redirects=True)
                html = resp.get_data(as_text=True)
                
                self.assertEqual(resp.status_code, 200)
                self.assertIn('Access unauthorized',html)

                testuser1 = User.query.filter_by(username="testuser1").first()
                testuser2 = User.query.filter_by(username="testuser2").first()
                
                with c.session_transaction() as sess:
                                    sess[CURR_USER_KEY] = testuser1.id
                
                resp = c.get(f"/users/{testuser1.id}/following")
                html = resp.get_data(as_text=True)
                self.assertIn(testuser2.username,html)

    def test_toggle_like(self):
        """Can a user toggle likes on a message"""
        with self.client as c:
            testuser1 = User.query.filter_by(username="testuser1").first()

            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = testuser1.id

            resp = c.get(f"/users/{testuser1.id}/likes", follow_redirects=True)
            html = resp.get_data(as_text=True)
            
            self.assertEqual(resp.status_code, 200)
            message3 = Message.query.filter_by(text="Test Message 3").first()
            self.assertNotIn(message3.text,html)

            resp = c.post(f"/users/toggle_like/{message3.id}", data={}, follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)

            testuser1 = User.query.filter_by(username="testuser1").first()

            resp = c.get(f"/users/{testuser1.id}/likes")
            html = resp.get_data(as_text=True)

            message3 = Message.query.filter_by(text="Test Message 3").first()
            self.assertIn(message3.text,html)

            resp = c.post(f"/users/toggle_like/{message3.id}", data={}, follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)

            testuser1 = User.query.filter_by(username="testuser1").first()

            resp = c.get(f"/users/{testuser1.id}/likes")
            html = resp.get_data(as_text=True)

            message3 = Message.query.filter_by(text="Test Message 3").first()
            self.assertNotIn(message3.text,html)
    
    def test_unauthorized_toggle_like(self):
        """Can a user toggle likes on a message"""
        with self.client as c:
            testuser1 = User.query.filter_by(username="testuser1").first()
            message3 = Message.query.filter_by(text="Test Message 3").first()

            resp = c.post(f"/users/toggle_like/{message3.id}", data={}, follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized",html)

            testuser1 = User.query.filter_by(username="testuser1").first()
            
            with c.session_transaction() as sess:
                            sess[CURR_USER_KEY] = testuser1.id
            resp = c.get(f"/users/{testuser1.id}/likes")
            html = resp.get_data(as_text=True)

            message3 = Message.query.filter_by(text="Test Message 3").first()
            self.assertNotIn(message3.text,html)
    
    def test_edit_user_profile(self):
        """Can a user edit their user profile"""
        with self.client as c:
                testuser1 = User.query.filter_by(username="testuser1").first()
                user1_id = testuser1.id

                with c.session_transaction() as sess:
                    sess[CURR_USER_KEY] = testuser1.id

                resp = c.post(f"/users/profile", data={
                    "username": "editeduser1",
                    "email": "editedemail@test.com",
                    "password": "testuser",
                    "image_url": "edited_img.png",
                    "header_image_url": "edited_header_img.png",
                    "bio": "edited bio"
                },follow_redirects=True)
                html = resp.get_data(as_text=True)
                
                self.assertEqual(resp.status_code, 200)
                testuser1 = User.query.get(user1_id)
                self.assertEqual(testuser1.email,"editedemail@test.com")
                
                resp = c.get(f"/users/{testuser1.id}")
                html = resp.get_data(as_text=True)

                self.assertIn("editeduser1",html)
                self.assertIn("editedemail@test.com",html)
                self.assertIn("edited_img.png",html)
                self.assertIn("edited_header_img.png",html)
                self.assertIn("edited bio",html)
                self.assertNotIn("testuser1",html)

    def test_incorrect_password_edit_user_profile(self):
            """Can a user edit their user profile"""
            with self.client as c:
                    testuser1 = User.query.filter_by(username="testuser1").first()
                    user1_id = testuser1.id

                    with c.session_transaction() as sess:
                        sess[CURR_USER_KEY] = testuser1.id

                    resp = c.post(f"/users/profile", data={
                        "username": "editeduser1",
                        "email": "editedemail@test.com",
                        "password": "badpassword",
                        "image_url": "edited_img.png",
                        "header_image_url": "edited_header_img.png",
                        "bio": "edited bio"
                    },follow_redirects=True)
                    html = resp.get_data(as_text=True)
                    
                    self.assertEqual(resp.status_code, 200)
                    testuser1 = User.query.get(user1_id)
                    self.assertEqual(testuser1.email,"test@test.com")
                    self.assertIn("Incorrect password",html)
                    
                    resp = c.get(f"/users/{testuser1.id}")
                    html = resp.get_data(as_text=True)

                    self.assertNotIn("editeduser1",html)
                    self.assertNotIn("editedemail@test.com",html)
                    self.assertNotIn("edited_img.png",html)
                    self.assertNotIn("edited_header_img.png",html)
                    self.assertNotIn("edited bio",html)
                    self.assertIn("testuser1",html)

    def test_unauthorized_edit_user_profile(self):
        """Can an anonymous user edit a user's profile"""
        with self.client as c:
                resp = c.post(f"/users/profile", data={
                    "username": "editeduser1",
                    "email": "editedemail@test.com",
                    "password": "badpassword",
                    "image_url": "edited_img.png",
                    "header_image_url": "edited_header_img.png",
                    "bio": "edited bio"
                },follow_redirects=True)
                html = resp.get_data(as_text=True)
                
                self.assertEqual(resp.status_code, 200)
                self.assertIn("Access unauthorized", html)

    def test_delete_user_profile(self):
        """Can a user delete their profile"""
        with self.client as c:
                testuser1 = User.query.filter_by(username="testuser1").first()
                user1_id = testuser1.id

                with c.session_transaction() as sess:
                    sess[CURR_USER_KEY] = testuser1.id

                resp = c.post(f"/users/delete", data={
                },follow_redirects=True)
                html = resp.get_data(as_text=True)
                
                self.assertEqual(resp.status_code, 200)
                testuser1 = User.query.get(user1_id)
                self.assertIsNone(testuser1)
                
                resp = c.get(f"/users/{user1_id}")
                self.assertEqual(resp.status_code, 404)

    def test_unauthorized_delete_user_profile(self):
        """Can an anonymous user delete a profile"""
        with self.client as c:
                resp = c.post(f"/users/delete", data={
                },follow_redirects=True)
                html = resp.get_data(as_text=True)
                
                self.assertEqual(resp.status_code, 200)
                self.assertIn("Access unauthorized", html)