# IronDog Sensors

## Polar H10

### Overview

This package enables you to connect to your Polar H10 and read the following data in real time from a python script: 
- Heart rate
- Inter-Beat Interval (heart rate variation)
- ECG
- Accelerometer (x, y, z)

### Thank you!

This package draws heavily from the [dont-hold-your-breath](https://github.com/kbre93/dont-hold-your-breath) 
repository. Big thanks to [kbre93](https://github.com/kbre93) for making it available under the MIT License.

### Installation

The communication with the Polar H10 is based on Bluetooth Low Energy protocol. I am using the 
[Bleak](https://github.com/hbldh/bleak) library. Install it in your environment with `pip install bleak`.
Then copy the `Sensors` folder into your project directory. You can now import this module into your program by

```python
from Sensors.Polar import PolarH10
```

### Usage

Example program: [observerPolarH10.py](./observePolarH10.py)

#### Setup

To uniquely identify a Polar H10, I am using its address. If you don't have it, you can get it by running the 
[`getAddressPolarH10.py`](./getAddressPolarH10.py) script. Once you have the address, which looks something like 
`C9:C4:09:A0:49:1D`, you can make a connection with the Polar H10 using the bleak library:

```python
import asyncio
from bleak import BleakClient

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
```

In the `async def run(client)` you can define what information you want to get and how to handle it. First, let's 
make a polar object:

```python
from Sensors.Polar import PolarH10

polar = PolarH10(client)
```
#### Battery Status

To get the Model and the battery status, use the `await polar.print_device_info()` function.

#### Heart Rate and Inter beat interval

```python
def handle_hr(timestamp, heart_rate):
    formatted_time = datetime.fromtimestamp(timestamp)
    hr_file.write(f"{formatted_time},{heart_rate}\n")


def handle_hrv(timestamp, hrv):
    formatted_time = datetime.fromtimestamp(timestamp)
    print(f"HR Variability: {formatted_time} {hrv}")
    hrv_file.write(f"{formatted_time},{hrv}\n")


await polar.start_hr_observation(hr_user_function=handle_hr, hr_variability_user_function=handle_hrv)
```

The `start_hr_observation()` methods takes as parameters functions which are called each time a value is read from 
the H10. These functions get the timestamp and the value as input. 

#### ECG

```python
def handle_ecg(timestamp, ecg):
    formatted_time = datetime.fromtimestamp(timestamp)
    print(f"ECG: {formatted_time} {ecg}")
    ecg_file.write(f"{formatted_time},{ecg}\n")

await polar.start_ecg_observation(ecg_user_function=handle_ecg)
```

The `start_ecg_observation()` methods takes a function as parameter, which is called for each ecg value from the H10.
The H10 only provides one frequency, 130 Hz, as sampling rate.

#### Accelerometer

```python
def handle_acc(timestamp, x, y, z):
    formatted_time = datetime.fromtimestamp(timestamp)
    acc_file.write(f"{formatted_time},{x},{y},{z}\n")
    
await polar.start_acc_observation(acc_user_function=handle_acc, frequency=25)
```
In addition to a function, the `start_acc_observation()` method also takes the sampling rate as input. The H10 
allows for frequencies of 25, 50, 100, and 200 Hz. Any other value will raise an error.

#### Closing 

Don't forget to call `await polar.disconnect()` at the end of your program.

### Note about TimeStamp

As a timestamp, I am not using the Polar measurement but the one from device running the python program (using 
`time.time()`). This will lead 
to slight deviations, as there will be a delay between measurement and receiving the data. Still, this enables 
syncing with other processes on the device. THe ECG and the Accelerometer data are send in packets from the H10. I 
am deducing an individual timestamp for each measurement by subtracting the position of the measurement in the 
packet times the sampling rate from the timestamp the packet arrived at the device.