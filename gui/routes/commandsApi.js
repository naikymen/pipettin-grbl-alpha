'use strict';

const express = require('express');
const getMainHelper = require('../lib/mainHelper');
const getCommander = require('../lib/commander');
const getProtocolBuilder = require('../lib/protocolBuilder');
const router = express.Router();
const mainHelper = getMainHelper();

router.post('/kill', async function (req, res) {
  const commander = getCommander(req);
  commander.kill();
  res.json({ok: true, killed: true});
});

router.post('/goto', async function (req, res) {
  // TODO: validate input
  const workspace = req.body.workspace;
  const itemName = req.body.itemName;
  const contentName = req.body.contentName;
  const port = req.body.port;
  const baudrate = req.body.baudrate;

  try {
    const workspaceData = await req.db.workspaces.findOne({name: workspace.name});

    if (workspaceData) {
      const itemData = mainHelper.getItem(itemName, workspaceData);
      if (itemData) {
        const contentData = mainHelper.getContent(contentName, itemData);
        if (contentData) {
          const commander = getCommander(req);
          commander.runCalibrationCommand('goto', port, port, baudrate, workspaceData.name, itemData.name, contentData.name);
          res.json({ok: true, console: true});
        } else {
          res.json({error: 'Error executing command: content not found. Error 3.'});
        }
      } else {
        res.json({error: 'Error executing command: item not found. Error 3.'});
      }
    } else {
      res.json({error: 'Error executing command: workspace not found. Error 2.'});
    }
  } catch (e) {
    console.log(e);
    res.json({error: 'Unexpected error executing command. Error: 1.'});
  }
});

router.post('/move', async function (req, res) {
  // TODO: validate input
  const port = req.body.port;
  const baudrate = req.body.baudrate;
  const axis = req.body.axis;
  const distance = req.body.distance;

  try {
    const commander = getCommander(req);
    const args = {
      port,
      baudrate,
      'move': axis,
      distance
    };

    commander.runCommand(args);
    res.json({ok: true, console: true});
  } catch (e) {
    console.log(e);
    res.json({error: 'Unexpected error executing `move` command. Error: 1.'});
  }
});

router.post('/home', async function (req, res) {
  // TODO: validate input
  const port = req.body.port;
  const baudrate = req.body.baudrate;
  const axis = req.body.axis;

  try {
    const commander = getCommander(req);
    const args = {
      port,
      baudrate,
      'home': axis
    };

    commander.runCommand(args);
    res.json({ok: true, console: true});
  } catch (e) {
    console.log(e);
    res.json({error: 'Unexpected error executing `home` command. Error: 1.'});
  }
});

router.post('/execute-protocol', async function (req, res) {
  // TODO: validate input
  const port = req.body.port;
  const baudrate = req.body.baudrate;
  const workspaceName = req.body.workspaceName;
  const hlp = req.body.hlp;
  const output = req.body.output;

  try {
    const workspace = await req.db.workspaces.findOne({name: workspaceName});
    if (workspace) {
      for (let i = 0; i < workspace.items.length; i++) {
        workspace.items[i].platformData = await req.db.platforms.findOne({name: workspace.items[i].platform});
      }
      const pb = getProtocolBuilder();
      const middleLevelProtocol = await pb.build(hlp, workspace);
      if (middleLevelProtocol) {
        await req.db.protocols.insertOne(middleLevelProtocol);
        if (!output) {
          const commander = getCommander(req);
          const args = {
            port,
            baudrate,
            'run-protocol': middleLevelProtocol.name
          };
          commander.runCommand(args);
        }
      }

      res.json({ok: true, console: true, middleLevelProtocol, output});
    } else {
      res.json({error: 'Workspace not found.'});
    }
  } catch (e) {
    console.log(e);
    res.json({error: 'Unexpected error executing protocol. Error: 1.'});
  }
});

module.exports = router;
