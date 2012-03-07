"""
Testing for the Deployment Module

:author: Dan Goldsmith <djgoldsmith@googlemail.com>
"""

"""

"""

#Python Library Imports
import unittest
import datetime

#Python Module Imports
from sqlalchemy import create_engine
import sqlalchemy.exc

import testmeta

models = testmeta.models

#from cogent.push import remoteModels as remoteModels
import cogent.push.Pusher as Pusher

REMOTE_URL = "sqlite:///remote.db"
LOCAL_URL = "sqlite:///test.db"

class TestPush(testmeta.BaseTestCase):
    """Test the Push Functionality.

    For the moment I think we need to overload the standard setup, teardown methods
    Otherwise we will not be able to make any changes to the database

    """

    @classmethod
    def setUpClass(self):
        """Called the First time this class is called.
        This means that we can Init the testing database once per testsuite
        
        We need to override the standard class here, as we also want to create a Remote
        database connection.
        """

        #This is a little bit hackey, but it works quite nicely at the moment.
        #Basically creates an empty remote database that we can connect to.
        # print "Initialising Remote Engine"
        engine = create_engine(REMOTE_URL)
        models.initialise_sql(engine,False)
        remoteSession = sqlalchemy.orm.sessionmaker(bind=engine)
        self.remoteSession = remoteSession
        self.engine = engine

        remoteEngine = sqlalchemy.create_engine("sqlite:///remote.db")
        localEngine =  sqlalchemy.create_engine("sqlite:///test.db")

        push = Pusher.Pusher()
        push.init_remote(remoteEngine)
        push.init_local(localEngine)
        self.push = push
         #push.testRemoteQuery()
         #push.testLocalQuery()
        

        #What is pretty cool is the idea we can also  recreate the database to clean it out each time
        #models.initialise_sql(self.engine,True)


    def testSetup(self):
        print "Testing setup or remote and local database"
        #Query from local database
        localSession = testmeta.Session()
        remoteSession = self.remoteSession()

        print "Querying Local"
        theQry = localSession.query(models.RoomType)
        for item in theQry:
            print "--> {0}".format(item)

        print "Query Remote"
        theQry = remoteSession.query(models.RoomType)
        for item in theQry:
            print "--> {0}".format(item)
            
    def testPushSetup(self):
        print "Testing if the Push Setup works properly"""
        self.push.testRemoteQuery()
        self.push.testLocalQuery()
        

    def testConnection(self):
        """Can we connect to remote databases with various strings"""
        pass

    def testFullTransfer(self):
        """Can we transfer everything across"""
        pass

    

    


if __name__ == "__main__":
    unittest.main()
