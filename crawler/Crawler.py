"""
Future tasks:
1. multithread: it seems that this process is not that safe for multithreading, for two threads can
   get the same url because after one thread get a url, this url is not automaticly deleted, thus 
   another thread can fetch the same url, but when deleting, the second one will have a problem that
   the url is already deleted by the first thread.

   Possible solution: maintain a queue, use pop() to get url and avoid the situation stated above.
   The queue would extract data from cassandra before the queue get empty.
"""


from cassandra.cluster import Cluster
from ConfigParser import SafeConfigParser
from sets import Set
from bs4 import BeautifulSoup as bs

import urllib2
import os
import yaml
import Queue
import time
import argparse
import logging


logging.basicConfig()
logger = logging.getLogger('Crawler')
logger.setLevel(logging.DEBUG)


def fetch_data(url, session, data_table, parsed_data_table):
  response = urllib2.urlopen(url)
  html = response.read()
  soup = bs(html,'html.parser')
  soup.prettify()
  for href in soup.find_all('a', href = True):
    website = href['href']
    if(website[0:4] == 'http'):
      check_parsed_data = session.execute("SELECT * FROM %s WHERE website = '%s'" %(parsed_data_table, website))
      if not check_parsed_data:
        check_data_table = session.execute("SELECT * FROM %s WHERE website = '%s'" %(data_table, website) )
        if not check_data_table:
          session.execute("INSERT INTO %s (website) VALUES ('%s')" %(data_table, website))
          logger.debug("%s is added to %s" %(website, data_table))
  logger.debug('hrefs stored into database')


def process_data(session,url,data_table,parsed_data_table):
  result = session.execute("SELECT website FROM %s LIMIT 1" %data_table)
  url = result.__getitem__(0).__getnewargs__()[0]
  fetch_data(url, session, data_table, parsed_data_table)
  session.execute("DELETE FROM %s WHERE website = '%s'" %(data_table, url))
  session.execute("INSERT INTO %s (website) VALUES ('%s')" %(parsed_data_table, url))
  logger.debug('%s is deleted from %s after processing' %(url, data_table))


logger.info('Start to parse data from config file')
parser = SafeConfigParser()
config_path = os.getcwd() + '/config.ini'
parser.read(config_path)

contact_points = parser.get('BASIC_CONFIG','CASSANDRA_CONTACT_POINTS')
keyspace = parser.get('BASIC_CONFIG', 'CASSANDRA_KEYSPACE')
data_table = parser.get('BASIC_CONFIG','DATA_TABLE')
parsed_data_table = parser.get('BASIC_CONFIG', 'PARSED_DATA_TABLE')
logger.info('Basic config updated')

logger.debug('start cassandra')
cluster = Cluster(
  contact_points = contact_points.split(',')
)
session = cluster.connect()
session.execute("CREATE KEYSPACE IF NOT EXISTS %s WITH replication = {'class':'SimpleStrategy', 'replication_factor':'3'}" %keyspace)
session.set_keyspace(keyspace)
session.execute("CREATE TABLE IF NOT EXISTS %s (website text, PRIMARY KEY (website))" % data_table)
session.execute("CREATE TABLE IF NOT EXISTS %s (website text, PRIMARY KEY (website))" % parsed_data_table)
logger.debug('cassandra started, keyspace and table are ready')

while True:
  result = session.execute("SELECT website FROM %s LIMIT 1" %data_table)
  url = result.__getitem__(0).__getnewargs__()[0]
  fetch_data(url, session, data_table, parsed_data_table)
  session.execute("DELETE FROM %s WHERE website = '%s'" %(data_table, url))
  session.execute("INSERT INTO %s (website) VALUES ('%s')" %(parsed_data_table, url))
  logger.debug('%s is deleted from %s after processing' %(url, data_table))
  time.sleep(1)
