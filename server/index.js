var express = require('express');
var app = express();
var sqlite3 = require('sqlite3').verbose();
var db = new sqlite3.Database('../database.db');

app.get('/', function (req, res) {
  res.header("Access-Control-Allow-Origin", "*");
  db.all("SELECT * FROM services", function(err, allRows) {
    res.send(allRows);
  });
});

app.listen(3000, function () {
  console.log('App listening on port 3000!');
});
