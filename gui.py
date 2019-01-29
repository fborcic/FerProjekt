import Tkinter as tk
import tkFileDialog
import ttk
import csv
import os.path

from base import DepthProfileFigureCanvas, DepthProfileFigure, DepthProfile
from available_models import MODELS

class SelectFrame(tk.Frame):
    def __init__(self, objlist):
        tk.Frame.__init__(self)
        self.varobjlist = []
        for obj in objlist:
            name = obj.PRESENTABLE_NAME
            var = tk.IntVar()
            cbox = tk.Checkbutton(self, text=name, variable=var)
            cbox.pack(anchor='w')
            self.varobjlist.append((obj, var))

    def get_selected(self):
        out = []
        for obj, var in self.varobjlist:
            if var.get():
                out.append(obj)
        return out

class DecoApp(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)

        self.title("Deco model tester")
        self.prof_fig = DepthProfileFigure([])

        self.file_list = tk.Listbox(self)
        self.add_button = tk.Button(self, command=self.add_file, text="Add Profile")
        self.remove_button = tk.Button(self, command=self.remove_file, text="Remove Profile")
        self.run_button = tk.Button(self, command=self.run, text="Run Calculations", state=tk.DISABLED)
        self.exit_button = tk.Button(self, command=self.destroy, text="Exit")

        self.graph = DepthProfileFigureCanvas(self, self.prof_fig)
        self.cb_frame = SelectFrame(MODELS)
        
        self.textarea = tk.Text(self, background='#EEEEEE', state=tk.NORMAL, 
                                relief=tk.SUNKEN, borderwidth=2, height=10)
        self.textarea.insert(tk.END, 'Load profiles to begin\n')

        self.file_list.grid(column=0, row=0, columnspan=2, rowspan=2, sticky='nswe')
        self.add_button.grid(column=0, row=2, columnspan=1, rowspan=1, sticky='nswe')
        self.remove_button.grid(column=1, row=2, columnspan=1, rowspan=1, sticky='nswe')
        self.run_button.grid(column=0, row=3, columnspan=1, rowspan=1, sticky='nswe')
        self.exit_button.grid(column=1, row=3, columnspan=1, rowspan=1, sticky='nswe')

        self.graph.grid(column=2, row=0, columnspan=2, rowspan=4)
        self.cb_frame.grid(column=0, row=4, columnspan=2, rowspan=1)
        
        self.textarea.grid(column=2, row=4, columnspan=2, rowspan=1)

        self.grid_rowconfigure(4, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(2, weight=1)
        self.grid_columnconfigure(3, weight=1)

        self.profiles = {}

    def add_file(self):
        filename = tkFileDialog.askopenfilename(title="Select file")
        if filename is None:
            return

        self.run_button.configure(state=tk.NORMAL)
        name = str(len(self.profiles))+': '+os.path.basename(filename)
        with open(filename) as f:
            text = f.read()
        lines = text.strip().split('\n')
        pairs = [l.split(',') for l in lines]
        samples = [(float(time.strip()), float(depth.strip())) for time, depth in pairs]
        profile = DepthProfile(samples, label=name)
        self._add_profile(name, profile)

    def _add_profile(self, name, profile):
        self.profiles[name] = profile
        self.prof_fig.add_profile(profile)
        self.graph.redraw()
        self.file_list.insert(tk.END, name)

    def _remove_profile(self, sel_name):
        profile = self.profiles[sel_name]
        self.prof_fig.rm_profile(profile)
        del self.profiles[sel_name]
        self.graph.redraw()

    def remove_file(self):
        try:
            sel_index = int(self.file_list.curselection()[0])
        except IndexError:
            return
        sel_name = self.file_list.get(sel_index)
        self.file_list.delete(sel_index)
        self._remove_profile(sel_name)

    def run(self):
        deco_methods = self.cb_frame.get_selected()
        if not deco_methods:
            self.textarea.insert(tk.END, 'Please select some calculation methods\n')
            return
        for btn in self.add_button, self.remove_button, self.run_button:
            btn.configure(state=tk.DISABLED)
        self.file_list.delete(0, tk.END)

        in_profiles = self.profiles.keys()
        for profile_name in in_profiles:
            for method in deco_methods:
                new_profile = self.profiles[profile_name].duplicate()
                new_profile.label += ' (%s)'%method.PRESENTABLE_NAME
                deco = method(new_profile)
                deco.append_deco()
                self.textarea.insert(tk.END, deco.report())
                self._add_profile(new_profile.label, new_profile)
            self._remove_profile(profile_name)


app = DecoApp()
app.mainloop()


