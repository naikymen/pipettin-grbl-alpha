'use strict';

const express = require('express');
const pcrMix = require('../lib/pcrMix.js');
const router = express.Router();

function getUniqueName (name, count, fieldName, arr, noSpace) {
  const posibleName = name + (noSpace ? '' : ' ') + (count || '');
  for (let i = 0; i < arr.length; i++) {
    if (arr[i][fieldName] === posibleName) {
      return getUniqueName(name, ++count, fieldName, arr, noSpace);
    }
  }
  return posibleName;
}

router.post('/test', function (req, res) {
  res.json({ok: 1});
});

router.get('/workspaces/:name', async function (req, res) {
  const name = req.params.name;
  const workspace = await req.db.workspaces.findOne({name});
  if (workspace) {
    for (let i = 0; i < workspace.items.length; i++) {
      workspace.items[i].platformData = await req.db.platforms.findOne({name: workspace.items[i].platform});
    }
    res.json(workspace);
  } else {
    res.json(false);
  }
});

router.get('/platforms/:name', async function (req, res) {
  const name = req.params.name;
  const p = await req.db.platforms.findOne({name});
  res.json(p);
});

router.post('/platforms', async function (req, res) {
  const platform = req.body;
  // TODO: validate input
  try {
    await req.db.platforms.insertOne(platform);
    res.json({ok: true});
  } catch (e) {
    if (e.code === 11000) {
      res.json({error: 'There is another platform with this name. Choose a different name.'});
      return;
    }
    res.json({error: 'Unexpected error creating the Platform.'});
  }
});

router.post('/hl-protocols', async function (req, res) {
  const hlProtocol = req.body;
  // TODO: validate input
  if (hlProtocol.template) {
    hlProtocol.templateDefinition = {};
  }
  try {
    await req.db.hLprotocols.insertOne(hlProtocol);
    const newProtocol = await req.db.hLprotocols.findOne({name: hlProtocol.name});
    console.log('newProtocol', newProtocol);
    res.json({ok: true, newProtocol});
  } catch (e) {
    if (e.code === 11000) {
      res.json({error: 'There is another protocol with this name. Choose a different name.'});
      return;
    }
    res.json({error: 'Unexpected error creating the protocol.'});
  }
});

async function createPlatformsForTemplate (field, data, workspace, offset, req) {
  const platformName = data.templateDefinition[field].split('_CREATE_')[1];
  const platformData = await req.db.platforms.findOne({name: platformName});
  const newName = getUniqueName(platformData.name, 1, 'name', workspace.items);
  workspace.items.push({
    'platform': platformData.name,
    'name': newName,
    position: {
      x: offset,
      y: offset
    },
    'content': [],
    platformData
  });
  data.templateDefinition[field] = newName;
}

router.put('/hl-protocols/:name', async function (req, res) {
  // TODO: validate input
  const data = req.body;
  const name = req.body.name;
  if (data._id) {
    delete data._id;
  }
  const workspace = await req.db.workspaces.findOne({name: data.workspace});
  for (let i = 0; i < workspace.items.length; i++) {
    workspace.items[i].platformData = await req.db.platforms.findOne({name: workspace.items[i].platform});
  }

  let workspaceEdited = false;

  if (data.isTemplate) {
    delete data.isTemplate;
    if (data.template && data.template === 'pcr_mix') {
      if (data.templateDefinition) {
        workspaceEdited = true;
        if (data.templateDefinition.tube15Platform.indexOf('_CREATE_') > -1) {
          await createPlatformsForTemplate('tube15Platform', data, workspace, 1, req);
        }
        if (data.templateDefinition.PCRtubePlatform.indexOf('_CREATE_') > -1) {
          await createPlatformsForTemplate('PCRtubePlatform', data, workspace, 10, req);
        }
        if (data.templateDefinition.tipsPlatform.indexOf('_CREATE_') > -1) {
          await createPlatformsForTemplate('tipsPlatform', data, workspace, 20, req);
        }
        if (data.templateDefinition.trashPlatform.indexOf('_CREATE_') > -1) {
          await createPlatformsForTemplate('trashPlatform', data, workspace, 30, req);
        }

        for (let i = 0; i < workspace.items.length; i++) {
          if (workspace.items[i].name === data.templateDefinition.tube15Platform) {
            workspace.items[i].content = [];
          }
          if (workspace.items[i].name === data.templateDefinition.PCRtubePlatform) {
            workspace.items[i].content = [];
          }
        }
        data.steps = []; // Delete all current steps
        await pcrMix.process(data, workspace);
      }
    }
  }

  try {
    await req.db.hLprotocols.updateOne({name}, {$set: data});
    const editedProtocol = await req.db.hLprotocols.findOne({name});
    const returnData = {
      ok: true,
      protocol: editedProtocol
    };
    if (workspaceEdited) {
      returnData.newWorkspace = workspace;
    }
    res.json(returnData);
  } catch (e) {
    res.json({error: 'Unexpected error saving Protocol.'});
  }
});

router.get('/hl-protocols/:name', async function (req, res) {
  const name = req.params.name;
  const hlprotocolData = await req.db.hLprotocols.findOne({name});
  if (hlprotocolData) {
    res.json(hlprotocolData);
  } else {
    res.json(false);
  }
});

router.delete('/platforms/:name', async function (req, res) {
  const name = req.params.name;
  // TODO: validate input
  try {
    await req.db.platforms.deleteOne({name});
    res.json({ok: true});
  } catch (e) {
    console.log(e);
    res.json({error: 'Unexpected error deleting the Platform.'});
  }
});

router.delete('/hl-protocols/:name', async function (req, res) {
  const name = req.params.name;
  // TODO: validate input
  try {
    await req.db.hLprotocols.deleteOne({name});
    res.json({ok: true});
  } catch (e) {
    console.log(e);
    res.json({error: 'Unexpected error deleting the Protocol.'});
  }
});

router.delete('/workspaces/:name', async function (req, res) {
  const name = req.params.name;
  // TODO: validate input
  try {
    await req.db.workspaces.deleteOne({name});
    res.json({ok: true});
  } catch (e) {
    console.log(e);
    res.json({error: 'Unexpected error deleting the Workspace.'});
  }
});

router.put('/platforms/:name', async function (req, res) {
  const name = req.params.name;
  const data = req.body;
  // TODO: validate input
  try {
    await req.db.platforms.updateOne({name}, {$set: data});
    res.json({ok: true});
  } catch (e) {
    console.log(e);
    res.json({error: 'Unexpected error updating the Platform.'});
  }
});

router.post('/workspaces/:name', async function (req, res) {
  // TODO: validate input
  const name = req.params.name;
  const data = req.body;
  data.name = name;
  if (data._id) {
    delete data._id;
  }

  if (data && data.items && data.items.length) {
    data.items.map(i => {
      delete i.platformData;
    });
  }
  try {
    await req.db.workspaces.updateOne({name}, {$set: data}, {upsert: true});
    const workspace = await req.db.workspaces.findOne({name});
    if (workspace) {
      for (let i = 0; i < workspace.items.length; i++) {
        workspace.items[i].platformData = await req.db.platforms.findOne({name: workspace.items[i].platform});
      }
      res.json({ok: true, data: workspace});
    } else {
      res.json({error: 'Unexpected error saving workspace. Error: 1.'});
    }
  } catch (e) {
    console.log(e);
    res.json({error: 'Unexpected error saving workspace. Error: 2.'});
  }
});

module.exports = router;
