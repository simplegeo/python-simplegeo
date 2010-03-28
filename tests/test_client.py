import unittest
import simplegeo

class ClientTest(unittest.TestCase):
    MY_OAUTH_KEY = 'my-key'
    MY_OAUTH_SECRET = 'my-secret'
    
    def setUp(self):
        self.client = simplegeo.Client(self.MY_OAUTH_KEY, self.MY_OAUTH_SECRET)

    # Add tests!


if __name__ == '__main__':
    unittest.main()