/* global $ io d3 alert prompt FileReader confirm ace */

let socket;
const WORKAREA_WIDTH = 300;
const WORKAREA_HEIGHT = 200;

function init () {
  socket = io.connect();
  socket.on('welcome', function (data) {
    console.log(data);
  });
  loadSerialPorts();
  // loadWorkspace('pcrMixTestTemplateWorkspace');

  socket.on('console', function (consoleData) {
    const currentContent = $('#console').html();
    consoleData = escapeHtml(consoleData);
    $('#console').html(currentContent + consoleData);
    document.getElementById('console').scrollTop = document.getElementById('console').scrollHeight;

    console.log('consoleData', consoleData);
  });

  socket.on('human_intervention_required', function (data) {
    console.log('human intervention received!');
    $('#humanActionPanelData').html(data.text);
    $('#humanActionPanel').modal('show');
    console.log(data);
  });

  socket.on('alert', function (data) {
    console.log('alert received!');
    $('#protocol2codeSayPanelData').html(data.text);
    $('#protocol2codeSayPanel').modal('show');
    console.log(data);
  });

  socket.on('tool_data', function (data) {
    console.log('tool_data received!');
    $('#toolData').html(JSON.stringify(data));
    console.log(data);
  });
}

function escapeHtml (unsafe) {
  return unsafe
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function stopHumanIntervention () {
  $('#humanActionPanel').modal('hide');
  $('#humanActionPanelData').html('');
  socket.emit('human_intervention_cancelled', {});
}

function doneHumanIntervention () {
  $('#humanActionPanel').modal('hide');
  $('#humanActionPanelData').html('');
  socket.emit('human_intervention_continue', {});
}

function responsivefy (svg) {
  const container = d3.select(svg.node().parentNode);
  const width = parseInt(svg.style('width'), 10);
  const height = parseInt(svg.style('height'), 10);
  const aspect = width / height;
  svg.attr('viewBox', `0 0 ${width} ${height}`)
    .attr('preserveAspectRatio', 'xMinYMid')
    .call(resize);

  // add a listener so the chart will be resized
  // when the window resizes
  // multiple listeners for the same event type
  // requires a namespace, i.e., 'click.foo'
  // api docs: https://goo.gl/F3ZCFr
  d3.select(window).on(
    'resize.' + container.attr('id'),
    resize
  );
  function resize () {
    const w = parseInt(container.style('width'));
    svg.attr('width', w);
    svg.attr('height', Math.round(w / aspect));
  }
}

function pad (val, padStr) {
  const str = '' + val;
  const ans = padStr.substring(0, padStr.length - str.length) + str;
  return ans;
}

/*
function move(me) {
  var nx = d3.event.x-parseInt(d3.select(me).attr("width"))/2
  var ny = d3.event.y-parseInt(d3.select(me).attr("height"))/2
  d3.select(me).attr('x', nx).attr('y', ny);
}
*/

function updateCoordinates (x, y) {
  $('#coordinates').html(pad(parseInt(x), '0000') + ',' + pad(parseInt(y), '0000'));
}

function drawGrid (svgContainer, w, h, space) {
  const wdots = parseInt(w / space);
  const hdots = parseInt(h / space);
  let firstW = space;
  let firstH = space;
  for (let r = 0; r < hdots; r++) {
    for (let c = 0; c < wdots; c++) {
      svgContainer.append('rect')
        .attr('x', firstW)
        .attr('y', firstH)
        .attr('width', 0.3)
        .attr('height', 0.3)
        .attr('fill', '#000000');
      firstW = firstW + space;
    }
    firstW = space;
    firstH = firstH + space;
  }
}

function getItemByName (workspace, itemName) {
  if (workspace && workspace.items && workspace.items.length) {
    for (let i = 0; i < workspace.items.length; i++) {
      if (workspace.items[i].name === itemName) {
        return workspace.items[i];
      }
    }
  }
  return false;
}

function generateIdContent (item, content, prefix) {
  return (prefix || '') + item.name.split(' ').join('_').split('.').join('_') + item.platformData.name.split(' ').join('_').split('.').join('_') + content.name.split(' ').join('_').split('.').join('_');
}

function getContentByName (itemName, contentName) {
  itemName = decodeURI(itemName);
  contentName = decodeURI(contentName);
  const itemData = getItemByName(activeWorkspace, itemName);
  if (itemData && itemData.content && itemData.content.length) {
    for (let i = 0; i < itemData.content.length; i++) {
      if (itemData.content[i].name === contentName) {
        return itemData.content[i];
      }
    }
  }
}

function getUniqueName (name, count, fieldName, arr, noSpace) {
  const posibleName = name + (noSpace ? '' : ' ') + (count || '');
  for (let i = 0; i < arr.length; i++) {
    if (arr[i][fieldName] === posibleName) {
      return getUniqueName(name, ++count, fieldName, arr, noSpace);
    }
  }
  return posibleName;
}

function editPlatformWorkspaceName (name) {
  name = decodeURI(name);
  const newName = prompt('Enter a new name', name);
  if (newName === null) {
    return;
  }
  if (newName.trim() === '') {
    return;
  }

  const item = getItemByName(activeWorkspace, name);
  if (item) {
    item.name = getUniqueName(newName, 0, 'name', activeWorkspace.items, true);
    drawWorkspace(activeWorkspace);
  }
  console.log(item);
  console.log('Cambiar a:' + newName);
}

function deleteContent (itemName, contentName, redraw) {
  itemName = decodeURI(itemName);
  contentName = decodeURI(contentName);
  const itemData = getItemByName(activeWorkspace, itemName);
  if (itemData && itemData.content && itemData.content.length) {
    for (let i = 0; i < itemData.content.length; i++) {
      if (itemData.content[i].name === contentName) {
        console.log('borrar:');
        console.log(itemData.content[i]);
        itemData.content.splice(i, 1);
        if (redraw) {
          drawWorkspace(activeWorkspace);
        }
      }
    }
  }
}

let dr = true;
const dragcontainer = d3.drag()
  .on('drag', function (d) {
    if (dr === true) {
      d3.select(this).attr('transform', 'translate(' + (d.x = d3.event.x) + ',' + (d.y = d3.event.y) + ')');
      const item = getItemByName(activeWorkspace, d.name);
      if (item) {
        const x = item.position.x + d.x;
        const y = item.position.y + d.y;
        updateCoordinates(x, y);
      }
    } else {
      d3.select(window).on('.drag', null);
    }
  }).on('start', function (d) {
    dr = true;
    if (!d3.event.sourceEvent.target.__data__.dragAnchor) {
      dr = false;
      return;
    }
    // d3.select(this).raise().attr("stroke", "black");
  }).on('end', function (d) {
    console.log('end');
    if (dr === true) {
      const item = getItemByName(activeWorkspace, d.name);
      if (item) {
        item.position.x = parseInt(item.position.x + d.x);
        item.position.y = parseInt(item.position.y + d.y);
        drawWorkspace(activeWorkspace);
      }
    }
  });

function showNotification (type, text) {
  $('#global-noti-text').html(text);
  $('#global-noti-icon').removeClass('fa-info');
  $('#global-noti-icon').removeClass('fa-exclamation-circle');
  $('#global-noti-icon').removeClass('fa-check');

  $('#global-noti-box').removeClass('alert-primary');
  $('#global-noti-box').removeClass('alert-danger');
  $('#global-noti-box').removeClass('alert-success');

  const icons = {
    info: {i: 'fa-info', b: 'alert-primary'},
    error: {i: 'fa-exclamation-circle', b: 'alert-danger'},
    ok: {i: 'fa-check', b: 'alert-success'}
  };
  if (icons[type]) {
    $('#global-noti-icon').addClass(icons[type].i);
    $('#global-noti-box').addClass(icons[type].b);
  }

  $('#global-notification').show();
  if (!$('#global-notification').hasClass('active')) {
    $('#global-notification').addClass('active');
    setTimeout(function () {
      $('#global-notification').removeClass('active');
    }, 200);
  }
  setTimeout(function () {
    $('#global-notification').hide();
  }, 5000);
}

function dismissGlobalAlert () {
  $('#global-notification').hide();
}

function clickWell (d) {
  console.log('clickWell.d', d);
  console.log('clickWell.this', this);
  $('.cc').removeClass('selected-content');
  $('.cc').addClass('content-list-item');

  selectStyle(d, this);

  d3.selectAll('circle.content').each(function (stateData) {
    console.log('entreaca');
    stateData.selected = true;
    selectStyle(stateData, this, false);
  });

  showContentOptions();
  showCalibrationOptions();

  // console.log(i);
  // console.log(d3.event)
  // console.log(d3.event.target.r)
  d3.event.stopPropagation();
}

function clickEmptyTip (d) {
  console.log('Click empty tip');
  console.log(d);
  $('.cc').removeClass('selected-content');
  $('.cc').addClass('content-list-item');
  // console.log(this);

  selectStyle(d, this, true);

  showContentOptions();
  showCalibrationOptions();

  // console.log(i);
  // console.log(d3.event)
  // console.log(d3.event.target.r)
  d3.event.stopPropagation();
}

function showContentOptions () {
  const selectedWells = d3.selectAll('circle').filter(function (well) {
    // console.log('well', well);
    return (well.selected === true) && (well.type === 'well' || well.type === 'tip');
  });
  const totalSelected = selectedWells.size();
  console.log('Seleccionados: ' + totalSelected);
  if (totalSelected === 0) {
    $('#insertContentOption').hide();
  } else {
    $('#insertContentOption').show();
  }
}

function showCalibrationOptions () {
  console.log('mme lalman');
  const selectedWells = d3.selectAll('circle.content').filter(function (c) {
    // console.log('well', well);
    return (c.selected === true);
  });
  const totalSelected = selectedWells.size();
  console.log('Seleccionados Contenido: ' + totalSelected);
  if (totalSelected === 0) {
    $('#calibrationToolsMenu').hide();
  } else {
    $('#calibrationToolsMenu').show();
  }
}

function insertTube () {
  let latestItem;
  d3.selectAll('circle').filter(function (well) {
    return (well.selected === true) && (well.type === 'well');
  }).each(function (well) {
    const item = getItemByName(activeWorkspace, well.item.name);

    if (typeof item.content !== 'object') {
      item.content = [];
    }
    latestItem = item;
    item.content.push({
      index: well.index,
      maxVolume: well.platformData.defaultMaxVolume || 0,
      name: getUniqueName('tube', 1, 'name', item.content, true),
      position: {col: well.c, row: well.r},
      tags: [],
      type: 'tube',
      volume: 0
    });
  });

  drawWorkspace(activeWorkspace, function () {
    const newCircle = d3.select('#' + generateIdContent(latestItem, latestItem.content[latestItem.content.length - 1], 'draw')).node();
    // console.log('newCircle', newCircle);
    selectStyle({selected: false}, newCircle, true);
    // console.log('latestItem', latestItem);
    selectContent(latestItem, [latestItem.content[latestItem.content.length - 1]], true, {selected: true});
  });
}

function selectContentByNames (itemName, contentName) {
  const item = getItemByName(activeWorkspace, itemName);
  const content = getContentByName(itemName, contentName);
  if (content) {
    const newCircle = d3.select('#' + generateIdContent(item, content, 'draw')).node();
    selectStyle({selected: false}, newCircle, true);
    selectContent(item, [content], true, {selected: true}, true);
  }
}

function selectText (obj) {
  obj.select();
}

function focusContent (obj, itemName, contentName) {
  console.log('focus!', itemName, contentName);
  itemName = decodeURI(itemName);
  contentName = decodeURI(contentName);
  selectContentByNames(itemName, contentName);
}

function insertTip () {
  d3.selectAll('circle').filter(function (well) {
    // console.log('well', well);
    return (well.selected === true) && (well.type === 'tip');
  }).each(function (well) {
    // console.log(well);
    const item = getItemByName(activeWorkspace, well.item.name);
    if (typeof item.content !== 'object') {
      // console.log('reseteado');
      item.content = [];
    }
    item.content.push({
      index: well.index,
      maxVolume: well.platformData.defaultMaxVolume || 0,
      name: getUniqueName('tip', 1, 'name', item.content, true),
      position: {col: well.c, row: well.r},
      tags: [],
      type: 'tip',
      volume: 0
    });
    drawWorkspace(activeWorkspace);
  });
}

function drawTubeRack (svgContainer, item, isPreview) {
  const id = generateId(item);
  const group = svgContainer.append('g')
    .attr('id', id)
    .datum({x: 0, y: 0, name: item.name})
    .call(dragcontainer);

  group.append('rect')
    .attr('x', item.position.x)
    .attr('y', item.position.y)
    .attr('width', item.platformData.width)
    .attr('height', item.platformData.length)
    .attr('fill', item.platformData.color);
  if (!isPreview) {
    addDeleteIcontoItem(group, item);
  }

  let firstC = 0;
  let firstR = 0;
  let index = 0;
  for (let r = 0; r < item.platformData.wellsRows; r++) {
    for (let c = 0; c < item.platformData.wellsColumns; c++) {
      index++;
      const cx = parseInt(item.position.x) + parseInt(item.platformData.firstWellCenterX) + parseInt(firstC);
      const cy = parseInt(item.position.y) + parseInt(item.platformData.firstWellCenterY) + parseInt(firstR);
      group.append('circle')
      .attr('cx', cx)
      .attr('cy', cy)
      .attr('r', item.platformData.wellDiameter / 2)
      .attr('fill-opacity', '0.3')
      .style('stroke', '#ffffff')
      .style('stroke-width', '0.2px')
      .attr('fill', '#ffffff')
      .datum({type: 'well', c: c + 1, r: r + 1, index, platformData: item.platformData, item})
      .on('click', clickWell);

      const content = hasContent(item, c, r);
      if (content) {
        drawContent(group, item, content, cx, cy);
      }
      firstC = firstC + item.platformData.wellSeparationX;
    }
    firstC = 0;
    firstR = firstR + item.platformData.wellSeparationY;
  }
  drawTextName(group, item);
}

function _mrect (x, y, w, h) {
  return 'M' + [x, y] + ' l' + [w, 0] + ' l' + [0, h] + ' l' + [-w, 0] + 'z';
}

function generateId (item) {
  item.name.split(' ').join('_').split('.').join('_') + item.platformData.name.split(' ').join('_').split('.').join('_');
}

function drawTipsRack (svgContainer, item, isPreview) {
  const id = generateId(item);
  const group = svgContainer.append('g')
    .attr('id', id)
    .datum({x: 0, y: 0, name: item.name})
    .call(dragcontainer);

  const rect = group.append('rect')
    .attr('x', item.position.x)
    .attr('y', item.position.y)
    .attr('width', item.platformData.width)
    .attr('height', item.platformData.length)
    .attr('fill', item.platformData.color)
    .on('click', function () {
      console.log('platform click');
      d3.selectAll('circle.tiphole').each(function (stateData) {
        if (stateData.selected) {
          stateData.selected = true;
          selectStyle(stateData, this);
          showContentOptions();
        }
      });

      d3.select(window).on('mousemove.selection', null).on('mouseup.selection', null);
      selection.attr('visibility', 'hidden');
    });

  const selection = svgContainer.append('path')
  .attr('class', 'selection')
  .attr('visibility', 'hidden');

  const startSelection = function (start) {
    selection.attr('d', _mrect(start[0], start[0], 0, 0))
      .attr('visibility', 'visible');
  };

  const moveSelection = function (start, moved) {
    selection.attr('d', _mrect(start[0], start[1], moved[0] - start[0], moved[1] - start[1]));
  };

  const endSelection = function (start, end) {
    const tempSelec = svgContainer.append('rect')
    .attr('x', Math.min(start[0], end[0]))
    .attr('y', Math.min(start[1], end[1]))
    .attr('width', Math.abs(start[0] - end[0]))
    .attr('height', Math.abs(start[1] - end[1]))
    .attr('visibility', 'hidden')
    .attr('class', 'temp');

    const d = {
      x: parseInt(tempSelec.attr('x'), 10),
      y: parseInt(tempSelec.attr('y'), 10),
      width: parseInt(tempSelec.attr('width'), 10),
      height: parseInt(tempSelec.attr('height'), 10)
    };
    d3.selectAll('circle.tiphole').each(function (stateData) {
      if (stateData.x - stateData.radio >= d.x && stateData.x + stateData.radio <= d.x + d.width && stateData.y - stateData.radio >= d.y && stateData.y + stateData.radio <= d.y + d.height) {
        if (hasContent(stateData.item, stateData.c - 1, stateData.r - 1)) {
          return;
        }
        // console.log('state', stateData)
        // console.log(this);
        stateData.selected = false;
        selectStyle(stateData, this);
      }
    });
    svgContainer.selectAll('rect.temp').remove();
    selection.attr('visibility', 'hidden');
    showContentOptions();
  };

  rect.on('mousedown', function () {
    const subject = d3.select(window);
    const parent = this.parentNode;
    const start = d3.mouse(parent);

    startSelection(start);
    subject.on('mousemove.selection', function () {
      moveSelection(start, d3.mouse(parent));
    }).on('mouseup.selection', function () {
      endSelection(start, d3.mouse(parent));
      subject.on('mousemove.selection', null).on('mouseup.selection', null);
    });
  });

  if (!isPreview) {
    addDeleteIcontoItem(group, item);
  }

  let firstC = 0;
  let firstR = 0;
  let index = 0;
  for (let r = 0; r < item.platformData.wellsRows; r++) {
    for (let c = 0; c < item.platformData.wellsColumns; c++) {
      index++;
      const cx = parseInt(item.position.x) + parseInt(item.platformData.firstWellCenterX) + parseInt(firstC);
      const cy = parseInt(item.position.y) + parseInt(item.platformData.firstWellCenterY) + parseInt(firstR);
      group.append('circle')
      .attr('cx', cx)
      .attr('cy', cy)
      .attr('r', item.platformData.wellDiameter / 2)
      .attr('fill-opacity', '0.3')
      .style('stroke', '#ffffff')
      .style('stroke-width', '0.2px')
      .attr('fill', '#ffffff')
      .attr('class', 'tiphole')
      .datum({type: 'tip', c: c + 1, r: r + 1, index, platformData: item.platformData, item, x: cx, y: cy, radio: item.platformData.wellDiameter / 2})
      .on('click', clickEmptyTip);

      const content = hasContent(item, c, r);
      if (content) {
        drawContent(group, item, content, cx, cy);
      }
      firstC = firstC + item.platformData.wellSeparationX;
    }
    firstC = 0;
    firstR = firstR + item.platformData.wellSeparationY;
  }
  drawTextName(group, item);
}

function drawBucket (svgContainer, item, isPreview) {
  const id = generateId(item);
  const group = svgContainer.append('g')
    .attr('id', id)
    .datum({x: 0, y: 0, name: item.name})
    .call(dragcontainer);

  group.append('rect')
    .attr('x', item.position.x)
    .attr('y', item.position.y)
    .attr('width', item.platformData.width)
    .attr('height', item.platformData.length)
    .attr('fill', item.platformData.color);
  if (!isPreview) {
    addDeleteIcontoItem(group, item);
  }
  drawTextName(group, item);
}

// https://qph.fs.quoracdn.net/main-qimg-b7a6acfaf4b13b7824d1b8fe28bace4d

function drawPetriDish (svgContainer, item, isPreview) {
  const id = generateId(item);
  const group = svgContainer.append('g')
    .attr('id', id)
    .datum({x: 0, y: 0, name: item.name})
    .call(dragcontainer);

   // group.attr("transform", "rotate(30,"+item.position.x+","+item.position.y+" )")

  group.append('circle')
    .attr('cx', item.position.x)
    .attr('cy', item.position.y)
    .attr('r', item.platformData.diameter / 2)
    .attr('fill-opacity', '0.4')
    .style('stroke', '#ffffff')
    .style('stroke-width', '0.6px')
    .attr('fill', item.platformData.color)
    // .attr("transform", "rotate(30,"+item.position.x+","+item.position.y+" )")
    .on('click', function () {
      console.log('Petri click');
      const mouse = d3.mouse(this);
      console.log('mouse', mouse);

      if (typeof item.content !== 'object') {
        item.content = [];
      }

      let indexes = item.content.map(function (ind) {
        return ind.index;
      });
      indexes = indexes.length ? indexes : [0];
      console.log('indexes', indexes);
      let nextIndex = Math.max.apply(Math, indexes);

      console.log('nextIndex', nextIndex);

      const nextcontent = {
        index: ++nextIndex,
        maxVolume: 0,
        name: getUniqueName('colony', 1, 'name', item.content, true),
        position: {col: parseInt(mouse[0] - item.position.x), row: parseInt(mouse[1] - item.position.y)},
        tags: [],
        type: 'colony',
        volume: 1
      };
      console.log(nextcontent);

      item.content.push(nextcontent);
      drawWorkspace(activeWorkspace);
      showCalibrationOptions();
    });

  if (!isPreview) {
    addDeleteIcontoItem(group, item);
  }
  drawTextName(group, item);
  if (typeof item.content !== 'object') {
    item.content = [];
  }

  item.content.map(function (cont) {
    // drawContent(group, item, [cont], cont.position.col, cont.position.row);
    group.append('circle')
      .attr('cx', item.position.x + cont.position.col)
      .attr('cy', item.position.y + cont.position.row)
      .attr('r', cont.volume)
      .attr('fill-opacity', '0.7')
      .style('stroke', '#ffffff')
      .style('stroke-width', '0.5px')
      .attr('fill', '#ffffff')
      .attr('class', 'content')
      .datum({type: 'content-colony'})
      .attr('id', generateIdContent(item, cont, 'draw'))
      .on('click', function (d) {
        selectStyle(d, this, true);
        selectContent(item, [cont], true, d);
        showCalibrationOptions();
        // console.log('drawContent.d', d);
        // console.log('drawContent.this', this);
      }).append('svg:title')
        .text(cont.name);
  });
}

function drawTextName (svgContainer, item) {
  const textPosition = {
    x: item.position.x + 1,
    y: item.position.y + 3
  };
  if (item.platformData.type === 'PETRI_DISH') {
    textPosition.x = item.position.x - (item.platformData.diameter / 2) + 1;
    textPosition.y = item.position.y - (item.platformData.diameter / 2) + 3;
  }

  svgContainer.append('text')
      .attr('x', textPosition.x)
      .attr('y', textPosition.y)
      .text(item.name)
      .attr('font-family', 'sans-serif')
      .attr('font-size', '3px')
      .attr('fill', 'black')
      .style('cursor', 'move')
      .datum({dragAnchor: true});
      // .call(dragcontainer);
}

function removeItemFromWorkspace (name, workspace, redraw) {
  if (workspace && workspace.items && workspace.items.length) {
    for (let i = 0; i < workspace.items.length; i++) {
      if (workspace.items[i].name === name) {
        workspace.items.splice(i, 1);
        if (redraw) {
          drawWorkspace(workspace);
        }
      }
    }
  }
}

function updateWorkspaceAfterPlatformEdit (platform, workspace) {
  if (workspace && workspace.items && workspace.items.length) {
    for (let i = 0; i < workspace.items.length; i++) {
      if (workspace.items[i].platform === platform.name) {
        workspace.items[i].platformData = platform;
        drawWorkspace(workspace);
      }
    }
  }
}

function addDeleteIcontoItem (group, item) {
  // delete icon
  const pos = {
    x: item.position.x + item.platformData.width - 3.1,
    y: item.position.y + 3.1
  };

  if (item.platformData.type === 'PETRI_DISH') {
    pos.x = (item.position.x + item.platformData.diameter / 2) - 8;
    pos.y = (item.position.y - item.platformData.diameter / 2) + 5;
  }

  group.append('text')
    .attr('x', pos.x)
    .attr('y', pos.y)
    .attr('font-size', '3px')
    .attr('class', 'fa')
    .text('\uf1f8')
    .style('cursor', 'pointer')
    .style('color', '#e16d6d')
    .on('click', function () {
      removeItemFromWorkspace(item.name, activeWorkspace, true);
      d3.event.stopPropagation();
    });
}

function hasContent (item, col, row) {
  if (item && item.content && item.content.length) {
    const content = item.content.filter(function (c) {
      return (c.position.col === (col + 1) && c.position.row === (row + 1));
    });
    return content.length ? content : false;
  }
  return false;
}

let _selectedContent = '';

function selectContent (item, content, animate, d, noGoto) {
  const id = generateIdContent(item, content[0]);
  selectContentById(id, animate, d, noGoto);
}

function selectContentById (id, animate, d, noGoto) {
  console.log('Click content', id);
  $('.cc').removeClass('selected-content');
  $('.cc').addClass('content-list-item');
  if (d && d.selected) {
    _selectedContent = id;
    const obj = document.getElementById(id);
    if (obj) {
      $('#' + id).removeClass('content-list-item');
      $('#' + id).addClass('selected-content');
      const contactTopPosition = obj.offsetTop - 20;
      if (noGoto) {
        return;
      }
      if (animate) {
        $('#left').animate({scrollTop: contactTopPosition});
      } else {
        $('#left').scrollTop(contactTopPosition);
      }
    }
  }
}

function selectStyle (d, obj, deselectAll) {
  // console.log('selectStyle.d.selected', d)
  // console.log('selectStyle.this(obj)', obj)
  if (deselectAll) {
    d3.selectAll('circle').each(function (stateData) {
      if (d3.select(obj).attr('id') !== d3.select(this).attr('id')) {
        stateData.selected = true;
        // console.log('attr.id', d3.select(this).attr('id'));
        selectStyle(stateData, this, false);
      }
    });
  }

  if (d.selected) {
    d3.select(obj).raise().style('stroke-width', '0.2px');
    d3.select(obj).raise().style('stroke', '#ffffff');
    d3.select(obj).raise().style('stroke-dasharray', null);
    // d3.select(obj).raise().classed('sel', false);
    d.selected = false;
  } else {
    d3.select(obj).raise().style('stroke', '#000000');
    d3.select(obj).raise().style('stroke-dasharray', ('1, 1'));
    d3.select(obj).raise().style('stroke-width', '0.5px');
    // d3.select(obj).raise().attr("class","sel")
    d.selected = true;
  }
}

function drawContent (svgContainer, item, content, x, y) {
  const maxVol = content[0].maxVolume || item.platformData.defaultMaxVolume || 0;
  const vol = content[0].volume || 0;

  let fillPorc = parseInt(vol * 100 / maxVol, 10);
  fillPorc = isNaN(fillPorc) ? 0 : fillPorc;

  // console.log('fillPorc', fillPorc);

  const grad = svgContainer.append('defs').append('linearGradient').attr('id', 'grad' + fillPorc)
    .attr('x1', '0%').attr('x2', '0%').attr('y1', '100%').attr('y2', '0%');
  grad.append('stop').attr('offset', fillPorc + '%').style('stop-color', 'lightblue');
  grad.append('stop').attr('offset', '0%').style('stop-color', 'white');

  svgContainer.append('circle')
    .attr('cx', x)
    .attr('cy', y)
    .attr('r', (item.platformData.wellDiameter / 2) + 1)
    .attr('fill-opacity', '0.7')
    .style('stroke', '#ffffff')
    .style('stroke-width', '0.5px')
    .attr('fill', 'url(#grad' + fillPorc + ')')
    // .attr("class", "content")
    .attr('class', 'content grad' + fillPorc)
    .datum({type: 'content'})
    .attr('id', generateIdContent(item, content[0], 'draw'))
    .attr('item', item.name)
    .attr('platform', item.platformData.name)
    .attr('name', content[0].name)
    .on('click', function (d) {
      selectStyle(d, this, true);
      selectContent(item, content, true, d);
      showContentOptions();
      showCalibrationOptions();
      // console.log('drawContent.d', d);
      // console.log('drawContent.this', this);
    })
    .append('svg:title')
      .text(content[0].name);

  if (content[0].tags && content[0].tags.length && item.platformData.wellDiameter) {
    const semiCircles = content[0].tags.length;
    const arcLength = (Math.PI * 2) / semiCircles;
    let startAngle = 0;
    let endAngle = arcLength;
    for (let ti = 0; ti < semiCircles; ti++) {
      const arc = d3.arc()
        .innerRadius((item.platformData.wellDiameter / 2) + 2)
        .outerRadius((item.platformData.wellDiameter / 2) + 2)
        .startAngle(startAngle)
        .endAngle(endAngle);

      svgContainer.append('path')
        .attr('transform', 'translate(' + x + ',' + y + ')')
        .style('stroke', colorHash(content[0].tags[ti]).hex)
        .style('stroke-width', '0.7px')
        .attr('d', arc);
      startAngle += arcLength;
      endAngle += arcLength;
    }
  }
}

function colorHash (inputString) {
  let sum = 0;

  for (let i in inputString) {
    sum += inputString.charCodeAt(i);
  }

  const r = ~~(('0.' + Math.sin(sum + 1).toString().substr(6)) * 256);
  const g = ~~(('0.' + Math.sin(sum + 2).toString().substr(6)) * 256);
  const b = ~~(('0.' + Math.sin(sum + 3).toString().substr(6)) * 256);

  const rgb = 'rgb(' + r + ', ' + g + ', ' + b + ')';

  let hex = '#';

  hex += ('00' + r.toString(16)).substr(-2, 2).toUpperCase();
  hex += ('00' + g.toString(16)).substr(-2, 2).toUpperCase();
  hex += ('00' + b.toString(16)).substr(-2, 2).toUpperCase();

  return {r, g, b, rgb, hex};
}

function drawPlatformPreview (platformData) {
  $('#platformPreviewDraw').html('');
  const svgContainer = d3.select('#platformPreviewDraw').append('svg')
          .attr('width', WORKAREA_WIDTH)
          .attr('height', WORKAREA_HEIGHT);

  // Draw working area
  svgContainer.append('rect')
    .attr('x', 0)
    .attr('y', 0)
    .attr('width', WORKAREA_WIDTH)
    .attr('height', WORKAREA_HEIGHT)
    .attr('fill', '#ededed');
  drawGrid(svgContainer, WORKAREA_WIDTH, WORKAREA_HEIGHT, 10);

  const pos = {
    x: (svgContainer.attr('width') / 2) - (platformData.width / 2),
    y: (svgContainer.attr('height') / 2) - (platformData.length / 2)
  };
  if (platformData.type === 'PETRI_DISH') {
    pos.x = svgContainer.attr('width') / 2;
    pos.y = svgContainer.attr('height') / 2;
  }

  const item = {
    name: platformData.name,
    position: pos,
    platformData
  };

  switch (platformData.type) {
    case 'TUBE_RACK':
      drawTubeRack(svgContainer, item, true);
      break;
    case 'TIP_RACK':
      drawTipsRack(svgContainer, item, true);
      break;
    case 'PETRI_DISH':
      drawPetriDish(svgContainer, item, true);
      break;
    case 'BUCKET':
      drawBucket(svgContainer, item, true);
      break;
  }

  svgContainer.call(responsivefy);
}

function updateContentName (inputObj, itemName, contentName, redraw) {
  console.log('updateContentName', inputObj);
  console.log('new Name:', $(inputObj).val());
  itemName = decodeURI(itemName);
  contentName = decodeURI(contentName);
  if (contentName === $(inputObj).val()) return;
  const itemData = getItemByName(activeWorkspace, itemName);
  if (itemData && itemData.content && itemData.content.length) {
    for (let i = 0; i < itemData.content.length; i++) {
      if (itemData.content[i].name === contentName) {
        itemData.content[i].name = getUniqueName($(inputObj).val(), 0, 'name', itemData.content, true);
        $(inputObj).val(itemData.content[i].name);
        if (redraw) {
          drawWorkspace(activeWorkspace);
        }
      }
    }
  }
}

function updateContentVolume (inputObj, itemName, contentName, redraw) {
  console.log('updateContentVolume', inputObj);
  console.log('new volume:', $(inputObj).val());
  itemName = decodeURI(itemName);
  contentName = decodeURI(contentName);
  const itemData = getItemByName(activeWorkspace, itemName);
  if (itemData && itemData.content && itemData.content.length) {
    for (let i = 0; i < itemData.content.length; i++) {
      if (itemData.content[i].name === contentName) {
        console.log('Editar:');
        console.log(itemData.content[i]);
        let nv = $(inputObj).val().trim();
        nv = parseInt(nv, 10);
        if (isNaN(nv)) {
          nv = 0;
        }
        itemData.content[i].volume = nv;
        if (redraw) {
          drawWorkspace(activeWorkspace);
        }
      }
    }
  }
}

function inputKeyPress (inputObj, e) {
  if (e.keyCode === 13) {
    inputObj.blur();
  }
}

function drawLeftPanel (workspace, cb) {
  $.ajax({
    url: '/workspace-panel',
    type: 'POST',
    data: JSON.stringify({workspace, collapseStatus}),
    contentType: 'application/json',
    // dataType: 'json',
    success: function (html) {
      $('#left').html(html);
      if (_selectedContent) {
        console.log('basura', _selectedContent);
        selectContentById(_selectedContent, false);
      }
      if (cb) cb();
    },
    error: function (e) {
      console.log(e);
      alert('Unexpected Error');
    }
  });
}

function drawWorkspace (workspace, dcb) {
  if (workspace) {
    $('#draw').html('');
    const drawG = function () {
      const svgContainer = d3.select('#draw').append('svg')
        .attr('width', WORKAREA_WIDTH)
        .attr('height', WORKAREA_HEIGHT);

      // Draw working area
      svgContainer.append('rect')
        .attr('x', 0)
        .attr('y', 0)
        .attr('width', WORKAREA_WIDTH)
        .attr('height', WORKAREA_HEIGHT)
        .attr('fill', '#ededed');
      svgContainer.on('mousemove', function () {
        const mouse = d3.mouse(this);
        updateCoordinates(mouse[0], mouse[1]);
      });

      drawGrid(svgContainer, WORKAREA_WIDTH, WORKAREA_HEIGHT, 10);

      workspace.items.map(function (item) {
        switch (item.platformData.type) {
          case 'TUBE_RACK':
            drawTubeRack(svgContainer, item);
            break;
          case 'TIP_RACK':
            drawTipsRack(svgContainer, item);
            break;
          case 'PETRI_DISH':
            drawPetriDish(svgContainer, item);
            break;
          case 'BUCKET':
            drawBucket(svgContainer, item);
            break;
        }
      });

      // scale
      svgContainer.call(responsivefy);

      if (dcb) dcb();
    };

    if (dcb) {
      drawLeftPanel(workspace, drawG);
    } else {
      drawLeftPanel(workspace);
      drawG();
    }
    drawProtocolPanel(workspace, activeProtocol);
  }
}

function drawWorkspaceHeader () {
  if (activeWorkspace) {
    $('#workspaceName').html(unescape(activeWorkspace.name || 'Untitled-1'));
    $('#saveWorkspaceMenuItem').show();
    $('#saveWorkspaceGlobalButton').show();
    $('#saveAsWorkspaceMenuItem').show();
    $('#exportWorkspaceMenuItem').show();
    $('#deleteMenuItem').show();
    $('#closeMenuItem').show();
    $('#left').show();
    $('#toolBar').show();
    $('#right').show();
  } else {
    console.log('llege aca');
    $('#workspaceName').html('');
  }
}

function closeMenu () {
  closing = true;
  newWorkspaceMenu();
}

function deleteMenu () {
  deleteWorkspace(activeWorkspace.name || 'Untitled-1', function () {
    resetWorkspace();
  });
}

function saveWorkspace (name, workspace, cb) {
  console.log(workspace);
  $.ajax({
    url: '/api/workspaces/' + name || workspace.name,
    type: 'POST',
    data: JSON.stringify(workspace),
    contentType: 'application/json',
    dataType: 'json',
    success: function (result) {
      console.log(result);
      if (result.error) {
        alert(result.error);
        return;
      }
      showNotification('ok', 'Workspace saved');
      console.log(result);
      cb(result.data);
    },
    error: function () {
      alert('Unexpected Error');
    }
  });
}

function saveWorkspaceMenu (cb, message) {
  let name = activeWorkspace.name || 'Untitled-1';

  if (name === 'Untitled-1') {
    name = prompt(message || 'Save as', name);
    if (name === null) {
      return;
    }
  }
  if (name.trim() === '') {
    return;
  }
  activeWorkspace.name = name;

  saveWorkspace(name, activeWorkspace, function (data) {
    activeWorkspace.name = data.name;
    drawWorkspaceHeader();
    console.log('Save done...');
    if (cb) cb();
  });
}

function saveAsWorkspaceMenu () {
  let name = activeWorkspace.name || 'Untitled-1';

  name = prompt('Save as', name);
  if (name === null) {
    return;
  }
  if (name.trim() === '') {
    return;
  }
  saveWorkspace(name, activeWorkspace, function (data) {
    console.log('Save done...');
    activeWorkspace.name = data.name;
    drawWorkspaceHeader();
  });
}

function exportWorkspaceMenu () {
  saveWorkspaceMenu(function () {
    $.ajax({
      url: '/api/workspaces/' + activeWorkspace.name,
      type: 'GET',
      contentType: 'application/json',
      dataType: 'json',
      success: function (result) {
        console.log(result);
        if (result.error) {
          alert(result.error);
          return;
        }
        if (result) {
          download('workspace_' + result.name + '.json', JSON.stringify(result, null, 2));
          showNotification('ok', 'Workspace exported succesfully.');
        }
      },
      error: function () {
        alert('Unexpected error.');
      }
    });
  });
}

function exportPlatform (name) {
  $.ajax({
    url: '/api/platforms/' + name,
    type: 'GET',
    contentType: 'application/json',
    dataType: 'json',
    success: function (result) {
      console.log(result);
      if (result.error) {
        alert(result.error);
        return;
      }
      if (result) {
        if (result._id) delete result._id;
        download('platform_' + result.name + '.json', JSON.stringify(result, null, 2));
        showNotification('ok', 'Platform exported succesfully.');
      }
    },
    error: function () {
      alert('Unexpected error.');
    }
  });
}

function exportProtocol (name) {
  $.ajax({
    url: '/api/hl-protocols/' + name,
    type: 'GET',
    contentType: 'application/json',
    dataType: 'json',
    success: function (result) {
      console.log(result);
      if (result.error) {
        alert(result.error);
        return;
      }
      if (result) {
        if (result._id) delete result._id;
        download('hlprotocol_' + result.name + '.json', JSON.stringify(result, null, 2));
        showNotification('ok', 'Protocol exported succesfully.');
      }
    },
    error: function () {
      alert('Unexpected error.');
    }
  });
}

function fileSelected (e, a) {
  const file = e.target.files[0];
  const reader = new FileReader();
  reader.readAsText(file, 'UTF-8');
  reader.onload = readerEvent => {
    const plainContent = readerEvent.target.result;
    if (plainContent) {
      try {
        const workspace = JSON.parse(plainContent);
        if (workspace.name && workspace.items) {
          workspace.items.map(function (w) {
            if (w.platformData && w.platformData.name) {
              // do not try this at home...
              delete w.platformData._id;
              $.ajax({
                url: '/api/platforms',
                type: 'POST',
                data: JSON.stringify(w.platformData),
                contentType: 'application/json',
                dataType: 'json',
                success: function (result) {
                  if (result.error) {
                    // ignore
                    return;
                  }
                },
                error: function () {
                  showErrorInModal('Unexpected error.');
                }
              });
            }
          });
          const newName = prompt('Import as', workspace.name);
          if (newName === null || newName.trim() === '') {
            return;
          }
          workspace.name = newName;

          activeWorkspace = workspace;
          activeProtocol = null;
          importing = null;
          drawWorkspaceHeader();
          drawWorkspace(workspace);
        } else {
          alert('Error importing Workspace. Name is missing.');
        }
      } catch (e) {
        console.log(e);
        alert('Error importing Workspace. Invalid format?');
      }
    }
  };
}

function fileSelectedPlatform (e) {
  const file = e.target.files[0];
  const reader = new FileReader();
  reader.readAsText(file, 'UTF-8');
  reader.onload = readerEvent => {
    const plainContent = readerEvent.target.result;
    if (plainContent) {
      try {
        const platform = JSON.parse(plainContent);
        if (platform.name && platform.type) {
          if (platform._id) delete platform._id;
          const newName = prompt('Import as', platform.name);
          if (newName === null || newName.trim() === '') {
            return;
          }
          platform.name = newName;
          $.ajax({
            url: '/api/platforms',
            type: 'POST',
            data: JSON.stringify(platform),
            contentType: 'application/json',
            dataType: 'json',
            success: function (result) {
              if (result.error) {
                alert(result.error);
                return;
              }
              showNotification('ok', 'Platform imported succesfully.');
              getPlatformsList();
            },
            error: function () {
              showErrorInModal('Unexpected error.');
            }
          });
        } else {
          alert('Error importing Platform. Name or type are missing.');
        }
      } catch (e) {
        console.log(e);
        alert('Error importing Platform. Invalid format?');
      }
    }
  };
}

function fileSelectedProtocol (e, a) {
  const file = e.target.files[0];
  const reader = new FileReader();
  reader.readAsText(file, 'UTF-8');
  reader.onload = readerEvent => {
    const plainContent = readerEvent.target.result;
    if (plainContent) {
      try {
        const protocol = JSON.parse(plainContent);
        if (protocol.name && protocol.workspace) {
          if (protocol._id) delete protocol._id;
          if (activeWorkspace && activeWorkspace.name !== protocol.workspace) {
            protocol.workspace = activeWorkspace.name;
            if (!confirm('Looks like the importing Protocol was made for a different Workspace. It may not work on the current Workspace. Do you want to import it anyway?')) {
              return;
            }
          }
          const newName = prompt('Import as', protocol.name);
          if (newName === null || newName.trim() === '') {
            return;
          }
          protocol.name = newName;
          $.ajax({
            url: '/api/hl-protocols',
            type: 'POST',
            data: JSON.stringify(protocol),
            contentType: 'application/json',
            dataType: 'json',
            success: function (result) {
              if (result.error) {
                alert(result.error);
                return;
              }
              drawProtocolPanel(activeWorkspace, activeProtocol);
              showNotification('ok', 'Protocol imported succesfully.');
            },
            error: function () {
              alert('Unexpected error.');
            }
          });
        } else {
          alert('Error importing Protocol. Name or workspace are missing.');
        }
      } catch (e) {
        console.log(e);
        alert('Error importing Protocol. Invalid format?');
      }
    }
  };
}

function importPlatform () {
  $('#file-selector-platform').trigger('click');
}

function importProtocol () {
  $('#file-selector-protocol').trigger('click');
}

function importWorkspaceMenu () {
  importing = true;
  if (activeWorkspace) {
    const title = activeWorkspace.name || 'Untitled-1';
    $('#saveWorkModalTitle').html('Do you want to save the changes you made to ' + title + ' workspace?');
    $('#closingWorkspace').modal('toggle');
    return;
  }
  importing = null;

  $('#dataPanel').html('');
  $('#loadingmodal').show();
  $('#file-selector').trigger('click');
}

function saveCurrent () {
  let name = activeWorkspace.name || 'Untitled-1';

  if (name === 'Untitled-1') {
    name = prompt('Save as', name);
    if (name === null) {
      return;
    }
  }
  if (name.trim() === '') {
    return;
  }

  saveWorkspace(name, activeWorkspace, function () {
    $('#closingWorkspace').modal('hide');
    if (opening) {
      loadWorkspace(opening, true);
      return;
    }
    createNewWorkspace();
  });
}

function dontSaveCurrent () {
  $('#closingWorkspace').modal('hide');
  if (opening) {
    loadWorkspace(opening, true);
    return;
  }
  if (importing) {
    resetWorkspace();
    $('#dataPanel').html('');
    $('#loadingmodal').show();
    $('#file-selector').trigger('click');
    importing = null;
    return;
  }
  createNewWorkspace();
}

function newWorkspaceMenu () {
  if (activeWorkspace) {
    const title = activeWorkspace.name || 'Untitled-1';
    $('#saveWorkModalTitle').html('Do you want to save the changes you made to ' + title + ' workspace?');
    $('#closingWorkspace').modal('toggle');
    return;
  }
  createNewWorkspace();
}

function resetWorkspace () {
  activeWorkspace = null;
  activeProtocol = null;
  closing = null;
  drawWorkspaceHeader();
  $('#draw').html('');
  $('#saveWorkspaceMenuItem').hide();
  $('#saveWorkspaceGlobalButton').hide();
  $('#saveAsWorkspaceMenuItem').hide();
  $('#exportWorkspaceMenuItem').hide();
  $('#deleteMenuItem').hide();
  $('#closeMenuItem').hide();
  $('#left').hide();
  $('#toolBar').hide();
  $('#right').hide();
}
function createNewWorkspace () {
  if (closing) {
    resetWorkspace();
    return;
  }
  activeWorkspace = {
    name: '',
    items: []
  };
  activeProtocol = null;
  drawWorkspace(activeWorkspace);
  drawWorkspaceHeader();
}

let activeWorkspace = null;
let activeProtocol = null;
let opening = null;
let closing = null;
let importing = null;

function loadWorkspace (name, force) {
  if (activeWorkspace && !force) {
    opening = name;
    const title = activeWorkspace.name || 'Untitled-1';
    $('#saveWorkModalTitle').html('Do you want to save the changes you made to ' + title + ' workspace?');
    $('#closingWorkspace').modal('toggle');
    return;
  }
  opening = null;

  $('#dataPanel').html('');
  $('#loadingmodal').show();
  $.get('/api/workspaces/' + name, function (workspace) {
    if (workspace) {
      $('#listModal').modal('hide');
      activeWorkspace = workspace;
      activeProtocol = null;
      drawWorkspaceHeader();
      drawWorkspace(workspace);
    }
    $('#loadingmodal').hide();
  });
}

function getWorkspacesList () {
  $('#loadingmodal').hide();
  $('#modalTitle').html('Workspaces');
  $.get('/workspaces-list', function (data1) {
    $('#dataPanel').html(data1);
  });
}

function getPlatformsList () {
  $('#loadingmodal').hide();
  $('#modalTitle').html('Availabe Platforms');
  $.get('/platforms-list', function (data1) {
    $('#dataPanel').html(data1);
  });
  return false;
}

function editPlatformPanel (name) {
  $('#dataPanel').html('');
  $('#loadingmodal').hide();
  $.get('/platforms-edit/' + name, function (html) {
    if (html) {
      $('#modalTitle').html('Edit Platform');
      $('#dataPanel').html(html);
      const editor = ace.edit('editor');
      editor.setTheme('ace/theme/monokai');
      editor.session.setMode('ace/mode/javascript');
      editor.resize();
      editor.setOption('maxLines', 100);
      editor.setOption('minLines', 20);
      editor.setOption('autoScrollEditorIntoView', true);
      editor.setShowPrintMargin(false);
      editorPreviewHandler(editor);
      drawPreviewEvent(editor)();
    }
  });
}

function newPlatformPanel () {
  $('#dataPanel').html('');
  $('#loadingmodal').hide();
  $.get('/platforms-edit', function (html) {
    $('#modalTitle').html('New platform');
    $('#dataPanel').html(html);
    const editor = ace.edit('editor');
    editor.setTheme('ace/theme/monokai');
    editor.session.setMode('ace/mode/javascript');
    editor.resize();
    editor.setOption('maxLines', 100);
    editor.setOption('minLines', 20);
    editor.setOption('autoScrollEditorIntoView', true);
    editor.setShowPrintMargin(false);
    editorPreviewHandler(editor);
    drawPreviewEvent(editor)();
  });
}

function drawPreviewEvent (editor) {
  return function (delta) {
    console.log(delta);
    // delta.start, delta.end, delta.lines, delta.action
    const comments = new RegExp("//.*", 'mg');
    const platformContentRaw = editor.getValue().replace(comments, '');
    try {
      const platformContent = JSON.parse(platformContentRaw.trim());
      drawPlatformPreview(platformContent);
    } catch (e) {
      // show error?
    }
  };
}

function editorPreviewHandler (editor) {
  editor.session.on('change', drawPreviewEvent(editor));
}

function showErrorInModal (text) {
  $('#loadinindicator').hide();
  $('#errorBox').html(text);
  $('#errorBox').show();
}

function editPlatform () {
  $('#loadinindicator').show();
  $('#errorBox').hide();
  const editor = ace.edit('editor');
  const comments = new RegExp("//.*", 'mg');
  const platformContentRaw = editor.getValue().replace(comments, '');
  try {
    const platformContent = JSON.parse(platformContentRaw.trim());
    $.ajax({
      url: '/api/platforms/' + platformContent.name,
      type: 'PUT',
      data: JSON.stringify(platformContent),
      contentType: 'application/json',
      dataType: 'json',
      success: function (result) {
        if (result.error) {
          showErrorInModal(result.error);
          return;
        }
        updateWorkspaceAfterPlatformEdit(platformContent, activeWorkspace);
        console.log(result);
        getPlatformsList();
      },
      error: function () {
        showErrorInModal('Unexpected error.');
      }
    });
  } catch (e) {
    console.log(e);
    showErrorInModal('Invalid JSON. Please check your definition.');
  }
}

function saveNewPlatform () {
  $('#loadinindicator').show();
  $('#errorBox').hide();
  const editor = ace.edit('editor');
  const comments = new RegExp("//.*", 'mg');
  const platformContentRaw = editor.getValue().replace(comments, '');
  try {
    const platformContent = JSON.parse(platformContentRaw.trim());
    $.ajax({
      url: '/api/platforms',
      type: 'POST',
      data: JSON.stringify(platformContent),
      contentType: 'application/json',
      dataType: 'json',
      success: function (result) {
        if (result.error) {
          showErrorInModal(result.error);
          return;
        }
        console.log(result);
        getPlatformsList();
      },
      error: function () {
        showErrorInModal('Unexpected error.');
      }
    });
  } catch (e) {
    console.log(e);
    showErrorInModal('Invalid JSON. Please check your definition.');
  }
}

function deletePlatform (name) {
  $('#loadinindicator').show();
  $('#errorBox').hide();

  if (confirm('This action cannot be undone. Are you sure you want to delete "' + unescape(name) + '" Platform? This will impact all Workspaces using this Platform.')) {
    $.ajax({
      url: '/api/platforms/' + name,
      type: 'DELETE',
      success: function (result) {
        if (result.error) {
          showErrorInModal(result.error);
          return;
        }
        console.log(result);
        getPlatformsList();
      }
    });
  }
}

function deleteWorkspace (name, cb) {
  $('#loadinindicator').show();
  $('#errorBox').hide();

  if (confirm('This action cannot be undone. Are you sure you want to delete "' + unescape(name) + '" Workspace?')) {
    $.ajax({
      url: '/api/workspaces/' + name,
      type: 'DELETE',
      success: function (result) {
        if (result.error) {
          showErrorInModal(result.error);
          return;
        }
        if (cb) {
          return cb();
        }
        console.log(result);
        getWorkspacesList();
      }
    });
  }
}

function insertItem (name) {
  $.get('/api/platforms/' + name, function (platformItem) {
    console.log(platformItem);
    if (platformItem && platformItem.name && activeWorkspace && activeWorkspace.items) {
      const position = {
        x: 1,
        y: 1
      };
      if (platformItem.type === 'PETRI_DISH') {
        position.x = platformItem.diameter / 2;
        position.y = platformItem.diameter / 2;
      }
      activeWorkspace.items.push({
        'platform': platformItem.name,
        'name': getUniqueName(platformItem.name, 1, 'name', activeWorkspace.items),
        position,
        'content': [],
        platformData: platformItem
      });
      drawWorkspace(activeWorkspace);
    }
  });
}

function loadPlatformsDropdown () {
  $('#platformsDropDownContent').html('Loading...');
  $.get('/platforms-dropdown', function (html) {
    $('#platformsDropDownContent').html(html);
  });
}

function loadSerialPorts () {
  $.get('/serialports-dropdown', function (html) {
    $('#serialPort').html(html);
  });
  return false;
}

function getSelectedContent () {
  const selectedContent = d3.selectAll('circle.content').filter(function (c) {
    // console.log('well', well);
    return (c.selected === true);
  });
  const totalSelected = selectedContent.size();
  if (totalSelected) return selectedContent;

  return 0;
}

function goToDialog () {
  $('#calibrationPaneltitle').html('GoTo Calibration');
  $('#calibrationPanelData').html('');

  const selected = getSelectedContent();
  if (selected) {
    const node = d3.select(selected.node());
    const item = node.attr('item');
    const platform = node.attr('platform');
    const name = node.attr('name');
    const content = getContentByName(item, name);
    const port = $('#serialPort').val();
    if (!port) {
      return alert('Please select a serial port.');
    }

    $.ajax({
      url: '/calibration-goto-panel',
      type: 'POST',
      data: JSON.stringify({workspace: activeWorkspace, item, platform, name, content}),
      contentType: 'application/json',
      success: function (html) {
        $('#calibrationPanelData').html(html);
        $('#calibrationPanel').modal('show');
        $('#calibrationAction').unbind('click');
        $('#calibrationAction').click(buildGoToAction(activeWorkspace, item, platform, name, content));
      },
      error: function (e) {
        console.log(e);
        alert('Unexpected Error');
      }
    });
  }
}

function buildGoToAction (workspace, itemName, platformName, contentName) {
  return function () {
    saveWorkspace(workspace.name, workspace, function (w) {
      console.log('salvado...Executar comando...', w);
      const port = $('#serialPort').val();
      const baudrate = $('#baudRate').val();
      $.ajax({
        url: '/api/run-command/goto',
        type: 'POST',
        data: JSON.stringify({command: 'goto', workspace: w, itemName, platformName, contentName, baudrate, port}),
        contentType: 'application/json',
        success: function () {
          $('#calibrationPanel').modal('hide');
          $('#calibrationPanelData').html('');
          // $("#calibrationAction").click(function(){});
        },
        error: function (e) {
          console.log(e);
          alert('Unexpected Error');
        }
      });
    });
  };
}

function manualMove (action) {
  const port = $('#serialPort').val();
  const baudrate = $('#baudRate').val();
  const stepSizeXY = $('#controlStepSizeXY').val().trim();
  const stepSizeZ = $('#controlStepSizeZ').val().trim();
  const stepSizeP = $('#controlStepSizeP').val().trim();

  console.log('Moving:' + action, stepSizeXY, stepSizeZ);

  if (!port) {
    return alert('Please select a serial port.');
  }
  let axis;
  let distance;
  let command;
  switch (action) {
    case '+x':
      axis = 'x';
      distance = stepSizeXY;
      command = 'move';
      break;
    case '-x':
      axis = 'x';
      distance = '-' + stepSizeXY;
      command = 'move';
      break;
    case '+y':
      axis = 'y';
      distance = stepSizeXY;
      command = 'move';
      break;
    case '-y':
      axis = 'y';
      distance = '-' + stepSizeXY;
      command = 'move';
      break;
    case '+z':
      axis = 'z';
      distance = stepSizeZ;
      command = 'move';
      break;
    case '-z':
      axis = 'z';
      distance = '-' + stepSizeZ;
      command = 'move';
      break;
    case '+p':
      axis = 'p';
      distance = stepSizeP;
      command = 'move';
      break;
    case '-p':
      axis = 'p';
      distance = '-' + stepSizeP;
      command = 'move';
      break;
    case 'home-xyz':
      command = 'home';
      axis = 'xyz';
      break;
    case 'home-x':
      command = 'home';
      axis = 'x';
      break;
    case 'home-y':
      command = 'home';
      axis = 'y';
      break;
    case 'home-z':
      command = 'home';
      axis = 'z';
      break;
    case 'home-p':
      command = 'home';
      axis = 'p';
      break;
  }

  const options = {command, baudrate, port, axis, distance};
  console.log('Sending options:', options);

  $.ajax({
    url: '/api/run-command/' + command,
    type: 'POST',
    data: JSON.stringify(options),
    contentType: 'application/json',
    success: function () {

    },
    error: function (e) {
      console.log(e);
      alert('Unexpected Error');
    }
  });
}

function removeSpecialChars (unsafe) {
  return unsafe.replace(/[^A-Za-z0-9.\-\_]/g, '');
}

function onlyUnique (value, index, self) {
  return (self.indexOf(value) === index) && value;
}

function startTagEditing (obj, cid) {
  cid = unescape(cid);
  $('#tc_' + cid).hide();
  $('#tic_' + cid).show();
  $('#ti_' + cid).focus();
}

function updateContentTags (obj, cid, itemName, contentName, redraw) {
  console.log('update tags');
  $('#tc_' + cid).show();
  $('#tic_' + cid).hide();
  const rawTags = $('#ti_' + cid).val();
  const rawTagsArr = rawTags.split(',');
  let tags = rawTagsArr.map(function (t) {
    return removeSpecialChars(t.trim().toLowerCase());
  });
  tags = tags.filter(onlyUnique);
  $('#ti_' + cid).val(tags.join(','));

  itemName = decodeURI(itemName);
  contentName = decodeURI(contentName);
  const itemData = getItemByName(activeWorkspace, itemName);
  if (itemData && itemData.content && itemData.content.length) {
    for (let i = 0; i < itemData.content.length; i++) {
      if (itemData.content[i].name === contentName) {
        console.log('Editar:');
        console.log(itemData.content[i]);
        itemData.content[i].tags = tags;
        if (redraw) {
          drawWorkspace(activeWorkspace);
        }
      }
    }
  }
}

function drawProtocolPanel (workspace, activeProtocol, cb) {
  $.ajax({
    url: '/protocol-panel',
    type: 'POST',
    data: JSON.stringify({workspace, activeProtocol, protocolPanelExpandStatus}),
    contentType: 'application/json',
    // dataType: 'json',
    success: function (html) {
      $('#right').html(html);
      if (cb) cb();
    },
    error: function (e) {
      console.log(e);
      alert('Unexpected Error');
    }
  });
}

function sort (steps) {
  function compare (a, b) {
    if (a.order < b.order) {
      return -1;
    }
    if (a.order > b.order) {
      return 1;
    }
    return 0;
  }

  return steps.sort(compare);
}

function arrayMove (arr, oldIndex, newIndex) {
  if (newIndex >= arr.length) {
    let k = newIndex - arr.length + 1;
    while (k--) {
      arr.push(undefined);
    }
  }
  arr.splice(newIndex, 0, arr.splice(oldIndex, 1)[0]);
  return arr; // for testing
}

function changeStepOrder (el, currentOrder) {
  const newOrder = prompt('Move step to position #', currentOrder);
  if (newOrder === null || !newOrder.trim() || isNaN(newOrder.trim())) return false; // canceled
  if (activeProtocol && activeProtocol.steps && activeProtocol.steps.length && newOrder <= activeProtocol.steps.length && newOrder > 0) {
    activeProtocol.steps = sort(activeProtocol.steps);
    const newOrderInt = parseInt(newOrder.trim(), 10) - 1;
    arrayMove(activeProtocol.steps, --currentOrder, newOrderInt);
    let orderCount = 0;
    activeProtocol.steps.map(s => {
      s.order = ++orderCount;
    });
  }
  drawProtocolPanel(activeWorkspace, activeProtocol);
}

function createNewProtocol () {
  if (!activeWorkspace.name) {
    saveWorkspaceMenu(continueWithSave, 'Please first save your workspace');
  } else {
    continueWithSave();
  }

  function continueWithSave () {
    const newName = $('#newProtocolName').val();
    const newDescription = $('#newProtocolDescription').val();
    const newtemplate = $('#newProtocolTemplate').val();
    saveNewProtocol(newName, newDescription, newtemplate, function (hlp) {
      $('#new-protocol-modal').modal('hide');
      document.getElementById('newProtocolForm').reset();
      activeProtocol = hlp;
      drawProtocolPanel(activeWorkspace, activeProtocol);
      if (newtemplate === 'pcr_mix') {
        editProtocolTemplateUI();
      }
    });
    return false;
  }
  return false;
}

function editProtocolTemplateUI () {
  if (confirm('This will save your workspace first. Are you OK to continue?')) {
    saveWorkspace(activeWorkspace.name, activeWorkspace, function () {
      $('#dataPanel').html('');
      $('#loadingmodal').hide();
      $.get('/protocol-template-edit/' + activeProtocol.name, function (html) {
        if (html) {
          $('#modalTitle').html('Edit Protocol Template');
          $('#dataPanel').html(html);
          $('#listModal').modal('show');
        }
      });
    });
  }
}

function addGroupItemToTemplate () {
  const t = document.querySelector('#componentItemForTemplates');
  const l = document.querySelector('#component-groups');
  const clone = document.importNode(t.content, true);
  l.appendChild(clone);
}

function countInArray (array, what) {
  return array.filter(item => item === what).length;
}

function saveTemplateProtocol () {
  if (confirm('This will clean and regenerate your workspace and protocol steps. Are you OK to continue?')) {
    const componentsNames = $("input[name='itemNames[]']").map(function () { return $(this).val().trim(); }).get();
    let componentsFwPrimers = $("input[name='fwPrimers[]']").map(function () { return $(this).val().trim(); }).get();
    let componentsRvPrimers = $("input[name='rvPrimers[]']").map(function () { return $(this).val().trim(); }).get();
    let componentsTemplates = $("input[name='templates[]']").map(function () { return $(this).val().trim(); }).get();

    let errorValidation = '';
    componentsNames.map(i => {
      if (!i) errorValidation = 'Invalid component name (empty). Please choose a name';
      if (countInArray(componentsNames, i) >= 2) errorValidation = 'Invalid component name (duplicated). Please choose a diferent name';
    });

    componentsFwPrimers = componentsFwPrimers.map(i => {
      if (!i) errorValidation = 'Invalid component fwPrimer definition (empty). Please complete.';
      return i.split(',').map(s => s.trim()).filter(s => s);
    });

    componentsRvPrimers = componentsRvPrimers.map(i => {
      if (!i) errorValidation = 'Invalid component rvPrimer definition (empty). Please complete.';
      return i.split(',').map(s => s.trim()).filter(s => s);
    });

    componentsTemplates = componentsTemplates.map(i => {
      if (!i) errorValidation = 'Invalid component template definition (empty). Please complete.';
      return i.split(',').map(s => s.trim()).filter(s => s);
    });

    if (parseFloat($('#volLossCompensation').val().trim()) > 1 || parseFloat($('#volLossCompensation').val().trim()) < 0) {
      errorValidation = 'Volume loss compensation must be a number bewatween 0 and 1';
    }

    if (errorValidation) {
      alert(errorValidation);
      return false;
    }

    const components = [];
    for (let i = 0; i < componentsNames.length; i++) {
      components.push({
        name: componentsNames[i],
        fwPrimers: componentsFwPrimers[i],
        rvPrimers: componentsRvPrimers[i],
        templates: componentsTemplates[i]
      });
    }

    activeProtocol.templateDefinition = {
      'tube15Platform': $('#platform1').val(),
      'PCRtubePlatform': $('#platform2').val(),
      'tipsPlatform': $('#platform3').val(),
      'trashPlatform': $('#platform4').val(),
      'finalVol': parseFloat($('#final_vol').val().trim()),
      'volLossCompensation': parseFloat($('#volLossCompensation').val().trim()),
      'dntpsStock': parseFloat($('#dntps_stock').val().trim()),
      'dntpsFinal': parseFloat($('#dntps_final').val().trim()),
      'primerStock': parseFloat($('#primer_stock').val().trim()),
      'primerFinal': parseFloat($('#primer_final').val().trim()),
      'polVol': parseFloat($('#pol_vol').val().trim()),
      'templateVol': parseFloat($('#template_vol').val().trim()),
      'bufferStock': parseInt($('#buffer_stock').val().trim()),
      'bufferFinal': 1,
      components,
      latestRegenerateWorkflow: $('#regenerateWorkspace').is(':checked'),
      latestRegenerateProtocol: $('#regenerateProtocol').is(':checked')
    };

    console.log('activeProtocol', activeProtocol);

    saveProtocol(true, function (newProtocol, newWorkspace) {
      activeProtocol = newProtocol;
      console.log('Protocol saved.');
      if (newWorkspace) {
        activeWorkspace = newWorkspace;
      }
      drawWorkspace(activeWorkspace);
      drawProtocolPanel(activeWorkspace, activeProtocol);
      document.getElementById('templateProtocolForm').reset();
      $('#modalTitle').html('');
      $('#listModal').modal('hide');
      $('#dataPanel').html('');
    });
    return false;
  }
  return false;
}

const collapseStatus = {};

function saveCollapseState (obj) {
  const newState = !$(obj).hasClass('collapsed');
  const target = $(obj).data('target').replace('#', '');
  collapseStatus[target] = newState;
}

function saveNewProtocol (name, desc, template, cb) {
  try {
    const protocol = {
      name,
      description: desc,
      workspace: activeWorkspace.name || '',
      template,
      steps: []
    };
    $.ajax({
      url: '/api/hl-protocols',
      type: 'POST',
      data: JSON.stringify(protocol),
      contentType: 'application/json',
      dataType: 'json',
      success: function (result) {
        if (result.error) {
          alert(result.error);
          return;
        }
        cb(result.newProtocol);
      },
      error: function () {
        alert('Unexpected error.');
      }
    });
  } catch (e) {
    console.log(e);
    alert('Unexpected error.');
  }
}

function saveProtocol (isTemplate, cb) {
  if (activeProtocol) {
    if (isTemplate) {
      activeProtocol.isTemplate = true;
    }
    try {
      $.ajax({
        url: '/api/hl-protocols/' + activeProtocol.name,
        type: 'PUT',
        data: JSON.stringify(activeProtocol),
        contentType: 'application/json',
        dataType: 'json',
        success: function (result) {
          if (result.error) {
            alert(result.error);
            return;
          }
          showNotification('ok', 'Protocol saved');
          if (cb) cb(result.protocol, result.newWorkspace);
        },
        error: function () {
          alert('Unexpected error.');
        }
      });
    } catch (e) {
      console.log(e);
      alert('Unexpected error.');
    }
  }
}

function deleteProtocol (name) {
  if (confirm('This action cannot be undone. Are you sure you want to delete "' + unescape(name) + '" Protocol? This will impact all Workspaces using this Protocol.')) {
    $.ajax({
      url: '/api/hl-protocols/' + name,
      type: 'DELETE',
      success: function (result) {
        if (result.error) {
          alert(result.error);
          return;
        }
        console.log(result);
        drawProtocolPanel(activeWorkspace, activeProtocol);
      }
    });
  }
}

function loadProtocol (name) {
  $.get('/api/hl-protocols/' + name, function (hlp) {
    if (hlp) {
      activeProtocol = hlp;
      drawProtocolPanel(activeWorkspace, activeProtocol);
    } else {
      alert('Protocol not found');
    }
  });
}

function closeProtocol () {
  toggleProtocolPanel(true);
  activeProtocol = null;
  drawWorkspace(activeWorkspace);
}
let protocolPanelExpandStatus = 'collapsed';

function toggleProtocolPanel (close) {
  if ($('#middle').hasClass('col-sm-8') && !close) {
    // expand
    $('#middle').removeClass('col-sm-8');
    $('#middle').addClass('col-sm-6');
    $('#right').removeClass('col-2');
    $('#right').addClass('col-4');
    $('#expand-protocol-icon').removeClass('fa-arrow-left');
    $('#expand-protocol-icon').addClass('fa-arrow-right');
    protocolPanelExpandStatus = 'expanded';
  } else {
    // collapse
    $('#middle').removeClass('col-sm-6');
    $('#middle').addClass('col-sm-8');
    $('#right').removeClass('col-4');
    $('#right').addClass('col-2');
    $('#expand-protocol-icon').removeClass('fa-arrow-right');
    $('#expand-protocol-icon').addClass('fa-arrow-left');
    protocolPanelExpandStatus = 'collapsed';
  }
}

function expandProtocolPanel (event) {
  event.preventDefault();
  event.stopPropagation();
  toggleProtocolPanel();
  drawWorkspace(activeWorkspace);
  return false;
}

function getNextOrder (steps) {
  steps = steps || [];
  let orders = steps.map(function (ind) {
    return ind.order;
  });
  orders = orders.length ? orders : [0];
  let nextOrder = Math.max.apply(Math, orders);
  return ++nextOrder;
}

function addStep () {
  if (activeProtocol) {
    const ord = getNextOrder(activeProtocol.steps);
    const emptyStep = {
      order: ord,
      name: getUniqueName('step', ord, 'name', activeProtocol.steps, true),
      type: ''
    };
    if ('steps' in activeProtocol) {
      activeProtocol.steps.push(emptyStep);
    } else {
      activeProtocol.steps = [emptyStep];
    }
    drawProtocolPanel(activeWorkspace, activeProtocol);
  }
}

function deleteStep (stepName, redraw) {
  if (confirm('Do you want to remove this step?')) {
    stepName = decodeURI(stepName);
    if (activeProtocol && activeProtocol.steps && activeProtocol.steps.length) {
      for (let i = 0; i < activeProtocol.steps.length; i++) {
        if (activeProtocol.steps[i].name === stepName) {
          console.log('borrar:');
          console.log(activeProtocol.steps[i]);
          activeProtocol.steps.splice(i, 1);
        }
      }
      // reorder
      let newOrder = 0;
      activeProtocol.steps.map(s => {
        s.order = ++newOrder;
      });
      if (redraw) {
        drawProtocolPanel(activeWorkspace, activeProtocol);
      }
    }
  }
}

function exportStep (stepName) {
  stepName = decodeURI(stepName);
  if (activeProtocol && activeProtocol.steps && activeProtocol.steps.length) {
    for (let i = 0; i < activeProtocol.steps.length; i++) {
      if (activeProtocol.steps[i].name === stepName) {
        download('HLPstep_' + activeProtocol.name + '_' + activeProtocol.steps[i].name + '.json', JSON.stringify(activeProtocol.steps[i], null, 2));
      }
    }
  }
}

function focusStep (obj, id) {
  $('.ccstep').removeClass('selected-step');
  $('.ccstep').addClass('step-list-item');
  $('#' + id).removeClass('step-list-item');
  $('#' + id).addClass('selected-step');
}

function updateStepName (inputObj, stepName, redraw) {
  console.log('updateStepName', inputObj);
  console.log('new Name:', $(inputObj).val());
  stepName = decodeURI(stepName);
  console.log('stepName', stepName);
  if (stepName === $(inputObj).val()) return;
  if (activeProtocol && activeProtocol.steps && activeProtocol.steps.length) {
    for (let i = 0; i < activeProtocol.steps.length; i++) {
      if (activeProtocol.steps[i].name === stepName) {
        activeProtocol.steps[i].name = getUniqueName($(inputObj).val(), 0, 'name', activeProtocol.steps, true);
        $(inputObj).val(activeProtocol.steps[i].name);
        if (redraw) {
          drawProtocolPanel(activeWorkspace, activeProtocol);
        }
      }
    }
  }
}

function updateStepSourceBy (obj, stepName) {
  stepName = decodeURI(stepName);
  const newVal = decodeURI($(obj).val());
  updateStep(stepName, 'definition.source.by', newVal, false);
  updateStep(stepName, 'definition.source.value', '', false);
  updateStep(stepName, 'definition.source.treatAs', 'same', true);
}

function updateStepTargetBy (obj, stepName) {
  stepName = decodeURI(stepName);
  const newVal = decodeURI($(obj).val());
  updateStep(stepName, 'definition.target.by', newVal, false);
  updateStep(stepName, 'definition.target.value', '', true);
}

function updateStepSourceTreatAs (obj, stepName) {
  stepName = decodeURI(stepName);
  const newVal = decodeURI($(obj).val());
  updateStep(stepName, 'definition.source.treatAs', newVal, true);
}

function updateStepTipFrom (obj, stepName) {
  stepName = decodeURI(stepName);
  const newVal = decodeURI($(obj).val());
  updateStep(stepName, 'definition.tip.item', newVal, true);
}

function updateStepTipTo (obj, stepName) {
  stepName = decodeURI(stepName);
  const newVal = decodeURI($(obj).val());
  updateStep(stepName, 'definition.tip.discardItem', newVal, true);
}

function updateStepTipMode (obj, stepName) {
  stepName = decodeURI(stepName);
  const newVal = decodeURI($(obj).val());
  updateStep(stepName, 'definition.tip.mode', newVal, true);
}

function updateStepVolumeType (obj, stepName) {
  stepName = decodeURI(stepName);
  const newVal = decodeURI($(obj).val());
  updateStep(stepName, 'definition.volume.type', newVal, true);
}

function updateStepVolumeTag (obj, stepName) {
  stepName = decodeURI(stepName);
  const newVal = decodeURI($(obj).val());
  updateStep(stepName, 'definition.volume.tag', newVal, true);
}

function updateStepVolume (obj, stepName) {
  stepName = decodeURI(stepName);
  const newVal = decodeURI($(obj).val());
  updateStep(stepName, 'definition.volume.value', newVal, true);
}

function updateStepType (obj, stepName) {
  stepName = decodeURI(stepName);
  const newVal = $(obj).val();
  updateStep(stepName, 'type', newVal, false);
  switch (newVal) {
    case 'SIMPLE_PIPETTIN':
      updateStep(stepName, 'definition', {source: {item: '', by: 'name'}, target: {item: '', by: 'name'}, volume: {type: 'fixed_each', value: 0}, tip: {mode: 'reuse'}}, true);
      break;
    case 'WAIT':
      updateStep(stepName, 'definition', {seconds: 0}, true);
      break;
    case 'COMMENT':
      updateStep(stepName, 'definition', {text: ''}, true);
      break;
    case 'HUMAN':
      updateStep(stepName, 'definition', {text: ''}, true);
      break;
    case 'MIX':
      updateStep(stepName, 'definition', {target: {item: '', by: 'name'}, mix: {type: 'content', percentage: 90, count: 2}, tip: {mode: 'reuse'}}, true);
      break;
    case '':
      updateStep(stepName, 'definition', {}, true);
      break;
  }
}

function updateStepSeconds (obj, stepName) {
  stepName = decodeURI(stepName);
  const newVal = decodeURI($(obj).val());
  updateStep(stepName, 'definition.seconds', newVal, true);
}

function updateStepMixPorcentage (obj, stepName) {
  stepName = decodeURI(stepName);
  const newVal = decodeURI($(obj).val());
  updateStep(stepName, 'definition.mix.percentage', newVal, true);
}

function updateStepMixCount (obj, stepName) {
  stepName = decodeURI(stepName);
  const newVal = decodeURI($(obj).val());
  updateStep(stepName, 'definition.mix.count', newVal, true);
}

function updateStepMixType (obj, stepName) {
  stepName = decodeURI(stepName);
  const newVal = decodeURI($(obj).val());
  updateStep(stepName, 'definition.mix.type', newVal, true);
}

function updateStepComment (obj, stepName) {
  stepName = decodeURI(stepName);
  const newVal = decodeURI($(obj).val());
  updateStep(stepName, 'definition.text', newVal.trim(), true);
}

function updateStepHummanTask (obj, stepName) {
  stepName = decodeURI(stepName);
  const newVal = decodeURI($(obj).val());
  updateStep(stepName, 'definition.text', newVal.trim(), true);
}

function updateStepItem (obj, path, stepName) {
  stepName = decodeURI(stepName);
  const newVal = decodeURI($(obj).val());
  updateStep(stepName, 'definition.' + path, newVal, true);
}

function updateStepEntryName (obj, path, stepName, stepType) {
  stepName = decodeURI(stepName);
  const newVal = decodeURI($(obj).val());
  updateStep(stepName, 'definition.' + path, newVal, stepType !== 'SIMPLE_PIPETTIN');
  if (stepType === 'SIMPLE_PIPETTIN') {
    updateStep(stepName, 'definition.source.treatAs', 'same', true);
  }
}

function updateStepEntryTag (obj, path, stepName, stepType) {
  stepName = decodeURI(stepName);
  const newVal = decodeURI($(obj).val());
  updateStep(stepName, 'definition.' + path, newVal, stepType !== 'SIMPLE_PIPETTIN');
  if (stepType === 'SIMPLE_PIPETTIN') {
    updateStep(stepName, 'definition.source.treatAs', 'same', true);
  }
}

function updateStep (stepName, field, value, redraw) {
  if (activeProtocol && activeProtocol.steps && activeProtocol.steps.length) {
    for (let i = 0; i < activeProtocol.steps.length; i++) {
      if (activeProtocol.steps[i].name === stepName) {
        // activeProtocol.steps[i][field] = value;
        accessIndex(activeProtocol.steps[i], field, value);
        if (redraw) {
          drawProtocolPanel(activeWorkspace, activeProtocol);
        }
      }
    }
  }
}

function accessIndex (obj, is, value) {
  if (typeof is === 'string') {
    return accessIndex(obj, is.split('.'), value);
  } else if (is.length === 1 && value !== undefined) {
    const v = obj[is[0]] = value;
    return v;
  } else if (is.length === 0) {
    return obj;
  }
  return accessIndex(obj[is[0]], is.slice(1), value);
}

function killProtocolProcess () {
  $.ajax({
    url: '/api/run-command/kill',
    type: 'POST',
    contentType: 'application/json',
    data: JSON.stringify({a: 1}),
    dataType: 'json',
    success: function (result) {
      console.log(result);
      if (result.error) {
        alert(result.error);
        return;
      }
    },
    error: function () {
      alert('Unexpected error.');
    }
  });
  return;
}

function runProtocol (cb) {
  const port = $('#serialPort').val();
  const baudrate = $('#baudRate').val();

  if (!port) {
    return alert('Please select a serial port.');
  }

  if (!activeWorkspace.name) {
    alert('Please save your workspace first and try again.');
    return;
  }
  saveWorkspace(activeWorkspace.name, activeWorkspace, function () {
    saveProtocol(false, function () {
      $.ajax({
        url: '/api/run-command/execute-protocol',
        type: 'POST',
        data: JSON.stringify({port, baudrate, hlp: activeProtocol, workspaceName: activeWorkspace.name}),
        contentType: 'application/json',
        dataType: 'json',
        success: function (result) {
          console.log(result);
          if (result.error) {
            alert(result.error);
            return;
          }
          if (cb) cb(result);
        },
        error: function () {
          alert('Unexpected error.');
        }
      });
    });
  });
}

function viewProtocolOutput (cb) {
  if (!activeWorkspace.name) {
    alert('Please save your workspace first and try again.');
    return;
  }
  saveWorkspace(activeWorkspace.name, activeWorkspace, function () {
    saveProtocol(false, function () {
      $.ajax({
        url: '/api/run-command/execute-protocol',
        type: 'POST',
        data: JSON.stringify({output: true, hlp: activeProtocol, workspaceName: activeWorkspace.name}),
        contentType: 'application/json',
        dataType: 'json',
        success: function (result) {
          console.log(result);
          if (result.error) {
            alert(result.error);
            return;
          }
          if (result.output) {
            // result.middleLevelProtocol
            download(result.middleLevelProtocol.name + '.json', JSON.stringify(result.middleLevelProtocol, null, 2));
          }
          if (cb) cb(result);
        },
        error: function () {
          alert('Unexpected error.');
        }
      });
    });
  });
}

function download (filename, text) {
  const element = document.createElement('a');
  element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(text));
  element.setAttribute('download', filename);
  element.style.display = 'none';
  document.body.appendChild(element);
  element.click();
  document.body.removeChild(element);
}

function editProtocol (name) {
  alert('TODO: Edit protocol name and description.');
}

function loadProtocolFromOtherWorkspace () {
  alert('TODO: List all protocols and allow load.');
}
