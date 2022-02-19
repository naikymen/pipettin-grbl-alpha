const express = require('express');
const router = express.Router();
const SerialPort = require('serialport');

router.get('/', function (req, res) {
  res.render('home', {title: ''});
});

router.get('/ping', function (req, res) {
  res.send({pong: new Date()});
});

router.get('/platforms-list', async function (req, res) {
  const list = await req.db.platforms.find({}).toArray();
  res.render('platformsList', {list});
});

router.get('/platforms-edit/:name', async function (req, res) {
  const name = req.params.name;
  const data = await req.db.platforms.findOne({name});
  if (data && data._id) {
    delete data._id;
  }
  res.render('platformsEdit', {mode: 'edit', data});
});

router.get('/protocol-template-edit/:name', async function (req, res) {
  const protocolName = req.params.name;
  const protocol = await req.db.hLprotocols.findOne({name: protocolName});
  const workspace = await req.db.workspaces.findOne({name: protocol.workspace});
  const platforms = await req.db.platforms.find({}).toArray();
  if (workspace && workspace.items && workspace.items.length) {
    for (let i = 0; i < workspace.items.length; i++) {
      workspace.items[i].platformData = await req.db.platforms.findOne({name: workspace.items[i].platform});
    }
  }
  if (protocol && protocol._id) {
    delete protocol._id;
  }

  /*
  console.log('=====workspace==========');
  console.log(workspace);
  console.log('====/workspace===========');

  console.log('======platforms=========');
  console.log(platforms);
  console.log('======/platforms=========');

  console.log('======protocol=========');
  console.log(protocol);
  console.log('======/protocol=========');
  */

  res.render('protocolPanel/protocolTemplateEdit', {mode: 'edit', protocol, workspace, platforms});
});

router.post('/workspace-panel', async function (req, res) {
  const workspace = req.body.workspace;
  const collapseStatus = req.body.collapseStatus;
  // const data = await req.db.platforms.findOne({name});
  if (workspace && workspace.items && workspace.length) {
    for (let i = 0; i < workspace.items.length; i++) {
      workspace.items[i].platformData = await req.db.platforms.findOne({name: workspace.items[i].platform});
    }
  }
  res.render('workspacePanel', {workspace, collapseStatus});
});

router.post('/protocol-panel', async function (req, res) {
  const workspace = req.body.workspace;
  const activeProtocol = req.body.activeProtocol;
  const protocolPanelExpandStatus = req.body.protocolPanelExpandStatus;
  // const data = await req.db.platforms.findOne({name});
  if (workspace && workspace.items && workspace.length) {
    for (let i = 0; i < workspace.items.length; i++) {
      workspace.items[i].platformData = await req.db.platforms.findOne({name: workspace.items[i].platform});
    }
  }
  const workspaceHLprotocols = await req.db.hLprotocols.find({workspace: workspace.name}).toArray();
  const allHLprotocols = await req.db.hLprotocols.find({}).toArray();
  res.render('protocolPanel', {workspace, allHLprotocols, workspaceHLprotocols, activeProtocol, protocolPanelExpandStatus});
});

router.post('/calibration-goto-panel', async function (req, res) {
  const workspace = req.body.workspace;
  const itemName = req.body.item;
  const platformName = req.body.platform;
  const content = req.body.content;
  // const data = await req.db.platforms.findOne({name});
  if (workspace && workspace.items && workspace.length) {
    for (let i = 0; i < workspace.items.length; i++) {
      workspace.items[i].platformData = await req.db.platforms.findOne({name: workspace.items[i].platform});
    }
  }

  res.render('calibrationGotoPanel', {workspace, content, platformName, itemName});
});

router.get('/platforms-edit/', async function (req, res) {
  res.render('platformsEdit', {mode: 'create'});
});

router.get('/platforms-dropdown', async function (req, res) {
  const data = await req.db.platforms.find({}).toArray();
  res.render('platformsDropdown', {data});
});

router.get('/serialports-dropdown', async function (req, res) {
  SerialPort.list().then(list => {
    if (list && list.length) {
      return list.filter(item => (item.manufacturer || '').indexOf('rduino') > -1 || (item.manufacturer || '').indexOf('FTDI') > -1);
    }
    return [];
  }).then(ports => {
    res.render('serialportsDropdown', {data: ports});
  }).catch(() => {
    res.render('serialportsDropdown', {data: []});
  });
});

router.get('/workspaces-list', async function (req, res) {
  const list = await req.db.workspaces.find({}).toArray();
  res.render('workspacesList', {list});
});

module.exports = router;
