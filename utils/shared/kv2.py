
import os
import collections
class Conv:
    def __init__(self) -> None:
        pass

    def GetDelimiter(self):
        return '"'
    def GetDelimiterLength(self):
        return 1


from io import BufferedReader 
class CUtlBuffer(collections.UserString):
    #...
    # eatcppcomment, isvalid

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


        #newdata = ''
        #for i, char in enumerate(self.data):
        #    if char == '\n':
        #        break
        #    newdata= self.data[i+1:]
        #self.data = newdata
        #return True

KEYVALUES_TOKEN_SIZE = 1024 * 32

# const char *KeyValues::ReadToken( CUtlBuffer &buf, bool &wasQuoted, bool &wasConditional )
class Token(collections.UserString):
    def __init__(self, data = "") -> None:
        super().__init__(data)
        self.wasQuoted = False
        self.wasConditional = False

    #    self.Buf: str = self.data
    #def __str__(self) -> str:
    #    return str(self.Buf)

class CKeyValuesTokenReader:
    def __init__(self, buf: CUtlBuffer) -> None:
        self.m_pKeyValues: KeyValues
        self.m_Buffer: CUtlBuffer = buf
        self.m_nTokensRead: int = 0
        #self.m_bUsePriorToken: bool = False
        #self.m_bPriorTokenWasQuoted: bool
        #self.m_bPriorTokenWasConditional: bool
        #self.TokenBuf: str
    
    def ReadToken(self):
        token = Token()

        if not self.m_Buffer:
            return 0

        while ( True ):
            self.m_Buffer.EatWhiteSpace()
            if not self.m_Buffer.IsValid(): return 0
            if not self.m_Buffer.EatCPPComment():
                break

        c_full = self.m_Buffer#[0]
        c = c_full[0]
        if not c_full or c == 0:
            return 0
        
        # read quoted strings specially
        if c == '\"':
            token.wasQuoted = True
            token.data = self.m_Buffer.GetDelimitedString(Conv(), KEYVALUES_TOKEN_SIZE)

            self.m_nTokensRead += 1
            self.m_Buffer.lcut(len(token)+2) # buffer workaround
            return token
        
        if c == '{' or c == '}':
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
            if c == '"' or c == '{' or c == '}':
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

    #def SeekBackOneToken(self):
    #    if self.m_bUsePriorToken:
    #        raise RuntimeError("It is only possible to seek back one token at a time")
    #    if self.m_nTokensRead == 0:
    #        raise RuntimeError("No tokens read yet")
    #    self.m_bUsePriorToken = True

from enum import IntEnum, Enum
from typing import Generator, Optional, Union, Iterable

class KeyValues: pass # Prototype LUL ( for typing to work inside own class functions)

class Sub(collections.UserList):
    def __init__(self, initlist: Union[int, float, str, Iterable[KeyValues]]) -> None:
        if initlist is Iterable:
            super().__init__(initlist=initlist)
        else:
            self.data = initlist
#class Key(collections.UserString): ...

from functools import partial, wraps

def _subkeylist_method(func, isSub = True):
        @wraps(func)
        def ret_fun(self, *args, **kwargs):
            if self.IsSub() == isSub:
                return func(self, *args, **kwargs)
            return None
        return ret_fun

class Value(Sub):
    def IsSub(self):
        return isinstance(self.data, list)

    real_decorator1 = partial(_subkeylist_method, isSub=True)
    real_decorator2 = partial(_subkeylist_method, isSub=False)

    @
    def GetValues(self):
        return self.data

    def __str__(self):
        if not self.IsSub():
            return str(self)
        return 


class KeyValues(object):
    "Key that holds a Value. Value can be a list holding other KeyValues"

    class Type(IntEnum):
            TYPE_NONE = 0, # hasChild
            TYPE_STRING = 1,
            TYPE_INT = 2,
            TYPE_FLOAT = 3,
            TYPE_PTR = 4,
            TYPE_WSTRING = 5,
            TYPE_COLOR = 6,
            TYPE_UINT64 = 7,    

    def __init__(self, k: Optional[str] = None, v: Union[int, float, str, Sub] = None):
        self.keyName =k.lower() if k else k
        
        self.value = v

        self.DataType: self.Type = self.Type.TYPE_NONE
        self.HasEscapeSequences: bool
        self.KeyNameCaseSensitive2: int
        
        # listlike pointery variables 
        self.Peer: KeyValues = None
        self.Sub: KeyValues = None
        self.Chain: KeyValues = None
    
    def Clear(self):
        del self.Sub
        self.Sub = None
        self.DataType = self.Type.TYPE_NONE

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
        print(tokenReader, tokenReader.__dict__)
        
        while True: # do while
            # the first thing must be a key
            s = tokenReader.ReadToken()
            print(s)
            if not buf.IsValid() or not s:
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
            if not name: # empty token, maybe "" or EOF
                print("got empty keyname")
                break
            if name[0] == '}' and not name.wasQuoted: # top level closed, stop reading
                break

            dat = KeyValues(name)
            value = tokenReader.ReadToken()
            foundConditional = value.wasConditional
            if value.wasConditional and value:
                bAccepted = self.EvaluateConditional(peek, pfnEvaluateSymbolProc)
                value = tokenReader.ReadToken()
            if value == 0:
                print("Got NULL key")
                break

            # support the '=' as an assignment, makes multiple-keys-on-one-line easier to read in a keyvalues file
            if value[0] == '=' and not value.wasQuoted:
                # just skip over it
                value = tokenReader.ReadToken()
                foundConditional = value.wasConditional
                if value.wasConditional and value:
                    bAccepted = self.EvaluateConditional(peek, pfnEvaluateSymbolProc)
                    value = tokenReader.ReadToken()
                if foundConditional and True:
                    # if there is a conditional key see if we already have the key defined and blow it away, last one in the list wins
                    ...
            if not value:
                break
            if value[0] == '}' and not value.wasQuoted:
                print("RecursiveLoadFromBuffer:  got } in key")
                break
            if value[0] == '{' and not value.wasQuoted:
                # sub value list
                dat.RecursiveLoadFromBuffer(resourceName, tokenReader)
            else:
                if value.wasConditional:
                    print("RecursiveLoadFromBuffer:  got conditional between key and value" )
                    break
                #if dat.GetValue(dat.Type.TYPE_STRING):
                #    dat.SetValue(dat.Type.TYPE_STRING, None)
                #    dat.sValue = None
                
                vlen = len(value)
                lval = 1337#int(value)
                fval = 1337.1#float(value)
                overflow = (lval == 2147483647 or lval == -2147483646)
                if value == "":
                    dat.DataType = self.Type.TYPE_STRING
                elif 18 == vlen and value[0] == '0' and value[1] == 'x':
                    dat.value = int(value, 0)
                    dat.DataType = self.Type.TYPE_UINT64
                elif len(str(fval).rstrip('0').rstrip('.')) > len(str(lval)): # TODO support this '1.511111111fafsadasd'
                    dat.flValue = fval
                    dat.DataType = self.Type.TYPE_FLOAT
                elif len(str(lval)) == vlen and not overflow:
                    dat.iValue = lval
                    dat.DataType = self.Type.TYPE_INT
                else:
                    dat.DataType = self.Type.TYPE_STRING

                if dat.DataType == self.Type.TYPE_STRING:
                    dat.sValue = value
                
                # Look ahead one token for a conditional tag
                #peek = tokenReader.ReadToken()
                #if peek.wasConditional:
                #    bAccepted = self.EvaluateConditional(peek, pfnEvaluateSymbolProc)
                #else:
                #    tokenReader.SeekBackOneToken()

                if bAccepted:
                    ...
                    # basically let it be on the list
                else:
                    # remove key from list
                    del dat
                
    def EvaluateConditional(self, **args):
        return True
    def __repr__(self):
        return f"({self.keyName}, {self.value})"
    #def __str__(self) -> str:
    #    key = self.keyName
    #    value = ""
    #    if self.DataType == KeyValues.Type.TYPE_NONE:
    #        for kv in [("key1", "value1"), ("key2", "value2")]:
    #            value += str(kv)
    #    else:
    #        value = str(self.sValue)
    #    return f"{key} {value}"

    

kv = KeyValues("$basetexture", "test")
import vdf
print(kv)
kv2 = vdf.VDFDict([("$basetexture", "test"), ("$basetextur2", "test"), ("$basetexture", "test"), ("Proxy", vdf.VDFDict([("$basetexture", "test"), ("$basetexture3", "test")]))])
print(kv.__dict__)
print(kv2)

print("BEGIN READ")
kv5 = KeyValues()
kv5.LoadFromFile(r"D:\Users\kristi\Documents\GitHub\source1import\utils\shared\keyvalue2.kv3")
print(kv5, kv5.__dict__)
print("END READ")
print("\n\n\n")


text = "//asdasd\nvalue {\"key\"  \"key\"  \"\"value }"
buffer = CUtlBuffer(text)
reader = CKeyValuesTokenReader(buffer)
#buffer.EatCPPComment()
print(f".\n{text}\n`")
print()
while((token:=reader.ReadToken()) != 0):
    print(f"{token}\t- quoted: {token.wasQuoted}")
print()
