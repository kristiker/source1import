#cstr.py

from functools import lru_cache
import re
__version__ = '2019.06.06'
 
re_base_zero = re.compile(r"(?i)\s*[\+\-]?0(x)?")

class strtod:
    def __init__(self, s, pos: int = 0) -> None:
        m = re.match(r'[+-]?\d*[.]?\d*(?:[eE][+-]?\d+)?', s[pos:])
        #if m.group(0) == '':
        #    raise ValueError('bad float: %s' % s[pos:])
        #self.value = float(m.group(0))
        self.string = s
        self.pos = pos
        if m:
            try:
                self.value = float(m.group(0))
            except ValueError:
                self.value = None
            self.endpos = pos + m.end()
        else:
            raise ValueError('Cannot convert to float')



@lru_cache(10)
def strtol_re(base):
    if not (0 <= base <= 36):
        raise ValueError('Expected base between 0 and 36.')
    a = r"(?i)\s*(?:[\+\-]?)"
    if base == 16:
        r = a + r"(?:0x)?[\u0030-\u0039\u0041-\u0046]*"
    elif base > 10:
        r = (a + "[\u0030-\u0039\u0041-{}]*".format(
            chr(ord('A') + base - 10)))
    else:
        r = (a + "[\u0030-{}]*".format(chr(ord('0') + base - 1)))
    return re.compile(r)
 
class strtol:
    """Small object to store result of conversion of string to int
     
    Arguments:
        s       : string to read
        base=10 : integer base between 0 and 36 inclusive.
        pos=0   : position where to read in the string.
         
    Strtol members:
        value   : an integer value parsed in the string.
        string  : the string that was read.
        pos     : the position where the integer was parsed.
        endpos  : the position in the string after the integer.
         
    Errors:
        If no valid conversion could be performed, ValueError is raised.
 
    see also:
        the linux manual of strtol
    """
    __slots__ = ('value', 'string', 'pos', 'endpos')
     
    def __init__(self, s, base=10, pos=0):
        self.string = s
        self.pos = pos

        if base == 0:
            m = re_base_zero.match(s, pos=pos)
            if m:
                base = 16 if m.group(1) else 8
            else:
                base = 10
        r = strtol_re(base)
        #print(r)
        #print(s[pos:])
        m = r.match(s, pos=pos)
        if m:
            try:
                self.value = int(m.group(0), base)
            except ValueError:
                self.value = None
            self.endpos = m.end()
        else:
            raise ValueError('Cannot convert to int')
 
if __name__ == '__main__':
    import unittest
     
    class Test_strtod(unittest.TestCase):
        def test_1(self):
            x = "3.1415913123"
            s = strtod(x)
            self.assertEqual(s.value, 3.1415913123)
        def test_main(self):
            x = 'lmao3.1515'
            s = strtod(x, pos=4)
            self.assertEqual(s.value, 3.1515)
            self.assertEqual(s.endpos, 10)
            self.assertEqual(s.pos, 4)
            self.assertIs(s.string, x)

    class Test_strtol(unittest.TestCase):
        def test_base_10(self):
            x = 'foo-324bar'
            s = strtol(x, pos=3)
            self.assertEqual(s.value, -324)
            self.assertEqual(s.endpos, 7)
            self.assertEqual(s.pos, 3)
            self.assertIs(s.string, x)
 
        def test_base_16(self):
            x = '  324Bbar'
            s = strtol(x, base=16)
            self.assertEqual(s.value, int('324BBA', 16))
            self.assertEqual(x[s.endpos:], 'r')
 
        def test_base_16_0x(self):
            x = '  -0x324Bbar'
            s = strtol(x, base=16)
            self.assertEqual(s.value, -int('324BBA', 16))
            self.assertEqual(x[s.endpos:], 'r')
 
        def test_base_0_0x(self):
            x = '  -0x324Bbar'
            s = strtol(x, base=0)
            self.assertEqual(s.value, -int('324BBA', 16))
            self.assertEqual(x[s.endpos:], 'r')
 
        def test_base_0(self):
            x = '  -324Bbar'
            s = strtol(x, base=0)
            self.assertEqual(s.value, -324)
            self.assertEqual(x[s.endpos:], 'Bbar')
 
        def test_base_0_octal(self):
            x = '  -0324Bbar'
            s = strtol(x, base=0)
            self.assertEqual(s.value, -int("324", 8))
            self.assertEqual(x[s.endpos:], 'Bbar')
 
        def test_base_20(self):
            x = '  -0324BgGar'
            s = strtol(x, base=20)
            self.assertEqual(s.value, -int("324BgGa", 20))
            self.assertEqual(x[s.endpos:], 'r')
 
        def test_empty_string(self):
            x = ''
            self.assertRaises(ValueError, strtol, x)
 
    unittest.main()