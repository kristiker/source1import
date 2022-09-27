
from typing import Optional, Sequence, Type
from parsimonious.grammar import Grammar
from parsimonious.nodes import Node, NodeVisitor

qcgrammar = Grammar(
    """
    qcfile = _? ((cmd / token / group_base) _*)*

    # to distinguish top level from other stuff
    cmd = ~"\\$[_$a-zA-Z][\w$/.]*"
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
        options: list["{list[atleast1_material, _]}"] # list of skins
    
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
        options: list[str]

    class body:
        name: str
        mesh_filename: str
        reverse: Optional[bool] = False
        scale: Optional[int] = 1
    
    class lod:
        threshold: int
        options: list[str]

    class model:
        name: str
        mesh_filename: str
    
    class animation:
        name: str

    class sequence:
        name: str
        mesh_filename: str
        #options: _options
    
    class declaresequence:
        name: str
    
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
                        d[key.text] = nested(QCBuilder.traverse_options(val.children[2]))
                        continue
                    d[key.text.strip('"')] = val.text.strip('"')
                return d

            self.__dict__.update(nested(trav))

class QCParseError(Exception): pass
class OptionParseError(Exception): pass

class QCBuilder(NodeVisitor):
    grammar = qcgrammar

    def __init__(self):
        super().__init__()
        self.qc = list()
        self.command_to_build = None
        self.bInGroup = False

    def push_command(self, command_cls: Type):
        # argless command (e.g. $staticprop)
        
        if not command_cls.__annotations__ and not hasattr(command_cls, "handle_options"):
            self.qc.append(command_cls())
            return
        self.command_to_build = command_cls()
    
    def push_argument(self, arg: str):
        # inefficient but works
        max = len(self.command_to_build.__annotations__)
        for i, (member, type) in enumerate(self.command_to_build.__annotations__.items(), 1):
            if member == "options":
                return
            #print(self.command_to_build, member, type)

            if not hasattr(self.command_to_build, member):
                if type == str:
                    arg = arg.strip('"')
                
                if type in (int, float):
                    # fix for 7.006ff000, passes ff000 as token
                    if not all(c in "0123456789.-" for c in arg):
                        return
                setattr(self.command_to_build, member, type(arg))
                # didn't run out yet
                if i < max:
                    return
        
        if hasattr(self.command_to_build, "handle_options"):
            return
        # ran out of members to fill
        self.qc.append(self.command_to_build)
        self.command_to_build = None
    
    @staticmethod
    def traverse_options(node: Node):
        if node.expr_name in ("token", "group"):
            yield node
            return
        for child in node:
            yield from QCBuilder.traverse_options(child)

    def push_argument_group(self, base_group_node: Node):
        
        if self.command_to_build is None:
            return "?"

        if hasattr(self.command_to_build, "handle_options"):
            self.command_to_build.handle_options(base_group_node.children[0].children[2])
        
        # just a list of tokens
        elif self.command_to_build.__annotations__.get("options") == list[str]:
            trav = QCBuilder.traverse_options(base_group_node.children[0].children[2])
            ls = []
            for option in trav:
                if option.expr_name != "token":
                    raise OptionParseError("Expected token, got group")
                ls.append(option.text.lower().strip('"'))

            setattr(self.command_to_build, "options", ls)

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
    
    def visit_token(self, node, _):
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
$body	mybody	"myfirstmodel-ref.smd" 0 2
$body	myhead "myfirstmodel-refhead.smd"

$bodygroup sights {
	studio mybody
	studio myhead
	blank
}

$staticprop
$surfaceprop	combine_metal
$CDmaterials	"models\props"

$sequencE idle	"myfirstmodel-ref.smd" { }

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
            qc = QCBuilder()
            commands = qc.parse(testqc)
            dicts = {
                "modelname": {'filename': 'props\\myfirstmodel .mdl'},
                "body": {'name': 'mybody', 'mesh_filename': 'myfirstmodel-ref.smd'},
                "bodygroup": {'name': 'sights', 'options': ['studio', 'mybody', 'studio', 'myhead', 'blank']},
                "staticprop": {},
                "surfaceprop": {'name': 'combine_metal'},
                "cdmaterials": {'folder': 'models\\props'},
                "sequence": {'name': 'idle', 'mesh_filename': 'myfirstmodel-ref.smd'},
                "collisionmodel": {'mesh_filename': 'myfirstmodel-phys.smd'},
                "keyvalues": {'"prop_data"': {'base': 'Metal.LargeHealth', 'allowstatic': '1', 'dmg.bullets': '0', 'dmg.fire': '0', 'dmg.club': '.35', 'multiplayer_break': 'both', 'BlockLOS': '1'}},
                "collisionjoints": {'mesh_filename': 'joints1'},
                "$collisiontext:unimplemented": None,
            }
            names = [cmd.__class__.__name__ if not isinstance(cmd, str) else cmd for cmd in commands]
            for name in dicts:
                self.assertTrue(name in names, msg=f"Expected to have {name} in command list {names}")
            
            for cmd in commands:
                if isinstance(cmd, str):
                    continue
                self.assertEqual(cmd.__dict__, dicts[cmd.__class__.__name__])

    unittest.main()
