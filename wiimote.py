import cwiid
import time
import asyncio
import sender
import numpy as np
import math
import json
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
print("This program is intended as a joke. While it technically works, that doesnt mean its worth using it.\nWiimotes give terrible tracking quality, and thats expected. This is not representitive of what slimevr can be.\n\n!!!IF YOU ACTUALLY WANT FBT, DO NOT USE THIS!!!\n\n")
time.sleep(1)
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
wiimote.rpt_mode = cwiid.RPT_MOTIONPLUS | cwiid.RPT_ACC
wiimote.enable(cwiid.FLAG_MOTIONPLUS)
wiimote.led=1

asyncio.run(main())
# Initialize variables
gyro_offsets = [0, 0, 0]  # Gyro offsets (initial orientation)
gyro_angles = [0, 0, 0]    # Gyro angles (current orientation)

try:
    while True:
        calibrationMode=input("Auto calibrate (recommended) [a] or use cached calibration [c]")
        if calibrationMode.strip() in ["a","c"]:
            break
    # Sample gyro rates to determine initial orientation
    if calibrationMode.strip()=="a":
        print("Sampling gyro rates for 2 seconds to determine initial orientation...")
        print("put wiimote face down and dont move it!")
        time.sleep(2)
        start_time = time.time()
        samples = 0
        acc_offsets_1 = [0, 0, 0]
        acc_offsets_2 = [0, 0, 0]       
        while time.time() - start_time < 2:
            motion_data = wiimote.state['motionplus']['angle_rate']
            accel_data = wiimote.state["acc"]
            acc_offsets_1 = [acc_offsets_1[i] + accel_data[i] for i in range(3)]
            gyro_offsets = [gyro_offsets[i] + motion_data[i] for i in range(3)]
            samples += 1
            time.sleep(0.01)
        gyro_offsets = [offset / samples for offset in gyro_offsets]
        acc_offsets_1 = [offset / samples for offset in acc_offsets_1]   
        

        
        print("Please turn the wiimote face up.")
        
        
        time.sleep(4)
        start_time = time.time()
        samples = 0
        while time.time() - start_time < 2:
            accel_data = wiimote.state["acc"]
            acc_offsets_2 = [acc_offsets_2[i] + accel_data[i] for i in range(3)]
            samples += 1
            time.sleep(0.01)
        acc_offsets_2 = [offset / samples for offset in acc_offsets_2]   
        acc_offsets= [sum(i)*0.5 for i in zip(acc_offsets_1,acc_offsets_2)]
        print(acc_offsets)
        print(acc_offsets_1)
        print(acc_offsets_2)
        with open("calibrationcache","w") as f:
            json.dump({
                "gyro_offsets":gyro_offsets,
                "acc_offsets":acc_offsets
            },f)
            
    else:
        try:
            with open("calibrationcache","r") as f:
                cal=json.load(f)
                gyro_offsets=cal["gyro_offsets"]
                acc_offsets=cal["acc_offsets"]
        except Exception as e:
            print("No calibration data cached. Exiting...")
            print(e)
            exit()
    print("Initial gyro offsets:", gyro_offsets)
    multiplier= 360/5700
    # Main loop to calculate angles
    now=time.perf_counter()
    yaw=0
    while True:
        time.sleep(0.02)
        
        # Read motionplus data
        motion_data = wiimote.state['motionplus']['angle_rate']
        accel_data = wiimote.state['acc']
        # Subtract initial offsets from accelerometer readings
        adjusted_acc = [(accel_data[i] - acc_offsets[i]) for i in range(3)]
        #print(adjusted_acc)
        # Calculate pitch and roll angles from accelerometer data
        pitch_acc = (math.atan2(adjusted_acc[0], math.sqrt(adjusted_acc[1]**2 + adjusted_acc[2]**2))) #there is no way in hell this actually does anything benefitial. I dont know how to sensorfusion, and i dont think chatgpt knows either. Ima just say i implemented acc, but in all honesty, i just copy pasted some code around, and it seems terrible, but maybe less terrible, idk.
       
        roll_acc = (math.atan2(-adjusted_acc[1], adjusted_acc[2]))
        pitch_acc,roll_acc=roll_acc,pitch_acc
        # Subtract initial offsets from gyro rates
        adjusted_rates = [(motion_data[i] - gyro_offsets[i]) * multiplier for i in range(3)]
        
        gyro_yaw_delta = math.radians(adjusted_rates[2] * math.cos(pitch_acc) + adjusted_rates[1] * math.sin(roll_acc) * math.sin(pitch_acc) + adjusted_rates[0] * math.cos(roll_acc) * math.sin(pitch_acc))
        # Integrate gyracc_offsets_2acc_offsets_2o rates to get angles
        gyro_angles = [(gyro_angles[i] + adjusted_rates[i] * (time.perf_counter()-now)) for i in range(0,3)]
        yaw-=gyro_yaw_delta

        # This looks like fancy math, and it looks like i know what im doing. Well ur wrong, i have no idea what this is. What i do know however, is that it does nothing. Correcting the gyro with accel is literally just placebo and does nothing since the accel is very very unreliable

        # Combine gyroscope and accelerometer data using a complementary filter (i know half of these words)
        alpha = 0.90  # Weight for gyroscope data
        dt=time.perf_counter()-now
        now=time.perf_counter()
        #pitch = alpha * (gyro_angles[0] + adjusted_rates[0] * dt) + (1 - alpha) * pitch_acc
        #roll = alpha * (gyro_angles)[2] + adjusted_rates[2] * dt) + (1 - alpha) * roll_acc
        pitch=-math.degrees(pitch_acc)
        roll=-math.degrees(roll_acc)
       
        # Update rotation sent to server
        # pitch, roll, yaw
        #print(pitch, "\t",roll,"\t",yaw) #print("Accelerometer values (X, Y, Z):", accel_data)
        asyncio.run(s.set_rotation(1, -pitch, -roll, -yaw))

        #in theory we now have gyro angles. This however is not a perfect approach. Since we are only reading the gyro, and gyros drift, so will our final output.
        #what we need to do is take the accel into account, and do sensor fusion to reach a better result.
        
        #now=time.perf_counter()
        #print(f"Gyro Angles (degrees): X={gyro_angles[0]:.2f}, Y={gyro_angles[1]:.2f}, Z={gyro_angles[2]:.2f}")
        
        #asyncio.run(s.set_rotation(1,0,0,gyro_angles[1]))
        #asyncio.run(s.set_rotation(1,-gyro_angles[0],-gyro_angles[2],-gyro_angles[1]))
except KeyboardInterrupt:
    print("Closing connection...")
    wiimote.close()
    print("Connection closed.")
