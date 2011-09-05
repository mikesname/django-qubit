"""
DJQubit test suite.
"""

from django.test import TestCase
from django.db.models import Max
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

    def test_update_information_object(self):
        othername = "Another Name"
        io = models.InformationObject.objects.get(identifier="Foobar")
        io.identifier = othername
        update = io.updated_at
        io.save()
        
        io = models.InformationObject.objects.get(pk=io.pk)
        self.assertEqual(othername, io.identifier)
        self.assertNotEqual(update, io.updated_at)


    def test_create_information_object(self):
        before = models.InformationObject.objects.count()
        root = models.InformationObject.objects.filter(parent=None)[0]
        ionew = models.InformationObject(identifier="TestCreate", parent=root)
        ionew.save()
        after = models.InformationObject.objects.count()
        self.assertEqual(before, after - 1)


    def test_nested_set_update(self):
        """
        Test nested-set values get updates correctly when
        a new node is created.
        """
        root = models.InformationObject.objects.filter(parent=None)[0]
        child = root.children.all()[0]
        self.assertEqual(root.lft, child.lft - 1)
        maxrgt = models.InformationObject.objects.aggregate(Max("rgt"))["rgt__max"]
        self.assertEqual(maxrgt, models.InformationObject.objects.count() * 2)

        newio = models.InformationObject(identifier="TreeTest", parent=None)
        newio.save()

        # the highest RGT value should be exactly twice the number of objects
        maxrgt2 = models.InformationObject.objects.aggregate(Max("rgt"))["rgt__max"]
        self.assertEqual(maxrgt2, models.InformationObject.objects.count() * 2)

        # delete the object and check the nested set has been adjusted
        newio.delete()
        maxrgt3 = models.InformationObject.objects.aggregate(Max("rgt"))["rgt__max"]
        self.assertEqual(maxrgt3, models.InformationObject.objects.count() * 2)


        
