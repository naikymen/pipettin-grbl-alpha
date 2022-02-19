const express = require('express');
const path = require('path');
const logger = require('morgan');
const cookieParser = require('cookie-parser');
const bodyParser = require('body-parser');
const basicAuth = require('basic-auth');
const config = require('config');
const mongo = require('mongodb').MongoClient;
let db;

mongo.connect(config.mongo, {useUnifiedTopology: true}, async function (err, database) {
  if (err) {
    console.log(err);
    process.exit();
  }
  db = database.db('pipettin');
  db.createIndex('platforms', {'name': 1}, {unique: true});
  db.createIndex('workspaces', {'name': 1}, {unique: true});
  db.createIndex('protocols', {'name': 1}, {unique: true});
  db.createIndex('hLprotocols', {'name': 1}, {unique: true});
  db.platforms = db.collection('platforms');
  db.workspaces = db.collection('workspaces');
  db.protocols = db.collection('protocols');
  db.hLprotocols = db.collection('hLprotocols');
});

const indexRoute = require('./routes/index');
const apiRoute = require('./routes/mainApi');
const commandsRoute = require('./routes/commandsApi');

const app = express();

// Authentication handler
const basicAuthUser = process.env.BASIC_AUTH_USER || config.basicAuthUser;
const basicAuthPass = process.env.BASIC_AUTH_PASS || config.basicAuthPass;
const publicRoutes = [];

const authHandler = function (req, res, next) {
  // Allow if basic auth is not enabled
  if (!basicAuthUser || !basicAuthPass) return next();

  // Allow whitelisted public routes
  if (publicRoutes.indexOf(req.path) > -1) return next();

  function unauthorized (res) {
    res.set('WWW-Authenticate', 'Basic realm=Authorization Required');
    return res.sendStatus(401);
  }

  // Get basis auth credentials
  const user = basicAuth(req);
  if (!user || !user.name || !user.pass) {
    return unauthorized(res);
  }

  // Check credentials
  if (user.name === basicAuthUser && user.pass === basicAuthPass) {
    return next();
  }

  return unauthorized(res);
};

const dbHandler = function (req, res, next) {
  req.db = db;
  req.io = app.get('io');
  next();
};

app.set('views', path.join(__dirname, 'views'));
app.set('view engine', 'ejs');
app.use(logger('dev'));
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: false }));
app.use(cookieParser());
app.use(express.static(path.join(__dirname, 'public')));
app.use(authHandler);
app.use(dbHandler);
app.set('etag', false);

app.use('/', indexRoute);
app.use('/api', apiRoute);
app.use('/api/run-command', commandsRoute);

// error handlers
// catch 404 and forward to error handler
app.use(function (req, res, next) {
  const err = new Error('Endpoint not found...');
  err.status = 404;
  next(err);
});

// development error handler
// will print stacktrace
if (app.get('env') === 'development') {
  app.use(function (err, req, res) {
    console.log('==============dev handler=======', err);
    res.status(err.status || 500);
    res.send({
      message: err.message
      // error: err
    });
  });
}

// production error handler
// no stacktraces leaked to user
app.use(function (err, req, res) {
  console.log('================prod handler=====');
  res.status(err.status || 500);
  res.send({
    message: err.message
    // error: {}
  });
});

module.exports = app;
