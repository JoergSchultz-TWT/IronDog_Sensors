import asyncio
import sys
import time

import aioconsole
from bleak import BleakClient

from Sensors.Polar import PolarH10

ADDRESS = "C9:C4:09:A0:49:1D"


hr_file = open("data/hr_data.csv", "w")
hrv_file = open("data/hrv_data.csv", "w")
acc_file = open("data/acc_data.csv", "w")
ecg_file = open("data/ecg_data.csv", "w")


def handle_hr(heart_rate):
    hr_file.write(f"{time.time()},{heart_rate}\n")


def handle_hrv(hrv):
    print(f"HR Variability: {hrv}")
    hrv_file.write(f"{time.time()},{hrv}\n")


def handle_acc(x, y, z):
    acc_file.write(f"{time.time()},{x},{y},{z}\n")


def handle_ecg(ecg):
    print(f"ECG: {ecg}")
    ecg_file.write(f"{time.time()},{ecg}\n")


async def run(client):
    polar = PolarH10(client)
    await polar.print_device_info()
    await polar.start_hr_observation(hr_user_function=handle_hr, hr_variability_user_function=handle_hrv)
    await polar.start_acc_observation(acc_user_function=handle_acc)
    await polar.start_ecg_observation(ecg_user_function=handle_ecg)
    await aioconsole.ainput('Running: Press a key to quit\n')
    print("Stopping Polar data...", flush=True)
    await polar.disconnect()
    hr_file.close()
    hrv_file.close()
    acc_file.close()
    ecg_file.close()
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
