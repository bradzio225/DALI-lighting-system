import eventlet
import time

from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from dali_controller import *
from datetime import datetime

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

class Background_regulator(object):


    enable = False
    unit_of_work = 0

    def __init__(self, socketio, master):
        self.master = master
        self.socketio = socketio
        self.enable = True
        self.setpoint = 0
        self.Kp = 0
        self.Ki = 0
        self.error = 0
        self.error_sum = 0
        self.actual_dali_value = 0
        #self.file = open("/home/pi/Desktop/pomiar5.csv", "a")
        #self.file.write("Time,Error,Actual_dali_value,actual_light_level,Setpoint\n")


    def update_gains(self, setpoint, Kp, Ki):
        self.setpoint = setpoint
        self.Kp = Kp
        self.Ki = Ki
        broadcast_with_DAPC(self.master, self.actual_dali_value)
        self.enable = True

    def start(self):
        while self.enable:
            actual_light_level=light_level(self.master)
            eventlet.sleep(0.5)
            # time.sleep(1.5)
            actual_light_level=light_level(self.master)
            self.actual_dali_value = self.__update_values(light_level=actual_light_level)
            broadcast_with_DAPC(self.master, self.actual_dali_value)
            eventlet.sleep(0.5)
            # time.sleep(0.5)


    def __update_values(self, light_level):
        print("Light Level : " + format(light_level,'.2f') + " lx")
        print(f"Dali_value_old: {self.actual_dali_value}")
        self.error = self.setpoint - light_level
        print("error = " + format(self.error))
        self.error_sum += self.error
        if abs(self.error) < 20:
            self.error_sum = 0
        print("error sum = " + format(self.error_sum))
        self.actual_dali_value = self.actual_dali_value + int(self.error * self.Kp) + int(self.error_sum * self.Ki)
        if abs(self.error) > 3 and abs(self.error) < 12:
            if self.error > 0:
                self.actual_dali_value += 1
            else:
                self.actual_dali_value -= 1
        if self.actual_dali_value > 254:
            self.actual_dali_value = 254
        if self.actual_dali_value < 0:
            self.actual_dali_value = 0
        if abs(self.error_sum) > 250:
            self.error_sum = 0
        print(f"actual_dali_value_new: {self.actual_dali_value}")
        #self.file.write(str(datetime.now())+","+str(self.error)+","+str(self.actual_dali_value)+","+str(light_level)+","+str(self.setpoint)+"\n")
        #self.file.flush()
        return self.actual_dali_value

    def stop(self):
        self.enable = False
        #self.file.close()

@app.route("/")
def index():
    return render_template("index.html")

@socketio.on("bus_init")
def bus_init():
    print("Bus initialization")
    global master
    master = daliMaster.daliMaster()
    masterAddress = defines.LW14_I2C_ADDRESS
    if master.begin(masterAddress) == defines.ERROR :
        quit()
    global regulator
    regulator = Background_regulator(socketio, master)

@socketio.on("short_address_setup")
def setup_short_address(incoming_data):
    try:
        print(f"Your new short address: {int(incoming_data['short_address'])}")
        set_short_address(master=master, short_address=int(incoming_data['short_address']))
    except ValueError:
        emit('message', {'data':"Please select your short address"})

@socketio.on("short_address_power_level")
def short_address_power_level(incoming_data):
    try:
        print(f"Your lamp with short address: {int(incoming_data['lamp_short_address'])} will have {int(incoming_data['lamp_level'])} power level")
        power_level_with_definied_sa(master=master, selected_short_address=int(incoming_data['lamp_short_address']), level=int(incoming_data['lamp_level']))
    except ValueError:
        emit('message', {'data':"Please select your short address and lamp level"})

@socketio.on("broadcast_command")
def broadcast_command(incoming_data):
    try:
        print(f"Execute indirect power level command nr {int(incoming_data['command_number'])}")
        broadcast_with_command(master=master, indirect_command=int(incoming_data['command_number']))
    except ValueError:
        emit('message', {'data':"Please select your command number"})

@socketio.on("broadcast_DAPC")
def broadcast_DAPC(incoming_data):
    try:
        print(f"All conected lamps power level: {int(incoming_data['power_level'])}")
        broadcast_with_DAPC(master=master, power_level=int(incoming_data['power_level']))
    except ValueError:
        emit('message', {'data':"Please select your power level"})

@socketio.on("automatic_control_start")
def automatic_control_start(incoming_data):
    try:
        print(f"Automatic control started with setpoint: {int(incoming_data['setpoint'])}, Kp: {float(incoming_data['Kp'])} and Ki: {float(incoming_data['Ki'])}")
        print(regulator.enable)
        regulator.update_gains(setpoint=int(incoming_data['setpoint']), Kp=float(incoming_data['Kp']), Ki=float(incoming_data['Ki']))
        socketio.start_background_task(target=regulator.start)
    except ValueError:
        emit('message', {'data':"Please select your setpoint, Kp and Ki"})

@socketio.on("automatic_control_stop")
def automatic_control_stop():
    try:
        print('STOP')
        regulator.stop()
        print(regulator.enable)
        emit('message', {'data':'regulator stopped'})
    except ValueError:
        emit('message', {'data':'stopped error'})

@socketio.on("check_register")
def check_register():
    register = status_register(master=master)
    print(register)
    emit("register", {"data": str(register)}) 
    # emit("register", {"data": str(1)})

if __name__ == "__main__":
    socketio.run(app, host= "192.168.0.45", port=5000, debug=True)