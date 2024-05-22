import vqf
import asyncio
import cwiid
from sys import exit
import numpy as np
from scipy.spatial.transform import Rotation
import json
import sender
import time
import math

rate = 100 #tracking rate in hz
rbe = True
mbe = False
caltime = 2

class Wiimote:
    def __init__(self, cwiidObject,vqfObject,index) -> None:
        self.wiimote = cwiidObject
        self.vqf = vqfObject
        self.index = index
        self.gyroOff = [5000.,7000.,7000.]
        self.accOff = [128.,128.,128.]
        self.sensOffset = [0.07,0.07,0.07]
        pass
    def getgyro(self):
        return np.array([math.radians(i-k)*m for i,k,m in zip(self.wiimote.state['motionplus']['angle_rate'],self.gyroOff,self.sensOffset)])
    def getacc(self):
        acc = np.array([i-k for i,k in zip(self.wiimote.state['acc'],self.accOff)])
        print(acc)
        return acc
    
    
async def start_connect():
    s = sender.sender()
    print("Starting connection to SlimeVR server...")
    await s.setup()
    print(f"Connected to server at {s.get_slimevr_ip()}")
    return s
    

wiimotes=[]

print("Copyright (c) 2024 Every-fucking-one, except the Author")
print("Disclaimer go here. tldr: dont use this.")


numMotes = int(input("How many wiimotes do you want to use?  "))
if numMotes not in range(1,16):
    print("no")
    exit(1)

for i in range(numMotes):
    print("Connect wiimote ", i)
    wiimote=None
    vqf=vqf.VQF(1/rate)
    vqf.setRestBiasEstEnabled(rbe)
    vqf.setMotionBiasEstEnabled(mbe)
    while not wiimote:
        try:
            wiimote = cwiid.Wiimote()
        except RuntimeError:
            print("Failed to connect. Retrying...")
    print("Wiimote connected!")
    wiimote.rpt_mode = cwiid.RPT_MOTIONPLUS | cwiid.RPT_ACC
    wiimote.enable(cwiid.FLAG_MOTIONPLUS)
    wiimote.led=i+1
    wiimotes.append(Wiimote(wiimote,vqf,i))
    
gyro = [0,0,0]
acc = [0,0,0]
s = asyncio.run(start_connect())
for wiimote in wiimotes:
    asyncio.run(s.create_imu(wiimote.index+1))
    input("press enter to start calibration")
    
    now = time.perf_counter()
    samples = 0
    while (time.perf_counter()-now < caltime):
        samples += 1
        gyro_raw = wiimote.wiimote.state['motionplus']['angle_rate']
        accel_raw = wiimote.wiimote.state["acc"]
        gyro = [gyro[i] + gyro_raw[i] for i in range(3)]

    wiimote.gyroOff=[i/samples for i in gyro]


now = time.perf_counter()
while True:
    for wiimote in wiimotes:

        vqf = wiimote.vqf
        #vqf.updateGyr(np.array(wiimote.getgyro()))
        #vqf.updateAcc(np.array(wiimote.getacc()))
        vqf.update(wiimote.getgyro(),wiimote.getacc())
    
        asyncio.run(s.set_quaternion_rotation(wiimote.index+1,vqf.getQuat6D()))
    time.sleep(max(((1/rate)-(time.perf_counter()-now)),0))
    now = time.perf_counter()