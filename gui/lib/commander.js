const config = require('config');
const proc = require('child_process');

let running = false;
let child;
const communicationMode = config.communicationMode || 'process';

function commander (req) {
  function buildCommand (options) {
    const args = ['-u', config.protocol2gcodePath];
    Object.keys(options).map(o => {
      args.push('--' + o);
      args.push(`${options[o]}`);
    });
    return {
      command: 'python3',
      args
    };
  }

  function kill () {
    // emit a kill protocol event through the socket, received by the commander service daemon.
    const killOptions = {
      reason: 'none'
    };
    req.io.emit('kill_commander', killOptions);

    if (child) {
      child.kill();
    }
    running = false;
    req.io.emit('console', '\nForce kill!');
  }

  function executeCommand (command, args) {
    if (running === true) {
      console.log('Wait for current execution.');
      req.io.emit('console', '> Wait for current execution! The command was not executed.\n');
      return;
    }
    console.log('Ejecutando: ', command, args);
    req.io.emit('console', '> ' + command + ' ' + args.join(' ') + '\n');
    running = true;
    child = proc.spawn(command, args, {
      detached: true,
      stdio: [ 'inherit' ]
    });
    child.unref();
    child.stdout.on('data', function (data) {
      console.log('command stdout:', data.toString());
      req.io.emit('console', data.toString());
    });
    child.stderr.on('data', function (data) {
      console.log('command stderr:', data.toString());
      req.io.emit('console', data.toString());
    });

    child.on('exit', function (code) {
      running = false;
      console.log('Execution end: ', code);
      req.io.emit('console', '> Execution finished. Exit code: ' + code + '\n');
    });

    child.on('error', function (err) {
      running = false;
      req.io.emit('console', '> Execution error:' + JSON.stringify(err) + '\n');
    });
  }

  function runCalibrationCommand (command, port1, port2, baudrate, workspaceName, itemName, contentName) {
    const options = {
      port: port1,
      baudrate,
      calibration: 'goto',
      workspace: workspaceName,
      item: itemName,
      content: contentName
    };

    const ex = buildCommand(options);
    if (communicationMode === 'ws') {
      console.log(`CommunicationMode: ${communicationMode}`);
      console.log('Sending websocket message p2g_command', options);
      req.io.emit('p2g_command', options);
      return;
    }
    executeCommand(ex.command, ex.args);
  }

  function runCommand (options) {
    const ex = buildCommand(options);
    if (communicationMode === 'ws') {
      console.log(`CommunicationMode: ${communicationMode}`);
      console.log('Sending websocket message p2g_command', options);
      req.io.emit('p2g_command', options);
      return;
    }
    executeCommand(ex.command, ex.args);
  }

  return {
    runCalibrationCommand,
    runCommand,
    kill
  };
}

module.exports = commander;
