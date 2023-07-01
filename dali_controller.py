#!/usr/bin/python3


import daliMaster
import defines
import dali
import smbus
import eventlet
import time


def set_short_address(master, short_address):
    try:
        master.checkRange(short_address, 0, 63)
    except ValueError as e:
        print(e.args)
        quit()

    print('Your lamp new address {0}'.format(short_address))
    dtr = master.getShortAddress(short_address, defines.LW14_MODE_CMD)
    broadcastAddr = master.getBroadcastAddress(defines.LW14_MODE_CMD)

    print("\n##### Store new address into DTR #####")
    if master.clean() == defines.ERROR or master.specialCmd(dali.DALI_STORE_TO_DTR, dtr) == defines.ERROR :
        quit("unable to set DTR!")
    if master.waitForIdle() == defines.ERROR :
        quit("Idle timetimeout!")

    print("\n##### Read DTR back and check it again #####")
    if master.clean() == defines.ERROR or master.queryCmd(broadcastAddr, dali.DALI_QUERY_CONTENT_DTR)== defines.ERROR :
        quit("unable to read DTR back!")
    if master.waitForTelegram_1() == defines.ERROR :
        quit()
    regVal = master.read("command")
    if not regVal == dtr :
        quit("DTR does not match! {0}:{1}").format(regVal, dtr)

    print("\n##### DTR and Address match! Now save it as new address #####")
    if master.configCmd(broadcastAddr, dali.DALI_DTR_AS_SHORT_ADDRESS) == defines.ERROR :
        quit()
    if master.waitForIdle() == defines.ERROR :
        quit("Idle timeout!")

    print("\n##### Ask if there is a ballast with the given address that is able to communicate #####")
    shortAddress = master.getShortAddress(short_address, defines.LW14_MODE_CMD)
    if master.clean() == defines.ERROR or master.queryCmd(shortAddress, dali.DALI_QUERY_BALLAST) == defines.ERROR :
        quit()
    if master.waitForTelegram_1() == defines.ERROR :
        quit("response timeout!")
    if master.read("command") != defines.DALI_YES :
        quit()

    print("\n##### Well, now make it flash")
    if master.indirectCmd(shortAddress, dali.DALI_MAX_LEVEL) == defines.ERROR :
        quit()
    if master.waitForReady() == defines.ERROR :
        quit()
    time.sleep(2)
    if master.indirectCmd(shortAddress, dali.DALI_OFF) == defines.ERROR :
        quit()
    print("\n##### New address assigned and verified. Done. #####")

def power_level_with_definied_sa(master, selected_short_address, level):

    print("\nYour lamp nr {0} will be set to {1} level".format(selected_short_address, level))
    shortAddress = master.getShortAddress(selected_short_address, defines.LW14_MODE_DACP);
    if master.waitForReady() == defines.ERROR or master.directCmd(shortAddress, level) == defines.ERROR :
        quit('error')

    print('\n Now we will ask lamp to confirm required power level')
    time.sleep(1)
    shortAddress = master.getShortAddress(selected_short_address, defines.LW14_MODE_CMD);

    if master.clean() == defines.ERROR :
        quit('error')

    if master.waitForReady() == defines.ERROR  or master.queryCmd(shortAddress, dali.DALI_QUERY_ACTUAL_LEVEL) == defines.ERROR :
        quit('error')

    if master.waitForTelegram_1() == defines.ERROR :
        quit('error')

    res = master.read("command")

    if res == defines.ERROR :
        quit('error')

    print("\n##### Actual lamp level is {0}. Done. #####".format(res))

def broadcast_with_command(master, indirect_command):

    mode = defines.LW14_MODE_CMD
    daliAddress = master.getBroadcastAddress(mode)
    if master.indirectCmd(daliAddress, indirect_command) == defines.ERROR :
        quit()
    print("\n #### Done")

def broadcast_with_DAPC(master, power_level):
    mode = defines.LW14_MODE_DACP
    daliAddress = master.getBroadcastAddress(mode)
    if master.directCmd(daliAddress, power_level) == defines.ERROR :
        quit()
    print("\n #### Done")

def status_register(master):
    status_dict = master.read("status")
    return status_dict

def automatic_control(master, setpoint, Kp, Ki, enabled):

    mode = defines.LW14_MODE_DACP
    daliAddress = master.getBroadcastAddress(mode)

    error_sum = 0
    actual_dali_value = 50
    light_level = master.light_in_lux_data()
    if master.directCmd(daliAddress, actual_dali_value) == defines.ERROR :
            quit()
    while enabled == True:

        if not enabled:
            break
        print(enabled)
        eventlet.sleep(1)
        light_level= master.light_in_lux_data()
        print("Light Level : " + format(light_level,'.2f') + " lx")
        error = int(setpoint - light_level)
        print("error = " + format(error))
        error_sum += error
        if abs(error) < 40:
            error_sum = 0
        print("error sum = " + format(error_sum))
        actual_dali_value = actual_dali_value + int(error * Kp) + int(error_sum * Ki)
        if actual_dali_value > 254:
            actual_dali_value = 254
        if actual_dali_value < 0:
            actual_dali_value = 0
        if abs(error) > 4 and abs(error) < 11:
            eventlet.sleep(2)
            if error > 0:
                actual_dali_value += 1
            else:
                actual_dali_value -= 1
        print(f"actual_dali_value: {actual_dali_value}")
        if master.directCmd(daliAddress, actual_dali_value) == defines.ERROR :
            quit()
        eventlet.sleep(1)

def light_level(master):
    light_level= master.light_in_lux_data()
    return light_level

