from enum import Enum
import shutil
import time
from typing import List
from esxi_controller import ESXiController, SnapshotCreationError, SnapshotRemovalError


class VMPowerState(Enum):
    OFF = 'poweredOff'
    ON = 'poweredOn'


class BKPState(Enum):
    COMPLETED = 0
    FAILED = 1


class VirtualMachine:
    __id = ""
    __name = ""
    __snapshot_id = ""
    __initial_state = ""
    __vm_folder = ""
    __bkp_folder = "BKP/"

    def __init__(self, vmid: str, vmname: str, vm_folder: str):
        self.__id = vmid
        self.__name = vmname
        self.__vmdk_files = ESXiController.getVMDKFiles(self.__id)
        self.__initial_state = VMPowerState(
            ESXiController.checkPowerState(self.__id))
        self.__vm_folder = vm_folder

    @property
    def get_power_state(self):
        return VMPowerState(ESXiController.checkPowerState(self.__id))

    @property
    def is_final_power_state_correct(self) -> bool:
        return self.__initial_state == self.get_power_state

    @property
    def get_bkp_folder_name(self) -> str:
        return self.__bkp_folder

    @property
    def get_vm_path(self) -> str:
        return self.__vm_folder

    @property
    def get_vm_data(self) -> str:
        return self.__id+" "+self.__name

    @property
    def get_vmdk_files(self) -> List[str]:
        return self.__vmdk_files

    def makeSnapshot(self):
        print("Creating the BKP Snapshot in "+self.get_vm_data)
        self.__snapshot_id = ESXiController.create_snapshot(self.__id)

    def removeSnapshot(self):
        print("Removing the BKP Snapshot in "+self.get_vm_data)
        ESXiController.remove_snapshot(self.__id, self.__snapshot_id)

    def deleteLastBKP(self):
        print("Deleting last backup folder")
        shutil.rmtree(self.get_vm_path+self.get_bkp_folder_name,
                      ignore_errors=True)

    def poweroff(self):
        if self.get_power_state == VMPowerState.ON:
            ESXiController.shutdown(self.__id)
            print("Powering OFF "+self.get_vm_data)
            while self.get_power_state != VMPowerState.OFF:
                time.sleep(5)
            print("Powered OFF "+self.get_vm_data)

    def returnToInitialPowerState(self):
        print("The initial power state of "+self.get_vm_data +
              " was "+str(self.__initial_state))

        if self.get_power_state != self.__initial_state and self.get_power_state == VMPowerState.OFF:
            self.poweron()

        print("The current power state of "+self.get_vm_data +
              " is "+str(self.get_power_state))

    def poweron(self):
        if self.get_power_state == VMPowerState.OFF:
            ESXiController.poweron(self.get_vm_data)
            print("Powering ON "+self.get_vm_data)
            while self.get_power_state != VMPowerState.ON:
                time.sleep(5)
            print("Powered ON "+self.get_vm_data)

    def makeBackup(self):
        self.deleteLastBKP()
        if self.get_power_state == VMPowerState.OFF:
            self.coldBackupStrategy()
        else:
            self.hotBackupStrategy()

    def hotBackupStrategy(self):
        print("HOT BACKUPING ", self.get_vm_data)
        try:
            self.copyAllNeededFiles()
            self.makeSnapshot()
            self.copyVMDKFiles()
            self.removeSnapshot()
        except SnapshotCreationError:
            # self.poweroff()
            # self.makeBackup()
            print("Should Cold Backup But Not NOW")

        except:
            try:
                self.removeSnapshot()
            except SnapshotRemovalError:
                pass
        self.returnToInitialPowerState()

    def coldBackupStrategy(self):
        print("COLD BACKUPING ", self.get_vm_data)
        self.poweroff()
        try:
            self.copyAllNeededFiles()
            self.copyVMDKFiles()
        except:
            pass
        self.returnToInitialPowerState()

    def copyAllNeededFiles(self):
        bkp_path = self.get_vm_path+self.get_bkp_folder_name
        print("Copying general files to: "+bkp_path)
        ignored_files = shutil.ignore_patterns(
            '*.lck', '*.vmdk', '*.nvram', '*.log', '*.vswp')
        shutil.copytree(self.get_vm_path, bkp_path, ignore=ignored_files)

    def copyVMDKFiles(self):
        bkp_path = self.get_vm_path+self.get_bkp_folder_name
        print("Copying VMDK files to: "+bkp_path)
        for vmdk_file in self.get_vmdk_files:
            print("Current file: "+vmdk_file)
            shutil.copy(vmdk_file, bkp_path)
        print("VMDK Files Copy Succeed")
