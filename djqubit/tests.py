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


    def test_i18n_data_update(self):
        """
        I18n data is currently set in a horrid way because we can't
        instantiate the models (they have not primary key.)  So check
        setting the the dodgy way works.
        """
        io = models.InformationObject.objects.get(identifier="Foobar")
        updatetitle = "This is a new translated title"
        io.set_i18n("en", dict(
            title=updatetitle,
        ))
        self.assertEqual(io.get_i18n("en", "title"), updatetitle)

        # FIXME: Inserting i18n data not working for now
        # IntegrityError: PRIMARY KEY must be unique
        updatesource = "This should be a new foreign language"
        io.set_i18n("zx", dict(
            sources=updatesource,
        ))
        self.assertEqual(io.get_i18n("zx", "sources"), updatesource)




