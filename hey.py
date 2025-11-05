from mss import mss

with mss() as sct:
    # Get information about all monitors
    monitors_info = sct.monitors

    # The first element (monitors[0]) represents the combined bounding box of all monitors
    # You can get the total display size from this
    total_width = monitors_info[0]['width']
    total_height = monitors_info[0]['height']
    print(f"Total display size: {total_width}x{total_height}")