import asyncio
import sys
import aioconsole
from bleak import BleakClient

from Sensors.Polar import PolarH10

ADDRESS = "C9:C4:09:A0:49:1D"


def handle_hr(heart_rate):
    print(f"Heart Rate: {heart_rate}")


def handle_hrv(hrv):
    print(f"HR Variability: {hrv}")


def handle_acc(x, y, z):
    pass
    # print(f"ACC X: {x}  Y: {y}  Z: {z}")


def handle_ecg(ecg):
    print(f"ECG: {ecg}")


async def run(client):
    polar = PolarH10(client)
    await polar.print_device_info()
    await polar.start_hr_observation(hr_user_function=handle_hr, hr_variability_user_function=handle_hrv)
    await polar.start_acc_observation(acc_user_function=handle_acc)
    await polar.start_ecg_observation(ecg_user_function=handle_ecg)
    await aioconsole.ainput('Running: Press a key to quit\n')
    print("Stopping Polar data...", flush=True)
    await polar.disconnect()
    print("[CLOSED] application closed.", flush=True)
    sys.exit(0)


async def main():
    try:
        async with BleakClient(ADDRESS) as client:
            tasks = [
                asyncio.ensure_future(run(client)),
            ]
            await asyncio.gather(*tasks)
    finally:
        print("Stopped measuring")


asyncio.run(main())
