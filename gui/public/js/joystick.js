/* global $ manualMove */
dragElement(document.getElementById('joystick'));

function dragElement (elmnt) {
  let pos1 = 0;
  let pos2 = 0;
  let pos3 = 0;
  let pos4 = 0;
  if (document.getElementById(elmnt.id + '-header')) {
    // if present, the header is where you move the DIV from:
    document.getElementById(elmnt.id + '-header').onmousedown = dragMouseDown;
  } else {
    // otherwise, move the DIV from anywhere inside the DIV:
    elmnt.onmousedown = dragMouseDown;
  }

  function dragMouseDown (e) {
    e = e || window.event;
    e.preventDefault();
    // get the mouse cursor position at startup:
    pos3 = e.clientX;
    pos4 = e.clientY;
    document.onmouseup = closeDragElement;
    // call a function whenever the cursor moves:
    document.onmousemove = elementDrag;
  }

  function elementDrag (e) {
    e = e || window.event;
    e.preventDefault();
    // calculate the new cursor position:
    pos1 = pos3 - e.clientX;
    pos2 = pos4 - e.clientY;
    pos3 = e.clientX;
    pos4 = e.clientY;
    // set the element's new position:
    elmnt.style.top = (elmnt.offsetTop - pos2) + 'px';
    elmnt.style.left = (elmnt.offsetLeft - pos1) + 'px';
  }

  function closeDragElement () {
    // stop moving when mouse button is released:
    document.onmouseup = null;
    document.onmousemove = null;
  }
}

function toggleManualControl () {
  $('#joystick').toggle();
  if ($('#controlMenuButton').hasClass('btn-secondary')) {
    $('#controlMenuButton').removeClass('btn-secondary');
    $('#controlMenuButton').addClass('btn-dark');
    $('#joystick').focus();
  } else {
    $('#controlMenuButton').removeClass('btn-dark');
    $('#controlMenuButton').addClass('btn-secondary');
  }
}

$(document).ready(function () {
  $('#joystick').focusin(function () {
    $('#joystick-keyboard').show();
  });
  $('#joystick').focusout(function () {
    $('#joystick-keyboard').hide();
  });
});

function glow (elementSelector) {
  $(elementSelector).addClass('glow');
  setTimeout(function () {
    $(elementSelector).removeClass('glow');
  }, 200);
}

function joystickKeyPress (inputObj, e) {
  switch (e.keyCode) {
    case 87:
      // up
      manualMove('-y');
      glow('#joy_sub_y');
      break;
    case 83:
      // down
      manualMove('+y');
      glow('#joy_add_y');
      break;
    case 65:
      // left
      manualMove('-x');
      glow('#joy_sub_x');
      break;
    case 68:
      // rigth
      manualMove('+x');
      glow('#joy_add_x');
      break;
    case 82:
      // Z up
      manualMove('+z');
      glow('#joy_add_z');
      break;
    case 70:
      // Z down
      manualMove('-z');
      glow('#joy_sub_z');
      break;
    case 84:
      // P up
      manualMove('+p');
      glow('#joy_add_p');
      break;
    case 71:
      // P down
      manualMove('-p');
      glow('#joy_sub_p');
      break;
    case 90:
      // z home
      manualMove('home-z');
      glow('#joy_home_z');
      break;
    case 89:
      // y home
      manualMove('home-y');
      glow('#joy_home_y');
      break;
    case 88:
      // x home
      manualMove('home-x');
      glow('#joy_home_x');
      break;
    case 72:
      // zxy home
      manualMove('home-xyz');
      glow('#joy_home_xyz');
      break;
    case 80:
      // p home
      manualMove('home-p');
      glow('#joy_home_p');
      break;

  }
}
