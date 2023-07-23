import math
import time

from Sensors import constants


class PolarH10:

    def __init__(self, client):
        self._ecg_observed = False
        self._ecg_user_function = None
        self._acc_observed = False
        self._acc_user_function = None
        self.bleak_client = client
        self._hr_user_function = None
        self._hr_variability_user_function = None
        self._hr_observed = False

    async def print_device_info(self):
        text_blue = "\033[94m"
        text_reset = "\033[0m"
        model_number = await self.bleak_client.read_gatt_char(constants.MODEL_NBR_UUID)
        print(f"Model Number: {text_blue}{''.join(map(chr, model_number))}{text_reset}")
        battery_level = await self.bleak_client.read_gatt_char(constants.BATTERY_LEVEL_UUID)
        print(f"Battery Level: {text_blue}{int(battery_level[0])}%{text_reset}")

    async def _handle_hr_data(self, sender, data):
        """
        `data` is formatted according to the GATT Characteristic and Object Type 0x2A37 Heart Rate Measurement which is one of the three characteristics included in the "GATT Service 0x180D Heart Rate".
        `data` can include the following bytes:
        - flags
            Always present.
            - bit 0: HR format (uint8 vs. uint16)
            - bit 1, 2: sensor contact status
            - bit 3: energy expenditure status
            - bit 4: RR interval status
        - HR
            Encoded by one or two bytes depending on flags/bit0. One byte is always present (uint8). Two bytes (uint16) are necessary to represent HR > 255.
        - energy expenditure
            Encoded by 2 bytes. Only present if flags/bit3.
        - inter-beat-intervals (IBIs)
            One IBI is encoded by 2 consecutive bytes. Up to 18 bytes depending on presence of uint16 HR format and energy expenditure.
        """
        timestamp = time.time() # Take machine time, not Polar time to sync with other processes
        byte0 = data[0]  # heart rate format
        uint8_format = (byte0 & 1) == 0
        energy_expenditure = ((byte0 >> 3) & 1) == 1
        rr_interval = ((byte0 >> 4) & 1) == 1

        if not rr_interval:
            return

        first_rr_byte = 2
        if uint8_format:
            hr = data[1]
        else:
            hr = (data[2] << 8) | data[1]  # uint16
            first_rr_byte += 1
        if self._hr_user_function is not None:
            self._hr_user_function(timestamp ,hr)

        for i in range(first_rr_byte, len(data), 2):
            ibi = (data[i + 1] << 8) | data[i]
            # Polar H7, H9, and H10 record IBIs in 1/1024 seconds format.
            # Convert 1/1024 sec format to milliseconds.
            ibi = ibi / 1024 * 1000
            if self._hr_variability_user_function is not None:
                self._hr_variability_user_function(timestamp, ibi)

    async def start_hr_observation(self, hr_user_function, hr_variability_user_function):
        self._hr_user_function = hr_user_function
        self._hr_variability_user_function = hr_variability_user_function
        await self.bleak_client.start_notify(constants.HEART_RATE_MEASUREMENT_UUID, self._handle_hr_data)
        self._hr_observed = True
        print("Collecting HR data...", flush=True)

    async def stop_hr_observation(self):
        await self.bleak_client.stop_notify(constants.HEART_RATE_MEASUREMENT_UUID)
        self._hr_user_function = None
        self._hr_variability_user_function = None
        self._hr_observed = False
        print("Stopping HR data...", flush=True)

    @staticmethod
    def _convert_array_to_signed_int(data, offset, length):
        return int.from_bytes(
            bytearray(data[offset: offset + length]), byteorder="little", signed=True,
        )

    @staticmethod
    def _convert_to_unsigned_long(data, offset, length):
        return int.from_bytes(
            bytearray(data[offset : offset + length]), byteorder="little", signed=False,
        )

    def _handle_acc_data(self, sender, data):
        if data[0] != 0x02:
            return
        frame_type = data[9]
        samples = data[10:]

        resolution = (frame_type + 1) * 8  # 16 bit
        step = math.ceil(resolution / 8.0)
        time_step = 0.005 # 200 Hz sample rate TODO Adapt if changeable
        n_samples = math.floor(len(samples)/(step*3))
        # timestamp = PolarH10._convert_to_unsigned_long(data, 1, 8)/1.0e9 # timestamp of the last sample
        timestamp = time.time() # Take machine time, not Polar time to sync with other processes
        sample_timestamp = timestamp - (n_samples-1)*time_step
        offset = 0
        while offset < len(samples):
            x = PolarH10._convert_array_to_signed_int(samples, offset, step)
            offset += step
            y = PolarH10._convert_array_to_signed_int(samples, offset, step)
            offset += step
            z = PolarH10._convert_array_to_signed_int(samples, offset, step)
            offset += step
            if self._acc_user_function is not None:
                self._acc_user_function(timestamp=sample_timestamp, x=x, y=y, z=z)
            sample_timestamp += time_step

    # TODO set frequency
    async def start_acc_observation(self, acc_user_function, frequency=200):
        self._acc_user_function = acc_user_function
        await self.bleak_client.write_gatt_char(constants.PMD_CHAR1_UUID, constants.ACC_WRITE, response=True)
        await self.bleak_client.start_notify(constants.PMD_CHAR2_UUID, self._handle_acc_data)
        self._acc_observed = True
        print("Collecting ACC data...", flush=True)

    async def _handle_ecg_data(self, sender, data):
        if data[0] != 0x00:
            return
        step = 3
        samples = data[10:]
        offset = 0
        time_step = 1.0/ 130 # Hard Coded ECG Frequency
        n_samples = math.floor(len(samples)/step)
        # timestamp = PolarH10._convert_to_unsigned_long(data, 1, 8)/1.0e9
        timestamp = time.time() # Take machine time, not Polar time to sync with other processes
        sample_timestamp = timestamp - (n_samples-1)*time_step
        while offset < len(samples):
            ecg = PolarH10._convert_array_to_signed_int(samples, offset, step)
            offset += step
            if self._ecg_user_function is not None:
                self._ecg_user_function(sample_timestamp, ecg)
            sample_timestamp += time_step

    async def start_ecg_observation(self, ecg_user_function):
        self._ecg_user_function = ecg_user_function
        await self.bleak_client.write_gatt_char(constants.PMD_CHAR1_UUID, constants.ECG_WRITE, response=True)
        await self.bleak_client.start_notify(constants.PMD_CHAR2_UUID, self._handle_ecg_data)
        self._ecg_observed = True
        print("Collecting ECG data...", flush=True)

    async def stop_acc_ecg_observation(self):
        await self.bleak_client.stop_notify(constants.PMD_CHAR2_UUID)
        self._ecg_observed = False
        self._acc_observed = False
        print("Stopping ECG and ACC data...", flush=True)

    async def disconnect(self):
        await self.stop_hr_observation() if self._hr_observed else None
        if self._acc_observed or self._ecg_observed:
            await self.stop_acc_ecg_observation()
        await self.bleak_client.disconnect()
