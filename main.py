import asyncio
from pprint import pprint

from mini_ble.atmotube_pro import (
    connect_to_atmotube,
    parse_atmotube_advert,
    parse_atmotube_chars,
    scan_for_atmotube,
)

ATMOTUBE_MAC_ADDR = "FC:D5:AF:FC:EC:68"


def print_atmotube_advert_data(advert):
    data = parse_atmotube_advert(advert)
    pprint(data)
    print("\n")


def print_atmotube_data(chars):
    data = parse_atmotube_chars(chars)
    pprint(data)
    print("\n")


async def main():
    device, advert = await scan_for_atmotube(ATMOTUBE_MAC_ADDR)
    print_atmotube_advert_data(advert)

    chars = await connect_to_atmotube(device)
    print_atmotube_data(chars)

    print("Done.")


if __name__ == "__main__":
    asyncio.run(main())
