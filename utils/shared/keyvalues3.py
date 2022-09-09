from pathlib import Path    
from dataclasses import dataclass
from uuid import UUID

@dataclass(frozen=True)
class KV3Header:
    encoding: str = 'text'
    encoding_ver: str = 'e21c7f3c-8a33-41c5-9977-a76d3a32aa0d'
    format: str = 'generic'
    format_ver: str = '7412167c-06e9-4698-aff2-e63eb59037e7'
    _common = '<!-- kv3 encoding:%s:version{%s} format:%s:version{%s} -->'
    def __str__(self):
        return self._common % (self.encoding, self.encoding_ver, self.format, self.format_ver)

@dataclass(frozen=True)
class resource:
    path: Path
    def __str__(self):
        return f'resource:"{self.path.as_posix().lower()}"'

class KV3File(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.header = KV3Header(format="source1imported")

    def __str__(self):
        kv3 = str(self.header) + '\n'

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

        kv3 += obj_serialize(self)

        return kv3

    def ToString(self):
        return self.__str__()

if __name__ == '__main__':
    import unittest
    class Test_KV3(unittest.TestCase):
        default_header = '<!-- kv3 encoding:text:version{e21c7f3c-8a33-41c5-9977-a76d3a32aa0d} format:generic:version{7412167c-06e9-4698-aff2-e63eb59037e7} -->'
        def test_default_header(self):
            self.assertEqual(str(KV3Header()), self.default_header)

        def test_custom_header(self):
            header = KV3Header('text2', '123-123', 'generic2', '234-234')
            headertext = '<!-- kv3 encoding:text2:version{123-123} format:generic2:version{234-234} -->'
            self.assertEqual(str(header), headertext)

        def test_kv(self):
            expect_text = f'{self.default_header}\n{{'+\
                '\n\ta = "asd asd"'+\
                '\n\tb = \n\t{\n\t\t"(2,)" = 3\n\t}'+\
                '\n\tc = ["listed_text1", "listed_text2"]\n}'
            self.assertEqual(
                KV3File(
                    a='asd asd',
                    b={(2,):3}, 
                    c=["listed_text1", "listed_text2"]
                ).ToString(),
                expect_text
            )

    unittest.main()
