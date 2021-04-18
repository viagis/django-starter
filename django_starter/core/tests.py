from django.test import TestCase, Client


class ViewsTestCase(TestCase):

    def setUp(self) -> None:
        pass

    def test_views(self):
        client = Client()
        # Frontend Views
        self.assertEqual(client.get('/').status_code, 200)
