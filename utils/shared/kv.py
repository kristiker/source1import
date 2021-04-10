import re
import vdf




stream = r'key1\n{key2 value\n\t"key3"\t"value"\n}'

class KV1TokenReader:
    QuotationMark = '"'
    ObjectStart = '{'
    ObjectEnd = '}'
    CommentBegin = '/' # Although Valve uses the double-slash convention, the KV spec allows for single-slash comments.
    ConditionBegin = '['
    ConditionEnd = ']'
    InclusionMark = '#'


def get2KV(buffer):
    ...

def LoadFromBuffer(buffer):
    ...


def kvsplit(s):
    slist = []
    news = ''
    commentSkip = False

    tokenComplete = False
    isQuoted = False
    for pos, char in enumerate(s):

        if char == '\n':
            commentSkip = False

        if char == '/' and s[pos+1] == '/':
            commentSkip = True
        if commentSkip: continue

        if tokenComplete:
            
            tokenComplete = False
            news = ''

        if char == '"':
            if isQuoted: isQuoted = False
            else: isQuoted = True
            continue

        print(repr(char))


        isLast = (pos == len(s)-1)
        if isLast: news += char

        if char.isspace() or isLast:
            if isQuoted:
                ...
            else:
                if news:
                    slist.append(news)
                    news = ''
                continue

        news += char

    return slist

def ReadKV(kvFile) -> vdf.VDFDict:

    kvDict = {}
    with open(kvFile, 'r') as kvFile:
        buffer = kvFile.read()
        
        tokenlist = kvsplit(buffer)#buffer.split(' ')

        commentSkip = False
        print(tokenlist)
        return
        for token in tokenlist:

            if commentSkip:
                if '\n' in token: commentSkip = False
                #continue

            if token[:2] == "//":
                commentSkip = True
            print(token)
        return
        
        for row, line in enumerate(kvFile):

            line = line.split("//", 1)[0].strip().lower()
            if not line or line.startswith('/'):
                continue
            #line += "\n" + line
            print(line.split())
            
            words = re.split(r'\s', line, maxsplit=1)
            words = list(filter(len, words))
            #print(words)
            #if "proxies" in line:
            #    collectNextLine = True
                

            if "}" in line and row != 0:
                break

    return kvDict


# readfile -> readbuffer -> readline -> readkvtuple


print(ReadKV(r"D:\Users\kristi\Documents\GitHub\source1import\utils\shared\keyvalue2.kv3"))



class DemezKeyValueBase:
    def GetAllItems(self, item_key: str) -> list:
        items = []
        if self._value_type == list:
            for value in self.value:
                if value.key == item_key:
                    items.append(value)
        return items


class DemezKeyValue(DemezKeyValueBase):
    def __init__(self, parent, key: str, value, condition: str = "", file_path: str = "", line_num: int = -1):
        super().__init__()
        self.parent = parent
        self.key = key
        self.value = value  # could be a list of KeyValueItems
        
        self._value_type = type(value)
        
        self.condition = condition
        
        self.line_num = line_num
        self.file_path = file_path
        
    def ToString(self, depth: int = 0, indent: int = 1, use_tabs: bool = True, use_quotes_for_keys: bool = True) -> str:
        if use_tabs:
            space = "{0}".format("\t" * (indent * depth))
        else:
            space = "{0}".format(" " * (indent * depth))
        
        if use_quotes_for_keys:
            string = "{0}\"{1}\"".format(space, self.key)
        else:
            string = space + self.key
        
        if self._value_type == list:
            # if self.parent.value.index(self) != 0:
            #     string = "\n" + string
            
            if indent != 0:
                string += "\n" + space + "{\n"
            else:
                string += "{"  # idk if i need spaces
            
            for dkv in self.value:
                string += dkv.ToString(depth+1, indent, use_tabs, use_quotes_for_keys)
                
            if indent != 0:
                string += space + "}\n"
            else:
                string += "}"
            
        elif self.value:
            value = " \"{0}\"".format(repr(self.value)[1:-1].replace('"', '\\"'))
            string += value
            
        if self.condition:
            if string.endswith("}\n"):
                string += " [{0}]".format(self.condition) + "\n"
            else:
                string += " [{0}]".format(self.condition)
        
        if indent != 0:
            return string + "\n"
        else:
            return string
        
    def AddItem(self, key: str, value=""):  # -> DemezKeyValue:
        if self._value_type == list:
            sub_dkv = DemezKeyValue(self, key, value, file_path=self.file_path)
            self.value.append(sub_dkv)
            return sub_dkv
        
    # maybe change to AddItemUpdate?
    def AddItemSingle(self, key: str, value=""):  # -> DemezKeyValue:
        """
        If an item with the same key already exists, update that one instead
        otherwise, add a new one
        :param key:
        :param value:
        :return DemezKeyValue:
        """
        sub_dkv = self.GetItem(key)
        if not sub_dkv:
            sub_dkv = DemezKeyValue(self, key, value, file_path=self.file_path)
            self.value.append(sub_dkv)
        else:
            sub_dkv.value = value
        return sub_dkv
        
    def GetItem(self, item_key: str):  # -> DemezKeyValue:
        if self._value_type == list:
            for value in self.value:
                if value.key == item_key:
                    return value
        
    def HasItem(self, item_key: str) -> bool:
        return bool(self.GetItem(item_key))

    # returns either a string or a list
    def GetItemValue(self, item_key: str):
        if self._value_type == list:
            for item in self.value:
                if item.key == item_key:
                    return item.value
            return ""

    def SetItemValue(self, item_key: str, new_value) -> None:
        if self._value_type == list:
            for item in self.value:
                if item.key == item_key:
                    item.value = new_value
        
    def GetInt(self) -> int:
        if self._value_type != list:
            try:
                return int(self.value)
            except ValueError:
                return int()  # None
        
    def GetFloat(self) -> float:
        if self._value_type != list:
            try:
                return float(self.value)
            except ValueError:
                return float()  # None
        
    def GetItemIntValue(self, item_key: str) -> int:
        if self._value_type == list:
            try:
                return int(self.GetItemValue(item_key))
            except ValueError:
                pass
        
    def GetItemFloatValue(self, item_key: str) -> float:
        if self._value_type == list:
            try:
                return float(self.GetItemValue(item_key))
            except ValueError:
                pass
        
    def GetAllKeysInItems(self) -> list:
        keys = []
        if self._value_type == list:
            [keys.append(kvi.key) for kvi in self.value]
        return keys
    
    def GetIndexInParent(self) -> int:
        """
        Return the index of the item in the parent key
        :return:
        """
        return self.parent.value.index(self)
        
    def Delete(self) -> None:
        """
        Removes this item from the parent key
        :return:
        """
        if type(self.parent) == DemezKeyValueRoot:
            if type(self.parent.value) == list:
                self.parent.value.remove(self)
        elif type(self.parent) == list:
            self.parent.remove(self)
    
    # TODO: maybe remove these 2 functions?
    def Unknown(self) -> None:
        self.Warning("Unknown Key")
    
    def InvalidOption(self, *valid_option_list) -> None:
        print( "WARNING: Invalid Option" )
        print( "\tValid Options:\n\t\t" + '\n\t\t'.join(valid_option_list) )
        self.PrintInfo()
    
    # would be cool if i could change the colors on this
    def FatalError(self, message) -> None:
        print("FATAL ERROR: " + message)
        self.PrintInfo()
        quit()
    
    # should Error and FatalError be the same?
    def Error(self, message: str) -> None:
        print("ERROR: " + message)
        self.PrintInfo()
    
    def Warning(self, message: str) -> None:
        print("WARNING: " + message)
        self.PrintInfo()
    
    def PrintInfo(self) -> None:
        if self.file_path:
            print("\tFile Path: " + self.file_path)
            
        if self.line_num != -1:
            print("\tLine: " + str(self.line_num))
        
        print("\tKey: " + self.key)

        if self.value and self._value_type != list:
            print("\tValue: " + self.value)


class DemezKeyValueRoot(DemezKeyValueBase):
    def __init__(self, file_path: str = ""):
        super().__init__()
        self.file_path = file_path
        self.value = []
        self._value_type = list
        
    def __iter__(self) -> iter:
        return self.value.__iter__()
        
    def __getitem__(self, item) -> DemezKeyValue:
        return self.value[item]
        
    def __extend__(self, item):
        return self.value[item]

    def append(self, item):
        self.value.append(item)

    def remove(self, item):
        self.value.remove(item)

    def index(self, item):
        self.value.index(item)
        
    def ToString(self, indent: int = 1, use_tabs: bool = True, use_quotes_for_keys: bool = True):
        final_str = ""
        for dkv in self.value:
            final_str += dkv.ToString(0, indent, use_tabs, use_quotes_for_keys)
        return final_str

    def AddItem(self, key: str, value) -> DemezKeyValue:
        sub_dkv = DemezKeyValue(self, key, value, file_path=self.file_path)
        self.value.append(sub_dkv)
        return sub_dkv

    def GetItem(self, item_key: str) -> DemezKeyValue:
        for value in self.value:
            if value.key == item_key:
                return value

    def GetItemValue(self, item_key: str):
        for item in self.value:
            if item.key == item_key:
                return item.value
        return ""
    
    def UpdateFile(self, indent: int = 1, use_tabs: bool = True, use_quotes_for_keys: bool = True) -> bool:
        """
        file_path must be set before calling
        Convert to string and write to file
        :param indent:
        :param use_tabs:
        :param use_quotes_for_keys:
        :return:
        """
        with open(self.file_path, "w", encoding="utf-8") as file:
            file.write(self.ToString(indent, use_tabs, use_quotes_for_keys))
        return True
    
    def UpdateFileSafe(self, indent: int = 1, use_tabs: bool = True, use_quotes_for_keys: bool = True) -> bool:
        """
        file_path must be set before calling
        Adds .bak to the existing file's name if it exists,
        Then write the new file, and then delete the backup if it exists
        :param indent:
        :param use_tabs:
        :param use_quotes_for_keys:
        :return:
        """
        if self.file_path:
            if os.path.isfile(self.file_path):
                os.rename(self.file_path, self.file_path + ".bak")
            self.UpdateFile(indent, use_tabs, use_quotes_for_keys)
            if os.path.isfile(self.file_path + ".bak"):
                os.remove(self.file_path + ".bak")
            return True
        return False
    
    
def FromDict(dct) -> DemezKeyValueRoot:
    dkv_root = DemezKeyValueRoot()
    
    for key, value in dct.items():
        if type(value) == dict:
            dkv = DemezKeyValue(dkv_root, key, [])
            _RecursiveDict(dkv, value)
        elif type(value) == list:
            dkv = DemezKeyValue(dkv_root, key, [])
            _RecursiveList(dkv, value)
        else:
            dkv = DemezKeyValue(dkv_root, key, str(value))
        dkv_root.append(dkv)
    
    return dkv_root


def _RecursiveDict(parent, dct):
    for key, value in dct.items():
        if type(value) == dict:
            dkv = DemezKeyValue(parent, key, [])
            _RecursiveDict(dkv, value)
        elif type(value) == list:
            dkv = DemezKeyValue(parent, key, [])
            _RecursiveList(dkv, value)
        else:
            dkv = DemezKeyValue(parent, key, str(value))
        parent.value.append(dkv)


def _RecursiveList(parent, lst):
    for value in lst:
        if type(value) == dict:
            dkv = DemezKeyValue(parent, "dict", [])
            _RecursiveDict(dkv, value)
        elif type(value) == list:
            dkv = DemezKeyValue(parent, "list", [])
            _RecursiveList(dkv, value)
        else:
            dkv = DemezKeyValue(parent, str(value), "")
        parent.value.append(dkv)
        
        
def FromString(string) -> DemezKeyValueRoot:
    lexer = DemezKeyValuesLexer(file=string)
    dkv_root = DemezKeyValueRoot()
    CreateBlock(lexer, dkv_root)
    return dkv_root
        
    
# TODO: maybe change to FromFile()?
#  or should i change the others to ReadDict() and ReadString()?
def ReadFile(path) -> DemezKeyValueRoot:
    lexer = DemezKeyValuesLexer(path)
    dkv_root = DemezKeyValueRoot(path)
    CreateBlock(lexer, dkv_root, os.getcwd() + os.sep + path)
    return dkv_root


def CreateBlock(lexer, parent, path="", sub_block=False):
    while lexer.chari < lexer.file_len:
        key, line_num = lexer.NextKey()
        
        next_symbol = lexer.NextSymbol()
        
        if not key:
            return
        
        if next_symbol == "{":
            condition = lexer.NextCondition()
            block = DemezKeyValue(parent, key, [], condition, path, line_num)
            CreateBlock(lexer, block, path, True)
            
        elif next_symbol == "}":
            if sub_block:
                condition = lexer.NextCondition()
                block = DemezKeyValue(parent, key, "", condition, path, line_num)
                parent.value.append(block)
            else:
                raise Exception("Not in Block on line " + str(lexer.linei))
            return
        
        elif line_num == lexer.linei:
            value = lexer.NextValue()
            condition = lexer.NextCondition()
            block = DemezKeyValue(parent, key, value, condition, path, line_num)
        
        else:
            condition = lexer.NextCondition()
            block = DemezKeyValue(parent, key, "", condition, path, line_num)
        
        parent.value.append(block)
        
    
class DemezKeyValuesLexer:
    def __init__(self, path="", file=""):
        self.chari = 0
        self.linei = 1
        self.path = path
        
        if path:
            with open(path, mode="r", encoding="utf-8") as file:
                self.file = file.read()
        elif file:
            self.file = file
        self.file_len = len(self.file) - 1

        self.chars_comment = {'/', '*'}
        self.chars_escape = {'"', '\'', '\\'}
        self.chars_quote = {'"', '\''}
        self.chars_cond = {'[', ']'}
        self.chars_item = {'{', '}'}
        self.chars_special = {'n': "\n"}
        
    def NextValue(self) -> str:
        value = ''
        while self.chari < self.file_len:
            char = self.file[self.chari]

            if char in self.chars_item:
                break
                
            if char in {' ', '\t', '='}:
                self.chari += 1
                if value:
                    break
                continue
    
            if char in self.chars_quote:
                value = self.ReadQuote(char)
                break
    
            # skip escape
            if char == '\\' and self.NextChar() in self.chars_escape:
                self.chari += 2
                value += self.file[self.chari]
    
            elif char == '\n':
                break

            elif char == '/' and self.NextChar() in self.chars_comment:
                self.SkipComment()
    
            else:
                if self.file[self.chari] in self.chars_cond:
                    break
                value += self.file[self.chari]
    
            self.chari += 1
        
        return value

    def NextChar(self):
        if self.chari + 1 >= self.file_len:
            return None
        return self.file[self.chari + 1]

    def NextKey(self) -> tuple:
        string = ''
        line_num = 0
        skip_list = {' ', '\t', '\n'}
        
        while self.chari < self.file_len:
            char = self.file[self.chari]
            
            if char in self.chars_item:
                line_num = self.linei
                break

            elif char in {' ', '\t'}:
                if string:
                    line_num = self.linei
                    break

            elif char in self.chars_quote:
                string = self.ReadQuote(char)
                line_num = self.linei
                break
            
            elif char == '\\' and self.NextChar() in self.chars_escape:
                self.chari += 2
                string += self.file[self.chari]
            
            elif char in skip_list:
                if string:
                    line_num = self.linei
                    break
                if char == '\n':
                    self.linei += 1
                
            elif char == '/' and self.NextChar() in self.chars_comment:
                self.SkipComment()
                
            else:
                string += self.file[self.chari]

            self.chari += 1
            
        return string, line_num

    def NextSymbol(self) -> str:
        while self.chari < self.file_len:
            char = self.file[self.chari]

            if char in self.chars_item:
                self.chari += 1
                return char

            elif char in self.chars_quote:
                return char
            
            # skip escape
            elif char == '\\' and self.NextChar() in self.chars_escape:
                self.chari += 2
            
            elif char == '/' and self.NextChar() in self.chars_comment:
                self.SkipComment()
                
            elif char == '\n':
                self.linei += 1
                
            elif char not in {' ', '\t'}:
                break

            self.chari += 1

    def PeekSymbol(self) -> str:
        temp_chari = self.chari
        temp_linei = self.linei
        last_symbol = ''
        while temp_chari < self.file_len:
            char = self.file[temp_chari]

            if char in self.chars_item:
                return char

            elif char in self.chars_quote:
                return char
            
            # skip escape
            elif char == '\\' and self.NextChar() in self.chars_escape:
                temp_chari += 2
            
            elif char == '/' and self.NextChar() in self.chars_comment:
                self.SkipComment()
                
            elif char == '\n':
                return char
                
            elif char not in {' ', '\t'}:
                break

            temp_chari += 1

    def NextCondition(self) -> str:
        condition = ''
        in_cond = False
        while self.chari < self.file_len:
            char = self.file[self.chari]
        
            if char in self.chars_item:
                break
        
            elif char == '[':
                # self.chari += 1
                in_cond = True
                # continue
        
            elif char == ']':
                self.chari += 1
                break
        
            elif char in {' ', '\t'}:
                pass
        
            elif char == '\n':
                # self.linei += 1
                # self.chari += 1
                break
        
            elif char == '/' and self.NextChar() in self.chars_comment:
                self.SkipComment()
        
            elif in_cond:
                condition += self.file[self.chari]
                
            else:
                break
        
            self.chari += 1
            
        return condition
    
    def SkipComment(self) -> None:
        self.chari += 1
        char = self.file[self.chari]
        if char == '/':
            while True:
                self.chari += 1
                if self.file[self.chari] == "\n":
                    self.linei += 1
                    break
    
        elif char == '*':
            while True:
                char = self.file[self.chari]
            
                if char == '*' and self.NextChar() == '/':
                    self.chari += 1
                    break
            
                if char == "\n":
                    self.linei += 1
            
                self.chari += 1

    def ReadQuote(self, qchar: str) -> str:
        quote = ''
        while self.chari < self.file_len:
            self.chari += 1
            char = self.file[self.chari]
        
            if char == '\\' and self.NextChar() in self.chars_escape:
                quote += self.NextChar()
                self.chari += 1
        
            elif char == '\\' and self.NextChar() in self.chars_special:
                quote += self.chars_special[self.NextChar()]
                self.chari += 1
                
            elif char == qchar:
                break
            else:
                quote += char
    
        self.chari += 1
        return quote

def GetSubkeys(self) -> Generator[KeyValues]: # new
        
        if self.DataType == KeyValues.Type.TYPE_NONE:
            return None
        iter = self.GetFirstSubKey()
        while (iter):
            yield iter
            iter = iter.GetNextKey()
"""
    def is_lone(self):
        return self.Peer == None

    def AddSubKey(self, subKey):
        assert self.is_lone()
        # add into subkey list
        if self.Sub == None:
            self.Sub == subKey
        else:
            temp = self.Sub # BUGWATCH: is this really equal to *pTempDat = m_pSub? Bare copy? changing things in temp changes them in sub?
            while next := temp.GetNextKey(): # scroll to last
                temp = next
            temp.SetNextKey(subKey)

    def RemoveSubKey(self, subKey):
        if not subKey:
            return
        # check the list pointer
        if self.Sub == subKey:
            self.Sub == subKey.Peer
        else:
            # look through the list
            kv = self.Sub
            while(kv.Peer):
                if kv.Peer == subKey:
                    kv.Peer = subKey.Peer
                    break
                kv = kv.Peer
        subKey.Peer = None

    def InsertSubKey(self, index: int, subKey: KeyValues):
        assert self.is_lone()
        if index == 0:
            subKey.Peer = self.Sub
            self.Sub = subKey
        else:
            currentIndex = 0
            for iter in self.GetSubkeys():
                currentIndex += 1
                if currentIndex == index:
                    subKey.Peer = self.Sub
                    self.Sub = subKey
                    return
            raise IndexError

        
    def ContainsSubKey(self, subKey: KeyValues) -> bool:
        iter = self.GetFirstSubKey()
        while (iter):
            if subKey == iter:
                return True
            iter = iter.GetNextKey()
        return False
    def SwapSubKey(self, existingSubkey: KeyValues, newSubKey: KeyValues): ...
    def ElideSubKey(self, subKey: KeyValues): ...
    def FindLastSubKey(self) -> Optional[KeyValues]:
        if not self.Sub:
            return

        # Scan for the last one
        lastChild = self.Sub
        while (lastChild and lastChild.Peer):
            lastChild = lastChild.Peer
        return lastChild
        
    def GetFirstSubKey(self):
        return self.Sub

    def GetNextKey(self):
        return self.Peer #WATCH cpp has checks for null self that dont make sense here

    def SetNextKey(self, dat: KeyValues):
        self.Peer = dat
"""
print(ReadFile(r"D:\Users\kristi\Documents\GitHub\source1import\utils\shared\keyvalue2.kv3").ToString())

#print(ReadFile(r"C:\Program Files (x86)\Steam\steamapps\common\Counter-Strike Global Offensive\csgo\scripts\ai\guardian\bt_config.kv3").ToString())
