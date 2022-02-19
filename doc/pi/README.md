# GUI Development utilities

For some of these X11 forwarding through SSH is good enough.

But if you must use UGS then X11 forwarding will not work well (a Java thing).

## bCNC and others through SSH

Setup SSH and X11 forwarding on the Pi (see: the internet).

Connect to your Pi with `ssh` using the `-X` option. Run `python -m bCNC` to start bCNC, and display it's GUI on your local machine.

## Through RDP

### On the Pi (remote)

Install XFCE: `sudo apt install xfce4`

Install xrdp: `sudo apt install xrdp`

Also useful: Arduino IDE, bCNC, UGS, ...

### On your machine (client)

Install Remmina and connect using the RDP protocol.
