"""

.. todo::

    Find out what this class is inteded to be used for


.. module:: host

.. codeauthor::  Ross Wiklins 
.. codeauthor::  James Brusey
.. codeauthor::  Daniel Goldsmith <djgoldsmith@googlemail.com>
"""

import sqlalchemy
import logging
log = logging.getLogger(__name__)

import meta
Base = meta.Base


class Host(Base):
    """
    Table to hold information about Hosts

    :var integer id: id (pk)
    :var string hostname: name
    :var DateTime lastupdate: lastupdate   
    """


    __tablename__ = "Host"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    hostname = sqlalchemy.Column(sqlalchemy.String(255))
    lastupdate = sqlalchemy.Column(sqlalchemy.DateTime)
        
