"""
Testing Code for the Push Script

Testing this gets a little complex as it relies on external modules.
So there is a little bit of legwork requried to get everything up and running

Database Setup
---------------

This expects two databases to be available.

1) Clean version of the database "pushSink" installed as per the webinterface
2) Version of the database "pushSource" installed and populated using the populate data script

Webserver Setup
----------------

* Create an instance of the webserver that is connected to the pushSink database. (test.ini)

Push Script Setup
------------------

* Make sure the config file points towards the test Server
* Remove any test_map.conf files

"""

#Python Library Imports
import unittest
import datetime

import logging
logging.basicConfig(level=logging.DEBUG,
                    format="%(asctime)s %(name)-10s %(levelname)-8s %(message)s",
                    datefmt = "%m-%d-%Y %H:%M",
                    )


import sqlalchemy

import cogent
import cogent.base.model as models
import cogent.base.model.meta as meta
import cogent.base.model.populateData as populateData
import cogent.push.RestPusher as RestPusher

BASE = meta.Base

#ENGINE URLS
SINKURL = "mysql://chuser@localhost/pushSink"
SOURCEURL = "mysql://chuser@localhost/pushSource"
#SINKURL = "sqlite:///sink_test.db"
#SOURCEURL = "sqlite:///source_test.db"


class TestPush(unittest.TestCase):
   
    @classmethod
    def setUpClass(self):
        """Check the setup works and that everything is how we expect it to be"""

        log = logging.getLogger("Test Push")
        """Create some database engines for testing"""
        logging.debug("Creating Engines")

        #Create our engines
        logging.debug("-> Sink Engine")

        sinkengine = sqlalchemy.create_engine(SINKURL)
        sinksession = sqlalchemy.orm.sessionmaker(bind=sinkengine)
        models.init_model(sinkengine)
        #Create Tables
        logging.debug("--> Creating Tables")
        BASE.metadata.create_all(sinkengine)
        logging.debug("--> Initialising Data")

        session = sinksession()
        populateData.init_data(session)
        session.flush()
        session.commit()
        session.close()

        logging.debug("-> Source Engine")
        sourceengine = sqlalchemy.create_engine(SOURCEURL)
        sourcesession = sqlalchemy.orm.sessionmaker(bind=sourceengine)
        models.init_model(sourceengine)
        #Create Tables
        logging.debug("--> Creating Tables")
        BASE.metadata.create_all(sourceengine)
        logging.debug("--> Initialising Data")

        session = sourcesession()
        populateData.init_data(session)
        session.flush()
        session.commit()
        session.close()
        

        logging.debug("Engines Created")
    
        self.log = log
        self.sourcesession = sourcesession
        self.sinksession = sinksession

        #Create a Push Server
        theServer = RestPusher.PushServer(SOURCEURL)
        log.info("Test Server is {0}".format(theServer))

        #Hack to get the Pusher Object
        thePusher = theServer.synclist[0]
        log.info("Test Pusher is {0}".format(thePusher))
        self.thePusher = thePusher


    @unittest.skip
    def test_sensortypes(self):
        """Test Sync Of Sensor Types"""
        source = self.sourcesession()
        sink = self.sinksession()
        log = self.log

        #Check the sensor types match at the start
        localSensor = models.SensorType(id=1000,name="TEST")

        source_data = source.query(models.SensorType).order_by(models.SensorType.id).all()
        sink_data = sink.query(models.SensorType).order_by(models.SensorType.id).all()
        self.assertEqual(source_data,sink_data)
        
        #What we want to to is test the syncList
        out = self.thePusher.sync_sensortypes()
        log.info("-- OUT {0}".format(out))

        self.assertTrue(out)

        #Nothing should have changed
        source_data = source.query(models.SensorType).order_by(models.SensorType.id).all()
        sink_data = sink.query(models.SensorType).order_by(models.SensorType.id).all()
        self.assertEqual(source_data,sink_data)

        # ----------------------------------------------------------

        #Now Add a new Sensor to the Local DB
        localSensor = models.SensorType(id=1000,name="TEST")
        source.add(localSensor)
        source.flush()
        source.commit()

        source = self.sourcesession()
        theQry = source.query(models.SensorType).filter_by(id=1000).first()
        log.debug("=== QRY {0}".format(theQry))

        #What we want to to is test the syncList
        log.debug("---> Synchronising Data")
        out = self.thePusher.sync_sensortypes()
        log.info("-- OUT {0}".format(out))

        #And Also fetch that particular sensor
        sink = self.sinksession()
        sinkSensor = sink.query(models.SensorType).filter_by(id = 1000).first()
        log.debug("Sink Sensor {0}".format(sinkSensor))
        self.assertEqual(sinkSensor,localSensor)

        #------------------------- AND SYNC REMOTE SIDE --------------------------

        #Now Add a new Sensor to the Local DB
        localSensor = models.SensorType(id=1001,name="TEST_TWO")
        sink.add(localSensor)
        sink.flush()
        sink.commit()

        #What we want to to is test the syncList
        out = self.thePusher.sync_sensortypes()
        #print "-- OUT {0}".format(out)

        source = self.sourcesession()
        sink = self.sinksession()
        source_data = source.query(models.SensorType).order_by(models.SensorType.id).all()
        sink_data = sink.query(models.SensorType).order_by(models.SensorType.id).all()
        self.assertEqual(source_data,sink_data)        

        log.debug("--> Cleaning Up")
        source_data = source.query(models.SensorType).filter(models.SensorType.id>=1000).delete()
        sink_data = sink.query(models.SensorType).filter(models.SensorType.id>=1000).delete()

        #Final Flush and commit
        source.flush()
        source.commit()
        
        sink.flush()
        sink.commit()
        
    @unittest.skip
    def testRoomTypes(self):
        """And Syncing room types"""
        source = self.sourcesession()
        sink = self.sinksession()

        #Check the sensor types match at the start
        source_data = source.query(models.RoomType).all()
        sink_data = sink.query(models.RoomType).all()

        self.assertEqual(source_data, sink_data)
        out = self.thePusher.sync_roomtypes()        
       
        #Now Add a new Sensor to the Local DB
        localItem = models.RoomType(id=1000,name="TEST")
        source.add(localItem)
        source.flush()
        source.commit()

        out = self.thePusher.sync_roomtypes()

        source = self.sourcesession()
        sink = self.sinksession()
        
        #Check this is in the sink
        theQry = sink.query(models.RoomType).filter_by(name="TEST").first()
        self.assertEqual(theQry,localItem)

        #Now Add a new Sensor to the Remote DB
        remoteItem = models.RoomType(id=1001,name="TEST_TWO")
        sink.add(remoteItem)
        sink.flush()
        sink.commit()

        out = self.thePusher.sync_roomtypes()

        source = self.sourcesession()
        sink = self.sinksession()

        theQry = source.query(models.RoomType).filter_by(name="TEST_TWO").first()
        self.assertEqual(theQry,remoteItem)

        self.log.debug("--> Cleaning up")
        source_data = source.query(models.RoomType).filter(models.RoomType.id>=5).delete()
        sink_data = sink.query(models.RoomType).filter(models.RoomType.id>=5).delete()

        #Final Flush and commit
        source.flush()
        source.commit()
        sink.flush()
        sink.commit()


    @unittest.skip
    def testRoom(self):
        """And Syncing room types"""
        
        #We need to sync room types so the Ids work properly
        self.thePusher.sync_roomtypes() # 

        source = self.sourcesession()
        sink = self.sinksession()


        source_data = source.query(models.Room).filter(models.Room.id>=13).delete()
        sink_data = sink.query(models.Room).filter(models.Room.id>=13).delete()

        #Final Flush and commit
        source.flush()
        source.commit()
        sink.flush()
        sink.commit()

        source = self.sourcesession()
        sink = self.sinksession()

        #Check the sensor types match at the start
        source_data = source.query(models.Room).all()
        sink_data = sink.query(models.Room).all()

        self.assertEqual(source_data, sink_data)

        out = self.thePusher.sync_rooms()        
        
        #Now Add a new Sensor to the Local DB
        localItem = models.Room(id=1000, roomTypeId = 1, name="TEST")
        source.add(localItem)
        source.flush()
        source.commit()

        self.log.debug("== Local Item is {0}".format(localItem))
        out = self.thePusher.sync_rooms()

        source = self.sourcesession()
        sink = self.sinksession()
        
        #Check this is in the sink
        theQry = sink.query(models.Room).filter_by(name="TEST").first()
        self.log.debug("-- Local, {0} Remote {1}".format(localItem,theQry))
        self.assertEqual(theQry,localItem)

        #Now Add a new Sensor to the Remote DB
        remoteItem = models.Room(id=1001, name="TEST_TWO", roomTypeId=2)
        sink.add(remoteItem)
        sink.flush()
        sink.commit()

        out = self.thePusher.sync_rooms()

        source = self.sourcesession()
        sink = self.sinksession()

        theQry = source.query(models.Room).filter_by(name="TEST_TWO").first()
        self.assertEqual(theQry,remoteItem)

        self.log.debug("--> Cleaning up")
        source_data = source.query(models.Room).filter(models.Room.id>=13).delete()
        sink_data = sink.query(models.Room).filter(models.Room.id>=13).delete()

        #Final Flush and commit
        source.flush()
        source.commit()
        sink.flush()
        sink.commit()

    @unittest.skip
    def testDeployment(self):
        """And Syncing room types"""
        
        #We need to sync room types so the Ids work properly

        source = self.sourcesession()
        sink = self.sinksession()

        source_data = source.query(models.Deployment).delete()
        sink_data = sink.query(models.Deployment).delete()

        #Final Flush and commit
        source.flush()
        source.commit()
        sink.flush()
        sink.commit()

        source = self.sourcesession()
        sink = self.sinksession()

        #There should be no deployments to begin with
        source_data = source.query(models.Deployment).all()
        sink_data = sink.query(models.Deployment).all()

        self.assertEqual(source_data, [])
        self.assertEqual(source_data, sink_data)

    
        localItem = models.Deployment(name="TEST")
        source.add(localItem)
        source.flush()
        source.commit()

        self.log.debug("== Local Item is {0}".format(localItem))
        out = self.thePusher.sync_deployments()

        source = self.sourcesession()
        sink = self.sinksession()
        
        #Check this is in the sink
        theQry = sink.query(models.Deployment).filter_by(name="TEST").first()
        self.log.debug("-- Local, {0} Remote {1}".format(localItem,theQry))
        self.assertEqual(theQry,localItem)

        #Now Add a new Sensor to the Remote DB
        remoteItem = models.Deployment(name="TEST_TWO")
        sink.add(remoteItem)
        sink.flush()
        sink.commit()

        out = self.thePusher.sync_deployments()

        source = self.sourcesession()
        sink = self.sinksession()

        theQry = source.query(models.Deployment).filter_by(name="TEST_TWO").first()
        self.assertEqual(theQry,remoteItem)

        self.log.debug("--> Cleaning up")
        source_data = source.query(models.Deployment).delete()
        sink_data = sink.query(models.Deployment).delete()

        #Final Flush and commit
        source.flush()
        source.commit()
        sink.flush()
        sink.commit()

    @unittest.skip
    def testSyncNodes(self):
        """Test that the node synch code works correctly"""
        source = self.sourcesession()
        sink = self.sinksession()

        source_data = source.query(models.Node).delete()
        sink_data = sink.query(models.Node).delete()

        #Final Flush and commit
        source.flush()
        source.commit()
        sink.flush()
        sink.commit()

        source = self.sourcesession()
        sink = self.sinksession()

        #There should be no Nodes to begin with
        source_data = source.query(models.Node).all()
        sink_data = sink.query(models.Node).all()

        self.assertEqual(source_data, [])
        self.assertEqual(source_data, sink_data)

    
        localItem = models.Node(id=101)
        source.add(localItem)
        source.flush()
        source.commit()

        self.log.debug("== Local Item is {0}".format(localItem))
        out = self.thePusher.sync_nodes()

        source = self.sourcesession()
        sink = self.sinksession()
        
        #Check this is in the sink
        theQry = sink.query(models.Node).filter_by(id=101).first()
        self.log.debug("-- Local, {0} Remote {1}".format(localItem, theQry))
        self.assertEqual(theQry, localItem)

        #Now Add a new Sensor to the Remote DB
        remoteItem = models.Node(id=102)
        self.log.debug("==>>=>> Remote {0}".format(remoteItem))
        sink.add(remoteItem)
        sink.flush()
        sink.commit()
        
        out = self.thePusher.sync_nodes()
    
        source = self.sourcesession()
        sink = self.sinksession()

        theQry = source.query(models.Node).filter_by(id=102).first()
        self.assertIsInstance(theQry,models.Node)
        #self.log.debug("====>> Remote {0}".format(remoteItem))
        #self.log.debug("====>> Local {0}".format(theQry))
        #return
        #self.assertEqual(theQry,remoteItem)

        self.log.debug("--> Cleaning up")
        source_data = source.query(models.Node).delete()
        sink_data = sink.query(models.Node).delete()

        #Final Flush and commit
        source.flush()
        source.commit()
        sink.flush()
        sink.commit()

    def testReadings(self):
        """Test that the Readings update works"""

        log = self.log
        

        #Cleanup
        session = self.sourcesession()
        theQry = session.query(models.Reading).delete()
        theQry = session.query(models.Location).delete()
        theQry = session.query(models.Node).delete()
        theQry = session.query(models.House).delete()
        theQry = session.query(models.Deployment).delete()
        session.commit()

        #Remote Session
        rsession = self.sinksession()
        theQry = rsession.query(models.Reading).delete()
        theQry = rsession.query(models.Location).delete()
        theQry = rsession.query(models.Node).delete()
        theQry = rsession.query(models.House).delete()
        theQry = rsession.query(models.Deployment).delete() 
        rsession.commit()

        #Populate the Database
        session = self.sourcesession()
        #And Create the relevant objects
        theDeployment = models.Deployment(name="Test Deployment")
        session.add(theDeployment)
        theHouse = models.House(address="Test Address",
                                deploymentId = theDeployment.id)
        session.add(theHouse)
        theNode = models.Node(id=101)
        session.add(theNode)
        

        #A Few Locations
        theRoom = session.query(models.Room).filter_by(name="Master Bedroom").first()
        theLocation = models.Location(houseId = theHouse.id,
                                      roomId = theRoom.id)

        session.add(theLocation)
        session.flush()
        #SensorType 0 should already exist

        READINGS = 100
        now = datetime.datetime.now()
        startDate = now - datetime.timedelta(seconds = 1*READINGS)
        log.debug("Now {0} Start {1}".format(now,startDate))

        for x in range(READINGS):
            thisReading = models.Reading(time=startDate,
                                         nodeId = 101,
                                         value = x,
                                         locationId = theLocation.id,
                                         typeId = 0)
            session.add(thisReading)
            startDate = startDate + datetime.timedelta(seconds=1)
        
        session.flush()
        session.commit()

        #Then Do the Preliminary Sync
        pusher = self.thePusher

        pusher.sync_sensortypes() #TST
        pusher.sync_roomtypes() #TST 
        pusher.sync_rooms()     #TST
        pusher.sync_deployments() #TST
        pusher.sync_nodes()
        pusher.load_mappings()

        #And upload the Readings
        pusher.upload_readings(theHouse)

        #Now we need to check all the items arrived as expected
        source = self.sourcesession()
        sink = self.sinksession()

        sourceQry = source.query(models.Reading).all()
        sinkQry = sink.query(models.Reading).all()

        self.assertEqual(sourceQry,sinkQry)
      


        #Lets repeat that to make sure everything works a second time
        startDate = datetime.datetime.now()

        ITEMS = 50
        for x in range(1):
            session = self.sourcesession()
            log.debug("Repeating {0} ".format(x))
            for x in range(ITEMS):

                thisReading = models.Reading(time=startDate,
                                             nodeId = 101,
                                             value = x,
                                             locationId = theLocation.id,
                                             typeId = 0)
                session.add(thisReading)
                startDate = startDate + datetime.timedelta(seconds=1)
        
                session.flush()
                session.commit() 

            #And upload the Readings
            pusher.load_mappings()
            pusher.upload_readings(theHouse)

            #Now we need to check all the items arrived as expected
            source = self.sourcesession()
            sink = self.sinksession()

            sourceQry = source.query(models.Reading).all()
            sinkQry = sink.query(models.Reading).all()

            self.assertEqual(sourceQry,sinkQry)               
            
            

        #Cleanup
        theQry = session.query(models.Reading).delete()
        theQry = session.query(models.Location).delete()
        theQry = session.query(models.Node).delete()
        theQry = session.query(models.House).delete()
        theQry = session.query(models.Deployment).delete()
        session.commit()

        #Remote Session
        rsession = self.sinksession()
        theQry = rsession.query(models.Reading).delete()
        theQry = rsession.query(models.Location).delete()
        theQry = rsession.query(models.Node).delete()
        theQry = rsession.query(models.House).delete()
        theQry = rsession.query(models.Deployment).delete() 
        rsession.commit()

        return
