"""
Functions to test the timing decorator function
"""

import sqlalchemy
import unittest
#import cogentviewer.tests.base as base

import time

import cogent
import cogent.base.model as models
import cogent.base.model.meta as meta   
#import models as models
#import models.meta as meta
#Unfortunately, due to the commit magic in the base test case, 
#This needs a seperate database, ottherwsie changes cannot be committed.

engine = sqlalchemy.create_engine("sqlite:///timings.db")
meta.Base.metadata.bind = engine

meta.Base.metadata.create_all(engine)  

class timingTest(unittest.TestCase):
    #We first need a function to test the dectorator

    @models.timings.timed
    def theFunc(self,sleeptime):
        print "Starting {0}".format(sleeptime)
        time.sleep(sleeptime)
        print "Done"

    @models.timings.timedtext("Func2")
    def theFuncTwo(self,sleeptime):
        time.sleep(sleeptime)
        print "f2"
        

    def testTimer(self):
        for x in range(2):
            print x
            self.theFunc(x)

        #Then check if the things are store
        print "----- QUERY ----"
        session = meta.Session()
        theQry = session.query(models.Timings)
        for item in theQry:
            print "--> {0}".format(item)

        session.flush()
        session.close()

    def testTimerTwo(self):
        for x in range(5):
            print x
            print self.theFuncTwo(x)
        
        
