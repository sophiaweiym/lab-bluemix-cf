# Copyright 2016, 2017 John J. Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Pet Test Suite

Test cases can be run with the following:
nosetests -v --with-spec --spec-color
"""

# import os
# import json
import unittest
from mock import MagicMock, patch
from requests import HTTPError, ConnectionError
from service.models import Pet, DataValidationError

VCAP_SERVICES = {
    'cloudantNoSQLDB': [
        {'credentials': {
            'username': 'admin',
            'password': 'pass',
            'host': 'localhost',
            'port': 5984,
            'url': 'http://admin:pass@localhost:5984'
            }
        }
    ]
}

######################################################################
#  T E S T   C A S E S
######################################################################
class TestPets(unittest.TestCase):
    """ Test Cases for Pet Model """

    def setUp(self):
        """ Initialize the Cloudant database """
        Pet.init_db("test")
        Pet.remove_all()

    def test_create_a_pet(self):
        """ Create a pet and assert that it exists """
        pet = Pet("fido", "dog", False)
        self.assertNotEqual(pet, None)
        self.assertEqual(pet.id, None)
        self.assertEqual(pet.name, "fido")
        self.assertEqual(pet.category, "dog")
        self.assertEqual(pet.available, False)

    def test_add_a_pet(self):
        """ Create a pet and add it to the database """
        pets = Pet.all()
        self.assertEqual(pets, [])
        pet = Pet("fido", "dog", True)
        self.assertNotEqual(pet, None)
        self.assertEqual(pet.id, None)
        pet.save()
        # Asert that it was assigned an id and shows up in the database
        self.assertNotEqual(pet.id, None)
        pets = Pet.all()
        self.assertEqual(len(pets), 1)
        self.assertEqual(pets[0].name, "fido")
        self.assertEqual(pets[0].category, "dog")
        self.assertEqual(pets[0].available, True)

    def test_update_a_pet(self):
        """ Update a Pet """
        pet = Pet("fido", "dog", True)
        pet.save()
        self.assertNotEqual(pet.id, None)
        # Change it an save it
        pet.category = "k9"
        pet.save()
        # Fetch it back and make sure the id hasn't changed
        # but the data did change
        pets = Pet.all()
        self.assertEqual(len(pets), 1)
        self.assertEqual(pets[0].category, "k9")
        self.assertEqual(pets[0].name, "fido")

    def test_delete_a_pet(self):
        """ Delete a Pet """
        pet = Pet("fido", "dog")
        pet.save()
        self.assertEqual(len(Pet.all()), 1)
        # delete the pet and make sure it isn't in the database
        pet.delete()
        self.assertEqual(len(Pet.all()), 0)

    def test_serialize_a_pet(self):
        """ Serialize a Pet """
        pet = Pet("fido", "dog", False)
        data = pet.serialize()
        self.assertNotEqual(data, None)
        self.assertNotIn('_id', data)
        self.assertIn('name', data)
        self.assertEqual(data['name'], "fido")
        self.assertIn('category', data)
        self.assertEqual(data['category'], "dog")
        self.assertIn('available', data)
        self.assertEqual(data['available'], False)

    def test_deserialize_a_pet(self):
        """ Deserialize a Pet """
        data = {"name": "kitty", "category": "cat", "available": True}
        pet = Pet()
        pet.deserialize(data)
        self.assertNotEqual(pet, None)
        self.assertEqual(pet.id, None)
        self.assertEqual(pet.name, "kitty")
        self.assertEqual(pet.category, "cat")
        self.assertEqual(pet.available, True)

    def test_deserialize_with_no_name(self):
        """ Deserialize a Pet that has no name """
        data = {"id":0, "category": "cat"}
        pet = Pet()
        self.assertRaises(DataValidationError, pet.deserialize, data)

    def test_deserialize_with_no_data(self):
        """ Deserialize a Pet that has no data """
        pet = Pet()
        self.assertRaises(DataValidationError, pet.deserialize, None)

    def test_deserialize_with_bad_data(self):
        """ Deserialize a Pet that has bad data """
        pet = Pet()
        self.assertRaises(DataValidationError, pet.deserialize, "string data")

    def test_save_a_pet_with_no_name(self):
        """ Save a Pet with no name """
        pet = Pet(None, "cat")
        self.assertRaises(DataValidationError, pet.save)

    def test_create_a_pet_with_no_name(self):
        """ Create a Pet with no name """
        pet = Pet(None, "cat")
        self.assertRaises(DataValidationError, pet.create)

    def test_find_pet(self):
        """ Find a Pet by id """
        Pet("fido", "dog").save()
        # saved_pet = Pet("kitty", "cat").save()
        saved_pet = Pet("kitty", "cat")
        saved_pet.save()
        pet = Pet.find(saved_pet.id)
        self.assertIsNot(pet, None)
        self.assertEqual(pet.id, saved_pet.id)
        self.assertEqual(pet.name, "kitty")

    def test_find_with_no_pets(self):
        """ Find a Pet with empty database """
        pet = Pet.find("1")
        self.assertIs(pet, None)

    def test_pet_not_found(self):
        """ Find a Pet that doesnt exist """
        Pet("fido", "dog").save()
        pet = Pet.find("2")
        self.assertIs(pet, None)

    def test_find_by_name(self):
        """ Find a Pet by Name """
        Pet("fido", "dog").save()
        Pet("kitty", "cat").save()
        pets = Pet.find_by_name("fido")
        self.assertNotEqual(len(pets), 0)
        self.assertEqual(pets[0].category, "dog")
        self.assertEqual(pets[0].name, "fido")

    def test_find_by_category(self):
        """ Find a Pet by Category """
        Pet("fido", "dog").save()
        Pet("kitty", "cat").save()
        pets = Pet.find_by_category("cat")
        self.assertNotEqual(len(pets), 0)
        self.assertEqual(pets[0].category, "cat")
        self.assertEqual(pets[0].name, "kitty")

    def test_find_by_availability(self):
        """ Find a Pet by Availability """
        Pet("fido", "dog", False).save()
        Pet("kitty", "cat", True).save()
        pets = Pet.find_by_availability(True)
        self.assertEqual(len(pets), 1)
        self.assertEqual(pets[0].name, "kitty")

    def test_create_query_index(self):
        """ Test create query index """
        Pet("fido", "dog", False).save()
        Pet("kitty", "cat", True).save()
        Pet.create_query_index('category')

    def test_disconnect(self):
        """ Test Disconnet """
        Pet.disconnect()
        pet = Pet("fido", "dog", False)
        self.assertRaises(AttributeError, pet.save)

    @patch('cloudant.database.CloudantDatabase.create_document')
    def test_http_error(self, bad_mock):
        """ Test a Bad Create with HTTP error """
        bad_mock.side_effect = HTTPError()
        pet = Pet("fido", "dog", False)
        pet.create()
        self.assertIsNone(pet.id)

    @patch('cloudant.document.Document.exists')
    def test_document_not_exist(self, bad_mock):
        """ Test a Bad Document Exists """
        bad_mock.return_value = False
        pet = Pet("fido", "dog", False)
        pet.create()
        self.assertIsNone(pet.id)

    @patch('cloudant.database.CloudantDatabase.__getitem__')
    def test_key_error_on_update(self, bad_mock):
        """ Test KeyError on update """
        bad_mock.side_effect = KeyError()
        pet = Pet("fido", "dog", False)
        pet.save()
        pet.name = 'Fifi'
        pet.update()
        #self.assertEqual(pet.name, 'fido')

    @patch('cloudant.database.CloudantDatabase.__getitem__')
    def test_key_error_on_delete(self, bad_mock):
        """ Test KeyError on delete """
        bad_mock.side_effect = KeyError()
        pet = Pet("fido", "dog", False)
        pet.create()
        pet.delete()

    @patch('cloudant.client.Cloudant.__init__')
    def test_connection_error(self, bad_mock):
        """ Test Connection error handler """
        bad_mock.side_effect = ConnectionError()
        self.assertRaises(AssertionError, Pet.init_db, 'test')


#     def test_http_error(self):
    # @patch.dict(os.environ, {'VCAP_SERVICES': json.dumps(VCAP_SERVICES)})
    # def test_vcap_services(self):
    #     """ Test if VCAP_SERVICES works """
    #     Pet.init_db()
    #     self.assertIsNotNone(Pet.client)
    #     Pet("fido", "dog", True).save()
    #     pets = Pet.find_by_name("fido")
    #     self.assertNotEqual(len(pets), 0)
    #     self.assertEqual(pets[0].name, "fido")


######################################################################
#   M A I N
######################################################################
if __name__ == '__main__':
    unittest.main()
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPets)
    unittest.TextTestRunner(verbosity=2).run(suite)
