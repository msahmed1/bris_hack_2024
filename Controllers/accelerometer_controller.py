import serial

# Opening serial port
ser = serial.Serial('/dev/cu.usbmodem101', 9600, timeout=1)

# Prev variable
prev_x = None
prev_y = None
prev_z = None
line = None

try:
    # While device is connected
    while True:
        jump_in_progress = False
        # Read line from serial port
        line = ser.readline().decode().strip()
        # Parsing the accelerometer output
        if line.startswith('X:') and "m/s^2" not in line:
            parts = line.split()
            # Splitting each axis into a variable
            x = float(parts[1])
            y = float(parts[3])
            z = float(parts[5])
            # Printing axis output for testing
            print(f"x: {x}")
            print(f"y: {y}")
            print(f"z: {z}")
            # Checking for a jump if there is a previous value
            if prev_z is not None:
                if z - prev_z > 500:
                    # Updating jump if true
                    jump_in_progress = True
                    print('Jump in progress')
            # Updating the previous values
            prev_y = y
            prev_x = x
            prev_z = z
# Keyboard interrupt closure
except KeyboardInterrupt:
    print("Exiting...")
    ser.close()
