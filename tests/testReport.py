
from sqlalchemy import create_engine
#from sqlalchemy.orm import sessionmaker
import urllib2
import time
from datetime import datetime, timedelta

import platform
import smtplib
import re

try:
    import cogent
except ImportError:
    #Assume we are running from the test directory
    print "Unable to Import Cogent Module Appending Path"
    import sys
    sys.path.append("../")


from cogent.base.model import *
from cogent.report import *

import unittest

class TestIP(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        """One off population of Database"""
        initDb()

    def test_lowbat(self):

        try:
            s = Session()

            x = lowBat(s)
            #print "test_lowbat:", x
            self.assertTrue(len(x) == 5)
            y = lowBat(s)
            self.assertTrue(len(y) == 0)
        finally:
            s.close()

    def test_packetyield(self):
        try:
            s = Session()
            x = packetYield(s)
            print ''.join(x)
            y = packetYield(s)
            #self.assertTrue(len(y) == 0)
            print ''.join(y)
        finally:
            s.close()

    def test_ccyield(self):
        try:
            s = Session()
            x = ccYield(s)
            y = ccYield(s)
            #self.assertTrue(len(y) == 0)
        finally:
            s.close()


def initDb():
    """Create some initial items in our database"""
    try:
        s = Session()
        h = House(address="Test house")
        s.add(h)
        rt = RoomType(name="Test")
        s.add(rt)
        r = Room(name="Example room", roomType=rt)
        s.add(r)
        ll = Location(house=h, room=r)
        s.add(ll)
        n = Node(id=22, location=ll)
        s.add(n)
        s.add(Node(id=23, location=ll))
        s.add(Node(id=24, location=ll))
        s.add(Node(id=4098, nodeTypeId=1, location=ll))
        s.add(Node(id=4099, nodeTypeId=1, location=ll))

        t = datetime.utcnow() - timedelta(days=1)
        for i in range(100):
            ns = NodeState(time=t,
                           nodeId=23,
                           parent=0,
                           localtime=0,
                           seq_num=(i+200)%256)
            s.add(ns)

            s.add(Reading(typeId=6,
                        time=t,
                        value=3.0 - i / 100.,
                        nodeId=22))

            s.add(Reading(typeId=11,
                          time=t,
                          value=300.0,
                          nodeId=4098))
            if i < 200:
                s.add(Reading(typeId=11,
                              time=t,
                              value=300.0,
                    nodeId=4099))
            
            if i > 6:
                s.add(NodeState(time=t,
                                nodeId=24,
                                parent=0,
                                localtime=0,
                                seq_num=(i*2+10)%256))
            t = t + timedelta(minutes=5)
            
        s.commit()
    finally:
        s.close()






    
        
if __name__ == "__main__":
    #initDb()
    engine = create_engine("sqlite:///", echo=False)
    Base.metadata.create_all(engine)
    init_model(engine)
    # try:
    #     s = Session()
    #     h = House(address="Test house")
    #     s.add(h)
    #     rt = RoomType(name="Test")
    #     s.add(rt)
    #     r = Room(name="Example room", roomType=rt)
    #     s.add(r)
    #     ll = Location(house=h, room=r)
    #     s.add(ll)
    #     n = Node(id=22, location=ll)
    #     s.add(n)
    #     s.add(Node(id=23, location=ll))
    #     s.add(Node(id=24, location=ll))
    #     s.add(Node(id=4098, nodeTypeId=1, location=ll))
    #     s.add(Node(id=4099, nodeTypeId=1, location=ll))

    #     t = datetime.utcnow() - timedelta(days=1)
    #     for i in range(288):
    #         ns = NodeState(time=t,
    #                        nodeId=23,
    #                        parent=0,
    #                        localtime=0)
    #         s.add(ns)

    #         s.add(Reading(typeId=6,
    #                     time=t,
    #                     value=3.0 - i / 288.,
    #                     nodeId=22))

    #         s.add(Reading(typeId=11,
    #                       time=t,
    #                       value=300.0,
    #                       nodeId=4098))
    #         if i < 200:
    #             s.add(Reading(typeId=11,
    #                           time=t,
    #                           value=300.0,
    #                 nodeId=4099))
            
    #         if i > 6:
    #             s.add(NodeState(time=t,
    #                             nodeId=24,
    #                             parent=0,
    #                             localtime=0))
    #         t = t + timedelta(minutes=5)
            
    #     s.commit()
    # finally:
    #     s.close()
    unittest.main()
