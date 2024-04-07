import cwiid
import time
import asyncio
import sender
import math

async def main():
    global s
    s = sender.sender()
    print("sender init")
    await s.setup()
    print("sender setup")
    print(f"SlimeVR server is at {s.get_slimevr_ip()}")
    await s.create_imu(1)
    print("sender imu init")
    await s.set_rotation(1,0,0,0)
    print("imu rotation")
    #await asyncio.sleep(4)
    await s.send_reset()
    print("yaw reset")

# Connect to the Wiimote
print("Press 1+2 on your Wiimote to connect...")
time.sleep(1)
wiimote = None
while not wiimote:
    try:
        wiimote = cwiid.Wiimote()
    except RuntimeError:
        print("Failed to connect. Retrying...")
print("Wiimote connected!")

# Enable motion sensing
wiimote.rpt_mode = cwiid.RPT_MOTIONPLUS
wiimote.enable(cwiid.FLAG_MOTIONPLUS)
time.sleep(3)
asyncio.run(main())
# Initialize variables
gyro_offsets = [0, 0, 0]  # Gyro offsets (initial orientation)
gyro_angles = [0, 0, 0]    # Gyro angles (current orientation)
try:
    # Sample gyro rates to determine initial orientation
    print("Sampling gyro rates for 2 seconds to determine initial orientation...")
    print("put wiimote face down and dont move it!")
    time.sleep(2)
    start_time = time.time()
    samples = 0
    while time.time() - start_time < 2:
        motion_data = wiimote.state['motionplus']['angle_rate']
        gyro_offsets = [gyro_offsets[i] + motion_data[i] for i in range(3)]
        samples += 1
        time.sleep(0.01)
    
    gyro_offsets = [offset / samples for offset in gyro_offsets]
    print("Initial gyro offsets:", gyro_offsets)
    multiplier= 360/5700
    # Main loop to calculate angles
    now=time.perf_counter()
    while True:
        #time.sleep(0.02)
        
        # Read motionplus data
        motion_data = wiimote.state['motionplus']['angle_rate']
        
        # Subtract initial offsets from gyro rates
        adjusted_rates = [(motion_data[i] - gyro_offsets[i]) * multiplier for i in range(3)]
        
        # Integrate gyro rates to get angles
        gyro_angles = [(gyro_angles[i] + adjusted_rates[i] * (time.perf_counter()-now)) for i in range(3)]  # 0.01 is the time interval
        now=time.perf_counter()
        # Print gyro angles
        #print(f"Gyro Angles (degrees): X={gyro_angles[0]:.2f}, Y={gyro_angles[1]:.2f}, Z={gyro_angles[2]:.2f}")
        
        #asyncio.run(s.set_rotation(1,0,0,gyro_angles[1]))
        asyncio.run(s.set_rotation(1,-gyro_angles[0],-gyro_angles[2],-gyro_angles[1]))
except KeyboardInterrupt:
    print("Closing connection...")
    wiimote.close()
    print("Connection closed.")
