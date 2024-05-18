import cwiid
import time
import asyncio
import sender
import math
import json
from vqf import VQF
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from scipy.spatial.transform import Rotation as R

#vqf = VQF(0.02)
dryrun=False #Just connect to wiimotes without connecting to the slimevr server

async def main():
    global s
    s = sender.sender()
    if not dryrun:
        print("sender init")
        await s.setup()
        print("sender setup")
        print(f"SlimeVR server is at {s.get_slimevr_ip()}")
        for i in range(numberWiimotes):
            await s.create_imu(i+1)
            await s.set_rotation(i+1,0,0,0)
            print("init imu ", i+1)
            #await asyncio.sleep(4)
    
def quaternion_to_euler(quaternion):
    # Ensure quaternion is normalized
    q = quaternion / np.linalg.norm(quaternion)
    
    # Convert quaternion to rotation matrix
    rotation_matrix = R.from_quat(q).as_matrix()
    
    # Extract Euler angles from rotation matrix
    euler_angles = R.from_matrix(rotation_matrix).as_euler('xyz', degrees=True)
    
    return euler_angles

print("This program is intended as a joke. While it technically works, that doesnt mean its worth using it.\nWiimotes give terrible tracking quality, and thats expected. This is not representitive of what slimevr can be.\n\n!!!IF YOU ACTUALLY WANT FBT, DO NOT USE THIS!!!\n\n")
time.sleep(1)
# Connect to the Wiimote
numberWiimotes=int(input("How many wiimotes do you want to connect? "))
if numberWiimotes==0:
    print("Congratulations, you picked the right number of wiimotes to use!")
    exit()
if numberWiimotes>1:
    print("\n\nI just wanna be *VERY* clear, that under no circumstances ever should you use wiimotes for fbt... Just dont... If you bought wiimotes for the purposes of FBT.. You probably made the worng choice.\nLike, honestly... How did we get to this point.. Is there something wrong? Do you need to talk about anything? Putting excessive ammounts of wiimotes into slimevr isnt healthy... \n\n")
    
    time.sleep(5)
print("Press 1+2 on your Wiimote to connect...")
time.sleep(1)
wiimotes=[]
vqfobjects=[]
for i in range(numberWiimotes):
    print("Connect wiimote ",i)
    wiimote = None
    while not wiimote:
        try:
            wiimote = cwiid.Wiimote()
        except RuntimeError:
            print("Failed to connect. Retrying...")
    print("Wiimote connected!")
    wiimotes.append(wiimote)
    vqf=VQF(0.01)
    vqf.setRestBiasEstEnabled(True)
    vqf.setMotionBiasEstEnabled(True)
    vqfobjects.append(vqf)
print(wiimotes)
# Enable motion sensing
for num,wiimote in enumerate(wiimotes):
    wiimote.rpt_mode = cwiid.RPT_MOTIONPLUS | cwiid.RPT_ACC
    wiimote.enable(cwiid.FLAG_MOTIONPLUS)
    wiimote.led=num+1
    time.sleep(0.1)

asyncio.run(main())
# Initialize variables
gyro_offsets = [0, 0, 0]  # Gyro offsets (initial orientation)
gyro_angles = [0, 0, 0]    # Gyro angles (current orientation)
all_gyro=[]
all_acc=[]
aa= np.array([0, 0, 0])
aj= np.array([0, 0, 0])
fig, ax = plt.subplots()
line1, = ax.plot([], [], label='Data 1')
line2, = ax.plot([], [], label='Data 2')
ax.legend()
def update(frame):
    if frame < len(aa):
        line1.set_data(np.arange(frame), aa[:frame])
        line2.set_data(np.arange(frame), aj[:frame])
        return line1, line2
ani = FuncAnimation(fig, update, frames=len(aa), blit=True)

try:
    for num,wiimote,vqf in zip(range(numberWiimotes),wiimotes,vqfobjects):
        if numberWiimotes==1:
            while True:
                calibrationMode=input("Auto calibrate (recommended) [a] or use cached calibration [c] ")
                if calibrationMode.strip() in ["a","c"]:
                    break
        else:
            print("Calibration caching is not available when using multiple wiimotes.")
            print("Please prepare wiimote ", num)
            time.sleep(5)
            calibrationMode="a"
        # Sample gyro rates to determine initial orientation
        if calibrationMode.strip()=="a":
            print("Sampling gyro rates for 2 seconds to determine initial orientation...")
            print("put wiimote face down and dont move it!")
            
            input("Press enter to continue...")
            time.sleep(1)
            print("calibration started...")
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
            
            input("Press enter to continue...")
            time.sleep(1)
            print("calibration started...")
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
            print("Time do to senscal because fuck you")
            print("I could give you instructions here... But fuck you, its your fault we have to do this. I didnt wanna, but you dont leave me another choice")
            input("By pressing enter you confirm that you do not have a life")
            gyrosens=[0,0,0]
            start_time = time.time()
            while time.time() - start_time < 20:
                motion_data = wiimote.state['motionplus']['angle_rate']
                gyrosens = [abs(gyrosens[i] + motion_data[i] - gyro_offsets[i]) for i in range(3)]
                time.sleep(0.01)
            #i am making this shit up as i go. I have no idea what any of this does, i wanna sleep
            sens=[(360/gyrosens[i]) for i in range(3)]
            print(sens)
            with open("calibrationcache","w") as f:
                json.dump({
                    "gyro_offsets":gyro_offsets,
                    "acc_offsets":acc_offsets,
                    "sens":sens
                },f)

        else:
            try:
                with open("calibrationcache","r") as f:
                    cal=json.load(f)
                    gyro_offsets=cal["gyro_offsets"]
                    acc_offsets=cal["acc_offsets"]
                    sens=cal["sens"]
            except Exception as e:
                print("No calibration data cached. Exiting...")
                print(e)
                exit()
        all_gyro.append(gyro_offsets)
        all_acc.append(acc_offsets)
        print("Initial gyro offsets:", gyro_offsets)
        #multiplier= math.radians(360/7000)*0.8 #This just applies to my wiimote. It probably wont apply to yours... And if you are using multiple wiimotes.. Good luck :3 (There used to be some sense behind this, i have since long abandoned this principle)
        now=time.perf_counter()
        yaw=0
    print("Starting to send imu data...")
    print("Please leave the wiimote still for a few seconds to establish initial orientation...")
    while True:
        time.sleep(0.01)
        for wiimote,accel_offsets,gyro_offsets,num in zip(wiimotes,all_acc,all_gyro,range(numberWiimotes)):
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
            adjusted_rates = [(motion_data[i] - gyro_offsets[i]) * math.radians(sens[i]) for i in range(3)]
            
            #Thy who shall read the following code be aware
            #This code was not made with logic or reasoning... Or even the smartness of chatgpt...
            #No, this code is pure anger and incompetence, and as a result does not work
            aj = np.array([-adjusted_rates[1],adjusted_rates[2],adjusted_rates[0]])
            vqf.updateGyr(aj)
            aa = np.array([-adjusted_acc[1],-adjusted_acc[2],-adjusted_acc[0]])
            #aa= np.array([0.,0.,0.])
            vqf.updateAcc(aa)
            print(aj,aa)
            plt.show()
            #fuck that part, i hate that
            
            
            gyro_yaw_delta = math.radians(adjusted_rates[2] * math.cos(pitch_acc) + adjusted_rates[1] * math.sin(roll_acc) * math.sin(pitch_acc) + adjusted_rates[0] * math.cos(roll_acc) * math.sin(pitch_acc))
            # Integrate gyracc_offsets_2acc_offsets_2o rates to get angles
            gyro_angles = [(gyro_angles[i] + adjusted_rates[i] * (time.perf_counter()-now)) for i in range(0,3)]
            yaw-=gyro_yaw_delta

            # This looks like fancy math, and it looks like i know what im doing. Well ur wrong, i have no idea what this is. What i do know however, is that it does nothing. Correcting the gyro with accel is literally just placebo and does nothing since the accel is very very unreliable
            #UPDATE: With amazing tech advances, its not placebo anymore! Its worse than placebo now!

            # Combine gyroscope and accelerometer data using a complementary filter (i know half of these words)
            alpha = 0.90  # Weight for gyroscope data (which is not used, and i should just delete this line of code, but here i am writing funny comments)
            dt=time.perf_counter()-now
            now=time.perf_counter()

            pitch=-math.degrees(pitch_acc)
            roll=-math.degrees(roll_acc)

            quat_6d = vqf.getQuat6D()
            #print(quat_6d)
            #print(vqf.normalize(quat_6d))
            # Calculate Euler angles from the quaternion
            roll = math.atan2(2 * (quat_6d[0] * quat_6d[1] + quat_6d[2] * quat_6d[3]), 1 - 2 * (quat_6d[1]**2 + quat_6d[2]**2))
            pitch = math.asin(2 * (quat_6d[0] * quat_6d[2] - quat_6d[3] * quat_6d[1]))
            yaw = math.atan2(2 * (quat_6d[0] * quat_6d[3] + quat_6d[1] * quat_6d[2]), 1 - 2 * (quat_6d[2]**2 + quat_6d[3]**2))

            # Convert Euler angles to degrees if needed
            roll_deg = math.degrees(roll)
            pitch_deg = math.degrees(pitch)
            yaw_deg = math.degrees(yaw)

            # Update rotation sent to server
            # pitch, roll, yaw
            if not dryrun:
                angles=quaternion_to_euler(quat_6d)
                #print(angles)
                asyncio.run(s.set_rotation(num+1, (angles[0]), (angles[1]), (angles[2])))
                #asyncio.run(s.set_quaternion_rotation(num+1, vqf.quatConj(quat_6d))) #do i know what quatConj does? Nope! Does it fix anything? Also nope. Im going to bed
                #asyncio.run(s.set_rotation(num+1, pitch_deg, roll_deg, yaw_deg))
                #asyncio.run(s.set_rotation(num+1, -pitch, -roll, -yaw))
                #for the love of god, dont ask why i invert pitch when i convert from radians to degerees, and then invert it again afterwards
            
except KeyboardInterrupt:
    print("Closing connection...")
    for wiimote in wiimotes:
        wiimote.close()
    print("Connection closed.")
