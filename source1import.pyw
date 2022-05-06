from dataclasses import dataclass
import functools
from pathlib import Path
from threading import Thread
from tkinter import filedialog, messagebox, ttk
from tkinter import *
import sys
import json

sys.path.insert(0, sys.path[0] + '\\utils')

import utils.shared.base_utils2 as sh

bg1 = "#363636"
bg2 = "#262627"
fg1 = "#b6b6b7"

@dataclass
class TabContext:
    frame: Frame
    enabled: IntVar
    further_options: dict
class SampleApp(Tk):
    def __init__(self, *args, **kwargs):
        Tk.__init__(self, *args, **kwargs)

        global bg1, bg2, fg1

        self.APP_TITLE = "Source 1 Asset Importer"

        self.is_running = False
        self.isSingle = IntVar()
        self.allChecked = IntVar()

        self.in_path = StringVar(name="IMPORT_GAME")
        self.out_path = StringVar(name="EXPORT_GAME")
        self.filter = StringVar(name="filter")

        self.Overwrite = IntVar(name='overwrite_all')

        self.Textures = IntVar(name='textures')
        self.Materials = IntVar(name='materials')
        self.Models = IntVar(name='models')
        self.Models_move = IntVar(value=True, name='models_move')
        self.Particles = IntVar(name='particles')
        self.Maps = IntVar(name='maps')
        self.Scenes = IntVar(name='scenes')
        self.Scripts = IntVar(name='scripts')
        self.Sessions = IntVar(name='sessions')

        self.vars = (self.in_path, self.out_path, self.filter, self.Overwrite, self.Textures,
            self.Materials, self.Models, self.Models_move,self.Particles,self.Scenes,self.Scripts,self.Sessions,
        )
        self.settings_file = Path.home() / "AppData/Roaming/source1import/settings.json"
        self.settings_file.parent.MakeDir()

        self.iconbitmap(Path(__file__).parent / 'utils/shared/icon.ico')
        self.minsize(480, 330)
        self.title(self.APP_TITLE)
        #self.maxsize(370, 350)
        self.configure(background=bg1)

        self.io_grid = Frame(self, width=310, height=100, bg=bg1)
        self.io_grid.pack(fill="both", expand=False, padx=6, pady=5 )#side="left", fill="both", )
        self.io_grid.grid_columnconfigure(0, weight=0, pad=2, minsize=12, uniform= True)
        self.io_grid.grid_rowconfigure(0, weight=0, pad=1, minsize=15, uniform= True)

        self.widgets: dict[int, Widget] = {}
        # Import game label, entry and picker
        self.widgets[3] = Entry(self, textvariable=self.in_path,relief=GROOVE, width=48, state=DISABLED, disabledbackground=bg2, disabledforeground="white")
        self.widgets[5] = Button(text=" ... ", command=lambda: self.pick_in_path())
        Label(self, text="Import Game :", fg = fg1, bg=bg1).grid(in_=self.io_grid,row=1,column=0,sticky="w")
        self.widgets[3].grid(row=1, column = 1, columnspan=2, in_=self.io_grid,sticky="we", pady=5, padx=3, ipady=2)
        self.widgets[5].grid(row=1, column = 3, in_=self.io_grid)

        # Export game label, entry and picker
        Label(self, text="Export Game :", bg=bg1, fg = fg1).grid(in_=self.io_grid,row=2,column=0,sticky="w")
        self.widgets[8] = Entry(self, textvariable=self.out_path, width=40, relief=GROOVE, state=DISABLED, disabledbackground=bg2, disabledforeground="white")
        self.widgets[8].grid(row=2, column= 1, columnspan=2, in_=self.io_grid,sticky="we", pady=5, padx=3, ipady=2)
        self.widgets[7] = Button(text=" ... ", command=lambda: self.pick_out_path(),relief=GROOVE,state=DISABLED)
        self.widgets[7].grid(row=2, column = 3, in_=self.io_grid)#.grid(row=2, column = 3, columnspan=2, rowspan = 1,in_=self.io_grid, sticky="wens")

        # Filter
        Label(self, text="Filter :", bg=bg1, fg = fg1).grid(in_=self.io_grid,row=3,column=0,sticky="w")
        self.widgets[2] = Entry(self, textvariable=self.filter, fg="white", bg=bg2, width=40, relief=GROOVE)
        self.widgets[2].grid(row=3, column= 1, columnspan=2, in_=self.io_grid,sticky="we", pady=5, padx=3, ipady=2)
        Button(text=" X ", command=lambda: self.filter.set(''),fg=fg1,bg=bg1,highlightcolor = bg1,relief=GROOVE).grid(row=3, column = 3, in_=self.io_grid)


        # Settings grid
        self.sett_grid = Frame(self, width=310, height=100, bg=bg1)
        self.sett_grid.pack(fill="both", expand=False, padx=20, pady=1)#side="left", fill="both", expand=True)
        self.sett_grid.grid_columnconfigure(0, weight=0, pad=2, minsize=12)
        self.sett_grid.grid_rowconfigure(0, weight=0, pad=1, minsize=15)


        self.widgets[40] = Checkbutton(text="Import All", variable=self.allChecked, command=self.checkbutton_toggle_all, bd = 2)
        self.widgets[40].grid(pady= 5, row = 0, column = 0, columnspan=2, in_=self.sett_grid, sticky="w")
        #self.widgets[1] = Checkbutton(self, text="Force Overwrite", variable=self.Overwrite,selectcolor=bg1, bd = 0)#.grid(row=1, sticky=W)
        #self.widgets[1].grid(pady= 5, row = 0, column = 1, columnspan = 2, in_=self.sett_grid, sticky="n")#.grid(row=0, sticky=W)


        style = ttk.Style()
        style.theme_create( "yummy", parent="default", settings={
                "TNotebook": {"configure": {"tabmargins": [2, 5, 2, 0], "background": bg1,"tabposition": "wn", "padding":[5,0]} },
                "TNotebook.Tab": {
                    "configure": {"padding": [5, 2, 15, 2], "foreground": fg1, "background": bg1, "bordercolor": bg2 },
                    "map":  {"foreground": [("selected", "white"), ("disabled", bg2)],
                            #"background": [("selected", bg2)],
                             }}})
        style.theme_use("yummy")
        # Settings tabs
        self.tab_notebook = ttk.Notebook(self, padding=0)
        self.tabs: dict[str, TabContext] = {}

        def add_tab(name: str, enable: IntVar, description: str) -> Frame:
            count = len(self.tabs)
            frame = Frame(self.tab_notebook)
            self.widgets[10+count] = Checkbutton(self, variable=enable, command=functools.partial(self.checkbutton_tab_update, name), bd = 0,selectcolor=bg1)
            self.widgets[10+count].grid(row = count+1, in_=self.sett_grid, sticky=W)
            self.widgets[30+count] = Label(self, text=description, wraplength=300, justify=LEFT, anchor=W)
            self.widgets[30+count].grid(in_=frame)
            self.tabs[name] = TabContext(frame, enable, {})
            return frame
        add_tab("textures", self.Textures, "Decompile VTF to sources")
        add_tab("materials", self.Materials, "Import VMT materials")
        
        Checkbutton(self, text="Move .mdls", variable=self.Models_move, bd = 0, selectcolor=bg1, bg=bg1, fg=fg1).grid(
            sticky="w", padx=0, pady=5,
            in_=add_tab("models", self.Models, "Generate VMDL models")
        )
        add_tab("particles", self.Particles, "Import particles")
        add_tab("maps", self.Maps, "Import VMF entities (soon)")
        add_tab("sessions", self.Sessions, "Convert Source Filmmaker Sessions")
        add_tab("scenes", self.Scenes, "Generate vcdlist from vcds")
        add_tab("scripts", self.Scripts, "Import various script files")

        self.tab_notebook.grid(in_=self.sett_grid, column=1, row=1, rowspan=len(self.tabs))#.pack(expand=1, fill="both")

        self.widgets[19]=Text(self, wrap=NONE, bd=1, relief=SUNKEN, height=7) #, textvariable=self.status
        self.widgets[19].see(END)

        for tab in self.tabs:
            self.tabs[tab].frame.configure(bg=bg1, highlightbackground=bg1, highlightcolor = bg1, padx=6, pady=6, relief=GROOVE)
            self.tab_notebook.add(self.tabs[tab].frame, text=tab.capitalize())

        self.Console = Console(self.widgets[19])

        # replace sys.stdout with our object
        sys.stdout = self.Console
        #font=('arial',16,'normal')
        for widget in self.widgets:
            if widget in range(30, 40):
                self.widgets[widget].configure(bg=bg1, fg =fg1, font='Helvetica 10')
                continue
            if widget != 2:
                self.widgets[widget].configure(bg=bg1, fg =fg1, highlightbackground=bg1, highlightcolor = bg1, relief=GROOVE, font='Helvetica 10 bold' if widget in (5,7) else 'Helvetica 10')

            if widget in (19, 999): # depth
                self.widgets[widget].configure(bg=bg2)

            if widget in (1,4,5,7,9,10,11,12,13,14,15,16,17,40): # buttons
                self.widgets[widget].configure(activebackground = bg2, activeforeground = "white")

        self.go_and_status = Frame(self, bg=bg1)
        self.go_and_status.pack(ipadx = 6, ipady = 1.1, padx = 6, pady = 6, side=BOTTOM, fill=BOTH)#side="left", fill="both", expand=True)
        self.go_and_status.grid_columnconfigure(0, weight=1)
        self.go_and_status.grid_rowconfigure(0, weight=1)

        self.status=StringVar()
        sh.status = self.status.set
        self.widgets[20]=Label(self, bd=1, relief=FLAT, textvariable=self.status, bg=bg2, fg=fg1, anchor=W)
        self.widgets[20].grid(in_=self.go_and_status, row=0, column=0, sticky="nsew", padx=2)
   
        self.gobutton = Button(width=10,text="Go", command=self.launch_importer_thread, bg=bg1, fg =fg1, activebackground = bg2, activeforeground = fg1, relief=GROOVE, disabledforeground=bg2)
        self.gobutton.grid(in_=self.go_and_status, row=0, column=1)
        
        self.widgets[19].pack(fill=BOTH, padx = 6, pady = 2, side=BOTTOM, expand=True)#, side=BOTTOM

        # restore app state from last session
        self.cfg = {'app_geometry':"480x500"}
        self.geometry("480x500")
        self.read_config()


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
        if self.out_path.get():
            if not sh.IMPORT_GAME:
                return
            try:
                sh.parse_out_path(Path(self.out_path.get()))
            except SystemExit as exc:
                self.out_path.set("")
                return
            else:
                self.gobutton.configure(state=NORMAL)
            try:
                print("Exporting to:\n"
                f" ROOT :  \"{sh.ROOT.as_posix()}\"\n"
                f" CONTENT :  {sh.EXPORT_CONTENT.relative_to(sh.ROOT).as_posix()}\n"
                f" GAME :  {sh.EXPORT_GAME.relative_to(sh.ROOT).as_posix()}"   
            )
            except (ValueError, AttributeError): # non-source2 export (sbox)
                print(f"Exporting everything to '{sh.EXPORT_GAME.as_posix()}'\n")
            
            print('=========================================================')
            
        #self.write_config()

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
        if self.is_running:
            return
        thread = Thread(target=self.go, daemon=True)
        thread.start()
        self.is_running: bool = property(fget=lambda:thread.is_alive())
        self.gobutton_update()

    def go(self):
        self.write_config()
        def stop():
            self.is_running = False
            self.gobutton_update()
        if not any(method.get() for method in (self.Textures,self.Materials,self.Models,self.Particles,self.Scenes,self.Scripts,self.Sessions)):
            messagebox.showinfo(title=self.APP_TITLE, message="No import function was selected")
            return stop()
        
        if len(self.filter.get()):
            sh.filter_ = self.filter.get()
            if "*" not in sh.filter_:
                sh.filter_ = "*" + sh.filter_  + "*"
        else:
            sh.filter_ = None

        if self.Textures.get():
            from utils import vtf_to_tga
            vtf_to_tga.sh = sh
            vtf_to_tga.OVERWRITE = self.Overwrite.get()
            try: vtf_to_tga.main()
            except Exception as e:
                print(e, "\nSomething went wrong while decompiling textures!")
            print('=========================================================')

        if self.Materials.get():
            try:
                from utils import materials_import
            except ModuleNotFoundError as e:
                print(e.msg, "(forgot to pip install -r requirements.txt)")
                return stop()
            materials_import.sh = sh
            materials_import.OVERWRITE_VMAT = self.Overwrite.get()
            materials_import.OVERWRITE_SKYBOX_VMATS = self.Overwrite.get()
            materials_import.OVERWRITE_SKYCUBES = self.Overwrite.get()
            try: materials_import.main()
            except Exception as e:
                print(e, "\nSomething went wrong while importing materials!")
            print('=========================================================')

        if self.Models.get():
            from utils import models_import
            models_import.sh = sh
            models_import.SHOULD_OVERWRITE = self.Overwrite.get()
            try: models_import.main()
            except Exception as e:
                print(e, "\nSomething went wrong while importing models!")
            print('=========================================================')
        
        if self.Particles.get():
            try:
                from utils import particles_import
            except ModuleNotFoundError as e:
                print(e.msg, "(forgot to pip install -r requirements.txt)")
                return stop()
            particles_import.sh = sh
            particles_import.OVERWRITE_PARTICLES = self.Overwrite.get()
            try: particles_import.main()
            except Exception as e:
                print(e, "\nSomething went wrong while importing particles!")
            print('=========================================================')
        
        if self.Scenes.get():
            from utils import scenes_import
            scenes_import.sh = sh
            try: scenes_import.main()
            except Exception as e:
                print(e, "\nSomething went wrong while importing scenes!")
            print('=========================================================')

        if self.Scripts.get():
            from utils import scripts_import
            scripts_import.sh = sh
            scripts_import.OVERWRITE_SCRIPTS = self.Overwrite.get()
            try:scripts_import.main()
            except Exception as e:
                print(e, "\nSomething went wrong while importing scripts!\n\t", e)
            print('=========================================================')
        class CustomException(Exception):...
        if self.Sessions.get():
            from utils import elements_import
            elements_import.sh = sh
            elements_import.SHOULD_OVERWRITE = self.Overwrite.get()
            try:elements_import.main()
            except SystemExit:
                ...
            except CustomException as e:
                print(e)
            except Exception as e:
                print(e, "\nSomething went wrong while importing sessions!\n\t", e)
            print('=========================================================')

        messagebox.showinfo(title=self.APP_TITLE, message="Looks like we are done!")
        return stop()

    def checkbutton_toggle_all(self):
        # .toggle, select, deselect
        self.allChecked.set(0 if not self.allChecked.get() else 1)
        for tab in self.tabs.values():
            tab.enabled.set(self.allChecked.get())

        self.checkbutton_tab_update()

    def verify_all_toggled(self):
        """Auto toggle Import All based on status of other checkboxes"""
        for tab in self.tabs.values():
            if self.allChecked.get(): # Import All is toggled on!
                if not tab.enabled.get(): # but this tab is not
                    self.allChecked.set(0) # so deselect Import All
                    break
            else: # Import All is toggled off
                if not tab.enabled.get(): # and I found a tab that is not toggled
                    return # it can't be toggled on, so don't bother checking the rest
        else:
            self.allChecked.set(1) # all tabs are toggled on, so select Import All

    def focus_tab(self, tabName: str):
        for tab in self.tab_notebook.tabs():
            if tabName == self.tab_notebook.tab(tab, option="text").lower():
                self.tab_notebook.select(tab)
                break

    def checkbutton_tab_update(self, specificTab: str = None):
        """Sets tab enable status and selects when one is toggled specifically"""
        self.verify_all_toggled()
        for tab in self.tab_notebook.tabs():
            capitalizedTabName = self.tab_notebook.tab(tab, option="text")
            if specificTab is not None and specificTab != capitalizedTabName.lower():
                continue
            if not getattr(self, capitalizedTabName).get():
                self.tab_notebook.tab(tab, state=DISABLED)
            else:
                self.tab_notebook.tab(tab, state=NORMAL)
                #if specificTab is not None:
                #    self.tab_notebook.select(tab)

    def gobutton_update(self):
        if self.is_running:
            self.gobutton.configure(state=DISABLED, text='Running')
        else:
            self.gobutton.configure(state=NORMAL, text='Go')
        
    def read_config(self):
        #print(Path(__file__).parent)qwe
        try:
            with open(self.settings_file, 'r') as fp:
                try: data = json.load(fp)
                except json.decoder.JSONDecodeError:
                    data = {}
                self.cfg.update(data)
        except (PermissionError, FileNotFoundError):
            pass
        self.geometry(self.cfg['app_geometry'])
        for var in self.vars:
            var.set(self.cfg.setdefault(var._name, var.get()))
        try:
            self.update_paths()
        except Exception:
            print("Wrong paths were configured.")
            self.in_path.set('')
            self.out_path.set('')
            self.write_config()
        self.checkbutton_tab_update()

    def write_config(self):
        for var in self.vars:
            self.cfg[var._name] = var.get()
        self.cfg['app_geometry'] = self.geometry()
        with open(self.settings_file, 'w') as fp:
            json.dump(self.cfg, fp, sort_keys=True, indent=4)

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


app = SampleApp("source1import")
app.mainloop()
