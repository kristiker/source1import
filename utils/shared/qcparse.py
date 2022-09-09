from typing import Optional, get_args, get_origin
from pathlib import Path
"""
crap qc parser
"""

class _options(list):
    "collection of commands"
    def __init__(self, option_list: list):
        super().extend(option_list)

class QCParse:
    class _command:
        def __init__(self, command_list: list):
            assert command_list[0] == f"${self.__class__.__name__}"

            for i, (var_name, type) in enumerate(self.__annotations__.items(), 1):
                if type is _options:
                    #setattr(self, var_name, "done")
                    continue
                if not get_origin(type):
                    setattr(self, var_name, type(command_list[i]))
                    continue
                if i >= len(command_list):
                    break

                type = get_args(type)[0]
                value = type(command_list[i])
                if type is bool:
                    value = type(int(command_list[i]))
                
                setattr(self, var_name, value)

        def update_options(self, option_list: list):
            self.options = _options(option_list)

    class staticprop(): pass
    
    class bodygroup(_command):
        name: str
        options: _options

    class body(_command):
        name: str
        mesh_filename: str
        reverse: Optional[bool] = False
        scale: Optional[int] = 1
    
    class model(_command):
        name: str
        mesh_filename: str
    
    class sequence(_command):
        name: str
        mesh_filename: str
        #class options:
        #    ...
        #opt: options
        
    @staticmethod
    def parse(qc_path: Path):
        qc: list["commands"] = []
        with qc_path.open() as fp:
            contents = fp.read()
            
            command = [""]
            argument_index = 0
            
            bYumEatingUntilNewLine = False
            bInQuotes = False
            bInGroup = False
            bNextAreOptionsForLast = False
            hLast: QCParse._command = None

            def finalize_token():
                nonlocal command, argument_index
                if len(command[argument_index]):
                    command[argument_index] = command[argument_index]#.strip('"')
                    argument_index+=1
                    command.append("")

            def finalize_command():
                nonlocal command, argument_index, bInGroup, bNextAreOptionsForLast, hLast
                if len(command) and len(command[0]):
                    
                    if (cls:=getattr(QCParse, command[0].strip('$'), None)) is not None:

                        # command with arguments
                        if issubclass(cls, QCParse._command):
                            try:
                                if "options" in cls.__annotations__ and not hasattr(cls(command), "options"):
                                    bNextAreOptionsForLast = True
                                command = cls(command)
                                print("command created:", command.__dict__)
                            except Exception:
                                print("command couldn't create:", command)
                        # single cmd
                        else:
                            command = cls
                            print("command added:", command.__name__)
                    else:
                        if bNextAreOptionsForLast:
                            bNextAreOptionsForLast = False
                            hLast.update_options(command)
                            print("command updated:", hLast.__dict__)
                            command = [""]
                            argument_index = 0
                            return False
                        else:
                            print("command parsed:", command)
                    hLast = command
                    qc.append(command)
                command = [""]
                argument_index = 0
                bInGroup = False
                return True

            for char in contents:
                # keep eating comments
                if bYumEatingUntilNewLine:
                    if char == '\n':
                        bYumEatingUntilNewLine = False
                    continue
                # skip whitespace
                if char in (' ', '\t', '\r') and not bInQuotes:
                    finalize_token()
                    continue
                # eat comments
                if char in ('/', '#', ';'):
                    bYumEatingUntilNewLine = True
                    continue
                elif char == '"':
                    bInQuotes = not bInQuotes
                    continue
                elif char == '{':
                    bInGroup = True
                elif char == '}':
                    if bInGroup:
                        bInGroup = False
                elif char == '\n':
                    if bInGroup:
                        finalize_token()
                        continue
                    finalize_command()
                    continue
                
                command[argument_index] += char

        return qc
