import asyncio
from bleak import BleakScanner


async def main():
    devices = await BleakScanner.discover()
    for device in devices:
        if device.name is not None and "Polar" in device.name:
            print(f"Polar Address: {device.address}")


asyncio.run(main())