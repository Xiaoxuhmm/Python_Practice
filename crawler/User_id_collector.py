import argparse
import requests
import logging
import atexit
import time

from sets import Set
from bs4 import BeautifulSoup as bs
from cassandra.cluster import Cluster
from requests import RequestException
from ConfigParser import SafeConfigParser



logging.basicConfig()
logger = logging.getLogger('user_id_collector.py')
logger.setLevel(logging.DEBUG)

def shutdown_hook():
    try:
        logger.info('Closing Cassandra Session')
        session.shutdown()
        logger.info('Cassandra Session closed')
    except Exception as e:
        logger.warn('Failed to close kafka connection, caused by: %s', e.message)

def data_clean(html):
    strs = html.split(';');
    cleaned_data = Set()
    chars = Set("{}=/:,")
    for str in strs:
        if '-' in str and 'http' not in str and 'div' not in str:
            str = str[0: -5]
            if any((c in chars) for c in str):
                continue
            else:
                if str == 'vote-thank':
                    continue
                if len(str) > 30:
                    continue
                cleaned_data.add(str)
    for user in cleaned_data:
        check_unprocessed_data = session.execute("SELECT * FROM %s WHERE user_id = '%s'" %(unprocessed_data, user))
        if not check_unprocessed_data:
            check_processed_data = session.execute("SELECT * FROM %s WHERE user_id = '%s'" %(processed_data, user))
            if not check_processed_data:
                try:
                    session.execute("INSERT INTO %s (user_id) VALUES('%s')" %(unprocessed_data, user))
                    session.execute("INSERT INTO %s (user_id) VALUES('%s')" %(data_for_info_collector, user))
                    logger.debug("write user_id to cassandra")
                    logger.debug('user_id is %s' %user)
                except Exception as e:
                    logger.warn('Failed write user_id to cassandra, caused by %s', e.message)
    


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('config_file', help = 'the location to config file')

    args = parser.parse_args()
    config_file = args.config_file
    logger.info('Get config file location %s' %config_file)

    logger.info('Start to config file')
    config_parser = SafeConfigParser()
    config_parser.read(config_file)

    contact_points = config_parser.get('USER_INFO_COLLECTOR','CONTACT_POINTS')
    keyspace = config_parser.get('USER_ID_COLLECTOR','KEYSPACE')
    processed_data = config_parser.get('USER_ID_COLLECTOR','PROCESSED_DATA')
    unprocessed_data = config_parser.get('USER_ID_COLLECTOR','UNPROCESSED_DATA')
    data_for_info_collector = config_parser.get('USER_ID_COLLECTOR','DATA_FOR_INFO_COLLECTOR')

    headers = {
    'User-Agent': config_parser.get('HEADERS_MESSAGE','USER_AGENT'),
    'Host': config_parser.get('HEADERS_MESSAGE','HOST'),
    'Referer': config_parser.get('HEADERS_MESSAGE','REFERER'),
    'authorization': config_parser.get('HEADERS_MESSAGE', 'AUTHORIZATION')
    }

    try:
        logger.info('start cassandra')
        cluster = Cluster(contact_points = contact_points.split(','))
        session = cluster.connect()
        session.execute("CREATE KEYSPACE IF NOT EXISTS %s WITH replication = {'class':'SimpleStrategy', 'replication_factor':'3'}" %keyspace)
        session.set_keyspace(keyspace)
        session.execute("CREATE TABLE IF NOT EXISTS %s (user_id text, PRIMARY KEY (user_id))" % processed_data)
        session.execute("CREATE TABLE IF NOT EXISTS %s (user_id text, PRIMARY KEY (user_id))" % unprocessed_data)
        logger.info('Cassandra started, keyspace and table are ready')
    except Exception as e:
        logger.warn('Failed to start Cassandra, caused by %s', e.message)



    atexit.register(shutdown_hook)

    max_page = None
    user_id = ''

    while True:
        select_result = session.execute("SELECT user_id FROM %s LIMIT 1" %unprocessed_data)
        user_id = select_result.__getitem__(0).__getnewargs__()[0]
        max_page = 1
        page  = 1

        try:
            while page <= max_page:
                try:
                    url = 'https://www.zhihu.com/people/' + user_id +'/following?page=' + '%d' %page
                    logger.info('Start to get info of user %s on page %d' %(user_id, page))
                    try:
                        response = requests.get(url, headers = headers, timeout = 5)
                        if response.status_code is not 200:
                            session.execute("DELETE FROM %s WHERE user_id = '%s'" %(unprocessed_data, user_id))
                            time.sleep(20)
                            continue
                        webpage = response.text
                    except RequestException as re:
                        logger.warn('Failed to get response from web server, caused by %s' %re.message)
                        time.sleep(20)
                        continue
                    if page is 1:
                        soup = bs(webpage, 'html.parser')
                        soup.prettify()
                        try: 
                            max_page = int(soup.find_all(class_='Button PaginationButton Button--plain')[-1].next_element)
                        except Exception:
                            max_page = 1    
                        logger.info('max page is %d' %max_page)
                    try:
                        logger.debug('Start to clean data')
                        data_clean(webpage)
                        logger.info('Get following user_ids on page %s' %page)
                    except Exception as e:
                        logger.warn('Failed to get user_ids on page %s' %page)
                        time.sleep(20)
                        continue
                except Exception as e:
                    logger.warn('Failed to get user_ids, caused by %s', e.message)
                    time.sleep(20)
                    continue
                time.sleep(20)
                page = page + 1
        except Exception as e:
            logger.warn('Failed to get following info of user %s' %user_id)
            time.sleep(20)
            continue
        try:
            session.execute("DELETE FROM %s WHERE user_id = '%s'" %(unprocessed_data, user_id))
            session.execute("INSERT INTO %s (user_id) VALUES ('%s')" %(processed_data, user_id))
        except Exception as e:
           logger.warn('Failed to delete processed user_id, caused by %s', e.message)
    
    

    # Get the max number of pages this user's following info has

    
    
    