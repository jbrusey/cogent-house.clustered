"""
Test for the Sensor Type Classes
"""


#from datetime import datetime
import datetime

#Python Module Imports
import sqlalchemy.exc


import json
import cogentviewer.models as models
import cogentviewer.tests.base as base

class TestRoom(base.ModelTestCase):

    def _serialobj(self):
        """Helper Method to provde an object to serialise"""
        theItem = models.Room(id=1,
                              name="Test Room",
                              roomTypeId = 1)
        return theItem

    def _dictobj(self):
        """Helper method to provide a dictionay representaiton of the object
        generated by _serialobj()"""

        theDict = {"__table__":"Room",
                   "id":1,
                   "name":"Test Room",
                   "roomTypeId" : 1 }
        return theDict

    def testEq(self):
        """Test for Equality"""
        item1 = models.Room(id=1,
                            name="Test Room",
                            roomTypeId = 1)
        item2 = models.Room(id=1,
                            name="Test Room",
                            roomTypeId = 1)

        self.assertEqual(item1,item2)
        self.assertReallyEqual(item1,item2)

        #Not massivly botherered about Id at the moment
        item2.id = 5
        self.assertEqual(item1,item2)
        self.assertReallyEqual(item1,item2)

    def testNEQ(self):
        item1 = models.Room(id=1,
                            name="Test Room",
                            roomTypeId = 1)
        item2 = models.Room(id=1,
                            name="Test Room",
                            roomTypeId = 1)

        self.assertEqual(item1,item2)

        item2.name = "FOO"
        self.assertNotEqual(item1,item2)
        self.assertReallyNotEqual(item1,item2)

        item2.name = item1.name
        item2.roomTypeId = 2

    def testCmp(self):
        """Test Compaison function

        (actually __lt__ for Py3K Comat)"""

        item1 = models.Room(id=1,
                            name="Test Room",
                            roomTypeId = 1)

        item2 = models.Room(id=1,
                            name="Test Room",
                            roomTypeId = 1)
        
        self.assertEqual(item1,item2)
        
        #Order On Name
        item2.name = "A_Test"
        self.assertGreater(item1,item2)

        item2.name = "Z_Test"
        self.assertLess(item1,item2)

        item2.name = item1.name
        item2.roomTypeId = 0
        self.assertGreater(item1,item2)

        item2.roomTypeId = 2
        self.assertLess(item1,item2)


    def testAssociations(self):
        """Test if backrefs and foriegn keys work correctly"""
        session = self.session

        roomtype = models.RoomType(name = "Foo Type")
        session.add(roomtype)
        session.flush()

        room = models.Room(name = "Test Room",
                           roomTypeId = roomtype.id)

        session.add(room)
        session.flush()

        session.commit()

        #And then do the check the backrefs etc
        qryroom = session.query(models.Room).filter_by(name="Test Room").first()

        print "-"
        print "-"*70
        print "OR RM: ",room
        print "NE RM: ",qryroom
        print "OR TY: ",roomtype 
        print "TY ID: ",qryroom.roomTypeId
        print "-"*70

        self.assertEqual(room,qryroom)

        #Check the Ids match
        qrytype = qryroom.roomTypeId
        
        self.assertEqual(qrytype, roomtype.id)

        #And check on the backrefs
        qrytype = qryroom.roomType
        self.assertEqual(qrytype,roomtype)

        
        
