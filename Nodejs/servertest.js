var url = require('url');
var redis = require('redis');
var underscore =require('underscore');
var express = require('express');
var fs = require('fs');
var app = express()

var redis_port = 6379
var redis_host = 'localhost'
var redisclient = redis.createClient(redis_port, redis_host);
var subscribe_topic = 'zhihu'

var server = require('http').createServer(app);



var io = require('/usr/local/lib/node_modules/socket.io')(server);

app.use('/', express.static(__dirname + '/public'));
app.use('/front', express.static(__dirname + '/public/front_end.js')) // allocated an address for file in server.
app.use('/io', express.static('/usr/local/lib/node_modules/socket.io'))
app.post('*',function(request, response){
	if(request.method === 'POST'){
		var path = url.parse(request.url,true);
		console.log(path.path);
		var info = String(path.path).substring(1)
		var range = info.split('-');
		var start = range[0];
		var end = range[1];
		console.log('Get range' + ' ' + range[0]+ ' ' + range[1]);
		redisclient.zrevrange('zhihu', start, end, 'withscores', function(err, members) {
        // the resulting members would be something like
        // ['userb', '5', 'userc', '3', 'usera', '1']
        // use the following trick to convert to
        // [ [ 'userb', '5' ], [ 'userc', '3' ], [ 'usera', '1' ] ]
        // learned the trick from
        // http://stackoverflow.com/questions/8566667/split-javascript-array-in-chunks-using-underscore-js
    		var lists=underscore.groupBy(members, function(a,b) {
        		return Math.floor(b/2);
    		});
    		console.log( underscore.toArray(lists) );
    		response.writeHead(200, {"Content-Type": "application/json"});
    		var json = JSON.stringify({lists});
    		io.emit(json)
		});
	}
})


server.listen(5000, '127.0.0.1');

// Server do not allowed client to visit its file system. In order to provide the file, this file 
//should firstly added in server. That means, we cannot access the file use http://localhost/path/to/file



/*
function (request, response){
	if(request.method === "GET"){
		fs.readFile(__dirname + '/public/index.html',function(err, html){
			if(err){
				throw err;
			}
			response.writeHeader(200,{"Content-Type": "text/html"});
			response.write(html);
			response.end();
		});
	}
	if(request.method === 'POST'){
		var path = url.parse(request.url,true);
		console.log(path.path);
		var info = String(path.path).substring(1)
		var range = info.split('-');
		var start = range[0];
		var end = range[1];
		console.log('Get range' + ' ' + range[0]+ ' ' + range[1]);
		redisclient.zrevrange('zhihu', start, end, 'withscores', function(err, members) {
        // the resulting members would be something like
        // ['userb', '5', 'userc', '3', 'usera', '1']
        // use the following trick to convert to
        // [ [ 'userb', '5' ], [ 'userc', '3' ], [ 'usera', '1' ] ]
        // learned the trick from
        // http://stackoverflow.com/questions/8566667/split-javascript-array-in-chunks-using-underscore-js
    		var lists=underscore.groupBy(members, function(a,b) {
        		return Math.floor(b/2);
    		});
    		console.log( underscore.toArray(lists) );
    		response.writeHead(200, {"Content-Type": "application/json"});
    		var json = JSON.stringify({lists});
    		io.emit(json)
		});
	}
}


var server = http.createServer(function (request, response){
	if(request.method === "GET"){
		var path = url.parse(request.url,true);
		var info = String(path.path).substring(1)
		var range = info.split('-');
		var start = range[0];
		var end = range[1];
		console.log('Get range' + ' ' + range[0] + ' ' + range[1]);
		redisclient.zrevrange('zhihu', start, end, 'withscores', function(err, members) {
        // the resulting members would be something like
        // ['userb', '5', 'userc', '3', 'usera', '1']
        // use the following trick to convert to
        // [ [ 'userb', '5' ], [ 'userc', '3' ], [ 'usera', '1' ] ]
        // learned the trick from
        // http://stackoverflow.com/questions/8566667/split-javascript-array-in-chunks-using-underscore-js
    		var lists=underscore.groupBy(members, function(a,b) {
        		return Math.floor(b/2);
    		});
    		console.log( underscore.toArray(lists) );
    		response.writeHead(200, {"Content-Type": "application/json"});
    		var json = JSON.stringify({lists});
    		response.end(json);
		});
	}
});

var io = require('/usr/local/lib/node_modules/socket.io').listen(server)

server.listen(5000);

*/