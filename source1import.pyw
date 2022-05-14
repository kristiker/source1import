from dataclasses import dataclass, field
import functools
from pathlib import Path
from threading import Thread
from tkinter import filedialog, messagebox, ttk
from tkinter import *
import sys
import json
from traceback import format_tb

sys.path.insert(0, sys.path[0] + '\\utils')

import utils.shared.base_utils2 as sh

bghighlight = "#414141"
bg1 = "#363636"
bg2 = "#262627"
fg1 = "#b6b6b7"

class ScriptError(Exception):...

@dataclass
class TabContext:
    frame: Frame
    enabled: IntVar
    further_options: dict
    module: str
    overwrite_ones: set = field(default_factory=set)

    def add_overwrite_toggles(self, *toggle_list: tuple[str, str]):
        self.overwrite_ones.update(option_name for option_name, _ in toggle_list)
        return self.add_toggles(*toggle_list)

    def add_toggles(self, *toggle_list: tuple[str, str]):
        for toggle_name, description in toggle_list:
            self.add_widget(toggle_name, IntVar(master=self.frame),
                functools.partial(Checkbutton, self.frame, command = self.frame.master.master.verify_all_overwrite,
                text=description,bd=0,selectcolor=bg1,bg=bg1,fg=fg1,activeforeground=fg1,activebackground=bg2)
            )
        return self

    def add_widget(self, key, var: Variable, widget_partial: functools.partial[Widget]):
        self.further_options[key] = var
        widget_partial(variable=var).grid(
            sticky="w", padx=0,# pady=5,
            in_=self.frame
        )
        return self

    def load_module(self):
        if self.module:
            return __import__(f"utils.{self.module}", fromlist=[self.module])

    def run(self):
        if not (module:= self.load_module()):
            return
        # FIXME HACK: some scripts are leaving this on nondefault EXPORT_GAME when they're done.
        sh.import_context['dest'] = sh.EXPORT_CONTENT
        module.sh = sh
        for option, var in self.further_options.items():
            setattr(module, option, var.get())
        try:
            module.main()
        except SystemExit:
            raise
        except ScriptError as e:  # Known error
            print(e)
        except Exception as e:  # Unknown error
            traceback = format_tb(e.__traceback__, None)
            for l in traceback:
                print(l, end='')
            print(f"Failed! Something went wrong with the {self.module} module!\n\t", e)
        print('=========================================================')

class SampleApp(Tk):
    def __init__(self, *args, **kwargs):
        Tk.__init__(self, *args, **kwargs)

        global bg1, bg2, fg1

        self.APP_TITLE = "Source 1 Asset Importer"

        self.is_running = False
        self.isSingle = IntVar()
        self.allChecked = IntVar()
        self.allOverwrite = IntVar()

        self.in_path = StringVar(name="IMPORT_GAME")
        self.out_path = StringVar(name="EXPORT_GAME")
        self.filter = StringVar(name="filter")
        self.destmod = StringVar(name="destmod", value=sh.destmod.value)

        #self.Overwrite = IntVar(name='overwrite_all')

        self.Textures = IntVar(name='textures')
        self.Materials = IntVar(name='materials')
        self.Models = IntVar(name='models')
        self.Particles = IntVar(name='particles')
        self.Maps = IntVar(name='maps')
        self.Scenes = IntVar(name='scenes')
        self.Scripts = IntVar(name='scripts')
        self.Sessions = IntVar(name='sessions')

        self.vars = (self.in_path, self.out_path, self.filter, self.Textures,
            self.Materials, self.Models,self.Particles,self.Scenes,self.Scripts,self.Sessions,
        )
        self.settings_file = Path.home() / "AppData/Roaming/source1import/settings.json"
        self.settings_file.parent.MakeDir()

        self.iconbitmap(Path(__file__).parent / 'utils/shared/icon.ico')
        self.minsize(480, 410)
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
        self.widgets[5] = Button(text="…", command=lambda: self.pick_in_path(),width=3)
        Label(self, text="Import Game :", fg = fg1, bg=bg1).grid(in_=self.io_grid,row=1,column=0,sticky="w")
        self.widgets[3].grid(row=1, column = 1, columnspan=2, in_=self.io_grid,sticky="we", pady=5, padx=5, ipady=3)
        self.widgets[5].grid(row=1, column = 3, in_=self.io_grid, ipady=0)

        # Export game label, entry and picker
        Label(self, text="Export Game :", bg=bg1, fg = fg1).grid(in_=self.io_grid,row=2,column=0,sticky="w")
        self.widgets[8] = Entry(self, textvariable=self.out_path, width=40, relief=GROOVE, state=DISABLED, disabledbackground=bg2, disabledforeground="white")
        self.widgets[8].grid(row=2, column= 1, columnspan=2, in_=self.io_grid,sticky="we", pady=5, padx=5, ipady=3)
        self.widgets[7] = Button(text="…", command=lambda: self.pick_out_path(),relief=GROOVE,state=DISABLED,width=3)
        self.widgets[7].grid(row=2, column = 3, in_=self.io_grid)#.grid(row=2, column = 3, columnspan=2, rowspan = 1,in_=self.io_grid, sticky="wens")

        # Filter
        Label(self, text="Filter :", bg=bg1, fg = fg1).grid(in_=self.io_grid,row=3,column=0,sticky="w")
        self.widgets[2] = Entry(self, textvariable=self.filter, fg="white", bg=bg2, width=40, relief=GROOVE)
        self.widgets[2].grid(row=3, column= 1, columnspan=2, in_=self.io_grid,sticky="we", pady=5, padx=5, ipady=4)
        self.widgets[1] = Button(text="❌", command=lambda: self.filter.set(''),font=15,fg=fg1,bg=bg1,highlightcolor=bg1,relief=GROOVE,width=3)
        self.widgets[1].grid(row=3, column = 3, in_=self.io_grid)


        self.sett_grid = Frame(self, width=310, bg=bg1, pady=0)
        self.sett_grid.pack(fill="both", expand=False, padx=15, pady=0, ipady=1)
        self.module_picking_grid = Frame(self, width=310, height=100, bg=bg1)
        self.module_picking_grid.pack(fill="both", expand=False, padx=15, pady=1, ipady=0)
        self.module_picking_grid.grid_columnconfigure(0, weight=0, pad=0)
        self.module_picking_grid.grid_rowconfigure(0, weight=0, pad=1, minsize=15)
        
        self.widgets[99] = Checkbutton(text="   Import All  ", variable=self.allChecked, command=self.checkbutton_toggle_all, width=11,selectcolor=bg1,padx=0)
        self.widgets[99].grid(pady= 2, row = 0, column = 0, columnspan=2, in_=self.sett_grid, sticky="w")
        self.widgets[53] = Checkbutton(self, text="Overwrite All", variable=self.allOverwrite, command=self.overwrite_toggle_all, selectcolor=bg1, width=10, bd=0, padx=4)
        self.widgets[53].grid(pady= 2, padx=4, row = 0, column = 2, in_=self.sett_grid, sticky="w")
        self.widgets[50] = OptionMenu(self, self.destmod, *(name.value for name in sh.eS2Game), command=lambda v: sh.update_destmod(sh.eS2Game(v)))
        self.widgets[50].grid(pady= 2, padx=0, row = 0, column = 4, in_=self.sett_grid, sticky="e")
        self.sett_grid.grid_columnconfigure(4, weight=2)
        self.widgets[50]["menu"].configure(bg=bg1,fg=fg1,activebackground=bghighlight,activeforeground="white", takefocus=0)
        

        style = ttk.Style()
        style.theme_create( "yummy", parent="alt", settings={
        "TNotebook": {
            "configure": {"tabmargins": [2, 5, 2, 0], "background": bg1,"tabposition": "wn", "padding":[5,0],"borderwidth":0,},
        },
        "TNotebook.Tab": {
            "configure": {"padding": [5, 4, 5, 2], "foreground": fg1, "background": bg1, "bordercolor": bg2, "width": 9, "focuscolor": bghighlight, "borderwidth": 0, "font": ("Arial", 10, "bold")},
            "map":  {"foreground": [("selected", "white"), ("disabled", bg2)],
                    "background": [("selected", bghighlight)],
                    "expand": [("selected", [2, 1, 1, 0])]
        }}})
        style.theme_use("yummy")
        # Settings tabs
        self.tab_notebook = ttk.Notebook(self, padding=0, width=341)
        self.tabs: dict[str, TabContext] = {}

        def add_tab(name: str, enable: IntVar, description: str, module: str = "") -> TabContext:
            count = len(self.tabs)
            frame = LabelFrame(self.tab_notebook, relief=GROOVE, bg=bg1, labelanchor="nw", text="", height=100)
            self.widgets[10+count] = Checkbutton(self, padx=0, pady=2, width=2, variable=enable, command=functools.partial(self.checkbutton_tab_update, name), bd=0,selectcolor=bg1)
            self.widgets[10+count].grid(row = count, in_=self.module_picking_grid, sticky=W)
            self.widgets[30+count] = Label(self, text="• "+description, justify=LEFT)
            self.widgets[30+count].grid(in_=frame)
            self.tabs[name] = TabContext(frame, enable, {}, module)
            return self.tabs[name]

        add_tab("textures", self.Textures, "Decompile VTF to sources", "vtf_to_tga").add_overwrite_toggles(
            ("OVERWRITE", "Overwrite Existing TGAs"),
        )
        add_tab("materials", self.Materials, "Import VMT materials", "materials_import").add_overwrite_toggles(
            ("OVERWRITE_VMAT", "Overwrite Existing VMATs"),
            ("OVERWRITE_SKYBOX_VMATS", "Overwrite Skybox VMATs"),
            ("OVERWRITE_SKYCUBES", "Overwrite Sky Images"),
        ).add_toggles(
            ("NORMALMAP_G_VTEX_INVERT", "Invert Normal Via Settings File"),
            ("SIMPLE_SHADER_WHERE_POSSIBLE", "Use Simple Shader if possible"),
            ("PRINT_LEGACY_IMPORT", "Print old material inside new"),
        )
        add_tab("models", self.Models, "Generate VMDL models", "models_import").add_overwrite_toggles(
            ("SHOULD_OVERWRITE", "Overwrite Existing VMDLs"),
            #("MOVE_MODELS", "Move .mdls"),
        )
        add_tab("particles", self.Particles, "Import particles", "particles_import").add_overwrite_toggles(
            ("OVERWRITE_PARTICLES", "Overwrite Existing Particles"),
        )
        #add_tab("maps", self.Maps, "Import VMF entities (soon)")
        add_tab("sessions", self.Sessions, "Import Source Filmmaker Sessions", "elements_import").add_overwrite_toggles(
            ("SHOULD_OVERWRITE", "Overwrite Existing Sessions"),
        )
        add_tab("scripts", self.Scripts, "Import various script files", "scripts_import").add_overwrite_toggles(
            ("OVERWRITE_SCRIPTS", "Overwrite Existing Scripts"),
        )
        add_tab("scenes", self.Scenes, "Generate vcdlist from vcds", "scenes_import").add_toggles(
            ("EVERYTHING_TO_ROOT", "Add everything to _root.vcdlist"),
        )
        self.tab_notebook.grid(in_=self.module_picking_grid, column=1, row=0, rowspan=len(self.tabs), columnspan=2)#.pack(expand=1, fill="both")

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
            if widget in range(30, 50): # Module title
                self.widgets[widget].configure(bg=bg1, fg ="white", font='Helvetica 11')
                continue
            if widget not in (2, 51): # Filter box is self configured
                self.widgets[widget].configure(bg=bg1, fg =fg1, highlightbackground=bg1, highlightcolor = bg1, relief=GROOVE, font='Helvetica 10 bold' if widget in (5,7) else 'Helvetica 10')
                if widget == 19: # Console has darker bg
                    self.widgets[widget].configure(bg=bg2)
            if widget in (1,4,5,7,9,10,11,12,13,14,15,16,17,50,51,53,99): # buttons
                self.widgets[widget].configure(bg=bg1,fg=fg1,activeforeground=fg1,activebackground=bg2)

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
        self.checkbutton_tab_update()

        # restore app state from last session
        self.cfg = {'app_geometry':"480x500"}
        self.geometry("480x500")
        self.read_config()
        Thread(target=self.read_default_module_options).start()


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
                self.destmod.set(sh.destmod.value)
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

    def get_filter(self):
        if len(self.filter.get()):
            filter = self.filter.get()
            if "*" not in filter:
                filter = "*" + filter  + "*"
            return filter

    def launch_importer_thread(self):
        if self.is_running:
            return
        sh.filter_ = self.get_filter()
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
        for tab in self.tabs.values():
            if tab.enabled.get():
                tab.run()
        messagebox.showinfo(title=self.APP_TITLE, message="Looks like we are done!")
        return stop()

    def overwrite_toggle_all(self):
        self.allOverwrite.set(0 if not self.allOverwrite.get() else 1)
        for tab in self.tabs.values():
            if not tab.enabled.get():
                continue
            for overwrite_opt in tab.overwrite_ones:
                tab.further_options[overwrite_opt].set(self.allOverwrite.get())

    def verify_all_overwrite(self):
        """Auto toggle Overwrite All based on status of other checkboxes"""
        for tab in self.tabs.values():
            if not tab.enabled.get():
                continue
            if self.allOverwrite.get(): # Overwrite All is toggled on!
                if not all(tab.further_options[overwrite_opt].get() for overwrite_opt in tab.overwrite_ones): # but this option is not
                    self.allOverwrite.set(0) # so deselect Overwrite All
                    break
            else: # Overwrite All is toggled off
                if not all(tab.further_options[overwrite_opt].get() for overwrite_opt in tab.overwrite_ones): # and I found an option that is not toggled
                    return # it can't be toggled on, so don't bother checking the rest
        else:
            self.allOverwrite.set(1) # all tabs are toggled on, so select Overwrite All

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
        self.verify_all_overwrite()
        if any(tab.enabled.get() for tab in self.tabs.values()):
            self.gobutton.configure(state=NORMAL)
            self.widgets[53].configure(state=NORMAL)
        else:
            self.gobutton.configure(state=DISABLED)
            self.widgets[53].configure(state=DISABLED)
            self.allOverwrite.set(0)
        for tab in self.tab_notebook.tabs():
            capitalizedTabName = self.tab_notebook.tab(tab, option="text")
            if specificTab is not None and specificTab != capitalizedTabName.lower():
                continue
            if not getattr(self, capitalizedTabName).get():
                self.tab_notebook.tab(tab, state=DISABLED)
            else:
                self.tab_notebook.tab(tab, state=NORMAL)
                if specificTab is not None or not self.tab_notebook.select():
                    self.tab_notebook.select(tab)

    def gobutton_update(self):
        if self.is_running:
            self.gobutton.configure(state=DISABLED, text='Running')
        else:
            self.gobutton.configure(state=NORMAL, text='Go')
    
    def read_default_module_options(self):
        for tab in self.tabs.values():
            module = tab.load_module()
            for option_variable_name, gui_var in tab.further_options.items():
                gui_var.set(getattr(module, option_variable_name, True))

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
        
        def _async():
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
        Thread(target=_async, daemon=True).start()

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
