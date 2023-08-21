#code by Spencer Lowery & Sky Niedzielski 2023 updated 8/21/23

from datetime import datetime
from tkinter import *
import time
import motorControl
import multiprocessing
import numpy as np
from matplotlib import pyplot as plt
from matplotlib.animation import FuncAnimation
from FaBo9Axis_MPU9250 import MPU9250

# Global variables
sys = None  # GravitySystem instance
loop = 0    # Loop counter
runTime = 0     # Initialize runTime

# Initialize variables to store data
time_data = []
gravity_data = []

# Create a figure and axis
fig, ax = plt.subplots()
line, = ax.plot([], [], lw=2)

#create queue for processing
data_queue = multiprocessing.Queue()

#open log file
logFile = open('log.txt', 'w')  # Open log file in write mode

class GravitySystem:
    def __init__(self):
        self.accelRom = MPU9250(address=0x68)
        self.runTime = 0
        self.gAvg = 0
        self.xTot = 0  # Initialize xTot
        self.yTot = 0  # Initialize yTot
        self.zTot = 0  # Initialize zTot
        self.xAvg = 0
        self.yAvg = 0
        self.zAvg = 0
        self.logFile = logFile  # Assign the opened logFile to an instance attribute
        self.time_data = []
        self.gravity_data = []

    def update_g_avg(self, accel):
        self.xTot += accel['x']
        self.yTot += accel['y']
        self.zTot += accel['z']
        # grav calc processing
        self.xAvg = self.xTot / loop
        self.yAvg = self.yTot / loop
        self.zAvg = self.zTot / loop
        self.gAvg = np.sqrt((self.xAvg ** 2) + (self.yAvg ** 2) + (self.zAvg ** 2))

        self.logFile.write(f"{loop}, {accel['x']}, {accel['y']}, {accel['z']}, "
                           f"{self.xAvg}, {self.yAvg}, {self.zAvg}, {self.gAvg}\n")
        self.time_data.append(time.time())
        self.gravity_data.append(self.gAvg)


    def gravityRun(self):
        startTime = time.time()
        rtime = self.runTime

        while (float(time.time() - startTime) < rtime) and not self.shutdown:
            try:
                accel = self.accelRom.readAccel()  # Use self.accelRom here
                self.update_g_avg(accel)

                loop += 1

            except:
                self.logFile.write("Unable to get data from accelerometer.\n")  # Use self.logFile here
                accelError += 1
                pass

def motor_process(data_queue):
    sys=motorControl.gravitySystem()
    while True:
    #motor operations and data in queue
        accel = sys.accelRom.readAccel()
        data_queue.put(accel)
        time.sleep(.1)

def graph_process(data_queue):
    def init():
        line.set_data([], [])
    return line,

def startAnimation(data_queue, run_time):
    def animate(i):
        global loop
        current_time = time.time()

        line.set_data(sys.time_data, sys.gravity_data)  # Use sys.time_data and sys.gravity_data
        ax.relim()
        ax.autoscale_view()

        elapsed_time = abs((datetime.now() - start_time)).total_seconds()
        remaining_time = run_time - elapsed_time
        plt.title(f'Gravity Tracking\nTime Elapsed: {elapsed_time:.2f} seconds')

        return line

    # Initialize variables
    global sys, loop
    sys = motorControl.GravitySystem()
    loop = 0
    start_time = datetime.now()

    ani = FuncAnimation(fig, animate, interval=1000)  # Update every 1 second
    plt.xlabel('Time')
    plt.ylabel('Gravity')
    plt.show()

if __name__ == "__main__":
    motor_process = multiprocessing.Process(target=motor_process, args=(data_queue,))
    graph_process = multiprocessing.Process(target=startAnimation, args=(data_queue, runTime))

    motor_process.start()
    graph_process.start()

    motor_process.join()
    graph_process.join()
    logFile.close()  # Close the log file when everything is done

def startSequence():

    start_time = datetime.now()  # Calculate the start time
    sys.setup(gInput.getdouble(gInput.get()), tInput.getdouble(tInput.get()))
    sys.run()

    startAnimation(sys, start_time)
    #check input values
    #start thread
    sys.setup(gInput.getdouble(gInput.get()), tInput.getdouble(tInput.get()))
    sys.run()
    #hide main screen open the secondary
    startTime = time.time()
    setupFrame.pack_forget()
    rTime(startTime)
    runFrame.pack()
    gUpdate()
    return

def eStop():
    sys.stop()
    runFrame.pack_forget()
    setupFrame.pack()

def rTime(sTime):
    tString = '{:.2f}'.format(time.time() - sTime)
    tLbl.config(text=tString)
    if(sys.rThread.is_alive()):
        tLbl.after(1000,rTime, sTime)
    else:
        eStop()

def gUpdate():
    gString = round(sys.gAvg,4)
    gLbl.config(text=gString)
    if(sys.rThread.is_alive()):
        gLbl.after(1000,gUpdate)

sys = motorControl.gravitySystem()

#window setup
root = Tk()
root.title("3D Clinostat")
root.option_add('*tearOff', FALSE)
root.minsize(400,300)

#contains all of the setup data
setupFrame = Frame(root)
setupFrame.pack()

#menu bar
mBar = Menu(root)
mFile = Menu(mBar)
mBar.add_cascade(menu=mFile, label="File")

#Sequence Start Button
startSequenceButton = Button(setupFrame, text = "Start", command=startSequence)
startSequenceButton.grid(row = 20, column = 2)

#Gravity Input
gInputFrame = LabelFrame(setupFrame, text="Desired Gravity(0-1)")
gInputFrame.grid(row=0, column=0, sticky=W)
gInput = Entry(gInputFrame, width=5, justify=RIGHT)
gInput.pack()

#Time Input
tInputFrame = LabelFrame(setupFrame, text="Experiment Time(hours)")
tInputFrame.grid(row=1, column=0, sticky=W)
tInput = Entry(tInputFrame, width=5, justify=RIGHT)
tInput.pack()

#Mechanical loading delay time Input
dInputFrame = LabelFrame(setupFrame, text="Delay Time(Minutes)")
dInputFrame.grid(row=2, column=0, sticky=W)
dInput = Entry(dInputFrame, width=5, justify=RIGHT)
dInput.pack()

#Homing device controlls
homeFrame = LabelFrame(setupFrame, text="Homing")
homeFrame.grid(row=5, column=0)

#Up button
homeUp = Button(homeFrame, text = '\u25B2', command=sys.rForward, repeatdelay=100, repeatinterval=100)
homeUp.grid(row = 0, column=2)

#Down button
homeDown = Button(homeFrame, text = '\u25BC', command=sys.rBackward, repeatdelay=100, repeatinterval=100)
homeDown.grid(row = 3, column=2)

#Left button
homeLeft = Button(homeFrame, text = '\u25C0', command=sys.rLeft, repeatdelay=100, repeatinterval=100)
homeLeft.grid(row = 2, column=1)

#Right button
homeRight = Button(homeFrame, text = '\u25B6', command=sys.rRight, repeatdelay=100, repeatinterval=100)
homeRight.grid(row = 2, column=3)

#mechanical loading configuration frame
mLoadFrame = LabelFrame(setupFrame, text="Mechanical Loading")
#mLoadFrame.grid(row=0, rowspan=6, column=3)

chamber1Lebel = Label(mLoadFrame, text="Chamber 1")
chamber1Lebel.grid(row=0,column=0)

chamber2Lebel = Label(mLoadFrame, text="Chamber 2")
chamber2Lebel.grid(row=1,column=0)

chamber3Lebel = Label(mLoadFrame, text="Chamber 3")
chamber3Lebel.grid(row=2,column=0)

chamber4Lebel = Label(mLoadFrame, text="Chamber 4")
chamber4Lebel.grid(row=3,column=0)

chamber5Lebel = Label(mLoadFrame, text="Chamber 5")
chamber5Lebel.grid(row=4,column=0)

chamber6Lebel = Label(mLoadFrame, text="Chamber 6")
chamber6Lebel.grid(row=5,column=0)

runFrame = Frame(root)

tLblFrame = LabelFrame(runFrame, text="Running Time")
tLblFrame.pack()
tLbl = Label(tLblFrame)
tLbl.pack()

gLblFrame = LabelFrame(runFrame, text="Gravity")
gLblFrame.pack()
gLbl = Label(gLblFrame)
gLbl.pack()

stopSequenceButton = Button(runFrame, text = "Stop", command=eStop)
stopSequenceButton.pack()

root.config(menu=mBar)
root.mainloop()
