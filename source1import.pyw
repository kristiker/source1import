#import shared.base_utils as sh
from pathlib import Path
import time
from tkinter import filedialog, messagebox
from tkinter import *
import sys
from winsound import MessageBeep
from subprocess import run as subrun, STDOUT, PIPE, CREATE_NEW_CONSOLE
import json

#os.chdir('utils')
sys.path.insert(0, sys.path[0] + '\\utils')

import utils.shared.base_utils2 as sh


fs = None
bg1 = "#363636"
bg2 = "#262627"
fg1 = "#b6b6b7"

class SampleApp(Tk):
    def __init__(self, *args, **kwargs):
        Tk.__init__(self, *args, **kwargs)

        global bg1, bg2, fg1

        self.APP_TITLE = "Source 1 Asset Importer"

        # VARS
        self.isRunning = False
        self.isSingle = IntVar()
        self.allChecked = False

        self.in_path = StringVar(name="in_path")
        self.out_path = StringVar(name="out_path")

        self.Overwrite = IntVar(name='overwrite_all')

        self.Textures = IntVar(name='textures')
        self.Materials = IntVar(name='materials')
        self.Models = IntVar(name='models')
        self.Models_move = IntVar(value=True, name='models_move')
        self.Particles = IntVar(name='particles')
        self.Scenes = IntVar(name='scenes')
        self.Scripts = IntVar(name='scripts')


        self.vars = (self.in_path, self.out_path, self.Overwrite, self.Textures,
            self.Materials, self.Models, self.Models_move,self.Particles,self.Scenes,self.Scripts,
        )
        #self.SOURCE2_ROOT = StringVar()

        self.widgets: dict[Widget] = {}
        if (path:= Path(r"D:\Games\steamapps\common\Source SDK Base 2013 Multiplayer\hl2\resource\game.ico")).exists():
            self.iconbitmap(path)

        self.geometry("480x500")
        self.minsize(480, 310)
        self.title(self.APP_TITLE)
        #self.maxsize(370, 350)
        self.configure(bg=bg1)

        self.io_grid = Frame(self, width=310, height=100, bg=bg1)
        self.io_grid.pack(fill="both", expand=False, padx=6, pady=5 )#side="left", fill="both", )
        self.io_grid.grid_columnconfigure(0, weight=0, pad=2, minsize=12, uniform= True)
        self.io_grid.grid_rowconfigure(0, weight=0, pad=1, minsize=15, uniform= True)

        #self.entry_frame
        #self.widgets[0] = Checkbutton(self, text="Single file", variable=self.isSingle,selectcolor="#414141")
        #self.widgets[0].grid(row=0, column = 3, in_=self.main_grid, sticky="w")#.grid(row=0, sticky=W)
        #self.widgets[1] = Checkbutton(self, text="Force Overwrite", variable=self.Overwrite,selectcolor="#414141")#.grid(row=1, sticky=W)
        #self.widgets[1].grid(row=0, column = 1, in_=self.io_grid, sticky="w")#.grid(row=0, sticky=W)
        #self.widgets[2] = Checkbutton(self, text="female", background="#414141",selectcolor="#414141")#.grid(row=1, sticky=W)
        #self.widgets[2].grid(row=0, column = 2, in_=self.main_grid, sticky="w")#.grid(row=0, sticky=W)

        self.widgets[3] = Entry(self, textvariable=self.in_path,relief=GROOVE, width=48, state=DISABLED, disabledbackground=bg2, disabledforeground="white")
        #self.widgets[4] = Button(text="File  ", command=lambda: self.pick_path(0),relief=GROOVE)
        self.widgets[5] = Button(text=" ... ", command=lambda: self.pick_in_path())
        Label(self, text="Import Game :", fg = fg1, bg=bg1).grid(in_=self.io_grid,row=1,column=0,sticky="w")
        self.widgets[3].grid(row=1, column = 1, columnspan=2, in_=self.io_grid,sticky="we", pady=5, padx=3, ipady=2)
        self.widgets[5].grid(row=1, column = 3, in_=self.io_grid)

        # Export content text and entry
        #Label(self, text="Export Content :", bg="#414141", fg = "white").grid(in_=self.io_grid,row=2,column=0,sticky="w")
        #self.widgets[6] = Entry(self, textvariable=self.EXPORT_CONTENT, width=24,relief=GROOVE)
        #self.widgets[6].grid(row=2, column= 1, columnspan=2, in_=self.io_grid,sticky="we", padx=1)

        # Export game text and entry
        Label(self, text="Export Game :", bg=bg1, fg = fg1).grid(in_=self.io_grid,row=2,column=0,sticky="w")
        self.widgets[8] = Entry(self, textvariable=self.out_path, width=40, relief=GROOVE, state=DISABLED, disabledbackground=bg2, disabledforeground="white")
        self.widgets[8].grid(row=2, column= 1, columnspan=2, in_=self.io_grid,sticky="we", pady=5, padx=3, ipady=2)

        # Choose button
        self.widgets[7] = Button(text=" ... ", command=lambda: self.pick_out_path(),relief=GROOVE,state=DISABLED)
        self.widgets[7].grid(row=2, column = 3, in_=self.io_grid)#.grid(row=2, column = 3, columnspan=2, rowspan = 1,in_=self.io_grid, sticky="wens")

       #Button(text="Overwrite All", command=self.overwrite_all).pack(anchor="w")
        self.sett_grid = Frame(self, width=310, height=100, bg=bg1)
        self.sett_grid.pack(fill="both", expand=False, padx=20, pady=1)#side="left", fill="both", expand=True)
        self.sett_grid.grid_columnconfigure(0, weight=0, pad=2, minsize=12)
        self.sett_grid.grid_rowconfigure(0, weight=0, pad=1, minsize=15)

        self.widgets[12] = Button(text="  Tick all  ", command=self.checkbutton_toggle_all, bd = 2)
        self.widgets[12].grid(pady= 5, row = 0, column = 0,in_=self.sett_grid, sticky="n")
        self.widgets[1] = Checkbutton(self, text="Force Overwrite", variable=self.Overwrite,selectcolor=bg1, bd = 0)#.grid(row=1, sticky=W)
        self.widgets[1].grid(pady= 5, row = 0, column = 1, columnspan = 2, in_=self.sett_grid, sticky="n")#.grid(row=0, sticky=W)


        self.widgets[13] = Checkbutton(self, text="Import Textures", variable=self.Textures, bd = 0,selectcolor=bg1, state=DISABLED)
        self.widgets[13].grid(row = 1, in_=self.sett_grid, sticky="w")

        self.widgets[9] = Checkbutton(self, text="Import Materials", variable=self.Materials, bd = 0,selectcolor=bg1)
        self.widgets[9].grid(row = 2, in_=self.sett_grid, sticky="w")

        self.widgets[10] = Checkbutton(self, text="Import Models", variable=self.Models, command=self.checkbutton_tree_update,bd = 0,selectcolor=bg1)
        self.widgets[10].grid(row = 3, in_=self.sett_grid, sticky="w")
        self.widgets[11] = Checkbutton(self, text="Move .mdls", variable=self.Models_move, command=self.checkbutton_tree_update,bd = 0, state=DISABLED,selectcolor=bg1)
        self.widgets[11].grid(row = 3, column = 1, in_=self.sett_grid, sticky="w", padx=20)

        self.widgets[14] = Checkbutton(self, text="Import Particles", variable=self.Particles, command=self.checkbutton_tree_update,bd = 0,selectcolor=bg1)
        self.widgets[14].grid(row = 4, in_=self.sett_grid, sticky="w")

        self.widgets[15] = Checkbutton(self, text="Import Scenes", variable=self.Scenes, command=self.checkbutton_tree_update,bd = 0,selectcolor=bg1)
        self.widgets[15].grid(row = 5, in_=self.sett_grid, sticky="w")

        self.widgets[16] = Checkbutton(self, text="Import Scripts", variable=self.Scripts, command=self.checkbutton_tree_update,bd = 0,selectcolor=bg1)
        self.widgets[16].grid(row = 6, in_=self.sett_grid, sticky="w")

        self.widgets[19]=Text(self, wrap=NONE, bd=1, relief=SUNKEN, height=7) #, textvariable=self.status
        self.widgets[19].see(END)
        self.Console = Console(self.widgets[19])

        # replace sys.stdout with our object
        sys.stdout = self.Console
        #self.console_scroll()
        #self.pack()
        #font=('arial',16,'normal')
        for widget in self.widgets:
            self.widgets[widget].configure(bg=bg1, fg =fg1, highlightbackground=bg1, highlightcolor = bg1, relief=GROOVE, font='Helvetica 10 bold' if widget in (5,7) else 'Helvetica 10')

            if widget in (19, 999): # depth
                self.widgets[widget].configure(bg=bg2)

            if widget in (1,4,5,7,9,10,11,12,13,14,15,16): # buttons
                self.widgets[widget].configure(activebackground = bg2, activeforeground = "white")

        #self.main_grid.grid_remove()
        #self.widgets[20].configure(bg="green", fg="white", font='Helvetica 10 bold')
        #self.widgets[20].pack(anchor='sw', fill=X, side=BOTTOM)
        
        #

        self.go_and_status = Frame(self, bg=bg1)
        self.go_and_status.pack(ipadx = 6, ipady = 1.1, padx = 6, pady = 6, side=BOTTOM, fill=BOTH)#side="left", fill="both", expand=True)
        self.go_and_status.grid_columnconfigure(0, weight=1)
        self.go_and_status.grid_rowconfigure(0, weight=1)

        self.status=StringVar()
        sh.status = self.status.set
        self.widgets[20]=Label(self, bd=1, relief=FLAT, textvariable=self.status, bg=bg2, fg=fg1, anchor=W)
        self.widgets[20].grid(in_=self.go_and_status, row=0, column=0)
    
        self.gobutton = Button(text="\tGo\t", command=self.launch_importer_thread, bg=bg1, fg =fg1, activebackground = bg2, activeforeground = fg1, relief=GROOVE, disabledforeground=bg2)
        self.gobutton.grid(in_=self.go_and_status, row=0, column=1)
        
        self.widgets[19].pack(fill=BOTH, padx = 6, pady = 2, side=BOTTOM, expand=True)#, side=BOTTOM
        
        self.importer_thread = Thread(target=self.go)

        # restore app state from last session
        self.cfg = {}
        Thread(target=self.read_config).start()
    

        #Button(text="hmmm", command=lambda: self.in_path.set("C:/here/theaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaare.xd")).pack()
        #self.entry.place(relx=.5, rely=.5, anchor="c")
        #self.button2.pack()
        #self.button3.pack()

    def status(self, text):
        self.status.set(text)

    def update_paths(self):
        if self.in_path.get():
            sh._args_known.__setattr__('src1gameinfodir', self.in_path.get())
            try:
                sh.parse_in_path()
            except SystemExit as exc:
                messagebox.showwarning(title="The path provided is invalid.",
                    message=f"{self.in_path.get()}\n\nERROR: {exc.args[0]}"
                )
                sh._args_known.__setattr__('src1gameinfodir', None)
                self.in_path.set("")
                self.widgets[7].configure(state=DISABLED)
                self.gobutton.configure(state=DISABLED)
                return
            else:
                self.Console.textbox.delete(1.0,END)
                print("Importing", sh.gameinfo.get('game', 'game with unreadable gameinfo'), f"('{Path(self.in_path.get()).name}')")
                self.widgets[7].configure(state=NORMAL)  
        if self.out_path.get(): # Both paths are provided.
            sh.parse_out_path(Path(self.out_path.get()))
            self.gobutton.configure(state=NORMAL)
            print()
            try:
                print(
                f"ROOT :  \"{sh.ROOT.as_posix()}\"\n"
                f"CONTENT :  {sh.EXPORT_CONTENT.relative_to(sh.ROOT).as_posix()}\n"
                f"GAME :  {sh.EXPORT_GAME.relative_to(sh.ROOT).as_posix()}\n"   
            )
            except (ValueError, AttributeError): # non-source2 export (sbox)
                print(f"Export everything to '{sh.EXPORT_GAME.as_posix()}'\n")
            
            print('=========================================================')
            
        self.update_config()

    def pick_in_path(self):
        if path := filedialog.askdirectory(initialdir=self.in_path.get()):
            self.in_path.set(Path(path).as_posix())
            #self.widgets[4].configure(font=f'Helvetica 10{" bold"*self.isSingle}')
            self.widgets[5].configure(font=f'Helvetica 10{" bold"*(not self.isSingle)}')
            self.update_paths()

    def pick_out_path(self):
        if path:= filedialog.askdirectory(initialdir=Path(self.in_path.get()).parent):
            self.out_path.set(Path(path).as_posix())
            self.update_paths()

    def launch_importer_thread(self):
        if self.importer_thread.is_alive():
            self.importer_thread.join()
        self.importer_thread.start()

    def go(self):
        #if self.isRunning: return
        self.update_config()
        
        #if self.Textures.get():
        #    from utils import vtf_to_tga
        #    vtf_to_tga.sh = sh
        #    vtf_to_tga.OVERWRITE = self.Overwrite.get()
        #    vtf_to_tga.main()
        #    print('=========================================================')

        if self.Materials.get():
            from utils import materials_import
            materials_import.sh = sh
            materials_import.OVERWRITE_VMAT = self.Overwrite.get()
            materials_import.OVERWRITE_SKYBOX_VMATS = self.Overwrite.get()
            materials_import.OVERWRITE_SKYCUBES = self.Overwrite.get()
            materials_import.main()
            print('=========================================================')

        if self.Models.get():
            from utils import models_import
            models_import.sh = sh
            models_import.SHOULD_OVERWRITE = self.Overwrite.get()
            models_import.main()
            print('=========================================================')
        
        if self.Particles.get():
            from utils import particles_import
            particles_import.sh = sh
            particles_import.OVERWRITE_PARTICLES = self.Overwrite.get()
            particles_import.main()
            print('=========================================================')
        
        if self.Scenes.get():
            from utils import scenes_import
            scenes_import.sh = sh
            scenes_import.main()
            print('=========================================================')

        if self.Scripts.get():
            from utils import scripts_import
            scripts_import.sh = sh
            scripts_import.OVERWRITE_SCRIPTS = self.Overwrite.get()
            scripts_import.main()
            print('=========================================================')

        messagebox.showinfo(title=self.APP_TITLE, message="Looks like we are done!")
        return
        if False: #textures or materials or models:
            #print("Went!", self.isSingle, self.Overwrite.get(), self.out_path.get())
            #if not (messagebox.askokcancel(title=self.APP_TITLE, message=
            #        "Are you sure you want to continue?\n" +
            #        f"\n" +
            #        ("\nTHIS WILL OVERWRITE YOUR EXISTING FILES!\n" if self.Overwrite.get() else "")
            #        )):
            #        return

            self.gobutton.configure(state=DISABLED)
            self.isRunning = True

            commandList = []
            i, o = self.in_path, self.EXPORT_CONTENT
            overwrite = ' -f' if self.Overwrite else ''

            if textures:
                commandList.append(f"python vtf_to_tga.py -i \"{i}\" -o \"{o}\"{overwrite}")
            if materials:
                commandList.append(f"python vmt_to_vmat.py -i \"{i}\" -o \"{o}\"{overwrite}")
            if models:
                nomove = '' if self.Models_move else ' -nomove'
                commandList.append(f"python mdl_to_vmdl.py -i \"{i}\" -o \"{o}\"{overwrite}{nomove}")

            commandList.append("echo ***** FINISHED *******")
            commandList.append("timeout /t 7")
            command = f'start "{self.APP_TITLE}" /wait cmd /c "{" && ".join(commandList)}"'
            print(f"RUNNING: {command}")
            self.processing_thread = threaded_cmd(command)
            self.processing_thread.start()

        else:
            messagebox.showinfo(title=self.APP_TITLE, message="No import function was selected")

    def checkbutton_toggle_all(self):
        # .toggle, select, deselect
        self.allChecked = not self.allChecked
        self.widgets[12].configure(text= "Untick all" if self.allChecked else " Tick all  ")
        #self.Textures.set(self.allChecked)
        self.Materials.set(self.allChecked)
        self.Models.set(self.allChecked)

        self.checkbutton_tree_update()

    def checkbutton_tree_update(self):
        models = self.Models.get()
        self.widgets[11].configure(state=NORMAL if models else DISABLED)
        if models: pass
        else: pass

    def read_config(self):
        self._rw_cfg(write=False)
        for var in self.vars:
            var.set(self.cfg.setdefault(var._name, var.get()))
        self.update_paths()
        self.checkbutton_tree_update()

    def update_config(self):
        for var in self.vars:
            self.cfg[var._name] = var.get()
        self._rw_cfg()

    def _rw_cfg(self, write=True):
        try:
            with open(Path(__file__).parent / Path("config.json"), 'w+' if write else 'r') as fp:
                try: data = json.load(fp)
                except json.decoder.JSONDecodeError:
                    data = {}

                self.cfg.update(data)

                if write:
                    json.dump(self.cfg, fp, sort_keys=True, indent=4)

        except (PermissionError, FileNotFoundError) as error:
            pass
            print(f"config.json: {error}")


class Console(): # create file like object
    def __init__(self, textbox: Text): # pass reference to text widget
        self.textbox = textbox # keep ref

    def write(self, text):
        if '\r' in text:
            text = text.replace('\r', '').strip()
            #text +='\n'
        self.textbox.insert(END, text) # write text to textbox
        self.console_scroll()
            # could also scroll to end of textbox here to make sure always visible

    def console_scroll(self):
        fully_scrolled_down = self.textbox.yview()[1] == 1.0
        if not fully_scrolled_down:
            self.textbox.see(END)

    def flush(self): # needed for file like object
        pass

from threading import Thread
class threaded_cmd(Thread):
    def __init__(self, command):
        self.command = command
        Thread.__init__(self)

    def run(self):
        subrun(self.command, cwd=Path(__file__).parent, shell=True)

app = SampleApp("source1import")

_print = print
def print(*args, **kw):
    _print(*args, **kw)
    app.widgets[19].see(END) # scroll down

app.mainloop()
