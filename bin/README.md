# mongodb 3.2.12 binaries

Compiled for 32-bit Raspbian in the Raspberry Pi 4.

See notes at `gui/README.md`.

## Startup commands

    sudo mongod --storageEngine=mmapv1

### Repair unclean shutdown

    sudo mongod --storageEngine=mmapv1 --repair
    sudo mongod --storageEngine=mmapv1

## CLI shell

    mongod
