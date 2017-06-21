import urllib2
import os
import yaml
import Queue
from sets import Set
from bs4 import BeautifulSoup as bs
import time

FILEPATH = os.path.expanduser('~') + '/cs105/course2/crawler/.crawler.yml'

class Crawler(object):
  urls = None
  q = None

  def __init__(self):
    self.q = Queue.Queue()
    self.urls = set()
    if os.path.isfile(FILEPATH):
      with open(FILEPATH, 'r+') as f:
        self.urls = set(yaml.load(f))
    else:
      self.urls.add(input('input begining url: '))
    for url in self.urls:
      self.q.put(url)

  def _save_to_file(self):
    with open(FILEPATH, 'w+') as f:
      yaml.dump(self.urls, f)

  def url_reader(self):
    url = self.q.get()
    self.urls.remove(url)
    response = urllib2.urlopen(url)
    html = response.read()
    soup = bs(html, 'html.parser')
    soup.prettify()
    for href in soup.find_all('a',href=True):
      self.urls.add(href['href'])
      self.q.put(href['href'])
    self._save_to_file()

  def display(self):
    if self.urls:
      print('here are the websites to crawl: ')
      for url in self.urls:
        print(url)

c = Crawler()
for i in range(10):
  c.url_reader()
  c.display()
  time.sleep(1)

