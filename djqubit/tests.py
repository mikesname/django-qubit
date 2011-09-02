"""
DJQubit test suite.
"""

from django.test import TestCase
import models

class InformationObjectTest(TestCase):
    fixtures = ["test_fixtures.json"]
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_information_object(self):
        io = models.InformationObject.objects.get(identifier="Foobar")
        self.assertEqual(io.class_name, "QubitInformationObject")


