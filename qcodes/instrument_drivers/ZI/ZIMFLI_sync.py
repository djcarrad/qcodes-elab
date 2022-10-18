from zhinst.ziPython import ziDAQServer
from zhinst.utils import utils
import time




daq = ziDAQServer("localhost", 8004, 6)

# mds = daq.multiDeviceSyncModule()
# mds.set('group', 0)


def MDS_addDevice(device):
    currentDevList = daq.getByte('/zi/mds/groups/0/devices')
    newDevList = currentDevList + ',' + device

    daq.setByte('/zi/mds/groups/0/devices', newDevList)
    return


def MDS_setDevices(devList):
    daq.setByte('/zi/mds/groups/0/devices', devList)
    return


def MDS_getMaster():
    devList = daq.getByte('/zi/mds/groups/0/devices')
    pos = devList.find(",")
    master = devList[0:pos]

    return master


def MDS_getSlaves():
    devList = daq.getByte('/zi/mds/groups/0/devices')
    pos = devList.find(",")
    slaveString = devList[pos+1:]
    slaveList = slaveString.split(",")

    return slaveList


def li_matchFreq(liList):
    masterF = liList[0].osc0_freq()

    for dev in liList[1:]:
        dev.osc0_freq(masterF)

    return





def syncLockins(liList):

    devList = []
    for dev in liList:
        devList.append(dev.serial)

    devString = ','.join(devList)

    mds = daq.multiDeviceSyncModule()
    mds.set('group', 0)
    mds.set('recover', 1)
    mds.execute()

    MDS_setDevices(devString)
    mds.set('devices', devString)

    for dev in liList[1:]:
        dev.clock_src("10MHz")

    mds.set('start', 1)

    li_matchFreq(liList)


    timeout = time.time() + 180
    while True:
        status = mds.get("status")
        if status["status"][0] == -1:
            raise Exception("Failed to sync")


        if status["status"][0] == 2:
            break

        if time.time() > timeout:
            raise Exception("Sync Timeout")



    mds.set('phasesync', 1)
    print("Successfully synced")

    return










