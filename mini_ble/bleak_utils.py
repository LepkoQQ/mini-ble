def is_winrt_data(platform_data):
    if isinstance(platform_data, tuple) and len(platform_data) > 1:
        return platform_data[1].__class__.__name__ == "_RawAdvData"
    return False


def is_platform_data_populated(platform_data, scanning_mode):
    """
    In active scanning mode WinRT data is populated in 2 steps:
        - first the advertisement data is populated (passive scan)
        - then the scan data is populated (active scan)
    This function checks if both data sets are populated.
    """
    if is_winrt_data(platform_data) and scanning_mode == "active":
        return platform_data[1].adv and platform_data[1].scan
    return True


def raw_manufacturer_data(platform_data):
    """
    Extract manufacturer data to a list to prevent multiple identical company
    ids overwriting each other.
    """
    mft_data = []

    if is_winrt_data(platform_data):
        data = platform_data[1]
        for args in filter(lambda d: d is not None, data):
            for m in args.advertisement.manufacturer_data:
                mft_data.append((m.company_id, bytes(m.data)))
    else:
        raise NotImplementedError("Unsupported platform data")

    return mft_data
