import vqf
import asyncio
import cwiid
from sys import exit
import numpy as np
from scipy.spatial.transform import Rotation
import sender
import time

rate = 100 # tracking rate in hz
rbe = True # technically this might mean we might not need to calibrate the gyro, but im doing it anyway
mbe = False # 2 hour reset on wiimotes when?
caltime = 2 # 2 seconds of gyro calibration seems to work fine

class Wiimote:
    def __init__(self, cwiidObject,vqfObject,index) -> None:
        self.wiimote = cwiidObject
        self.vqf = vqfObject
        self.index = index
        self.gyroOff = [7000.,7000.,7000.]
        self.accOff = [128.,128.,128.]
        self.sensOffset = [0.001,0.001,0.001]
        # The gyro is the only thing thats actually calibrated, but it looks like the values for acc and sens work well when set like this
        # You could play around with them to see if results improve
        pass
    def getgyro(self):
        gyro = np.array([(i-k)*m for i,k,m in zip(self.wiimote.state['motionplus']['angle_rate'],self.gyroOff,self.sensOffset)])
        #gyro[0] = -gyro[0]
        return gyro
    def getacc(self):
        acc = np.array([(i-k)/3 for i,k in zip(self.wiimote.state['acc'],self.accOff)])
        #acc[0] = -acc[0]
        return acc
    
    
def toEuler(quat):
    rot = Rotation.from_quat(quat)
    return rot.as_euler("xyz")

def toQuat(euler):
    rot = Rotation.from_euler("xyz",euler)
    return rot.as_quat()

async def start_connect():
    s = sender.sender()
    print("Starting connection to SlimeVR server...")
    await s.setup()
    print(f"Connected to server at {s.get_slimevr_ip()}")
    return s
    

wiimotes = []

print("Copyright (c) 2024 Every-fucking-one, except the Author")
print("""
THIS PROJECT IS FOR ENTERTAINMENT PURPOSES ONLY!

If you want to have actual fbt, DO NOT USE THIS!
Wiimotes are bad. Their tracking quality does
not reflect the tracking quality of slime.

This project is not affiliated with or endorsed by
Nintendo or SlimeVR

In case Im still not clear enough,
!!! DO NOT USE THIS !!!""")
time.sleep(2)

numMotes = int(input("How many wiimotes do you want to use?  "))
if numMotes == 0:
    print("Good, you made the right choice !")
    exit(1)

if numMotes < 6:
    print("I just wanna be very clear that this is not a fbt solution. Dont treat it as such.")
    time.sleep(2)

if numMotes >= 6:
    print("Consider getting professional help.")
    time.sleep(5)
    print("In all seriousness though, its highly unlikely bluetooth can handle that many wiimotes.\nNo moral being or cheap bluetooth adapter can handle the power of that many wiimotes.")

for i in range(numMotes):
    print("Connect wiimote ", i)
    wiimote = None
    vqfObj = vqf.VQF(1/rate)
    vqfObj.setRestBiasEstEnabled(rbe)
    vqfObj.setMotionBiasEstEnabled(mbe)
    while not wiimote:
        try:
            wiimote = cwiid.Wiimote()
        except RuntimeError:
            print("Failed to connect. Retrying...")
    print("Wiimote connected!")
    wiimote.rpt_mode = cwiid.RPT_MOTIONPLUS | cwiid.RPT_ACC
    wiimote.enable(cwiid.FLAG_MOTIONPLUS)
    if numMotes <= 4:
        wiimote.led = (i+1)**2
    else:
        wiimote.led = i+1
    wiimotes.append(Wiimote(wiimote,vqfObj,i))
    
s = asyncio.run(start_connect())
for wiimote in wiimotes:
    gyro = [0,0,0]
    acc = [0,0,0]
    asyncio.run(s.create_imu(wiimote.index))
    input(f"Turn the wiimote face down, then press enter to start calibration for wiimote {wiimote.index}")
    time.sleep(1)
    print("Calibration started!")
    now = time.perf_counter()
    samples = 0
    while (time.perf_counter()-now < caltime):
        samples += 1
        gyro_raw = wiimote.wiimote.state['motionplus']['angle_rate']
        accel_raw = wiimote.wiimote.state["acc"]
        gyro = [gyro[i] + gyro_raw[i] for i in range(3)]

    wiimote.gyroOff=[i/samples for i in gyro]
    print("Calibration finished!")

print("I just wanne be very very clear, that YOU SHOULD NOT USE THIS")
time.sleep(1)
print("Starting to send IMU data...")
now = time.perf_counter()
neweuler = [0, 0, 0]
while True:
    for wiimote in wiimotes:
        vqfObj = wiimote.vqf
        vqfObj.update(wiimote.getgyro(),wiimote.getacc())
        quat = vqfObj.getQuat6D()
        euler = toEuler(quat)

        #No fucking idea why its in a weird format that requires this, but it works
        neweuler[0] = -euler[2]
        neweuler[1] = euler[1]
        neweuler[2] = -euler[0]
        
        quat = toQuat(neweuler)
        asyncio.run(s.set_quaternion_rotation(wiimote.index + 1, quat))
    time.sleep(max(((1 / rate) - (time.perf_counter() - now)), 0))
    now = time.perf_counter()