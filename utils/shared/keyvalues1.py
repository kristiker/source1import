# keyvalues1.py

# cppkeyvalues is nice for parsing, but we need an actual python object to work efficiently

from collections import Counter
from typing import Any, Generator, Optional, Sequence
try:
    from cppkeyvalues import KeyValues, _dec_subkeyvalue
except:
    from shared.cppkeyvalues import KeyValues, _dec_subkeyvalue


class VDFDict(dict):
    def __init__(self, data=None):
        """
        This is a dictionary that supports duplicate keys and preserves insert order

        ``data`` can be a ``dict``, or a sequence of key-value tuples. (e.g. ``[('key', 'value'),..]``)
        The only supported type for key is str.

        Get/set duplicates is done by tuples ``(index, key)``, where index is the duplicate index
        for the specified key. (e.g. ``(0, 'key')``, ``(1, 'key')``...)

        When the ``key`` is ``str``, instead of tuple, set will create a duplicate and get will look up ``(0, key)``
        """
        self.__omap = []
        self.__kcount = Counter()

        if data is not None:
            if not isinstance(data, (list, dict)):
                raise ValueError("Expected data to be list of pairs or dict, got %s" % type(data))
            self.update(data)

    def __repr__(self):
        return f"{self.__class__.__name__}({repr(list(self.iteritems()))})"

    def __len__(self):
        return len(self.__omap)

    def _verify_key_tuple(self, key):
        if len(key) != 2:
            raise ValueError("Expected key tuple length to be 2, got %d" % len(key))
        if not isinstance(key[0], int):
            raise TypeError("Key index should be an int")
        if not isinstance(key[1], str):
            raise TypeError("Key value should be a str")

    def _normalize_key(self, key):
        if isinstance(key, str):
            key = (0, key)
        elif isinstance(key, tuple):
            self._verify_key_tuple(key)
        else:
            raise TypeError("Expected key to be a str or tuple, got %s" % type(key))
        return key

    def __setitem__(self, k, v) -> None:
        if k in self:
            return super().__setitem__(self._normalize_key(k), v)
        self.add(k, v)

    def add(self, key, value):
        if isinstance(key, str):
            key = (self.__kcount[key], key)
            self.__omap.append(key)
        elif isinstance(key, tuple):
            self._verify_key_tuple(key)
            if key not in self:
                raise KeyError("%s doesn't exist" % repr(key))
        else:
            raise TypeError("Expected either a str or tuple for key")
        if isinstance(value, dict):
            value = VDFDict(value)
        super().__setitem__(key, value)
        self.__kcount[key[1]] += 1

    def __getitem__(self, key):
        return super().__getitem__(self._normalize_key(key))

    def __delitem__(self, key):
        key = self._normalize_key(key)
        result = super().__delitem__(key)

        start_idx = self.__omap.index(key)
        del self.__omap[start_idx]

        dup_idx, skey = key
        self.__kcount[skey] -= 1
        tail_count = self.__kcount[skey] - dup_idx

        if tail_count > 0:
            for idx in range(start_idx, len(self.__omap)):
                if self.__omap[idx][1] == skey:
                    oldkey = self.__omap[idx]
                    newkey = (dup_idx, skey)
                    super().__setitem__(newkey, self[oldkey])
                    super().__delitem__(oldkey)
                    self.__omap[idx] = newkey

                    dup_idx += 1
                    tail_count -= 1
                    if tail_count == 0:
                        break

        if self.__kcount[skey] == 0:
            del self.__kcount[skey]

        return result

    def __iter__(self):
        return iter(self.iterkeys())

    def __contains__(self, key):
        return super().__contains__(self._normalize_key(key))

    def __eq__(self, other):
        if isinstance(other, VDFDict):
            return list(self.items()) == list(other.items())
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def clear(self):
        super().clear()
        self.__kcount.clear()
        self.__omap = list()

    def get(self, key, *args):
        return super().get(self._normalize_key(key), *args)

    def setdefault(self, key, default=None):
        if key not in self:
            self.add(key, default)
        return self.__getitem__(key)

    def pop(self, key):
        key = self._normalize_key(key)
        value = self.__getitem__(key)
        self.__delitem__(key)
        return value

    def popitem(self):
        if not self.__omap:
            raise KeyError("VDFDict is empty")
        key = self.__omap[-1]
        return key[1], self.pop(key)

    def update(self, data=None, **kwargs):
        if isinstance(data, dict):
            data = data.items()
        elif not isinstance(data, list):
            raise TypeError("Expected data to be a list or dict, got %s" % type(data))

        for key, value in data:
            if isinstance(value, list):
                #print(self.__class__)
                self.add(key, VDFDict(value))
            else:
                self.add(key, value)

    def iterkeys(self):
        return (key[1] for key in self.__omap)

    def keys(self):
        return list(self.iterkeys())

    def itervalues(self):
        return (self[key] for key in self.__omap)

    def values(self):
        return list(self.itervalues())

    def iteritems(self, indexed_keys = False):
        return ((key if indexed_keys else key[1], self[key]) for key in self.__omap)

    def items(self, indexed_keys = False):
        return list(self.iteritems(indexed_keys))

    def get_all_for(self, key):
        """ Returns all values of the given key """
        if not isinstance(key, str):
            raise TypeError("Key needs to be a string.")
        return [self[(idx, key)] for idx in range(self.__kcount[key])]

    def remove_all_for(self, key):
        """ Removes all items with the given key """
        if not isinstance(key, str):
            raise TypeError("Key need to be a string.")

        for idx in range(self.__kcount[key]):
            super().__delitem__((idx, key))

        self.__omap = list(filter(lambda x: x[1] != key, self.__omap))

        del self.__kcount[key]

    def has_duplicates(self):
        """
        Returns ``True`` if the dict contains keys with duplicates.
        Recurses through any all keys with value that is ``VDFDict``.
        """
        for n in getattr(self.__kcount, 'itervalues')():
            if n != 1:
                return True

        def dict_recurse(obj):
            for v in getattr(obj, 'itervalues')():
                if isinstance(v, VDFDict) and v.has_duplicates():
                    return True
                elif isinstance(v, dict):
                    return dict_recurse(v)
            return False

        return dict_recurse(self)
    def ToStr(self, level = 0):
        line_indent = '\t' * level
        s = ""
        s += "\n" + line_indent + '{\n'
        for key, value in self.items():
            if isinstance(value, VDFDict):
                s += line_indent + f"\t{key}{value.ToStr(level+1)}"
            else:
                s += line_indent + f'\t{key}\t"{value}"\n'
        s += line_indent + "}\n"
        return s

def _NoneOnException(func):
    def wrapper(*args, **kwargs):
        try: func(*args)
        except: return
    return wrapper

class KV(VDFDict):

    @classmethod
    def FromFile(cls, file, case_sensitive=False, escape=False):
        #breakpoint()
        cppkv = KeyValues(case_sensitive = case_sensitive, escape = escape)
        cppkv.LoadFromFile(file)
        return cls(cppkv.keyName, cppkv.value.ToBuiltin())

    @classmethod
    def CollectionFromFile(cls, file, case_sensitive=False, escape=False):
        keyName = file.name
        cppkv = KeyValues(keyName, case_sensitive = case_sensitive, escape = escape)
        cppkv.RecursiveLoadFromFile(file)
        return cls(keyName, cppkv.value.ToBuiltin())

    def __init__(self, keyName, value) -> None:
        self.keyName = keyName
        super().__init__(value)

    def __getitem__(self, key) -> Optional[Any]:
        'If key exists, value of key. Otherwise None'
        try:
            return super().__getitem__(key)
        except KeyError:
            return

    def __repr__(self):
        return f"{self.__class__.__name__}({self.keyName!r}, {list(self.iteritems())!r})"

    def __str__(self):
        return self.ToStr()

    def ToStr(self, level=0):
        line_indent = "\t" * level
        return line_indent + f'"{self.keyName}"{super().ToStr(level)}'

    def save(self, path):
        with open(path, 'w') as fp:
            fp.write(self.ToStr())

    def ToKeyValues(self):
        raise NotImplemented
        kv = KeyValues(self.keyName)
        kv.Sub = []
        for k, v in self.items():
            if isinstance(v, VDFDict):
                kv.value.append(v.ToKeyValues())
            else:
                kv.value.append(KeyValues(k, v))
        return kv

if __name__ == "__main__": # tests

    vmt = KV.FromFile(r'D:\Users\kristi\Desktop\WORK\test\materials\test_proxy.vmt', case_sensitive=True)
    #vmt['proxies'] = "kar"
    #vmt['proxies'] = "kar2"
    vmt.add('kar', "pidh")
    vmt.add('Proxies', "kar")

    for k, v in vmt.items():
        print(k)
        if isinstance(v, VDFDict):
            print("^^ was kv")

    z = zip(((k, v) for ((_, k), v) in vmt.items(True)), ((k, v) for (k, v) in vmt.items()))
    for r1, r2 in z:
        assert r1 == r2
