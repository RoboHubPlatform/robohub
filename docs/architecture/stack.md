# The firmware stack

What runs on a board, and how a reading leaves it. The host side — the gateway,
Mesh and the applications — is in {ref}`architecture/index`.

```text
                            rho protocol  (IDL)
                    one schema ──┬───────────────┬──
                                 │ C packed       │ Rho / Go
                                 ▼                ▼
┌───────────────────────────────────────────┐   ┌────────────────────┐
│               robohub-core                │   │  the gateway       │
│   event bus · scheduler · apps · diag     │   └────────────────────┘
└───────────────▲───────────────────────────┘
                │ publish / subscribe
      ┌─────────┴──────────┐
      │  robohub-telemetry │  filter · decimate · route · logs
      └───┬────────────┬───┘
          ▼            ▼
 ┌─────────────────┐ ┌──────────────────────┐
 │robohub-transport│ │ net (robohub-common) │
 │ COBS · Fletcher │ │ Wi-Fi and sockets    │
 │ sessions · tags │ │                      │
 └───┬─────────────┘ └──────┬───────────────┘
     ▼                      ▼
 USB CDC / UART / RS-485    TCP / UDP over Wi-Fi or Ethernet
```

## The modules

| Module | What it is |
|--------|------------|
| `robohub-common` | The contracts: the HAL (gpio, i2c, spi, uart, rs485, onewire, adc, pwm, timer, …), the driver interfaces (temperature, humidity, pressure, light, …), the OSAL and the network contract `robohub/net.h`. Weak defaults where a platform may be absent. |
| `robohub-core` | The application runtime: the event bus, the scheduler, the app lifecycle, diagnostics. Bare-metal OSAL defaults. |
| `robohub-transport` | Turns a byte stream into validated frames: COBS, a Fletcher-16 check, a byte-at-a-time parser, and the authenticated sessions of `secure.h`. No allocation. |
| `robohub-telemetry` | Binds the event bus to sinks (transport, socket) with per-event decimation and log interception. |
| `robohub-freertos` | Middleware: the OSAL over FreeRTOS. |
| `robohub-drivers` | Device drivers, the sensor module boards Mesh fits to a node, and the examples a node image is built from. |
| `robohub-devices` | Integrations for network devices — plugs, inverters — that a gateway or Mesh reaches over HTTP, MQTT or Modbus. |
| `robohub-pico`, `robohub-esp32`, `robohub-stm32`, `robohub-avr`, `robohub-linux` | Platforms: the HAL on a family of parts, its board support packages and, where there is one, its network port. |

## One reading, end to end

A temperature driver publishes its reading on the event bus; it names no
transport.

1. `robohub-core` carries the event to its subscribers.
2. `robohub-telemetry`, subscribed to that event, writes the payload to every
   enabled sink — a transport and, at once, a socket if one is registered.
3. `robohub-transport` frames it: `msg_id · tx_id · payload_len · payload ·
   check`, little-endian, COBS-encoded, `0x00`-delimited. With a session open,
   the payload area also carries the session id, a counter and a tag
   ({ref}`secure telemetry <architecture/secure-telemetry>`).
4. The link writes the bytes — USB CDC, a UART or a socket.

The payload is the packed struct a `rho protocol` schema generates, so the
gateway decodes the same bytes into the same value. What happens after that is
{ref}`architecture/reading`.

## The rule that holds it together

Every platform-dependent thing has a contract and a weak default low in the tree
(the OSAL in core, the network in `common`), and a platform or middleware
supplies the strong definition. A program is the same whether the RTOS, the
network or the sensor is there — and a board that has none of them still links.

## The network ports

The network contract is implemented on the Pico W (`pico_net.c`, over lwIP's raw
API) and on Linux (`linux_net.c`); the POSIX test in `robohub-common` is the
reference. The ESP32 port, over `esp_netif` and `esp_wifi`, is not written yet.
See {ref}`networking <architecture/networking>`.
