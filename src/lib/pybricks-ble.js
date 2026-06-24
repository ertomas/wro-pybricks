// pybricks-ble.js
// ---------------------------------------------------------------------------
// Comunicación con un hub Pybricks por Web Bluetooth.
//
// Módulo independiente y sin dependencias: copialo a cualquier proyecto web
// (debe servirse por https:// o localhost, y solo funciona en Chrome/Edge,
// principalmente en Android). No funciona en iPhone/Safari ni en Firefox.
//
// Uso básico:
//
//   import { PybricksHub } from './pybricks-ble.js';
//
//   const hub = new PybricksHub();
//   hub.addEventListener('connect',    e => console.log('conectado', e.detail.name));
//   hub.addEventListener('disconnect', () => console.log('desconectado'));
//   hub.addEventListener('stdout',     e => console.log('hub:', e.detail.text));
//   hub.addEventListener('appdata',    e => console.log('appdata:', e.detail.bytes));
//
//   await hub.connect();                 // abre el diálogo de Bluetooth
//   await hub.sendAppData([h, s, v]);    // escribe en el buffer de AppData del hub
//   hub.disconnect();
//
// En el hub (MicroPython, firmware Pybricks >= 4.0):
//
//   from pybricks.messaging import AppData
//   app = AppData([(0, 3)])              # modo 0, 3 bytes
//   h, s, v = app.get_bytes(mode=0)
// ---------------------------------------------------------------------------

// UUID del servicio y de la característica de comando/evento del firmware Pybricks.
export const PYBRICKS_SERVICE_UUID = 'c5f50001-8280-46da-89f4-6d8051e4aeef';
export const PYBRICKS_COMMAND_EVENT_UUID = 'c5f50002-8280-46da-89f4-6d8051e4aeef';

// Comandos: teléfono -> hub (primer byte del paquete).
const CMD_STOP_USER_PROGRAM = 0x00;
const CMD_START_USER_PROGRAM = 0x01;
const CMD_WRITE_STDIN = 0x06;
const CMD_WRITE_APP_DATA = 0x07;

// Eventos: hub -> teléfono (primer byte de la notificación).
const EVT_STATUS = 0x00;
const EVT_STDOUT = 0x01;
const EVT_APP_DATA = 0x02;

/** ¿El navegador soporta Web Bluetooth? */
export function isWebBluetoothSupported() {
  return typeof navigator !== 'undefined' && !!navigator.bluetooth;
}

/**
 * Hub Pybricks accesible por Web Bluetooth.
 *
 * Es un EventTarget: escuchá los eventos `connect`, `disconnect`, `stdout`,
 * `appdata` y `status` con addEventListener.
 */
export class PybricksHub extends EventTarget {
  constructor() {
    super();
    this.device = null;
    this.characteristic = null;
    this._writeBusy = false;
  }

  /** ¿Hay un hub conectado en este momento? */
  get connected() {
    return !!this.device?.gatt?.connected;
  }

  /** Nombre del hub conectado (o null). */
  get name() {
    return this.device?.name || null;
  }

  /**
   * Abre el diálogo de Bluetooth y se conecta al hub.
   * Tiene que llamarse desde un gesto del usuario (click).
   * @returns {Promise<string>} el nombre del hub.
   */
  async connect() {
    if (!isWebBluetoothSupported()) {
      throw new Error('Web Bluetooth no está disponible en este navegador.');
    }

    this.device = await navigator.bluetooth.requestDevice({
      filters: [{ services: [PYBRICKS_SERVICE_UUID] }],
      optionalServices: [PYBRICKS_SERVICE_UUID],
    });
    this.device.addEventListener('gattserverdisconnected', () => this._onDisconnected());

    const server = await this.device.gatt.connect();
    const service = await server.getPrimaryService(PYBRICKS_SERVICE_UUID);
    this.characteristic = await service.getCharacteristic(PYBRICKS_COMMAND_EVENT_UUID);
    await this.characteristic.startNotifications();
    this.characteristic.addEventListener('characteristicvaluechanged', (e) => this._onNotify(e));

    this.dispatchEvent(new CustomEvent('connect', { detail: { name: this.name } }));
    return this.name;
  }

  /** Cierra la conexión Bluetooth. */
  disconnect() {
    if (this.device?.gatt?.connected) {
      this.device.gatt.disconnect();
    }
  }

  _onDisconnected() {
    this.characteristic = null;
    this.dispatchEvent(new Event('disconnect'));
  }

  _onNotify(event) {
    const data = new Uint8Array(event.target.value.buffer);
    const type = data[0];
    const bytes = data.slice(1);
    if (type === EVT_STDOUT) {
      const text = new TextDecoder().decode(bytes);
      this.dispatchEvent(new CustomEvent('stdout', { detail: { bytes, text } }));
    } else if (type === EVT_APP_DATA) {
      this.dispatchEvent(new CustomEvent('appdata', { detail: { bytes } }));
    } else if (type === EVT_STATUS) {
      this.dispatchEvent(new CustomEvent('status', { detail: { bytes } }));
    }
  }

  async _write(byteArray) {
    if (!this.characteristic) {
      throw new Error('Hub no conectado.');
    }
    await this.characteristic.writeValueWithResponse(new Uint8Array(byteArray));
  }

  /**
   * Escribe en el buffer pre-asignado por AppData en el hub.
   * @param {Iterable<number>} bytes datos a escribir.
   * @param {number} [offset=0] posición dentro del buffer (16-bit LE).
   */
  async writeAppData(bytes, offset = 0) {
    await this._write([CMD_WRITE_APP_DATA, offset & 0xff, (offset >> 8) & 0xff, ...bytes]);
  }

  /**
   * Igual que writeAppData pero descarta la escritura si la anterior todavía
   * está en curso. Ideal para streaming a alta frecuencia (cámara, IMU, etc.).
   * @returns {Promise<boolean>} true si se envió, false si se descartó.
   */
  async sendAppData(bytes, offset = 0) {
    if (this._writeBusy) return false;
    this._writeBusy = true;
    try {
      await this.writeAppData(bytes, offset);
      return true;
    } finally {
      this._writeBusy = false;
    }
  }

  /**
   * Escribe en stdin del hub (lo que en MicroPython leés con input()/read()).
   * @param {string|Iterable<number>} data texto o bytes.
   */
  async writeStdin(data) {
    const bytes = typeof data === 'string' ? new TextEncoder().encode(data) : data;
    await this._write([CMD_WRITE_STDIN, ...bytes]);
  }

  /**
   * Arranca un programa cargado en el hub.
   * @param {number} [slot] número de slot; si se omite, usa el activo.
   */
  async startProgram(slot) {
    await this._write(slot === undefined ? [CMD_START_USER_PROGRAM] : [CMD_START_USER_PROGRAM, slot]);
  }

  /** Detiene el programa en ejecución en el hub. */
  async stopProgram() {
    await this._write([CMD_STOP_USER_PROGRAM]);
  }
}
