"""

  User_id_collector:
                     ________________________________________________________                                       
                    V                                                       ^
             User_id: (read from cassandra)  ==>  get followees' ids ==> send to Kafka 
                        ensure no duplicate                                 |
  User_info_collector:                                                      |
                                        get basic user info     <=== read from kafka        
                                                |__
                                                    |    ==>            send to kafka
                                                                            |
  Spark Data Processor                              read from kafka    <____|
                                                                            |
        store in cassandra for further use  <===    read from kafka    <____|

"""
import argparse
import requests
import logging
import time
import atexit
import json

from sets import Set
from kafka import KafkaProducer
from kafka.errors import KafkaError
from bs4 import BeautifulSoup as bs
from cassandra.cluster import Cluster
from requests import RequestException
from ConfigParser import SafeConfigParser


logging.basicConfig()
logger = logging.getLogger('zhihu user info collector')
logger.setLevel(logging.INFO)

#Because requests is not thread safe, thus i don't use it. Or Processing can be used.

def shutdown_hook():
    try:
        logger.info('Flushing pending message to kafka,timeout is set to 10s')
        producer.flush(10)
        logger.info('Finish flushing pending messages to kafka')
    except KafkaError as ke:
        logger.warn('Failed to flush pending messages to kafka, cuased by: %s', ke.message)
    finally:
        try:
            logger.info('Closing Cassandra Session')
            session.shutdown()
            logger.info('Cassandra Session closed')
        except Exception as e:
            logger.warn('Failed to close kafka connection, caused by: %s', e.message)


class Crawler:
    user_id = ''
    url = ''
    proxies = ''
    headers = ''

    # kafka topics:
    user_info_topic = ''
    followship_topic = ''

    # Cassandra tables
    data_table = ''
    unprocessed_data = ''

    user_name = ''
    user_gender = ''
    user_headline = ''
    user_work_info = ''
    user_edu_info = ''
    user_following = 0
    user_followers = 0


    def __init__(self, user_id, proxy, headers, user_info_topic, followship_topic, data_table, unprocessed_data):
        self.user_id = user_id
        self.headers = headers
        self.proxies = {'http': proxy}
        self.url = 'https://www.zhihu.com/people/' + user_id +'/following?page=1'

        self.user_info_topic = user_info_topic
        self.followship_topic = followship_topic

        self.data_table = data_table
        self.unprocessed_data = unprocessed_data



    def info_collector(self, session):
        try:
            logger.debug('Start to get connection to zhihu')
            response = requests.get(self.url, headers = self.headers, proxies = self.proxies, timeout = 5)
            if response.status_code is not 200:
                logger.warn('Cannot get user info due to response code %d' %response.status_code)
                return
            logger.debug('Get response from zhihu!')
        except RequestException as re:
            logger.warn('Failed to get connection to web server, caused by: %s', re.message)
            return

        html = html = response.text
        soup = bs(html, 'html.parser')
        soup.prettify()

        try: 
            self.user_name = soup.find(class_='ProfileHeader-name').next_element
            logger.debug('Get user name')
            if soup.find(class_='Icon Icon--male'):
                self.user_gender = 'male'
            else:
                self.user_gender = 'female'
            logger.debug('Get user gender')
            if len(repr(soup.find(class_='RichText ProfileHeader-headline').next_element)) < 300:
                self.user_headline = soup.find(class_='RichText ProfileHeader-headline').next_element
                logger.debug('Get user headline')
            else:
                logger.info('User headline is set to null due to headline out of range!')
            user_info_tags = soup.find_all(class_='ProfileHeader-infoItem')
            try:
                self.user_work_info = user_info_tags[0].get_text()
            except Exception:
                logger.info('Cannot get user work info')
            try:
                self.user_edu_info = user_info_tags[1].get_text()  # stand for user education background
            except Exception:
                logger.info('Cannot get user education background')     
            try:
                self.user_work_info = user_info_tags[0].get_text()
            except Exception:
                logger.info('Cannot get user work info')
            try:
                self.user_edu_info = user_info_tags[1].get_text()
            except Exception:
                logger.info('Cannot get user education background')
            try:
                self.user_following = int(soup.find(class_='NumberBoard FollowshipCard-counts').contents[0].find(class_='NumberBoard-value').next_element)
                self.user_followers = int(soup.find(class_='NumberBoard FollowshipCard-counts').contents[2].find(class_='NumberBoard-value').next_element)
                logger.debug('Get user followship info')
            except Exception:
                logger.info('Cannot get user followship info')
        except Exception as e:
            logger.warn('Failed to collect user info, caused by %s' %e.message)
        try:
            session.execute("DELETE FROM %s WHERE user_id = '%s'" %(self.unprocessed_data, self.user_id))
        except Exception:
            logger.warn('Failed to delete processed user_id %s' %self.user_id)
    
    def send_to_kafka(self, producer):
        user_basic_info = {'user_id':'%s' %self.user_id, 
                           'user_name':'%s' %self.user_name, 
                           'user_headline':'%s' %self.user_headline, 
                           'user_work_info':'%s' %self.user_work_info,
                           'user_edu_info': '%s' %self.user_edu_info
                           }
        user_data = json.dumps(user_basic_info)
        try:
            producer.send(topic = self.user_info_topic, value = user_data)
        except KafkaError as ke:
            logger.warn('Failed to send user_basic info to kafka, caused by %s', ke.message)

        following_info = {
            'item':'user_following', 'number': '%d' %self.user_following      
        }
        following = json.dumps(following_info)
        try:
            producer.send(topic = self.followship_topic, value = following)
        except KafkaError as ke:
            logger.warn('Failed to send user following info to kafka, caused by %s', ke.message)

        followers_info = {
            'item':'user_followers', 'number': '%d' %self.user_followers      
        } 
        followers = json.dumps(followers_info)
        try:
            producer.send(topic = self.followship_topic, value = followers)
        except KafkaError as ke:
            logger.warn('Failed to send user followers info to kafka, caused by %s', ke.message)

    def save_data(self, session):
        session.execute(
            "INSERT INTO %s (user_id, user_name, user_gender, user_headline, user_work_info, user_edu_info) VALUES('%s', '%s','%s','%s','%s','%s')" 
            % (self.data_table, self.user_id, self.user_name, self.user_gender, 
            self.user_headline, self.user_work_info, self.user_edu_info))



    


# Kafka config data: Can get config from file
kafka_broker = 'localhost:9092'
consumer_topic = 'zhuhu_user_id'  
user_info_topic = 'zhihu_user_info'
followship_topic = 'zhihu_user_followship'

# cassandra config data: Can get config from file
contact_points = 'localhost'
keyspace = 'zhihu_user_info'
data_table = 'user_basic_info'
unprocessed_data = 'unprocessed_user'

# Start cassandra
logger.debug('start cassandra')
cluster = Cluster(
  contact_points = contact_points.split(',')
)
session = cluster.connect()
session.execute("CREATE KEYSPACE IF NOT EXISTS %s WITH replication = {'class':'SimpleStrategy', 'replication_factor':'3'}" %keyspace)
session.set_keyspace(keyspace)
session.execute("CREATE TABLE IF NOT EXISTS %s (user_id text, user_name text, user_gender text, user_headline text, user_work_info text, user_edu_info text, PRIMARY KEY (user_id))" % data_table)
logger.debug('cassandra started, keyspace and table are ready')

# Start kafka
producer = KafkaProducer(bootstrap_servers = kafka_broker)

# Set headers for http requests: Can get config from file
headers = {
'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.104 Safari/537.36',
'Host':'www.zhihu.com',
'Referer':'https://www.zhihu.com',
'authorization':'oauth c3cef7c66a1843f8b3a9e6a1e3160e20'
}

# Set proxies for http requests: Can get config from file
proxies = {
    'http://180.180.49.24:8080',
    'http://218.92.219.86:8080',
    'http://121.30.197.38:8080',
    'http://113.140.43.136:80',
    'http://120.27.49.85:8090',
    'http://121.11.65.6:8080'
}

atexit.register(shutdown_hook)

while True:
    for proxy in proxies:
        user_id = ''
        select_result = session.execute("SELECT user_id FROM %s LIMIT 1" %unprocessed_data)
        try:
            user_id = select_result.__getitem__(0).__getnewargs__()[0]
        except Exception:
            logger.info('failed to get user_id')
        logger.info('Start to fetch information for user_id: %s' %user_id)
        crawler = Crawler(user_id, proxy, headers, user_info_topic, followship_topic, data_table, unprocessed_data)
        crawler.info_collector(session)
        crawler.save_data(session)
        crawler.send_to_kafka(producer)
        logger.info('User info collected.')
        time.sleep(4)
