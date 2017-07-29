/*
$(function(){
	var start = 0;
	var end = 0;
	$("#check-user-button").click(function(){
		"use strick"
		xhr = new XMLHttpRequest();
		var range = parseInt(range[0]);
		start = parseInt(rang[0]);
		end = parseInt(range[1]);
		var url = 'localhost:5000/' + range[0] + '-' + range[1];
		xhr.open('GET', url, true);
		xhr.onreadystatechange = function(){
			if(xhr.readystate == 4 && xhr.status == 200){
				console.log(xhr.responseText);
			}
		}
		xhr.send();


		var myArray = new Array(10);
        var zhihu_user_table = "<table class='table table-bordered'><thead class='thead-inverse'>";
        zhihu_user_table+="<tr><th>#</th><th>User Name</th><th>User ID</th><th>Followees</th></tr></thead><tbody>";
        for (var i=0; i < myArray.length; i++) {
            zhihu_user_table+="<tr><th scope='row'>"+ (i + 1) + "</th><td></td><td></td><td></td></tr>";
        }
        zhihu_user_table+="</tbody></table>";
		$("#tables").append(zhihu_user_table);
	});

	function createtable() {
	// body...

	var myArray = new Array(8);
    var zhihu_user_table = "<table class='table table-bordered' id = 'user-table'><thead class='thead-inverse'>";
    zhihu_user_table+="<tr><th>#</th><th>User Name</th><th>User ID</th><th>Followees</th></tr></thead><tbody>";
    for (var i=0; i < myArray.length; i++) {
        zhihu_user_table+="<tr><th scope='row'>"+ (i + 1) + "</th><td></td><td></td><td></td></tr>";
    }
    zhihu_user_table+="</tbody></table>";
    document.getElementById("tables").innerHTML = zhihu_user_table;

    function(){
		"use strick"
		$.ajax({
			url = 'localhost:5000';
			type: 'GET'
		}
}
});
*/




$(function(){

	$("#check-user-button").click(function(){
		var range = $('#range').val();
		var xhttp = new XMLHttpRequest();
		xhttp.open('POST' ,'http://localhost:5000/1-20' , true);

		xhttp.send()

		$('#range').val("");

		var myArray = new Array(8);
    	var zhihu_user_table = "<table class='table table-bordered' id = 'user-table'><thead class='thead-inverse'>";
    	zhihu_user_table+="<tr><th>#</th><th>User Name</th><th>User ID</th><th>Followees</th></tr></thead><tbody>";
    	for (var i=0; i < myArray.length; i++) {
    	    zhihu_user_table+="<tr><th scope='row'>"+ (i + 1) + "</th><td></td><td></td><td></td></tr>";
    	}
    	zhihu_user_table+="</tbody></table>";
   		document.getElementById("tables").innerHTML = zhihu_user_table;
   		//Note: I used append here, but when i click check twice, it created another table below the original one.
   		//And here is the solution to that question.
	});

	function createtable() {

		var myArray = new Array(8);
    	var zhihu_user_table = "<table class='table table-bordered' id = 'user-table'><thead class='thead-inverse'>";
    	zhihu_user_table+="<tr><th>#</th><th>User Name</th><th>User ID</th><th>Followees</th></tr></thead><tbody>";
    	for (var i=0; i < myArray.length; i++) {
    	    zhihu_user_table+="<tr><th scope='row'>"+ (i + 1) + "</th><td></td><td></td><td></td></tr>";
    	}
    	zhihu_user_table+="</tbody></table>";
   		document.getElementById("tables").innerHTML = zhihu_user_table;
   		//Note: I used append here, but when i click check twice, it created another table below the original one.
   		//And here is the solution to that question.
   	}

   	function newDataCallback(message){
   		var parsed = JSON.parse(message);
   		console.log(parsed);
   	}

   	var sockets = io();

   	sockets.on('data', function (data) {
    	newDataCallback(data);
    });

});