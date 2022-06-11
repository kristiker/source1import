
from particles_import import pcf_to_vpcf, ObjectP, BoolToSetKV, Discontinued

global_changes = {
    'initializers':{
        'm_nAxis': 'm_nComponent',
        'm_bScaleInitialRange': BoolToSetKV('m_nSetMethod', "PARTICLE_SET_SCALE_CURRENT_VALUE"),
        'm_bScaleCurrent': BoolToSetKV('m_nSetMethod', "PARTICLE_SET_SCALE_INITIAL_VALUE"),
        #'m_bUseHighestEndCP': Discontinued('m_bUseHighestEndCP', 9)
    },
    'operators':{
        'm_bScaleInitialRange': BoolToSetKV('m_nSetMethod', "PARTICLE_SET_SCALE_CURRENT_VALUE"),
        'm_bScaleCurrent': BoolToSetKV('m_nSetMethod', "PARTICLE_SET_SCALE_INITIAL_VALUE"),
    },
    'emitters':{},
    'forces': {},
    'constraints': {},
}

def codesplit(s) -> list:
    "str.split(',') but doesnt split inside quotes"
    parts = []

    inquote = False
    part = ''
    for i, char in enumerate(s, 1):
        if char == ',' or i == len(s):
            if not inquote:
                parts.append(part)
                part = ''
                continue
        if char == '"':
            inquote = not inquote
        part += char
    return parts

my_ops = {}
def parse_operator(line: str):
    parts = line.replace('DEFINE_PARTICLE_OPERATOR', '').lstrip(' \t(').rstrip(');').split(',')
    if len(parts) == 3:
        key = parts[1].strip().strip('"')
        val = parts[0].strip()
        my_ops[key] = val
        subs.setdefault(val, {})

subs = {}
def parse_sub(op, line):
    if not line:
        return
    defines = (
        'DMXELEMENT_UNPACK_FIELD_USERDATA',
        'DMXELEMENT_UNPACK_FIELD_UTLSTRING_USERDATA',
        'DMXELEMENT_UNPACK_FIELD_UTLSTRING',
        'DMXELEMENT_UNPACK_FIELD_STRING_USERDATA',
        'DMXELEMENT_UNPACK_FIELD_STRING',
        'DMXELEMENT_UNPACK_FIELD',
        'DMXELEMENT_UNPACK_FLTX4',
    )
    for define in defines:
        if not line.startswith(define):
            continue
        replaced = line.replace(define, '')
        if replaced.strip(' \t(') == replaced:
            continue
        else:
            line = replaced.strip(' \t(')
            break
    
    line = line.lstrip()
        
    b = codesplit(line)#line.split(',')

    key = b[0].strip().strip('"')
    if len(b) < 4:
        val = b[2].replace(')', '').strip()
    else:
        val = b[3].replace(')', '').strip()
        if '"' in val:
            val = b[2].strip()
    
    if '.' in val:
        o, val = tuple(val.split('.', 1))
        val = ObjectP(o, val)

    val = global_changes[main].get(val, val)
    if main == 'forces':
        if val[-1] == ']' and val[-3] == '[':
            val = val[:-3] + val[-2]

    subs.setdefault(op, {})[key] = val

main = 'emitters'
f = r'cstrike15_src/particles/builtin_particle_emitters.cpp'
main = 'forces'
f = r'cstrike15_src/particles/builtin_particle_forces.cpp'
main = 'constraints'
f = '/cstrike15_src/particles/builtin_constraints.cpp'
with open(f, 'r') as fp:
    unpack = ''
    unpack_lines = []

    op_begin = 'BEGIN_PARTICLE_OPERATOR_UNPACK'
    op_end = 'END_PARTICLE_OPERATOR_UNPACK'
    if main == 'initializers':
        op_begin = 'BEGIN_PARTICLE_INITIALIZER_OPERATOR_UNPACK'
    #elif main == 'operators':
    #    op_begin = 'BEGIN_PARTICLE_OPERATOR_UNPACK'
    for line in fp.readlines():
        line = line.strip()
        if line.startswith('//'):
            continue
        if line.startswith('DEFINE_PARTICLE_OPERATOR'):
            parse_operator(line)
            continue
        
        if line.startswith(op_begin):
            unpack = line.replace(op_begin, '').lstrip(' (').rstrip(') ')#.strip()
            continue
        elif line.startswith(op_end):
            unpack = ''
            continue
        if unpack:
            parse_sub(unpack, line)
out = ''

def get_subs(op):
    rv = ''
    #print(subs.keys())
    for k, v in subs[op].items():
        v = f"{v!r}"
        if not isinstance(v, str):
            v = v.strip("'")
    
        rv += f"{' '*12}{k!r}: {v},\n"
    return rv

for op in my_ops:
    if "'" in op:
        out += f"{' '*8}"+f'"{op}"' + f": ('{my_ops[op]}', {'{'}\n{get_subs(my_ops[op])}{' '*8}{'}'}),\n"
    else:
        out += f"{' '*8}'{op}': ('{my_ops[op]}', {'{'}\n{get_subs(my_ops[op])}{' '*8}{'}'}),\n"

print(out)


def verify_ops():
    addthese = ''
    ctx = pcf_to_vpcf.get(main)
    if isinstance(ctx, tuple):
        ctx = ctx[1]
    for k, v in my_ops.items():
        if k not in ctx:
            addthese += f"{' '*8}'{k}': '{v}',\n"
        else:
            if ctx[k] != v:
                print(f"Mismatch with `{k}`:  '{ctx[k]}' != '{v}'")
    if addthese:
        print()
        print(addthese)
        print()

def verify_subs():
    ctx = pcf_to_vpcf.get(main)
    if isinstance(ctx, tuple):
        ctx = ctx[1]
    for op in subs:
        addthese = ''
        print(f' ~~~ {op}')
        if isinstance(ctx.get(op), tuple):
            ctx = ctx.get(op)[1]
        for k, v in subs[op].items():
            if k not in ctx: # (k in ctx and ctx[k] == '')
                addthese += f"{' '*12}'{k}': '{v}',\n"
            #else:
                #if ctx[k] != v:
                #    if not isinstance(ctx[k], str): continue
                #    print(f"Mismatch with `{k}`:  '{ctx[k]}' != '{v}'")
        if addthese:
            #print()
            print(addthese)
            print()

#verify_subs()
#verify_ops()