import asyncio
import sys
from datetime import datetime

import aioconsole
from bleak import BleakClient

from Sensors.Polar import PolarH10

ADDRESS = "C9:C4:09:A0:49:1D"


hr_file = open("data/hr_data.csv", "w")
hrv_file = open("data/hrv_data.csv", "w")
acc_file = open("data/acc_data.csv", "w")
ecg_file = open("data/ecg_data.csv", "w")


def handle_hr(timestamp, heart_rate):
    formatted_time = datetime.fromtimestamp(timestamp)
    hr_file.write(f"{formatted_time},{heart_rate}\n")


def handle_hrv(timestamp, hrv):
    formatted_time = datetime.fromtimestamp(timestamp)
    print(f"HR Variability: {formatted_time} {hrv}")
    hrv_file.write(f"{formatted_time},{hrv}\n")


def handle_acc(timestamp, x, y, z):
    formatted_time = datetime.fromtimestamp(timestamp)
    acc_file.write(f"{formatted_time},{x},{y},{z}\n")


def handle_ecg(timestamp, ecg):
    formatted_time = datetime.fromtimestamp(timestamp)
    print(f"ECG: {formatted_time} {ecg}")
    ecg_file.write(f"{formatted_time},{ecg}\n")


async def run(client):
    polar = PolarH10(client)
    await polar.print_device_info()
    await polar.start_hr_observation(hr_user_function=handle_hr, hr_variability_user_function=handle_hrv)
    # Frequency = 25Hz, 50Hz, 100Hz or 200Hz
    await polar.start_acc_observation(acc_user_function=handle_acc, frequency=25)
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
