from typing import Dict, List, Any
import re

def divide_in_chunks(to_chunk: List[Any], size: int) -> List[Any]:
    lst = [] # type: List[Any]
    for i in range(0, len(to_chunk), size):
        lst += [ to_chunk[i:i+size]  ]
    return lst

def parse_get_all_vms(output: str) -> List[Dict[str, str]]:
    m = divide_in_chunks( re.findall(r'(.*?)(?:[ \t]{2,}|\n)', output), 6 )

    vms = [] # type: List[Dict['str', 'str']]
    aux = {} # type: Dict['str', 'str']
    headers = m[0] # type: List[str]
    m = m[1:]

    for vm in m:
        for index, value in enumerate(vm):
            if value != '':
                aux[headers[index]] = value
        vms += [ aux.copy() ]
    return vms