# Systemd units for pipetting-grbl

Unit definitions reside at `~/.config/systemd/user/`.

After editing a unit, reload them with `systemctl --user daemon-reload`.

**Importantly**, run `sudo loginctl enable-linger $USER` at least once as the `pi` user.

Also run `sudo apt-get install python-systemd python3-systemd` to install the systemd modules required by the "commander" unit.

Some status info is printed on login by bash (see ~/.bashrc).
use standard systemctl commands to check on the services manually.
For example:

```bash
systemctl --user status nodegui.service
systemctl --user status commander.service
```

Useful bash aliases:

```bash
alias commander_restart='systemctl --user restart commander.service; journalctl --user-unit commander -f'
alias gui_restart='systemctl --user restart nodegui.service; journalctl --user-unit nodegui -f'
```

## Node "GUI" unit

Located at: `systemd.units/nodegui.service`

For development, this file uses `nodemon` instead of `node`. A compatible (legacy) nodemon version was installed with:

```bash
sudo npm install -g nodemon@2.0.12 # Details at https://github.com/remy/nodemon/issues/1948#issuecomment-953665876
```

The unit file should use `node` instead, for deployment.

## Python3 "commander" unit

Located at: `systemd.units/commander.service`

Learn more about it in `protocol2gcode/commander.py `.
