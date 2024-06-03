import vqf
import asyncio
import wiiuse
from sys import exit
import numpy as np
from scipy.spatial.transform import Rotation
import sender
import time

rate = 100 # tracking rate in hz
rbe = True # technically this might mean we might not need to calibrate the gyro, but im doing it anyway
mbe = True # 2 hour reset on wiimotes when?
caltime = 2 # 2 seconds of gyro calibration seems to work fine
mac = [0x01, 0x02, 0x03, 0x04, 0x05, 0x06] # change this if you want to run multilpe slimewiir sessions on the same network
print("""
Hello there.
This does not work :3
The library to read wiimote input features no documentation whatsoever, so this uses the wrong data, because i cant read the gyro.
Wiimotes suck anyway.
This is only here because cwiid doesnt run on windows, but to be fair, i dont like windows so i dont mind a terrible experience.
""")
time.sleep(5)
async def start_connect(mac):
    s = sender.sender(mac)
    print("Starting connection to SlimeVR server...")
    await s.setup()
    print(f"Connected to server at {s.get_slimevr_ip()}")
    return s
    
wiimote = wiiuse.init(1)
vqfObj = vqf.VQF(1/rate)
vqfObj.setRestBiasEstEnabled(rbe)
vqfObj.setMotionBiasEstEnabled(mbe)
connected=False
mote = None
while not connected:
    found = wiiuse.find(wiimote, 1, 5)
    print(f"found {found} wiimotes")
    if found:
        connected = wiiuse.connect(wiimote, 1)
        print("connected to wiimote")
    
print("Wiimote connected!")
wiiuse.rumble(wiimote[0],1)
time.sleep(0.2)
wiiuse.rumble(wiimote[0],0)
wiiuse.set_leds(wiimote[0], wiiuse.LED_1)
now = time.time()
while time.time()-now < 10:
    wiiuse.poll(wiimote,1)
    print("waiting cuz buggy :3")
wiiuse.motion_sensing(wiimote[0],1)
a = wiimote[0]
a.motionplus = True
s = asyncio.run(start_connect(mac))
asyncio.run(s.create_imu(1))
while True:
    if wiiuse.poll(wiimote,1):
        #wiiuse.accel(wiimote[0])
        pitch, roll, alpha = a.contents.accel_calib.st_pitch, a.contents.accel_calib.st_roll, a.contents.accel_calib.st_alpha
        asyncio.run(s.set_rotation(1, pitch,roll,alpha))
