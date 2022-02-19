# GUI

## Structure

En backend de NodeJS.

Todo empieza en "bin/www", que levanta un servidor http de Node y sirve lo que está en "public/".

Para cada ruta o path del URL hay un handler en app.js.

La ruta principal "/" va a "routes/index.js" que de acuerdo al URL renderea algun template de la carpeta "views/".

Tamibén está lo que devuelve JSON en "rotes/mainApi.js"

Las funciones del HTML estan todas en "public/js/app.js".
Por ejemplo "saveNewPlatform()" hace un "POST" request a la API de platforms para guardar el JSON de una platform en mongo.

Observaciones:

* las rutas de un router ("routes/") son relativas a como se declararon en el "app.js" (usando el comando "app.use()").
* en los request handlers, "res.json" es equivalente a un "return()" de un objeto json en otros lenguajes. Podria ser "res.send" para mandar texto plano, etc.
* Las formas de los contents son dibujadas por "public/js/app.js drawContent()". El orden de los elementos del SVG (en "z") corresponde con el orden del agregado de elementos en "drawContent()".
* Los colorcitos de los tags se arman por hash en "views/workspacePanel.ejs".
* No se puede compartir el código del frontend (en "public") y del backend (en "views" y "routes") al mismo tiempo.
* El joystick está en "public/js/joystick.js".
* Hay un "public/css/style.css". El "#" es un "id" de un HTML tag, y el "." corresponde a una "clase" de un HTML tag.

## Requirements

- node.js
- mongodb > 2.6

```bash
sudo apt install nodejs npm pkg-config libusb-1.0-0-dev libudev-dev
sudo systemctl enable mongodb
```

### Building and installing mongodb 3.2.12 on Raspbian 32-bit

Mongo needs to be > 2.6 to work with the node driver. see: https://mongobooster.useresponse.com/topic/wire-version

I followed this guide: https://koenaerts.ca/compile-and-install-mongodb-on-raspberry-pi/

#### Prepare

```bash
sudo apt update
sudo apt upgrade
sudo apt install wget scons build-essential
sudo apt install libboost-filesystem-dev libboost-program-options-dev libboost-system-dev libboost-thread-dev
sudo apt install python-pymongo

mkdir -p mongo/install
cd mongo/install
wget https://fastdl.mongodb.org/src/mongodb-src-r3.2.12.tar.gz
# https://github.com/mongodb/mongo/archive/r3.2.12.tar.gz
tar xvf mongodb-src-r3.2.12.tar.gz
cd mongodb-src-r3.2.12

sudo dd if=/dev/zero of=/mytempswapfile bs=1024 count=524288
sudo chmod 0600 /mytempswapfile
sudo mkswap /mytempswapfile
sudo swapon /mytempswapfile
```

Prepare some more:

```bash
cd src/third_party/mozjs-38/
./get_sources.sh
./gen-config.sh arm linux
cd -
```

#### Build

First edit some files:

- Add `#include sys/sysmacros.h` to the file `src/mongo/db/storage/mmap_v1/mmap_v1_engine.cpp`

> There are some warnings treated as errors by cc1plus, so disable that behaviour and compile anyway. I skipped compilation of mongos.

Then build:

```bash
scons mongo mongod --wiredtiger=off --mmapv1=on --disable-warnings-as-errors  # guessing i do not need mongos
```

Reduce binary sizes:

```bash
strip -s mongo
strip -s mongod
```

#### Compilation notes

At first i tried to compile by ignoring two warnings by adding lines to the SConstruct file after `if myenv.ToolchainIs('clang', 'gcc')`:

```
        # AddToCCFLAGSIfSupported(myenv, '-Wno-parentheses')
        # AddToCCFLAGSIfSupported(myenv, '-Wnonnull-compare')
```

But the `nonnull-compare` warning was still raised as an error. I do not know what I am doing... so please help improve this if you know how :)

I did not look at all warnings during compilation so there may be other type of ignored warnings. Like "-Wstringop-truncation" (?)


#### Install and cleanup

Install:

```bash
cd build/opt/mongo
sudo cp mongo mongod /usr/local/bin/
```

Cleanup:

```bash
reboot
sudo swapoff /mytempswapfile
sudo rm /mytempswapfile
```

#### Configure mongod

Edit `/etc/mongod.conf` such that:

```
# mongod.conf

# for documentation of all options, see:
#   http://docs.mongodb.org/manual/reference/configuration-options/

# Where and how to store data.
storage:
  dbPath: /var/lib/mongodb
  journal:
    enabled: true
  engine: mmapv1
#  mmapv1:
#  wiredTiger:

# where to write logging data.
systemLog:
  destination: file
  logAppend: true
  path: /var/log/mongodb/mongod.log

# network interfaces
net:
  port: 27017
  bindIp: 127.0.0.1
```

The most important bit is the `engine: mmapv1` setting.

#### Enable run on boot

Using `/etc/rc.local`, adding the following line before `exit 0`:

```bash
mongod --config /etc/mongod.conf
```

**NOT USED**. Enable unit service:

```bash
sudo systemctl enable mongodb
```

**NOT USED**. Using init:

* `/etc/init.d/mongodb`
* Which uses the config file: `/etc/mongodb.conf`

### Manually start mongod

```bash
sudo mongod --storageEngine=mmapv1
```

### Install mongotools

https://github.com/mongodb/mongo-tools

The defaults from raspberry pi repos worked for the `mongoimport` command.

See `defaults/README.md` for usage examples.

## Start the GUI

There is a systemctl service unit for this now. See files in the `systemd.units` directory.

Open the GUI by visiting http://localhost:3333

To start it manually, `cd` to the `gui` directory and run:

```bash
npm install  # is this necessary?
node bin/www
```

## TODO

- refactor frontend (app.js)
- error handling for protocol builder (now the step is skipped if there is a missing requirement)
- global config in mongo (area size, etc)
- import  steps
- item overwrite options (color, max volume, default heights)
- do not allow to refresh the page
- enhance content selection and multi tag
- allow background for petri and rotation option 
- allow "all" in targets/sources selection in protocol step

## Bugs

- Step selection is not working sometimes
- Save protocol is not saving if you are in a text area (programate click)
