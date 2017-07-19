# Zhihu Crawler

1. The zhihu crawler contains User_id_collector.py,  zhihu_user_info_collector.py,  zhihu_user_processing.py, zhihu_crawler.ini
2. User_id_collector.py fetch people's ID which used to form a url, which we could get user information from.
zhihu_user_info_collector.py is used to fetch user information such as name, headline, education background, work information and followship. The basic information are stored in cassandra and followship information are send to kafka.
3. zhihu_user_processing.py read data from kafka can calculate the average following people and followees of users.
4. zhihu_crawler.ini is a config file for this program.

## Basic Idea
The basic idea is extract data from users' following page including the people's ID that this user is following and we can also get user's basic info from this page.


## Problem and Solutions

[Problem 1] Get html file from web server.
Problem Description: When try to connect to zhihu, I used urllib2 and requset, however, both received error message.  urllib2 I got errono 111, and for request, I get requests response 500. How ever I could open this website in Browser and in postman. 

Reason and Solution:
In browser, the headers would be added in a http requests. Some web server would check headers to find if requests come from real browsers. 
By using package requests, we can set headers and add it in requests and pretend we are browsers.

Further improvement: I just found that some users' pages are set not allowed to read unless logging in. So cookies are necessary to add.


[Problem 2] How to parse data
In a zhihu webpage, only part of data right in html, and others are formed by javascript. So I cannot use BeautifulSoup to extract data directly.  There are also some info contained in comment part of a html file, how to parse those info efficiently ? 
Possible Solutions:
The possible solution is that: 
1. parse the data manually. by split the file and desigh a way to extract the data.
2. Use some tools such as PyV8, or PhantomJs to build a js env and form the full page, and extract data from the full page. However, this solution will cost huge sources.
3. Maybe the best way. Read the js code, analysis it and send request directly and to get the data.


[Problem 3] Remove duplicate
Problem Discription:  Different users can follow same guys, that means we could get an ID for mutiple times. 
Possible Solution: In order to parse a same user only once, I stored data in cassandra, which basicly use hash to store and find a row of data. I stored all the IDs in a table in two cassandra tables, one is to store IDs that we don't use, and another stores used IDs.  By checking this two table, we can simply remove duplicate IDs.  

Further question: how does a crawler remove duplicate in industry? I find that the crawler frame scrapy use hash set to remove duplicate, is cassandra a good solution if the amount of data keep growing ?


[Problem 4] The in coordination of fetch IDs and user information.
Problem Discription: If a user follows many people, those people's IDs would distributed on different pages.  
```sh
For example:  User A - Following Page 1,
			  User A - Following Page 2,
			  User A - Following Page 3,
			  User A - Following Page 4. 
```
In this case, the crawler has to traverse all those pages to get all the IDs, but in this process, crawler would only get the user information of A.  So I decide to seperate this into two program, one fetch the IDs, another one to collect user information.

Further question and improvement: I find a possible solution is that send request for following information table from servers directly. But it seems that the web server has set the limitation to how many pieace of info we could get in one query ?  I am not sure, may be this is another way to improve this program.


[Problem 5] multi-threading or multi-processing or multi ? 
In zhihu's robot.txt crawler delay is set to 10. In case my IP is blocked, I used proxies. However I meet some prolem how to do that.
Firstly, I come up with scheduler, hope that would help me. But sooner, I find my IDs to visit are all stored in cassandra. If I use multi-thread, it could caused an ID being used for multiple times.
```sh
For example:
			thread A				table:      thread B
				|_____get________ >row 1			|
				| sleep				   ^			|
				|					   |___get______|
				|					   		thread B sleep
				|_______delete______>				|
									  <___delete____|
```
This is what I thought, would that truly happen?  Is that possible for cassandra to avoid that? 
In this problem, I find two possible solution:
1. Use a queue, to get data into a queue, every time the queue fetch IDs from cassandra, it delete those IDs. 
2. Use kafka partitions directly, and each thread read from a certain kafka partition. Then they would have no confliction.
My quesition is, which one is better? and what solution is used in practical usage? 


However, I find another problem.  The requests that connect to web server is not threading safe. And its possible they get message that designated to another thread if used.  
Possible Solution: I searched on the website, and I find distributed crawler is used at industral level. And it is also said the main part is asynchronous and non-block sockets are the solution. My question is that what solution is truly used in industry ?


[The most important question]
I'm not a cs students, and I know there is a lot of inapropiate way of coding and designing. Q A Q. Hope I could some adivce on this part.

Thank you soooooooo much! 
