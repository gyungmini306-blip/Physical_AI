"""Windows desktop dashboard for ESP32 USB serial + Bluetooth LE.
Run: python dashboard.py --port COM3
"""
import argparse
import asyncio
import queue
import threading
import time
import tkinter as tk
from tkinter import ttk

from protocol import JsonLines, State

SERVICE_UUID = "7a8c0001-a83b-4c47-9b37-cda143808888"
TX_UUID = "7a8c0002-a83b-4c47-9b37-cda143808888"
RX_UUID = "7a8c0003-a83b-4c47-9b37-cda143808888"
DEVICE_NAME = "SmartHomeCare-ESP32"

class Bridge:
    def __init__(self, messages):
        self.messages = messages
        self.running = True
        self.serial = None
        self.ble_loop = None
        self.ble_client = None
        self.ble_ready = False
        self.serial_ready = False

    def usb_worker(self, port):
        try:
            import serial
            with serial.Serial(port, 115200, timeout=0.2) as ser:
                self.serial = ser
                self.serial_ready = True
                self.messages.put(('status', f'USB connected: {port}'))
                parser = JsonLines()
                while self.running:
                    for packet in parser.feed(ser.read(256)):
                        self.messages.put(('data', packet))
        except Exception as exc:
            self.messages.put(('status', f'USB unavailable: {exc}'))
        finally:
            self.serial_ready = False
            self.serial = None

    async def ble_worker(self):
        try:
            from bleak import BleakClient, BleakScanner
            self.messages.put(('status', 'Scanning for BLE device...'))
            device = await BleakScanner.find_device_by_name(DEVICE_NAME, timeout=12.0)
            if device is None:
                self.messages.put(('status', 'BLE device not found (check Bluetooth radio)'))
                return
            parser = JsonLines()
            async with BleakClient(device) as client:
                self.ble_client = client
                self.ble_ready = True
                self.messages.put(('status', 'BLE connected'))
                def on_notify(_sender, payload):
                    for packet in parser.feed(payload):
                        self.messages.put(('data', packet))
                await client.start_notify(TX_UUID, on_notify)
                while self.running and client.is_connected:
                    await asyncio.sleep(0.2)
                if client.is_connected:
                    await client.stop_notify(TX_UUID)
        except Exception as exc:
            self.messages.put(('status', f'BLE unavailable: {exc}'))
        finally:
            self.ble_ready = False
            self.ble_client = None

    def ble_thread(self):
        loop = asyncio.new_event_loop()
        self.ble_loop = loop
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.ble_worker())
        finally:
            self.ble_loop = None
            loop.close()

    def ack(self):
        if self.serial_ready and self.serial:
            try:
                self.serial.write(b'ACK\n')
                self.messages.put(('status', 'ACK sent via USB'))
            except Exception as exc:
                self.messages.put(('status', f'USB ACK failed: {exc}'))
        if self.ble_ready and self.ble_client and self.ble_loop:
            future = asyncio.run_coroutine_threadsafe(
                self.ble_client.write_gatt_char(RX_UUID, b'ACK', response=True), self.ble_loop
            )
            def done(f):
                try:
                    f.result()
                    self.messages.put(('status', 'ACK sent via BLE'))
                except Exception as exc:
                    self.messages.put(('status', f'BLE ACK failed: {exc}'))
            future.add_done_callback(done)

class Dashboard:
    def __init__(self, window, port, enable_ble):
        self.window = window
        self.window.title('ESP32 Smart Home Care — USB + BLE')
        self.window.geometry('760x590')
        self.messages = queue.Queue()
        self.state = State()
        self.bridge = Bridge(self.messages)
        self.last_received = 0.0
        self.status = tk.StringVar(value='Not connected')
        self.pir = tk.StringVar(value='—')
        self.ir = tk.StringVar(value='—')
        self.alert = tk.StringVar(value='—')
        self.counts = tk.StringVar(value='PIR: 0   IR: 0   Alerts: 0')
        self.link = tk.StringVar(value='Offline')

        frame = ttk.Frame(window, padding=20)
        frame.pack(fill='both', expand=True)
        ttk.Label(frame, text='SMART HOME CARE', font=('Segoe UI', 22, 'bold')).pack(anchor='w')
        ttk.Label(frame, text='Live sensor status — USB and Bluetooth LE', font=('Segoe UI', 10)).pack(anchor='w', pady=(0, 18))
        for label, variable in [('PIR motion', self.pir), ('IR proximity', self.ir), ('Alert / ACK', self.alert)]:
            row = ttk.Frame(frame)
            row.pack(fill='x', pady=7)
            ttk.Label(row, text=label, font=('Segoe UI', 12), width=19).pack(side='left')
            ttk.Label(row, textvariable=variable, font=('Segoe UI', 13, 'bold')).pack(side='left')
        ttk.Label(frame, textvariable=self.counts, font=('Segoe UI', 11)).pack(anchor='w', pady=10)
        ttk.Button(frame, text='Acknowledge Alert (ACK)', command=self.bridge.ack).pack(anchor='w', pady=8)
        ttk.Label(frame, textvariable=self.link).pack(anchor='w')
        ttk.Label(frame, textvariable=self.status, foreground='#596579').pack(anchor='w', pady=(2, 14))
        ttk.Label(frame, text='Recent events', font=('Segoe UI', 12, 'bold')).pack(anchor='w')
        self.events = tk.Listbox(frame, height=11, font=('Consolas', 10))
        self.events.pack(fill='both', expand=True, pady=7)
        ttk.Label(frame, text='Demo only: not a certified safety or emergency alert device.', foreground='#8b5d29').pack(anchor='w')
        if port:
            threading.Thread(target=self.bridge.usb_worker, args=(port,), daemon=True).start()
        if enable_ble:
            threading.Thread(target=self.bridge.ble_thread, daemon=True).start()
        window.protocol('WM_DELETE_WINDOW', self.close)
        self.poll()

    def poll(self):
        try:
            while True:
                kind, payload = self.messages.get_nowait()
                if kind == 'status':
                    self.status.set(payload)
                elif kind == 'data':
                    if self.state.update(payload):
                        self.last_received = time.monotonic()
                        self.pir.set('MOTION' if payload.get('pir') else 'CLEAR')
                        self.ir.set('DETECTED' if payload.get('ir') else 'CLEAR')
                        self.alert.set('ACKNOWLEDGED' if payload.get('ack') else ('ACTIVE' if payload.get('alert') else 'NORMAL'))
                        self.counts.set('PIR: {}   IR: {}   Alerts: {}'.format(
                            payload.get('pirCount', 0), payload.get('irCount', 0), payload.get('alertCount', 0)))
                        self.events.delete(0, 'end')
                        for sec, event in self.state.events:
                            self.events.insert('end', f'{sec:>6}s | {event}')
        except queue.Empty:
            pass
        self.link.set('USB: {}  |  BLE: {}  |  {}'.format(
            'on' if self.bridge.serial_ready else 'off',
            'on' if self.bridge.ble_ready else 'off',
            'LIVE' if self.last_received and time.monotonic() - self.last_received < 4 else 'NO RECENT DATA'))
        self.window.after(150, self.poll)

    def close(self):
        self.bridge.running = False
        self.window.destroy()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', default='COM3', help='USB serial port (use empty string to disable)')
    parser.add_argument('--no-ble', action='store_true', help='Disable BLE connection attempt')
    args = parser.parse_args()
    root = tk.Tk()
    Dashboard(root, args.port, not args.no_ble)
    root.mainloop()

if __name__ == '__main__':
    main()
