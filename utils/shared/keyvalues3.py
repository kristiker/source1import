from pathlib import Path    
from dataclasses import dataclass

@dataclass(frozen=True)
class KV3Header:
    encoding: str = 'text'
    format: str = 'generic'
    common = '<!-- kv3 encoding:%s:version{e21c7f3c-8a33-41c5-9977-a76d3a32aa0d} format:%s:version{7412167c-06e9-4698-aff2-e63eb59037e7} -->'
    def __str__(self):
        return self.common % (self.format, self.encoding)

@dataclass(frozen=True)
class resource:
    path: Path
    def __str__(self):
        return f'resource:"{self.path.as_posix()}"'

def dict_to_kv3_text(kv3dict: dict, header: KV3Header = KV3Header()):
    kv3: str = str(header) + '\n'

    def obj_serialize(obj, indent = 1, dictKey = False):
        preind = ('\t' * (indent-1))
        ind = ('\t' * indent)
        if obj is None:
            return 'null'
        elif isinstance(obj, bool):
            if obj: return 'true'
            return 'false'
        elif isinstance(obj, str):
            return '"' + obj + '"'
        elif isinstance(obj, list):
            s = '['
            if any(isinstance(item, dict) for item in obj):  # TODO: only non numbers
                s = f'\n{preind}[\n'
                for item in obj:
                    s += (obj_serialize(item, indent+1) + ',\n')
                return s + preind + ']\n'

            return f'[{", ".join((obj_serialize(item, indent+1) for item in obj))}]'
        elif isinstance(obj, dict):
            s = preind + '{\n'
            if dictKey:
                s = '\n' + s
            for key, value in obj.items():
                #if value == [] or value == "" or value == {}: continue
                if not isinstance(key, str):
                    key = f'"{key}"'
                s +=  ind + f"{key} = {obj_serialize(value, indent+1, dictKey=True)}\n"
            return s + preind + '}'
        else: # int, float, resource
            # round off inaccurate dmx floats
            if type(obj) == float:
                obj = round(obj, 6)
            return str(obj)

    kv3 += obj_serialize(kv3dict)

    return kv3