import shared.base_utils as sh
from pathlib import Path
from tkinter import filedialog, messagebox
from tkinter import *
from winsound import MessageBeep
from subprocess import run as subrun, STDOUT, PIPE
import json

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

        self.IMPORT_GAME = StringVar(name="IMPORT_GAME")
        self.EXPORT_GAME = StringVar(name="EXPORT_GAME")

        self.Overwrite = IntVar(name='overwrite_all')

        self.Textures = IntVar(name='textures')
        self.Materials = IntVar(name='materials')
        self.Models = IntVar(name='models')
        self.Models_move = IntVar(value=True, name='models_move')
        self.Models.Move = "LOl"

        self.vars = (self.IMPORT_GAME, self.EXPORT_GAME, self.Overwrite, self.Textures, self.Materials, self.Models, self.Models_move)
        #self.SOURCE2_ROOT = StringVar()

        self.cfg = {}
        self.read_config()

        self.widgets = {}
        if (path:= Path(r"D:\Games\steamapps\common\Source SDK Base 2013 Multiplayer\hl2\resource\game.ico")).exists():
            self.iconbitmap(path)

        self.geometry("476x380")
        self.minsize(476, 380)
        self.title(self.APP_TITLE)
        #self.maxsize(370, 350)
        self.configure(bg=bg1)

        self.status=StringVar()
        #self.widgets[20]=Label(self, bd=1, relief=FLAT, anchor=S, textvariable=self.status, bg="red")
        #self.status.set('Importing Finished! - Ky eshte shiriti i statusit')
        #self.widgets[20].pack(fill=X, side=TOP)

        self.io_grid = Frame(self, width=310, height=100, bg=bg1)
        self.io_grid.pack(fill="both", expand=False, padx=6, pady=5 )#side="left", fill="both", expand=True)
        self.io_grid.grid_columnconfigure(0, weight=0, pad=2, minsize=12, uniform= True)
        self.io_grid.grid_rowconfigure(0, weight=0, pad=1, minsize=15, uniform= True)

        #self.entry_frame
        #self.widgets[0] = Checkbutton(self, text="Single file", variable=self.isSingle,selectcolor="#414141")
        #self.widgets[0].grid(row=0, column = 3, in_=self.main_grid, sticky="w")#.grid(row=0, sticky=W)
        #self.widgets[1] = Checkbutton(self, text="Force Overwrite", variable=self.Overwrite,selectcolor="#414141")#.grid(row=1, sticky=W)
        #self.widgets[1].grid(row=0, column = 1, in_=self.io_grid, sticky="w")#.grid(row=0, sticky=W)
        #self.widgets[2] = Checkbutton(self, text="female", background="#414141",selectcolor="#414141")#.grid(row=1, sticky=W)
        #self.widgets[2].grid(row=0, column = 2, in_=self.main_grid, sticky="w")#.grid(row=0, sticky=W)

        self.widgets[3] = Entry(self, textvariable=self.IMPORT_GAME,relief=GROOVE, width=40, state=DISABLED, disabledbackground=bg2, disabledforeground="white")
        self.widgets[4] = Button(text="File  ", command=lambda: self.pick_path(0),relief=GROOVE)
        self.widgets[5] = Button(text="Folder", command=lambda: self.pick_path(1))
        Label(self, text="Import Game :", fg = fg1, bg=bg1).grid(in_=self.io_grid,row=1,column=0,sticky="w")
        self.widgets[3].grid(row=1, column = 1, columnspan=2, in_=self.io_grid,sticky="we", pady=5, padx=1, ipady=2)
        self.widgets[4].grid(row=1, column = 3, in_=self.io_grid, sticky="w")
        self.widgets[5].grid(row=1, column = 4, in_=self.io_grid, sticky="e")

        # Export content text and entry
        #Label(self, text="Export Content :", bg="#414141", fg = "white").grid(in_=self.io_grid,row=2,column=0,sticky="w")
        #self.widgets[6] = Entry(self, textvariable=self.EXPORT_CONTENT, width=24,relief=GROOVE)
        #self.widgets[6].grid(row=2, column= 1, columnspan=2, in_=self.io_grid,sticky="we", padx=1)

        # Export game text and entry
        Label(self, text="Export Game :", bg=bg1, fg = fg1).grid(in_=self.io_grid,row=2,column=0,sticky="w")
        self.widgets[8] = Entry(self, textvariable=self.EXPORT_GAME, width=40, relief=GROOVE, state=DISABLED, disabledbackground=bg2, disabledforeground="white")
        self.widgets[8].grid(row=2, column= 1, columnspan=2, in_=self.io_grid,sticky="we", pady=5, padx=1, ipady=2)

        # Choose button
        self.widgets[7] = Button(text="Choose", command=lambda: self.pick_path(2),relief=GROOVE)
        self.widgets[7].grid(row=2, column = 3, columnspan=2, rowspan = 1,in_=self.io_grid, sticky="wens")

       #Button(text="Overwrite All", command=self.overwrite_all).pack(anchor="w")
        self.sett_grid = Frame(self, width=310, height=100, bg=bg1)
        self.sett_grid.pack(fill="both", expand=False, padx=20, pady=1)#side="left", fill="both", expand=True)
        self.sett_grid.grid_columnconfigure(0, weight=0, pad=2, minsize=12)
        self.sett_grid.grid_rowconfigure(0, weight=0, pad=1, minsize=15)

        self.widgets[12] = Button(text="  Check all  ", command=self.checkbutton_toggle_all, bd = 2)
        self.widgets[12].grid(pady= 5, row = 0, column = 0,in_=self.sett_grid, sticky="n")
        self.widgets[1] = Checkbutton(self, text="Force Overwrite", variable=self.Overwrite,selectcolor=bg1, bd = 0)#.grid(row=1, sticky=W)
        self.widgets[1].grid(pady= 5, row = 0, column = 1, columnspan = 2, in_=self.sett_grid, sticky="n")#.grid(row=0, sticky=W)


        self.widgets[13] = Checkbutton(self, text="Import Textures", variable=self.Textures, bd = 0,selectcolor=bg1)
        self.widgets[13].grid(row = 1, in_=self.sett_grid, sticky="w")

        self.widgets[9] = Checkbutton(self, text="Import Materials", variable=self.Materials, bd = 0,selectcolor=bg1)
        self.widgets[9].grid(row = 2, in_=self.sett_grid, sticky="w")

        self.widgets[10] = Checkbutton(self, text="Import Models", variable=self.Models, command=self.checkbutton_tree_update,bd = 0,selectcolor=bg1)
        self.widgets[10].grid(row = 3, in_=self.sett_grid, sticky="w")
        self.widgets[11] = Checkbutton(self, text="Move .mdls", variable=self.Models_move, command=self.checkbutton_tree_update,bd = 0, state=DISABLED,selectcolor=bg1)
        self.widgets[11].grid(row = 3, column = 1, in_=self.sett_grid, sticky="w", padx=20)


        #self.widgets[10] = Checkbutton(self, text="Import Scripts", variable=self.Materials, command=self.material_sett, selectcolor="#414141", font='Helvetica 11', bd = 0)
        #self.widgets[10].grid(row = 2, column = 0, in_=self.sett_grid, sticky="w")

        self.widgets[19]=Text(self, wrap=NONE, bd=1, relief=SUNKEN, height=7) #, textvariable=self.status
        self.widgets[19].see(END)
        self.Console = Console(self.widgets[19])

        # replace sys.stdout with our object
        sys.stdout = self.Console
        #self.console_scroll()
        #self.pack()
        #font=('arial',16,'normal')
        for widget in self.widgets:
            self.widgets[widget].configure(bg=bg1, fg =fg1, highlightbackground=bg1, highlightcolor = bg1, relief=GROOVE, font='Helvetica 10 bold' if widget == 5 else 'Helvetica 10')

            if widget in (19, 999): # depth
                self.widgets[widget].configure(bg=bg2)

            if widget in (1,4,5,7,9,10,11,12,13): # buttons
                self.widgets[widget].configure(activebackground = bg2, activeforeground = "white")

        #self.main_grid.grid_remove()
        #self.widgets[20].configure(bg="green", fg="white", font='Helvetica 10 bold')

        self.gobutton = Button(text="\tGo\t", command=self.run_scripts, bg=bg1, fg =fg1, activebackground = bg2, activeforeground = fg1, relief=GROOVE, disabledforeground=bg2)
        self.gobutton.pack(anchor="se", ipadx = 6, ipady = 1.1, padx = 6, pady = 6, side=BOTTOM)#, side=BOTTOM)
        self.widgets[19].pack(fill=BOTH, padx = 6, pady = 2, side=BOTTOM, expand=True)#, side=BOTTOM

        self.main_msg()
        self.poll()
        #Button(text="hmmm", command=lambda: self.IMPORT_GAME.set("C:/here/theaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaare.xd")).pack()
        #self.entry.place(relx=.5, rely=.5, anchor="c")
        #self.button2.pack()
        #self.button3.pack()
        #self.IMPORT_GAME.set(str(Path(__file__).parent).capitalize())

    def main_msg(self):
        print("Welcome to the", self.APP_TITLE)
        #print(f"Files will be exported in either content/{Path(self.EXPORT_GAME.get()).name}, or game/{Path(self.EXPORT_GAME.get()).name}, depending on its type.")
        print(f"Files will be exported on either the /content/ or /game/ directory, depending on its type.")

    def poll(self):
        #print("YO POLLING")
        if hasattr(self, 'processing_thread'):
            if self.isRunning:
                if not self.processing_thread.is_alive():
                    self.isRunning = False
                    self.gobutton.configure(state=NORMAL)
                    #sys.stdout = self.Console
                    print("\n\t\t\t**** FINISHED ****\n")
                    MessageBeep()
            self.after(200, self.poll)
            return

        self.after(1000, self.poll)

    def fix_paths(self):
        if (not self.IMPORT_GAME.get()) or (not self.EXPORT_GAME.get()):
            return
        if (not Path(self.IMPORT_GAME.get()).exists()) or (not Path(self.EXPORT_GAME.get()).exists()):
            return

        self.fs = sh.Source("", self.IMPORT_GAME.get(), self.EXPORT_GAME.get())
        if self.fs:
            self.IMPORT_GAME.set(self.fs.IMPORT_GAME.as_posix())
            self.EXPORT_GAME.set(self.fs.EXPORT_GAME.as_posix())
            return True

    def pick_path(self, what):
        if what in (0, 1):
            self.isSingle = not what
            path = filedialog.askopenfilename(initialdir=self.IMPORT_GAME) if self.isSingle else filedialog.askdirectory(initialdir=self.IMPORT_GAME)
            if path:
                self.IMPORT_GAME.set(Path(path).as_posix())
                #self.widgets[3].configure(show = path.split("/Half-Life Alyx/", 1)[-1])
                self.widgets[4].configure(font='Helvetica 10 bold' if self.isSingle else 'Helvetica 10')
                self.widgets[5].configure(font='Helvetica 10' if self.isSingle else 'Helvetica 10 bold')

        elif what == 2:
            path = filedialog.askdirectory()
            if path:
                self.EXPORT_GAME.set(Path(path).as_posix())

    def run_scripts(self):
        if self.isRunning: return
        self.update_config()

        rv = self.fix_paths()
        if not rv:
            messagebox.showwarning(title=self.APP_TITLE, message="The path provided is invalid")
            return

        textures =self.Textures.get()
        materials =self.Materials.get()
        models =self.Models.get()
        if textures or materials or models:
            #print("Went!", self.isSingle, self.Overwrite.get(), self.EXPORT_GAME.get())
            #if not (messagebox.askokcancel(title=self.APP_TITLE, message=
            #        "Are you sure you want to continue?\n" +
            #        f"\n" +
            #        ("\nTHIS WILL OVERWRITE YOUR EXISTING FILES!\n" if self.Overwrite.get() else "")
            #        )):
            #        return

            self.gobutton.configure(state=DISABLED)
            self.isRunning = True

            commandList = []
            i, o = self.fs.IMPORT_GAME, self.fs.EXPORT_CONTENT
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
        self.widgets[12].configure(text= "Uncheck all" if self.allChecked else " Check all  ")
        self.Textures.set(self.allChecked)
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
    def __init__(self, textbox): # pass reference to text widget
        self.textbox = textbox # keep ref

    def write(self, text):
        self.textbox.insert(END, text) # write text to textbox
            # could also scroll to end of textbox here to make sure always visible

    def console_scroll(self):
        fully_scrolled_down = self.textbox.yview()[1] == 1.0
        if fully_scrolled_down:
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

app = SampleApp("source2utils")

_print = print
def print(*args, **kw):
    _print(*args, **kw)
    app.widgets[19].see(END) # scroll down

app.mainloop()
