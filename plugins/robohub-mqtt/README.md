# robohub-mqtt

MQTT for RoboHub: a Mosquitto broker the keeper runs and looks after, and the bus
applications and devices meet on.

## What the keeper does with it

- **Installs what it needs** through the doctor: `mosquitto` and
  `mosquitto_passwd` (`apt install mosquitto`).
- **Runs its own broker** as a user service (`robohub-mqtt.service`) on port 1884,
  beside any system Mosquitto on 1883, with its configuration, password file, ACL
  file and persistence under `~/.rho/keeper/services/mqtt/`.
- **Listens on this machine** (127.0.0.1) unless the admin opens it to the network
  for devices; nobody connects without a broker user.
- **Makes a broker user for every application that binds the bus**, with a random
  password in the application's workspace, allowed the topics its manifest names:

  ```yaml
  bind:
    robohub.bus:
      providers: [robohub-provider-mqtt]
  bus:
    publish: [shelly/+/rpc]
    subscribe: [shelly/+/status/#, shelly/+/online]
  ```

  The application is told where the broker is (`ROBOHUB_BUS_URL`), its user
  (`ROBOHUB_BUS_USER`) and its password file (`ROBOHUB_BUS_PASSWORD_FILE`).
- **Makes a broker user for a device** an admin adds, allowed its own topic prefix.

The broker reloads its users and rules without dropping its connections.
