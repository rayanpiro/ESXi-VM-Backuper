from typing import Dict, List, Optional
import re
from os import popen
import utils

class PrintWrapper:
    @staticmethod
    def read():
        return ""

def print_wrapper(cmd: str):
    print(cmd)
    return PrintWrapper

class SnapshotRemovalError(BaseException):
    """The current snapshot cannot be removed automatically"""

class SnapshotCreationError(BaseException):
    """The current snapshot cannot be created automatically"""

def key_updater(vm_dict: Dict[str, str], key_to_update: str, new_value: str) -> Dict[str, str]:
    vm_dict[key_to_update] = new_value
    return vm_dict

class ESXiController:
    # Static variables
    __snapshot_name = "BKP SNAPSHOT - SHOULD BE REMOVED AUTOMATICALLY"
    __exec_func = popen
    datastores_path = "/vmfs/volumes"

    @staticmethod
    def getAllVMS() -> List[Dict[str, str]]:
        command = "vim-cmd vmsvc/getallvms"
        pipe = ESXiController.__exec_func(command)
        vms_list = utils.parse_get_all_vms(pipe.read())


        for vm_item in vms_list:
            m = re.search(r'\[(?P<dataStore>.+)\] (?P<diskFolder>.+\/).+\.vmx', vm_item['File'])
            if m != None:
                key_updater(vm_item, 'File', ESXiController.complete_path(m.group('dataStore'), m.group('diskFolder')))
        
        return vms_list


    @staticmethod
    def poweron(vmid: str):
        command="vim-cmd vmsvc/power.on " + vmid
        pipe = ESXiController.__exec_func(command)
        print(pipe.read())
    
    @staticmethod
    def checkPowerState(vmid: str) -> Optional[str]:
        command="vim-cmd vmsvc/get.summary " + vmid
        pipe = ESXiController.__exec_func(command)
        m = re.search(r'powerState = \"(?P<power_state>.*?)\"', pipe.read())
        if m != None:
            return m.group('power_state')
    
    @staticmethod
    def complete_path(dataStore: str, diskFile: str) -> str:
        return ESXiController.datastores_path + "/" + dataStore + "/" + diskFile

    @staticmethod
    def get_all_vmdk_files_by_vmdk_descriptor(dataStore: str, disk_folder: str, vmdk_descriptor: str) -> List[str]:
        vmdk_files = [ESXiController.complete_path(dataStore, disk_folder+vmdk_descriptor)] # type: List[str]
        vmdk_reader = open(vmdk_files[0], 'r', encoding='utf8')
        m = re.findall(r'\"(?P<disk_file>.+\.vmdk)\"', vmdk_reader.read()) # type: List[str]

        for index, _ in enumerate(m):
            if '/' not in m[index]:
                m[index] = ESXiController.complete_path(dataStore, disk_folder+m[index])
            
        vmdk_files += m
        vmdk_reader.close()
        vmdk_files.sort()
        return vmdk_files

    @staticmethod
    def getVMDKFiles(vmid: str) -> List[str]:
        command="vim-cmd vmsvc/device.getdevices " + vmid
        pipe = ESXiController.__exec_func(command)
        m = re.finditer(r'fileName = \"\[(?P<dataStore>.+)\] (?P<diskFolder>.+\/)(?P<diskFile>.+\.vmdk)\"', pipe.read())

        vmdk_files = [] # type: List[str]
        for vmdk in m:
            matches = vmdk.groupdict() # type: Dict[str, str]
            vmdk_files += ESXiController.get_all_vmdk_files_by_vmdk_descriptor(matches['dataStore'], matches['diskFolder'], matches['diskFile'])
        
        return vmdk_files
    
    @staticmethod
    def shutdown(vmid: str):
        command="vim-cmd vmsvc/power.shutdown " + vmid
        pipe = ESXiController.__exec_func(command)
        print(pipe.read())
    
    @staticmethod
    def create_snapshot(vmid: str) -> str:
        command="vim-cmd vmsvc/snapshot.create " + vmid + " \"" + ESXiController.__snapshot_name + "\""
        pipe = ESXiController.__exec_func(command)
        pipe.read()
        command="vim-cmd vmsvc/get.snapshotinfo " + vmid
        pipe = ESXiController.__exec_func(command)
        m = re.search(r'name = \"'+ESXiController.__snapshot_name+r'\",\s+description = \"\",\s+id = (?P<snapshot_id>\d+)', pipe.read())
        if m != None:
            return m.group('snapshot_id')
        else:
            raise SnapshotCreationError

    @staticmethod
    def remove_snapshot(vmid: str, snapshot_id: str):
        command="vim-cmd vmsvc/snapshot.remove " + vmid + " " + snapshot_id
        pipe = ESXiController.__exec_func(command)
        pipe.read()
        command="vim-cmd vmsvc/get.snapshotinfo " + vmid
        pipe = ESXiController.__exec_func(command)
        m = re.search(r'id = '+snapshot_id, pipe.read())
        if m != None:
            raise SnapshotRemovalError