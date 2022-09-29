
from typing import Optional, Sequence, Type, Union, get_origin, get_args
from parsimonious.grammar import Grammar
from parsimonious.nodes import Node, NodeVisitor

qcgrammar = Grammar(
    """
    qcfile = _? ((cmd / token_base / group_base) _*)*

    # to distinguish top level from other stuff
    cmd = ~"\\$[_$a-zA-Z][\w$/.]*"
    token_base = token ""
    group_base = group ""

    group = "{" _* ((_2complex4grammar / token / group) _*)* ("}" / ~"\Z")

    token = (variable / quoted / number)

    variable = ~r"[_$a-zA-Z][\S]*"
    quoted = ~r'"[^"]*"'
    number = (int? frac) / int
    int = "-"? ((digit1to9 digits) / digit)
    frac = "." digits
    digits = digit+
    digit = ~"[0-9]"
    digit1to9 = ~"[1-9]"

    # grab the whole thing, don't tokenize
    _2complex4grammar = flexfile

    flexfile = "flexfile" _ quoted _ "{" ~"[^}]*" _ "}"

    # statement = exp_var _ "=" _ expression
    # expression = "("? _ (factor (_ operation _ expression){,31} ) _ ")"?
    # factor = (exp_var / variable / number / function)
    # function = variable _ "(" _ (expression _ ("," _ expression _)* )? ")"
    # operation = ("+" / "-" / "*" / "/")
    # exp_var = ~"%[_$a-zA-Z][\w$/.]*"

    _ = __*
    __ = ~r"\s+" / comment / multiline_comment
    comment = ~"//[^\\r\\n]*"
    # This is dumber than the usual stuff, eating everything till it finds */ or EOF
    multiline_comment = ~"\\/\\*(.*?|\\s)*(\\*\\/|\\Z)"
    #multiline_comment = ~"/\\*[^*]*\\*+(?:[^/*][^*]*\\*+)*/"
    
    """
)

class Group(list): pass
class Token(str): pass

# These have a rule "Opening bracket must be on the same line"
# but it is not carried out here.
class TokensInlineOrGroup: pass

class QC:
    class include:
        filename: str

    class includemodel:
        filename: str
    
    class modelname:
        filename: str

    class pushd:
        path: str
    
    class popd(): pass

    class staticprop(): pass

    class surfaceprop:
        name: str
    
    class origin:
        x: float
        y: float
        z: float
    
    class contents:
        name: str

    class illumposition:
        x: float
        y: float
        z: float
    
    class attachment:
        name: str
        parent_bone: str
        x: float
        y: float
        z: float
        # TODO:
        # absolute: "OptionalTrueIfTokenPresent"
        # rigid: "OptionalTrueIfTokenPresent"
        # rotate: "OptionalKeyReadNextValues[3]"
    
    class cdmaterials:
        folder: str

    class texturegroup:
        name: str
        options: Group[Group[Token]]
    
    class renamematerial:
        current: str
        new: str

    class cbox:
        minx: float
        miny: float
        minz: float
        maxx: float
        maxy: float
        maxz: float
    
    class bbox:
        minx: float
        miny: float
        minz: float
        maxx: float
        maxy: float
        maxz: float

    class definebone:
        name: str
        parent: str
        posx: float
        posy: float
        posz: float
        rotx: float
        roty: float
        rotz: float
        rotx_fixup: float
        roty_fixup: float
        rotz_fixup: float
    
    class hierarchy:
        child_name: str
        parent_name: str

    class bodygroup:
        name: str
        options: Group[Token]

    class body:
        name: str
        mesh_filename: str
        # TODO: confirm these
        reverse: Optional[bool] = False
        scale: Optional[float] = 1
    
    class lod:
        threshold: int
        options: Group[Token]

    class model:
        name: str
        mesh_filename: str
    
    class animation:
        name: str

    class sequence:
        name: str
        options: TokensInlineOrGroup
    
    class declaresequence:
        name: str
    
    class weightlist:
        name: str
        options: TokensInlineOrGroup
    
    class defaultweightlist:
        options: TokensInlineOrGroup

    class collisionmodel:
        mesh_filename: str
        #options: _options

    class collisionjoints:
        mesh_filename: str
        #options: _options
    
    class keyvalues:
        def handle_options(self, options_node: Node):
            trav = QCBuilder.traverse_options(options_node)
            def nested(trav):
                d = {}
                for key, val in zip(trav, trav):
                    if key.expr_name != "token":
                        raise OptionParseError("Expected token as key, got group")
                    if val.expr_name == "group":
                        d[key.text.strip('"')] = nested(QCBuilder.traverse_options(val.children[2]))
                        continue
                    d[key.text.strip('"')] = val.text.strip('"')
                return d

            self.__dict__.update(nested(trav))

class QCParseError(Exception): pass
class OptionParseError(Exception): pass

from collections import deque

class QCBuilder(NodeVisitor):
    grammar = qcgrammar

    def __init__(self):
        super().__init__()
        self.qc = list()
        self.command_to_build: QC.bodygroup | None = None
        self.annotations_to_build = deque()
        self.bInGroup: bool = False

    def push_command(self, command_cls: Type):
        # Didn't finish the previous command
        if self.command_to_build is not None:
            # verify that the command is complete
            for member, type in self.command_to_build.__annotations__.items():
                if getattr(self.command_to_build, member, None) is None:
                    if member == "options":
                        self.command_to_build.options = Group()
                    else:
                        raise QCParseError(f"Missing member {member} in {self.command_to_build}")
            self.qc.append(self.command_to_build)

        if not command_cls.__annotations__ and not hasattr(command_cls, "handle_options"):
            self.qc.append(command_cls())
            return
        self.command_to_build = command_cls()
        self.annotations_to_build = deque(self.command_to_build.__annotations__.items())
    
    def push_argument(self, arg: str):
        member, type = self.annotations_to_build[0]
  
        bInlineOptions = False
        if member == "options":
            if type is not TokensInlineOrGroup:
                return
            type = str
            bInlineOptions = True

        bInlineOptional = get_origin(type) is Union
        bCommandBuiltYet = hasattr(self.command_to_build, member) and not bInlineOptional
        
        if bInlineOptions or not bCommandBuiltYet:
            if bInlineOptional:
                type = get_args(type)[0]
                if type is bool:
                    arg = True
            if type == str:
                arg = arg.strip('"')
            if type in (int, float):
                # fix for 7.006ff000, passes ff000 as token
                if not all(c in "0123456789.-" for c in arg):
                    return # raise TokenError
            if bInlineOptions:
                if not bCommandBuiltYet:
                    self.command_to_build.options = Group([type(arg)])
                else:
                    self.command_to_build.options.append(type(arg))
                return
            
            # Fill member 
            setattr(self.command_to_build, member, type(arg))
            self.annotations_to_build.popleft()
    
            # didn't run out yet
            if len(self.annotations_to_build):
                return
        
        if hasattr(self.command_to_build, "handle_options"):
            return
        # ran out of members to fill
        self.qc.append(self.command_to_build)
        self.command_to_build = None
    
    @staticmethod
    def traverse_options(node: Node):
        for child in node:
            if child.expr_name in ("token", "group"):
                yield child
                break
            yield from QCBuilder.traverse_options(child)

    @staticmethod
    def nested(node) -> Group[Token | Group[Token]]:
        rv = Group()
        trav = QCBuilder.traverse_options(node)
        for option in trav:
            # add group as a nested list of tokens
            if option.expr_name == "group":
                rv.append(QCBuilder.nested(option.children[2]))
                continue
            rv.append(option.text.strip('"'))
        return rv

    def push_argument_group(self, base_group_node: Node):
        
        if self.command_to_build is None:
            return "?"

        if hasattr(self.command_to_build, "handle_options"):
            self.command_to_build.handle_options(base_group_node.children[0].children[2])
        
        # just a list of tokens/groups { "a" "b" "c" { "d" "e" } }
        elif self.command_to_build.__annotations__.get("options") in (Group[Token], TokensInlineOrGroup):

            #print(base_group_node.children[0].children[2])

            ls = QCBuilder.nested(base_group_node.children[0].children[2])

            if getattr(self.command_to_build, "options", None) is not None:
                self.command_to_build.options.extend(ls)
            else:
                self.command_to_build.options = ls
        
        # a list of groups { { "a1" "b1" } { "a2" "b2" } }
        elif self.command_to_build.__annotations__.get("options") == Group[Group[Token]]:
            trav = QCBuilder.traverse_options(base_group_node.children[0].children[2])
            base_group = Group()
            for group in trav:
                if group.expr_name != "group":
                    raise OptionParseError(f"Expected group, got {group.expr_name}")
                subgr: Group[Token] = Group()
                a = QCBuilder.traverse_options(group.children[2])
                for token in a:
                    if token.expr_name != "token":
                        raise OptionParseError(f"Expected token, got {token.expr_name}")
                    subgr.append(token.text.strip('"'))
                base_group.append(subgr)
            
            self.command_to_build.options = base_group

        # options is the last member
        self.qc.append(self.command_to_build)
        self.command_to_build = None

    def visit_qcfile(self, node: Node, visited_children: Sequence[Node]):
        return self.qc
    
    def visit_cmd(self, node, visited_children):
        token_name = node.text.lower()

        if (cls:=getattr(QC, token_name[1:], None)) is not None:
            self.push_command(cls)
        else:
            self.qc.append(f"{token_name}:unimplemented")
        return node
    
    def visit_token_base(self, node, _):
        if self.command_to_build is None:
            return
        if not hasattr(self.command_to_build, "__annotations__"):
            return
        self.push_argument(node.text.lower())
    
    def visit_group_base(self, node, visited_children):
        self.push_argument_group(node)
        return node
    #def visit_comment(self, node, visited_children):
    #    print("comment:", node.text[2:].strip())
    #
    #def visit_flexfile(self, node, visited_children):
    #    print("flexfile contents", node.text)

    def generic_visit(self, *args):
        return args[0]

if __name__ == "__main__":
    testqc = \
"""
$modelname	"props\myfirstmodel .mdl"
$body	mybody	"myfirstmodel-ref.smd" 1 0.236
$body	myhead "myfirstmodel-refhead.smd"

$bodygroup sights {
	studio mybody
	studio myhead
	blank
}

$staticprop
$surfaceprop	combine_metal
$CDmaterials	"models\props"

$TextureGroup "skinfamilies" {
	{ "helicopter_news_adj"                "helicopter_news2"                } // TODO: fix this character making the other line a comment->\
	{ "..\hybridPhysx\helicopter_news_adj" "..\hybridPhysx\helicopter_news2" } //helicopter_news2 from models/hybridPhysx
	{ "..\hybridPhysx\helicopter_army"     "..\hybridPhysx\helicopter_army2" } //Could also add second $cdmaterials line and just use "helicopter_army2"
}


$sequencE idle	"myfirstmodel-ref.smd" { activity "ACT_IDLE" -1 fadein 0.2

    { event AE_MUZZLEFLASH 0 "357 MUZZLE" }
    { event 6001 0 "0" }
    snap
}

$collisionmodel	"myfirstmodel-phys.smd" {
	$concave
}

$keyvalues
{
	"prop_data"
	{
		"base" "Metal.LargeHealth"
		"allowstatic" "1"
		"dmg.bullets" "0"
		"dmg.fire" "0"
		"dmg.club" ".35"
	//	"dmg.explosive" "1" 
		"multiplayer_break"	"both"
		"BlockLOS"	"1"
	}

}

$collisionjoints "joints1"

$collisiontext
{
	"break"
	{
	"model" "props_unique\SubwayCarExterior01_SideDoor01_Damaged_01"
	"health" "10"
//	"fademindist" "10000"
//	"fademaxdist" "10000"
	}

// it doesn't close

/* neither does this comment

$collisionjoints "joints2"//lastcomment """
    import unittest
    class TestQC(unittest.TestCase):
        def test_parses_without_fail(self):
            qc = QCBuilder()
            qc.parse(testqc)
        def test_commands(self):
            self.maxDiff = None
            qc = QCBuilder()
            commands = qc.parse(testqc)
            expected_commands = [
                ("modelname", {'filename': 'props\\myfirstmodel .mdl'}),
                ("body", {'name': 'mybody', 'mesh_filename': 'myfirstmodel-ref.smd', 'reverse': True, 'scale': 0.236}),
                ("body", {'mesh_filename': 'myfirstmodel-refhead.smd', 'name': 'myhead'}),
                ("bodygroup", {'name': 'sights', 'options': ['studio', 'mybody', 'studio', 'myhead', 'blank']}),
                #("attachment", {'name': 'anim_attachment_rh',  'options': ['rotate', '-90.00', '-90.00', '0.00'], 'parent_bone': 'valvebiped.anim_attachment_rh', 'x': -0.0, 'y': -0.0, 'z': 0.0}),
                ("staticprop", {}),
                ("surfaceprop", {'name': 'combine_metal'}),
                ("cdmaterials", {'folder': 'models\\props'}),
                ("texturegroup", {'name': 'skinfamilies', 'options': [['helicopter_news_adj', 'helicopter_news2'], ['..\\hybridPhysx\\helicopter_army', '..\\hybridPhysx\\helicopter_army2']]}),
                ("sequence", {'name': 'idle', 'options': ['myfirstmodel-ref.smd','activity','ACT_IDLE','-1','fadein','0.2',['event', 'AE_MUZZLEFLASH', '0', '357 MUZZLE'],['event', '6001', '0', '0'], 'snap']}),
                ("collisionmodel", {'mesh_filename': 'myfirstmodel-phys.smd'}),
                ("keyvalues", {'prop_data': {'base': 'Metal.LargeHealth', 'allowstatic': '1', 'dmg.bullets': '0', 'dmg.fire': '0', 'dmg.club': '.35', 'multiplayer_break': 'both', 'BlockLOS': '1'}}),
                ("collisionjoints", {'mesh_filename': 'joints1'}),
                ("$collisiontext:unimplemented", None),
            ]
            names = [cmd.__class__.__name__ if not isinstance(cmd, str) else cmd for cmd in commands]
            expected_names = [cmd[0] for cmd in expected_commands]
            self.assertCountEqual(names, expected_names, "Where First=Parsed, Second=Expected")

            for (expected_name, expected_params), cmd in zip(expected_commands, commands):
                name = cmd if isinstance(cmd, str) else cmd.__class__.__name__
                options = None if isinstance(cmd, str) else cmd.__dict__
                print(f'("{name}", {options})')
                self.assertEqual(name, expected_name)
                self.assertEqual(options, expected_params, f"At command: {name}\np: {options}\ne: {expected_params}")

    unittest.main()
