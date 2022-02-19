# Start on boot

Este no funcionaba porque estaba "masked":

https://askubuntu.com/questions/61503/how-to-start-mongodb-server-on-system-start

Se puede des-enmascarar, es una version mas fuerte de "disable":

https://askubuntu.com/questions/919108/error-unit-mongodb-service-is-masked-when-starting-mongodb

https://askubuntu.com/questions/710420/why-are-some-systemd-services-in-the-masked-state

## /etc/rc.local

No hay un "service" de systemctl para mongod.

Agregar esta linea a `/etc/rc.local`:

    mongod --config /etc/mongod.conf

Tal que `/etc/mongod.conf` contenga:

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

######## Y SIGUE ... ######
```

Probar is anda corriendo `sudo mongod --config /etc/mongod.conf`

Si tira error de que falta `/var/log/mongodb/mongod.log`, crearlo con `sudo touch /var/log/mongodb/mongod.log`.
