# cppkeyvalues.py
# A keyvalues.cpp python rewrite

import collections
from warnings import warn

from ctypes import *
NULL = 0

class Conv:
    def GetDelimiter(self):
        return '"'
    def GetDelimiterLength(self):
        return 1

#from io import BufferedReader # ????
class CUtlBuffer(collections.UserString):

    def IsValid(self) -> bool:
        return self.data != ""

    def GetDelimitedString(self, conv: Conv, nMaxChars: int) -> str:
        
        string = CUtlBuffer(self.data)

        if not string.IsValid():
            return string # null, empty string
        if nMaxChars == 0:
            nMaxChars = 2147483647
        
        # skippp
        return string.split('"')[1][:nMaxChars]
        
        # just in case 1
        string.EatWhiteSpace()
        # Does the next bytes of the buffer match a pattern?
        # if ( !PeekStringMatch( 0, pConv->GetDelimiter() -> '"', pConv->GetDelimiterLength() -> 1) )
        if not string[0] == '"':
            return string

        #SeekGet( SEEK_CURRENT, pConv->GetDelimiterLength() ); start reading after the quote
        string = string[1:]

        nRead = 0
        while string.IsValid():
            if string[0] == '"':
                break
            
            c = getcharinternalwitffafsa()
            if nRead < nMaxChars:
                string[nRead] = c
                nRead += 1

        if nRead >= nMaxChars:
            nRead = nMaxChars - 1
        
    def lcut(self, n): self.data = self.data[n:]
    def rcut(self, n): self.data = self.data[:n]

    def PeekGet(self, i) -> list: # from start get i chars
        peek = []
        for j in range(i):
            try: char = self.data[j]
            except IndexError: char = 0
            peek.append(char)
        return peek
    
    def EatWhiteSpace(self):
        self.data = self.data.lstrip()

    def EatCPPComment(self) -> bool:
        #peek =  self.PeekGet(2)
        #print(f"our peek {peek}")
        #if (not peek or (peek[0] != '/') or (peek[1] != '/')):
        #    return False
        if (not self.data or (self.data[0] != '/') or (self.data[1] != '/')):
            return False

        self.lcut(2)#.data = self.data[2:]

        for i, char in enumerate(self.data, 1):
            if char != '\n':
                continue
            self.data = self.data[i:]
            return True

KEYVALUES_TOKEN_SIZE = 1024 * 32

# const char *KeyValues::ReadToken( CUtlBuffer &buf, bool &wasQuoted, bool &wasConditional )
class Token(collections.UserString):
    def __init__(self, data = "") -> None:
        super().__init__(data)
        self.wasQuoted = False
        self.wasConditional = False

class NullObj:
    def __bool__(self):
        return False
    def __eq__(self, other):
        if other == 0:
            return True

class NullToken(NullObj): # str
    def __init__(self, wasQuoted = False, wasConditional = False):
        self.wasQuoted = wasQuoted
        self.wasConditional = wasConditional

class CKeyValuesTokenReader:
    def __init__(self, buf: CUtlBuffer) -> None:
        self.m_Buffer: CUtlBuffer = buf
        self.m_nTokensRead: int = 0

        self.lastToken = Token()
    
    def ReadToken(self):
        nullToken = NullToken(self.lastToken.wasQuoted, self.lastToken.wasConditional) # 
        token = Token()
        self.lastToken = token

        if not self.m_Buffer:
            return nullToken

        while ( True ):
            self.m_Buffer.EatWhiteSpace()
            if not self.m_Buffer.IsValid(): return nullToken
            if not self.m_Buffer.EatCPPComment():
                break

        #c_full = self.m_Buffer#[0]
        c = self.m_Buffer[0]
        #not self.m_Buffer or 
        if c == 0:
            return nullToken
        
        # read quoted strings specially
        if c == '\"':
            token.wasQuoted = True
            token.data = self.m_Buffer.GetDelimitedString(Conv(), KEYVALUES_TOKEN_SIZE)

            self.m_nTokensRead += 1
            self.m_Buffer.lcut(len(token)+2) # buffer workaround
            return token
        
        if c == '{' or c == '}' or c == '=':
            token.data = c
            self.m_nTokensRead += 1
            self.m_Buffer.lcut(1) # buffer workaround
            return token


        # read in the token until we hit a whitespace or a control character
        bReportedError = False
        bConditionalStart = False
        nCount = 0

        charz = self.m_Buffer.PeekGet(len(self.m_Buffer)+1) # made up
        #print(charz)
        #while (True): #( c = (const char*)buf.PeekGet( sizeof(char), 0 ) )
        for c in charz:
    
            # end of file
            if c == 0:
                break
            # break if any control character appears in non quoted tokens
            if c == '"' or c == '{' or c == '}' or c == '=':
                break
            if c == '[':
                bConditionalStart = True
            if c == ']' and bConditionalStart:
                bConditionalStart = False
                self.wasConditional = True
            # break on whitespace
            if c.isspace() and not bConditionalStart:
                break
            if nCount < (KEYVALUES_TOKEN_SIZE-1):
                token.data += c
                nCount+=1
            elif(not bReportedError):
                bReportedError = True
                print(" ReadToken overflow")

        if not token.data:
            token.data = 0
        self.m_nTokensRead += 1

        self.m_Buffer.lcut(nCount) # buffer workaround
        return token

    def SeekBackOneToken(self): # and return it
        return self.lastToken

from enum import IntEnum, Enum
from typing import Generator, Optional, Sequence, Union, Iterable, TypedDict
from cstr import strtol, strtod

class KeyValues: pass # Prototype LUL ( for typing to work inside own class functions)

from functools import partial, wraps

def _dec_subkeyvalue(func, isSub = True):
        @wraps(func)
        def ret_fun(self, *args, **kwargs):
            if self.IsSub() == isSub:
                return func(self, *args, **kwargs)
            return None
        return ret_fun

class KeyValues: pass # Prototype LUL ( for typing to work inside own class functions)
class KVCollection: pass
class GenericValue: pass

#KVCollection = NewType("KVCollection", collections.UserList)

class KVValue:#(KVCollection):
    KVCollect = partial(_dec_subkeyvalue, isSub=True)
    KVSingle = partial(_dec_subkeyvalue, isSub=False)

    def __new__(cls, val) -> Union[KVCollection, GenericValue]:
        if cls is KVValue:
            # Iterator BUG here as every KV is considered Iterable simply becaue it has a __iter__
            # KV("", KV("", 2).value) -> KV("", []) instead of  KV("", 2)
            # KVValue(KVValue()) forces into KVCollection instead of preserving data type 
            if isinstance(val, Sequence) and not isinstance(val, str):
                cls = KVCollection
            else:
                cls = GenericValue
        self = object.__new__(cls)
        self.data = val
        return self

    def __init__(self, val: Union[int, float, str, Iterable[int], Iterable[KeyValues]]) -> None:
        self.data = val
        #self.fancyGetInt = self.data.__int__
        #self.fancyGetFlat = self.data.__float__

    def __iter__(self):
        if self.IsSub():
            return super().__iter__()
        return iter(()) # is this the behavior of cpp? i think so
    
    def append(self, item: KeyValues) -> None:
        print('Appending item', item)
        if not isinstance(item, KeyValues):
            raise ValueError("Can only add KeyValues")
        return super().append(item)

    def IsSub(self):
        return isinstance(self.data, list)

    @KVSingle
    def GetInt(self) -> int: return int(self.data) # atoi, int cast#
    @KVSingle
    def GetFloat(self) -> int: return float(self.data) # atof, float cast

    
    #@KVCollect
    def GetValues(self) -> Generator[KeyValues, None, None]:
        yield from self

    def __repr__(self):
        return repr(self.data)

    def ToStr(self, level = 0):
        line_indent = '\t' * level
        s = ""
        if self.IsSub():
            s += "\n" + line_indent + '{\n'
            for item in self:
                s += (item.ToStr(level+1))
            s += line_indent + "}\n"
        else:
            s = f'\t"{self.data}"\n'

        return s

class KVCollection(collections.UserList, KVValue): ...
class ColorValue(collections.UserList, KVValue): ... # unsigned char [4]
class GenericValue(KVValue): ... # int, float, char*, wchar*, ptr, 

class KVType(IntEnum):
    TYPE_NONE = 0, # hasChild
    TYPE_STRING = 1,
    TYPE_INT = 2,
    TYPE_FLOAT = 3,
    TYPE_PTR = 4,
    TYPE_WSTRING = 5,
    TYPE_COLOR = 6,
    TYPE_UINT64 = 7,    

class KeyValues(object):
    "Key that holds a Value. Value can be a list holding other KeyValues"


    def __init__(self, k: Optional[str] = None, v: Union[int, float, str, KVCollection] = None):
        self.keyName =k.lower() if k else k
        
        self.value = KVValue(v) # Iterator BUG

        self.DataType = KVType.TYPE_NONE
        self.HasEscapeSequences: bool
        self.KeyNameCaseSensitive2: int
        
        # listlike pointery variables 
        self.Peer: KeyValues = None
        #self.Sub: KeyValues = None
        self.Chain: KeyValues = None

        self._sValue: str = None
        self._wsValue: str = None
        self._iValue: int = None
        self._flValue: float = None
        self._Color: list = None

    #def __str__(self) -> str:
    #    return f"(\"{self.keyName}\": {self.value})"

    @property
    def Sub(self):
        return self.value.GetValues()
    @Sub.setter
    def Sub(self, subvalues: Iterable[KeyValues]):
        self.value = KVValue(subvalues)
    @Sub.deleter
    def Sub(self):
        del self.value
        self.value = GenericValue(None)
    @property ##### m_sValue
    def m_sValue(self):
        return self._sValue
    @m_sValue.setter
    def m_sValue(self, val: str):
        self.value = KVValue(val)
        self._sValue = val
    @m_sValue.deleter
    def m_sValue(self):
        self._sValue = None

    @property ##### m_iValue
    def m_iValue(self):
        return self._iValue
    @m_iValue.setter
    def m_iValue(self, val: float):
        self.value = KVValue(val)
        self._iValue = val
    @m_iValue.deleter
    def m_iValue(self):
        self._iValue = None
    
    @property ##### m_flValue
    def m_flValue(self):
        return self._flValue
    @m_flValue.setter
    def m_flValue(self, val: float):
        self.value = KVValue(val)
        self._flValue = val
    @m_flValue.deleter
    def m_flValue(self):
        self._flValue = None

    def FindKey(self, keyName, bCreate):
        if keyName is None:
            return self
        
        lastItem = None
        for dat in self.value:
            lastItem = dat
            if dat.keyName == keyName:
                break
        
        if not dat:
            if bCreate:
                ...
            else:
                return None

    
    def Clear(self):
        del self.Sub
        self.Sub = None
        self.DataType = KVType.TYPE_NONE

    def SetName(self, name: str):
        self.keyName = name.lower()

    def LoadFromFile(self, resourceName):
        with open(resourceName, 'r') as f:
            buf = CUtlBuffer(f.read())
            self.LoadFromBuffer(resourceName, buf)

    def LoadFromBuffer(self, resourceName, buf: CUtlBuffer) -> bool:
        previousKey: KeyValues = None
        currentKey: KeyValues = self
        includedKeys: "list[KeyValues]" = []
        baseKeys: "list[KeyValues]" = []
        #wasQuoted: bool
        #wasConditional: bool
        tokenReader = CKeyValuesTokenReader(buf) # (self, buf)
        #print(tokenReader, tokenReader.__dict__)
        
        while True: # do while
            # the first thing must be a key
            s = tokenReader.ReadToken()
            if not buf.IsValid() or s == 0:
                break

            if not s.wasQuoted and not s:
                # non quoted empty strings stop parsing
                # quoted empty strings are allowed to support unnnamed KV sections
                break

            if s == '#include' or s == '#base': # special include macro (not a key name)
                macro = str(s)
                s = tokenReader.ReadToken()
                # Name of subfile to load is now in s

                if not s:
                    print(f"{macro} is NULL.")
                else:
                    ...
                    #ParseIncludedKeys(resourceName, s, "baseKeys if #base else includedKeys") #TODO
            
                continue

            if not currentKey:
                currentKey = KeyValues(s)

                currentKey.HasEscapeSequences = self.HasEscapeSequences # same format has parent use

                if previousKey:
                    previousKey.SetNextKey(currentKey)
            else:
                currentKey.SetName(s)

            s = tokenReader.ReadToken()

            if s.wasConditional:
                s = tokenReader.ReadToken()

            if s and s[0] == '{' and not s.wasQuoted:
                # header is valid so load the file
                currentKey.Sub = []
                currentKey.RecursiveLoadFromBuffer(resourceName, tokenReader)
            else:
                print("LoadFromBuffer: missing {")
            
            if False:
                if previousKey:
                    previousKey.SetNextKey(None)

            if not buf.IsValid():
                break

    def RecursiveLoadFromBuffer(self, resourceName, tokenReader: CKeyValuesTokenReader):
        while True:
            bAccepted = True
            # get the key name
            name = tokenReader.ReadToken()
            if name == 0: # EOF stop reading
                print("got EOF instead of keyname")
                break
            if name == "": # empty token, maybe "" or EOF BUG this doesnt make sense for empty keys?
                print("got empty keyname")
                break
            if name[0] == '}' and not name.wasQuoted: # top level closed, stop reading
                break
            
            #if name == ".filelist":
            #    breakpoint()
            dat = KeyValues(name)
            self.value.append(dat)
            del name
            value = tokenReader.ReadToken()
            
            vne = (value != "") # value not empty -> True

            foundConditional = value.wasConditional
            if value.wasConditional and value:
                bAccepted = self.EvaluateConditional(peek, pfnEvaluateSymbolProc)
                value = tokenReader.ReadToken()
            if value == 0:
                print("Got NULL key")
                break

            
            # support the '=' as an assignment, makes multiple-keys-on-one-line easier to read in a keyvalues file
            if vne and value[0] == '=' and not value.wasQuoted: #value[0] == '=' value is sometimes empty giving IndexError
                # just skip over it
                value = tokenReader.ReadToken()
                foundConditional = value.wasConditional
                if value.wasConditional and value:
                    bAccepted = self.EvaluateConditional(peek, pfnEvaluateSymbolProc)
                    value = tokenReader.ReadToken()
                if foundConditional and True:
                    # if there is a conditional key see if we already have the key defined and blow it away, last one in the list wins
                    ...
            if value == 0:
                print("RecursiveLoadFromBuffer:  got NULL key" )
                break
            if vne and value[0] == '}' and not value.wasQuoted:
                print("RecursiveLoadFromBuffer:  got } in key")
                break
            if vne and value[0] == '{' and not value.wasQuoted:
                # sub value list
                dat.Sub = []
                dat.RecursiveLoadFromBuffer(resourceName, tokenReader)
            else:
                if value.wasConditional:
                    print("RecursiveLoadFromBuffer:  got conditional between key and value" )
                    break
                if dat.m_sValue:
                    del dat.m_sValue # dont need
                    dat.m_sValue = None

                length = len(value)
                pSEnd = length

                lval = strtol(str(value))
                pIEnd = lval.endpos
                lval = lval.value

                fval = strtod(str(value))
                pFEnd = fval.endpos
                fval = fval.value

                overflow: bool = (lval == 2147483647 or lval == -2147483646)
                if not vne:#value == "":
                    dat.DataType = KVType.TYPE_STRING
                elif 18 == length and value[0] == '0' and value[1] == 'x':
                    dat.m_sValue = str(int(str(value), 16)) # 16?
                    dat.DataType = KVType.TYPE_UINT64
                elif (pFEnd > pIEnd) and (pFEnd == pSEnd):#len(str(fval).rstrip('0').rstrip('.')) > len(str(lval)): # TODO support this '1.511111111fafsadasd'
                    dat.m_flValue = fval
                    dat.DataType = KVType.TYPE_FLOAT
                elif (pIEnd == pSEnd) and not overflow: # len(str(lval)) == length 
                    dat.m_iValue = lval
                    dat.DataType = KVType.TYPE_INT
                else:
                    dat.DataType = KVType.TYPE_STRING

                if dat.DataType == KVType.TYPE_STRING:
                    dat.m_sValue = str(value)
                
                # Look ahead one token for a conditional tag
                #peek = tokenReader.ReadToken()
                #if peek.wasConditional:
                #    bAccepted = self.EvaluateConditional(peek, pfnEvaluateSymbolProc)
                #else:
                #    tokenReader.SeekBackOneToken()

                if bAccepted:
                    ...
                    #self.value.append(dat)
                else:
                    # remove key from list
                    del self.value[dat]
                    del dat

    def EvaluateConditional(self, **args):
        return True
    def __repr__(self):
        return f"{self.__class__.__name__}({self.keyName!r}, {self.value.__class__.__name__}({self.value!r}))"

    def ToStr(self, level=0):
        line_indent = "\t" * level

        return line_indent + f'"{self.keyName}"{self.value.ToStr(level)}'


if __name__ == "__main__":

    from pathlib import Path

    def updateTestOutpt(file: Path):
        with open(file, "r") as fp:
            kv2 = KeyValues()
            kv2.LoadFromFile(file)
            newfile = file.parents[1] / "ndata" / file.name
            with newfile.open("w") as newfp:
                newfp.write(kv2.ToStr())

    for file in Path(r".\test\keyvalues\data").glob("*"):
        pass
        #updateTestOutpt(file)
    import unittest
 
    class Test_KeyValues(unittest.TestCase):
        def test_1(self):
            text = "//asdasd\nvalue {\"key\"  \"key\"  \"\"value }"
            text_expected = '"value"\n{\n\t"key"\t"key"\n}\n'
            kv = KeyValues()
            kv.LoadFromBuffer("as", CUtlBuffer(text))
            self.assertEqual(kv.ToStr(), text_expected)

    for i, file in enumerate(Path(r".\test\keyvalues\data").glob("*")):
        def test_filen(self):
            with (file.parents[1] / "ndata" / file.name).open() as e:
                expect = e.read()
                kv = KeyValues()
                kv.LoadFromFile(file.as_posix())

                self.assertEqual(kv.ToStr(), expect)
        setattr(Test_KeyValues, f"{test_filen.__name__}{i}", test_filen)

    unittest.main()