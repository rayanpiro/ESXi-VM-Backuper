#!/usr/bin/env python3

from typing import List
from esxi_controller import ESXiController
from virtual_machine import VirtualMachine

registered_vms = ESXiController.getAllVMS()
vm_list = [] # type: List[VirtualMachine]

for vm in registered_vms:
    vm_list.append( VirtualMachine(vm['Vmid'], vm['Name'], vm['File']) )

for vm in vm_list:
    print('VM Backup Process Start ', vm.get_vm_data)
    vm.makeBackup()
    print('VM Backuped ', vm.get_vm_data)
