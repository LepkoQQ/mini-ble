from bleak import BleakClient, BleakScanner

from .bleak_utils import is_platform_data_populated, raw_manufacturer_data

ATMOTUBE_PRO_SERVICE_UUID = "DB450001-8E9A-4818-ADD7-6ED94A328AB4"
ATMOTUBE_SGPC3_CHAR_UUID = "DB450002-8E9A-4818-ADD7-6ED94A328AB4"
ATMOTUBE_BME280_CHAR_UUID = "DB450003-8E9A-4818-ADD7-6ED94A328AB4"
ATMOTUBE_STATUS_CHAR_UUID = "DB450004-8E9A-4818-ADD7-6ED94A328AB4"
ATMOTUBE_PM_CHAR_UUID = "DB450005-8E9A-4818-ADD7-6ED94A328AB4"


async def scan_for_atmotube(MAC_ADDR):
    atmotube_device = None
    atmotube_advert = None

    scanning_mode = "active"

    async with BleakScanner(scanning_mode=scanning_mode) as scanner:
        async for device, advert in scanner.advertisement_data():
            if device.address == MAC_ADDR:
                print(f"Found {device.name} ({device.address})")
                atmotube_device = device
                atmotube_advert = advert
                if is_platform_data_populated(advert.platform_data, scanning_mode):
                    break

    return atmotube_device, atmotube_advert


async def connect_to_atmotube(device):
    chars = {}

    async with BleakClient(device, services=[ATMOTUBE_PRO_SERVICE_UUID]) as client:
        print(f"Connected to {device.name} ({device.address})")
        chars["SGPC3"] = await client.read_gatt_char(ATMOTUBE_SGPC3_CHAR_UUID)
        chars["BME280"] = await client.read_gatt_char(ATMOTUBE_BME280_CHAR_UUID)
        chars["STATUS"] = await client.read_gatt_char(ATMOTUBE_STATUS_CHAR_UUID)
        chars["PM"] = await client.read_gatt_char(ATMOTUBE_PM_CHAR_UUID)

    return chars


def _parse_info_byte(info_byte):
    return {
        # bit 8 reserved
        "sgpc3_ready": bool(info_byte & 0b01000000),
        # bit 6 reserved
        "less_than_30_min_since_last_charge": bool(info_byte & 0b00010000),
        "charging": bool(info_byte & 0b00001000),
        "bonded": bool(info_byte & 0b00000100),
        "error": bool(info_byte & 0b00000010),
        "pm_sensor_enabled": bool(info_byte & 0b00000001),
    }


def _parse_atmotube_passive_advert(data):
    if len(data) == 12:
        return {
            "voc": int.from_bytes(data[0:2]) / 1000,
            "device_id": f"{data[2]:02X}{data[3]:02X}",
            "humidity": data[4],
            "temperature": data[5],
            "pressure": int.from_bytes(data[6:10]) / 100,
            "info": _parse_info_byte(data[10]),
            "battery_level": data[11],
        }
    return {}


def _parse_atmotube_active_advert(data):
    if len(data) == 9:
        return {
            "pm1": int.from_bytes(data[0:2]),
            "pm25": int.from_bytes(data[2:4]),
            "pm10": int.from_bytes(data[4:6]),
            "firmware_version": f"{data[6]}.{data[7]}.{data[8]}",
        }
    return {}


def parse_atmotube_advert(advert):
    parsed_data = {}

    mft_data = raw_manufacturer_data(advert.platform_data)
    for company_id, data in mft_data:
        if company_id == 0xFFFF:
            if len(data) == 12:
                parsed_data.update(_parse_atmotube_passive_advert(data))
            if len(data) == 9:
                parsed_data.update(_parse_atmotube_active_advert(data))

    return parsed_data


def _parse_atmotube_sgpc3_char(data):
    if len(data) == 4:
        return {
            "voc": int.from_bytes(data[0:2], byteorder="little") / 1000,
            # bytes 3 and 4 are reserved
        }
    return {}


def _parse_atmotube_bme280_char(data):
    if len(data) == 8:
        return {
            "humidity": data[0],
            # byte 2 is a less precise temperature value
            "pressure": int.from_bytes(data[2:6], byteorder="little") / 100,
            "temperature": int.from_bytes(data[6:8], byteorder="little") / 100,
        }
    return {}


def _parse_atmotube_status_char(data):
    if len(data) == 2:
        return {
            "info": _parse_info_byte(data[0]),
            "battery_level": data[1],
        }
    return {}


def _parse_atmotube_pm_char(data):
    if len(data) == 12:
        return {
            "pm1": int.from_bytes(data[0:3], byteorder="little") / 100,
            "pm25": int.from_bytes(data[3:6], byteorder="little") / 100,
            "pm10": int.from_bytes(data[6:9], byteorder="little") / 100,
            "pm4": int.from_bytes(data[9:12], byteorder="little") / 100,
        }
    return {}


def parse_atmotube_chars(chars):
    parsed_data = {}

    if "SGPC3" in chars:
        parsed_data.update(_parse_atmotube_sgpc3_char(chars["SGPC3"]))
    if "BME280" in chars:
        parsed_data.update(_parse_atmotube_bme280_char(chars["BME280"]))
    if "STATUS" in chars:
        parsed_data.update(_parse_atmotube_status_char(chars["STATUS"]))
    if "PM" in chars:
        parsed_data.update(_parse_atmotube_pm_char(chars["PM"]))

    return parsed_data
