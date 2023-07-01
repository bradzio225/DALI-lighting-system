# DALI-lighting-system
DALI lighting control system using Raspberry Pi 3B+, LED-Warrior14, LED-Warrior11 modules and BH1750 light sensor.

Layout diagram:

![image](https://github.com/bradzio225/DALI-lighting-system/assets/62242230/4bf545b8-5ccf-4b9b-9f03-667a7fe353d5)

Real system:

![image](https://github.com/bradzio225/DALI-lighting-system/assets/62242230/477277bf-fb82-42c5-a17e-c20dd8fff6cc)

# Used components:
- Raspberry Pi 3B+ - system control unit and web server,
- LED-Warrior14 - I2C to DALI bus signals converter,
- LED-Warrior11 - DALI bus power supply,
- BH1750 - light intensity sensor,
- Tungsram DALI lamp.

# Files:
- dali.py - Python file with DALI const definitions,
- defines.py - Python file with LED-Warrior14 and BH1750 defines,
- daliMaster.py - Python file with DALI class and control methods,
- dali_controller.py - Python file with functions used to control whole system,
- app.py - Python file with server code and background regulator.
- templates/index.html - HTML page template

Server was created using Flask and SocketIO Python libraries. 

### Run guide:
1. Install python packages.
```
pip install -r requirements.txt
```
2. Set server IP address in app.py
```
if __name__ == "__main__":
    socketio.run(app, host= "192.168.0.45", port=5000, debug=True)
```
3. Run app.py
Type in your terminal:
```
python3 app.py
```
4. Open your IP address in browser.
5. Press Bus initialisation button.
6. Check LED-Warrior14 status register. If all bits are zeros then your DALI communication is working.

### Web page template:
![image](https://github.com/bradzio225/DALI-lighting-system/assets/62242230/e3593f1a-f82d-4cf0-adb3-b56427d3d8b6)

Implemented functions:
- Setting up DALI lamp short address,
- Setting up lamp power level with defined short address,
- Send DALI indirect power level command,
- Setting up power level as broadcast,
- Automatic control - using PI regulator to reach light intensity setpoint
