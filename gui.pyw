import tkinter
from io import BytesIO
from tkinter import Grid, Menu, W
from tkinter import filedialog as fd
from tkinter import ttk

import sv_ttk
from PIL import Image, ImageTk

from dds import *
from texture_functions import *
from Images import Error_Texture, icon
from utils.xfbin_lib.xfbin.structure.nut import Pixel_Formats
from xfbin_functions import *


class App(tkinter.Tk):
    def __init__(self):
        super().__init__()

        self.title("XFBIN Texture Editor")
        self.geometry("1000x600")
        self.iconphoto(True, tkinter.PhotoImage(data=icon))

        # self.iconbitmap("icon.ico")
        sv_ttk.set_theme('dark')

        # window frame
        self.window = ttk.Frame(self)
        self.window.pack(fill=tkinter.BOTH, expand=True)

        # Main Window Grid Configuration
        Grid.grid_columnconfigure(self.window, index=0, weight=1)
        Grid.grid_columnconfigure(self.window, index=1, weight=1)
        Grid.grid_columnconfigure(self.window, index=2, weight=1)

        Grid.grid_rowconfigure(self.window, index=0, weight=1)
        Grid.grid_rowconfigure(self.window, index=1, weight=3)
        Grid.grid_rowconfigure(self.window, index=2, weight=1)
        Grid.grid_rowconfigure(self.window, index=3, weight=1)

        # Upper Buttons and frame
        self.upper_frame1 = ttk.Frame(
            master=self.window, width=275, height=50,)
        self.upper_frame1.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        self.import_xfbin = ttk.Button(self.upper_frame1, text="Import XFBIN",
                                       width=10, command=self.open_xfbin)
        self.import_xfbin.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        self.export_xfbin = ttk.Button(self.upper_frame1, text="Export XFBIN",
                                       width=10, command=self.export_xfbin)
        self.export_xfbin.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

        self.upper_frame2 = ttk.Frame(
            master=self.window, width=275, height=50,)
        self.upper_frame2.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

        self.import_texture = ttk.Menubutton(self.upper_frame2, text="Import Texture",
                                             width=10)
        self.import_texture.grid(
            row=0, column=0, sticky="nsew", padx=5, pady=5)

        self.import_texture.menu = Menu(self.import_texture, tearoff=0)
        self.import_texture["menu"] = self.import_texture.menu
        self.import_texture.menu.add_command(
            label="Import as NUT", command=self.import_texture_nut)
        self.import_texture.menu.add_command(
            label="Import as DDS (Binary)", command=self.import_texture_dds)
        self.import_texture.menu.add_command(
            label="Import as PNG (Binary)", command=self.import_texture_png)

        self.export_texture = ttk.Menubutton(self.upper_frame2, text="Export Texture",
                                             width=10)
        self.export_texture.grid(
            row=0, column=1, sticky="nsew", padx=5, pady=5)
        self.export_texture.menu = Menu(self.export_texture, tearoff=0)
        self.export_texture['menu'] = self.export_texture.menu
        self.export_texture.menu.add_command(
            label="Export as NUT", command=self.export_nut)
        self.export_texture.menu.add_command(
            label="Export as DDS", command=self.export_dds)
        self.export_texture.menu.add_command(
            label="Export as PNG", command=self.export_png)

        # configure the grid in the upper frame
        Grid.grid_columnconfigure(self.upper_frame1, index=0, weight=1)
        Grid.grid_columnconfigure(self.upper_frame1, index=1, weight=1)
        Grid.grid_rowconfigure(self.upper_frame1, index=0, weight=1)

        Grid.grid_columnconfigure(self.upper_frame2, index=0, weight=1)
        Grid.grid_columnconfigure(self.upper_frame2, index=1, weight=1)
        Grid.grid_rowconfigure(self.upper_frame2, index=0, weight=1)
        # -----------------------------------------------------------------------------------------------------------------------

        # Xfbin and textures lists
        self.lists_frame = ttk.Frame(
            master=self.window, width=550, height=350)  # corner_radius=10,)
        self.lists_frame.grid(row=1, column=0, sticky="nsew",
                              padx=5, pady=5, columnspan=2)

        # treeview
        self.xfbin_list = ttk.Treeview(
            master=self.lists_frame, height=1, selectmode="extended")
        #self.xfbin_list.grid(row=0, column=0, sticky='nsew', padx=5, pady=5)
        self.xfbin_list.pack(side=tkinter.LEFT, fill=tkinter.BOTH, expand=True)
        self.xfbin_list.heading("#0", text="XFBIN Name")
        self.xfbin_list.column("#0", anchor=W, width=100)
        self.xfbin_list.bind("<<TreeviewSelect>>", self.update_texture_chunks)

        # treeview
        self.textures_list = ttk.Treeview(
            master=self.lists_frame, height=14, columns=("Count"), selectmode="extended")
        #self.textures_list.grid(row=0, column=1, sticky='nsew', padx=5, pady=5)
        self.textures_list.pack(
            side=tkinter.LEFT, fill=tkinter.BOTH, expand=True)
        self.textures_list.heading("#0", text="Texture Name")
        self.textures_list.column("#0", anchor='w', width=200)
        self.textures_list.heading("Count", text="Count")
        self.textures_list.column("Count", anchor='w', width=10, minwidth=10)
        self.textures_list.bind("<<TreeviewSelect>>", self.update_name_path)

        # configure the grid in the lists frame
        Grid.grid_columnconfigure(self.lists_frame, index=0, weight=1)
        Grid.grid_columnconfigure(self.lists_frame, index=1, weight=1)
        Grid.grid_rowconfigure(self.lists_frame, index=1, weight=1)
        # -----------------------------------------------------------------------------------------------------------------------

        self.texture_preview_frame = ttk.LabelFrame(
            master=self.window, width=350, height=350, text="Texture Preview")
        self.texture_preview_frame.grid(
            row=1, column=2, sticky='nsew', padx=5, pady=5)

        self.texture_preview = ttk.Label(
            master=self.texture_preview_frame, text='')
        self.texture_preview.place(relx=0.5, rely=0.49, anchor=tkinter.CENTER)

        # -----------------------------------------------------------------------------------------------------------------------

        # Texture info frame
        self.texture_info_frame = ttk.LabelFrame(
            master=self.window, width=350, height=100, text="Texture Info")
        self.texture_info_frame.grid(
            row=2, column=2, sticky='nsew', padx=5, pady=5, rowspan=2)

        # texture variables
        self.size_var = tkinter.StringVar(value="Size: ")
        self.type_var = tkinter.StringVar(value="Type: ")
        self.pixel_format_var = tkinter.StringVar(value="Pixel Format: ")
        self.mipmap_count_var = tkinter.StringVar(value="Mipmap Count: ")

        self.height_label = ttk.Label(
            master=self.texture_info_frame, textvariable=self.size_var, anchor="center")
        # update height when texture is selected
        self.height_label.grid(row=1, column=0, sticky='nsew', padx=3, pady=3)

        self.width_label = ttk.Label(
            master=self.texture_info_frame, textvariable=self.type_var, anchor="center")
        self.width_label.grid(row=1, column=1, sticky='nsew', padx=3, pady=3)

        self.pixel_format_label = ttk.Label(
            master=self.texture_info_frame, textvariable=self.pixel_format_var, anchor="center")
        self.pixel_format_label.grid(
            row=2, column=0, sticky='nsew', padx=3, pady=3)

        self.mipmap_count_label = ttk.Label(
            master=self.texture_info_frame, textvariable=self.mipmap_count_var, anchor="center")
        self.mipmap_count_label.grid(
            row=2, column=1, sticky='nsew', padx=3, pady=3)

        # configure the grid in the texture info frame
        Grid.grid_columnconfigure(self.texture_info_frame, index=0, weight=1)
        Grid.grid_columnconfigure(self.texture_info_frame, index=1, weight=1)
        Grid.grid_rowconfigure(self.texture_info_frame, index=0, weight=1)
        Grid.grid_rowconfigure(self.texture_info_frame, index=1, weight=1)
        Grid.grid_rowconfigure(self.texture_info_frame, index=2, weight=1)
        # -----------------------------------------------------------------------------------------------------------------------
        # lower buttons
        self.lower_buttons_frame1 = ttk.Frame(
            master=self.window, width=275, height=50,)
        self.lower_buttons_frame1.grid(
            row=2, column=0, sticky='nsew', padx=5, pady=5)

        self.remove_xfbin = ttk.Button(self.lower_buttons_frame1, text="Remove XFBIN",
                                       width=10, command=self.remove_xfbin)
        self.remove_xfbin.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        self.lower_buttons_frame2 = ttk.Frame(
            master=self.window, width=275, height=50,)
        self.lower_buttons_frame2.grid(
            row=2, column=1, sticky='nsew', padx=5, pady=5)

        self.copy_texture = ttk.Button(self.lower_buttons_frame2, text="Copy Texture",
                                       width=10, command=self.copy_tex)
        self.copy_texture.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        self.paste_texture = ttk.Button(self.lower_buttons_frame2, text="Paste Texture",
                                        width=10, command=self.paste_tex)
        self.paste_texture.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

        self.remove_texture = ttk.Button(self.lower_buttons_frame1, text="Remove Texture",
                                         width=10, command=self.remove_nut_texture)
        self.remove_texture.grid(
            row=0, column=1, sticky="nsew", padx=5, pady=5)

        # configure the grid in the lower buttons frame
        Grid.grid_columnconfigure(self.lower_buttons_frame1, index=0, weight=1)
        Grid.grid_columnconfigure(self.lower_buttons_frame1, index=1, weight=1)
        Grid.grid_rowconfigure(self.lower_buttons_frame1, index=0, weight=1)

        Grid.grid_columnconfigure(self.lower_buttons_frame2, index=0, weight=1)
        Grid.grid_columnconfigure(self.lower_buttons_frame2, index=1, weight=1)
        Grid.grid_rowconfigure(self.lower_buttons_frame2, index=0, weight=1)
        # -----------------------------------------------------------------------------------------------------------------------
        # Name and path frame
        self.lower_frame = ttk.Frame(master=self.window, width=550, height=50)
        self.lower_frame.grid(row=3, column=0, sticky='nsew',
                              padx=5, pady=5, columnspan=2)

        self.texture_name = ttk.Entry(master=self.lower_frame, width=15)
        self.texture_name.grid(row=0, column=0, sticky='nsew', padx=5, pady=5)
        self.texture_name.insert(0, "Texture Name")

        self.texture_path = ttk.Entry(master=self.lower_frame, width=30)
        self.texture_path.grid(row=0, column=1, sticky='nsew', padx=5, pady=5)
        self.texture_path.insert(0, "Texture Path")

        self.apply_button = ttk.Button(self.lower_frame, text="Apply",
                                       width=10, style="Accent.TButton", command=self.apply_name_path)
        self.apply_button.grid(row=0, column=2, sticky='nsew', padx=5, pady=5)

        # configure the grid in the lower frame
        Grid.grid_columnconfigure(self.lower_frame, index=0, weight=1)
        Grid.grid_columnconfigure(self.lower_frame, index=1, weight=1)
        Grid.grid_columnconfigure(self.lower_frame, index=2, weight=1)
        Grid.grid_rowconfigure(self.lower_frame, index=0, weight=1)
        # -----------------------------------------------------------------------------------------------------------------------
        # right click menus

        self.nut_menu = Menu(self.window, tearoff=0)
        self.nut_menu.add_command(
            label="Copy NUT Texture", command=self.copy_tex)
        self.nut_menu.add_command(
            label="Paste NUT Texture", command=self.paste_tex)
        self.nut_menu.add_command(
            label="Add Textures", command=self.add_texture)
        self.nut_menu.add_command(
            label= "Collapse All", command= self.collapse_all)
        self.nut_menu.add_command(
            label= "Expand All", command= self.expand_all)
        

        self.texture_menu = Menu(self.window, tearoff=0)
        self.texture_menu.add_command(
            label="Replace Texture (DDS)", command=self.replace_dds_texture)
        self.texture_menu.add_command(
            label="Replace Texture (PNG)", command=self.replace_png_texture)
        self.texture_menu.add_command(
            label="Remove Texture", command=self.remove_texture_)
        self.texture_menu.add_command(
            label= "Collapse All", command= self.collapse_all)
        self.texture_menu.add_command(
            label= "Expand All", command= self.expand_all)
        
        self.binary_menu = Menu(self.window, tearoff=0)
        self.binary_menu.add_command(
            label="Replace Texture (Binary)", command=self.replace_binary_texture)
        self.binary_menu.add_command(
            label="Remove Texture", command=self.remove_texture_)
        self.binary_menu.add_command(
            label= "Collapse All", command= self.collapse_all)
        self.binary_menu.add_command(
            label= "Expand All", command= self.expand_all)

        self.textures_list.bind("<Button-3>", self.show_right_click_menu)

        # -----------------------------------------------------------------------------------------------------------------------

    def open_xfbin(self):
        files = fd.askopenfilenames(
            title='Select one or more XFBINs', filetypes=[("XFBIN", "*.xfbin")])
        for file in files:
            filename = file.split("/")[-1][:-6]

            xfbin = read_xfbin(file)
            if xfbin == None:
                tkinter.messagebox.showerror("Error", "Error reading XFBIN")
            else:
                xfbins.append(xfbin)
                self.xfbin_list.insert('', tkinter.END, text=filename)
                #try checking if the file has textures or not
                hastextures = xfbin.get_chunks_by_type(nucc_type='nuccChunkTexture')
                has_binary_textures = xfbin.get_chunks_by_type(nucc_type='nuccChunkBinary')

                #select the new xfbin
                self.xfbin_list.selection_set(self.xfbin_list.get_children()[-1])

                if not hastextures and not has_binary_textures:
                    tkinter.messagebox.showwarning("Warning", "XFBIN has no textures")


    def update_texture_chunks(self, event):
        selection = self.xfbin_list.selection()
        if len(selection) > 0:
            index = self.xfbin_list.index(selection[0])
            xfbin = xfbins[index]
            if len(self.textures_list.get_children()) > 0:
                # clear tree
                for child in self.textures_list.get_children():
                    self.textures_list.delete(child)

            self.get_texture_chunks(xfbin)

            if len(self.textures_list.get_children()) > 0:
                #select the first texture
                self.textures_list.selection_set(self.textures_list.get_children()[0])

    def get_texture_chunks(self, xfbin):
        textures.clear()
        textures.extend(get_textures(xfbin))
        
        for i in range(len(textures)):
            if textures[i].type == "nut":
                texture: Texture = textures[i]
                self.textures_list.insert(
                    '', tkinter.END, iid=i, text=texture.name, values=(texture.data.texture_count))
                # insert a child
                for j in range(texture.data.texture_count):
                    self.textures_list.insert(i, 'end', text=f'Texture {j+1}')
        
            elif textures[i].type == "dds":
                texture: Texture = textures[i]
                self.textures_list.insert(
                    '', tkinter.END, iid=i, text=texture.name, values=(1))
            
            elif textures[i].type == "png":
                texture: Texture = textures[i]
                self.textures_list.insert(
                    '', tkinter.END, iid=i, text=texture.name, values=(1))


    def remove_xfbin(self):
        selection = self.xfbin_list.selection()
        if len(selection) > 0:
            for i in selection[::-1]:
                index = self.xfbin_list.index(i)
                self.xfbin_list.delete(i)
                xfbins.pop(index)

        if len(self.textures_list.get_children()) > 0:
            # clear textures tree
            for child in self.textures_list.get_children():
                self.textures_list.delete(child)
        # clear name and path
        self.texture_name.delete(0, tkinter.END)
        self.texture_path.delete(0, tkinter.END)

    def update_name_path(self, event):
        selection = self.textures_list.selection()
        if len(selection) > 0:
            index = self.textures_list.index(selection[0])
            parent = self.textures_list.parent(selection[0])
            if parent == '':
                texture: Texture = textures[index]
                if texture.type == "nut":
                    # clear current name and path
                    self.texture_name.delete(0, tkinter.END)
                    self.texture_path.delete(0, tkinter.END)
                    # add new name and path
                    self.texture_name.insert(0, texture.name)
                    self.texture_path.insert(0, texture.filePath)
                    # update texture preview and info
                    self.update_texture_preview(texture)
                    self.update_text_variables(texture.data.textures[0].height, texture.data.textures[0].width, "NUT",
                                            Pixel_Formats.get(texture.data.textures[0].pixel_format), texture.data.textures[0].mipmap_count)
                    
                elif texture.type == "dds":
                    self.texture_name.delete(0, tkinter.END)
                    self.texture_path.delete(0, tkinter.END)
                    self.texture_name.insert(0, texture.name)
                    self.texture_path.insert(0, texture.filePath)
                    self.update_texture_preview(texture)
                    self.update_text_variables(texture.height, texture.width, "DDS", texture.pixel_format, texture.mipmap_count)
                elif texture.type == "png":
                    self.texture_name.delete(0, tkinter.END)
                    self.texture_path.delete(0, tkinter.END)
                    self.texture_name.insert(0, texture.name)
                    self.texture_path.insert(0, texture.filePath)
                    self.update_texture_preview(texture)
                    self.update_text_variables(texture.height, texture.width, "PNG", texture.pixel_format, texture.mipmap_count)
            else:
                texture = textures[int(parent)]
                self.update_texture_preview(texture, int(index))
                self.update_text_variables(texture.data.textures[index].height, texture.data.textures[index].width, "NUT",
                                           Pixel_Formats.get(texture.data.textures[index].pixel_format), texture.data.textures[index].mipmap_count)

    def update_text_variables(self, height, width, type, format, mipmap_count):
        self.size_var.set(f'Size: {height} x {width}')
        self.type_var.set(f'Type: {type}')
        self.pixel_format_var.set(f'Pixel Format: {format}')
        self.mipmap_count_var.set(f'Mipmaps Count: {mipmap_count}')

    def apply_name_path(self):
        active = self.textures_list.focus()
        parent = self.textures_list.parent(active)
        if parent == '':
            texture_index = self.textures_list.index(active)
            texture = textures[texture_index]

            texture.name = self.texture_name.get()
            texture.filePath = self.texture_path.get()

            self.textures_list.item(active, text=texture.name)

    def export_xfbin(self):
        #export the selected xfbin
        selection = self.xfbin_list.selection()

        if len(selection) >= 2:
            export_errors = []

            items = [self.xfbin_list.item(i) for i in selection]
            paths = fd.askdirectory(
                title='Select a location to export the XFBINs')
            if paths != '':
                for i, item in enumerate(items):
                    xfbin = xfbins[self.xfbin_list.index(selection[i])]
                    path = paths + '/' + item['text'] + '.xfbin'
                    try:
                        write_xfbin(xfbin, path)
                    except:
                        export_errors.append(item['text'])

                if len(export_errors) > 0:
                    tkinter.messagebox.showerror(
                        "Error", f"Error exporting the following XFBINs:\n{export_errors}")
                else:
                    tkinter.messagebox.showinfo(
                        "Export XFBIN", "XFBINs exported successfully!")
        elif len(selection) > 0:
            item = self.xfbin_list.item(selection[0])
            xfbin_index = self.xfbin_list.index(selection[0])
            
            path = fd.asksaveasfilename(title='Select a location to export XFBIN',
                                        filetypes=[("XFBIN", "*.xfbin")],
                                        defaultextension=".xfbin",
                                        initialfile=f"{item['text']}.xfbin")
            if path != '':
                if len(selection) > 0:
                    xfbin = xfbins[xfbin_index]
                    write_xfbin(xfbin, path)
                # show message box
                tkinter.messagebox.showinfo(
                    "Export XFBIN", "XFBIN exported successfully!")

    def export_nut(self):
        texture = self.textures_list.selection()
        selection = [i for i in self.textures_list.selection(
        ) if self.textures_list.parent(i) == '']
        if len(selection) > 0:
            path = fd.askdirectory(
                title='Select a location to export the NUT texture',)
            if path != '':
                for tex in selection:
                    texture_index = self.textures_list.index(tex)
                    texture = textures[texture_index]
                    write_nut(texture, path)
            # show message box
            tkinter.messagebox.showinfo(
                "Export NUT", "NUT exported successfully!")
        else:
            tkinter.messagebox.showerror(
                "Error", "No texture selected to export")

    def export_dds(self):
        texture = self.textures_list.selection()
        selection = [i for i in self.textures_list.selection(
        ) if self.textures_list.parent(i) == '']
        if len(selection) > 0:
            path = fd.askdirectory(
                title='Select a location to export the DDS texture')
            if path != '':
                for tex in selection:
                    texture: NuccChunkTexture = textures[self.textures_list.index(
                        tex)]
                    write_dds(texture, path)
            # show message box
            tkinter.messagebox.showinfo(
                "Export DDS", "DDS exported successfully!")
        else:
            tkinter.messagebox.showerror(
                "Error", "No texture selected to export")

    def export_png(self):
        texture = self.textures_list.selection()
        selection = [i for i in self.textures_list.selection(
        ) if self.textures_list.parent(i) == '']
        if len(selection) > 0:
            path = fd.askdirectory(
                title='Select a location to export the PNG texture',)
            if path != '':
                for tex in selection:
                    texture: Texture = textures[self.textures_list.index(
                        tex)]
                    NutTexture_to_PNG(texture, path)
            # show message box
            tkinter.messagebox.showinfo(
                "Export PNG", "PNG exported successfully!")
        else:
            tkinter.messagebox.showerror(
                "Error", "No texture selected to export")

    def copy_tex(self):
        CopiedTextures.clear()
        selection = [i for i in self.textures_list.selection()
                     if self.textures_list.parent(i) == '']

        if len(selection) > 0:
            for i in selection:
                index = self.textures_list.index(i)
                print(index)
                texture = textures[index]
                CopiedTextures.append(texture)

    
    def paste_tex(self):
        selection = self.xfbin_list.selection()
        child_count = len(self.textures_list.get_children())
        if len(selection) > 0:
            for i, tex in enumerate(CopiedTextures):
                if tex.type == "nut":
                    chunk = create_texture_chunk(copy_texture(tex))

                elif tex.type == "dds" or tex.type == "png":
                    chunk = create_binary_chunk(tex)
                # add the texture chunk to the xfbin
                index = self.xfbin_list.index(selection[0])
                xfbin = xfbins[index]
                xfbin: Xfbin
                xfbin.add_chunk_page(chunk)

                self.update_texture_chunks(None)
                # select the new texture
                self.textures_list.selection_set(
                    self.textures_list.get_children()[-1])


    def update_texture_preview(self, texture, index=0):
        if texture:
            if texture.type == "dds":
                dds = BytesIO(texture.data)
                try:
                    image = Image.open(dds)
                except:
                    ErrorTex = tkinter.PhotoImage(data=Error_Texture)
                    image = Image.open('ErrorTexture.png')
            elif texture.type == "png":
                image = Image.open(BytesIO(texture.data))

            else:
                texture_data = texture.data.textures[index]
                if texture_data.pixel_format == 8:
                    image = texture_565(texture_data.texture_data,
                                        texture_data.width, texture_data.height)
                elif texture_data.pixel_format == 6:
                    image = texture_5551(texture_data.texture_data,
                                        texture_data.width, texture_data.height)
                elif texture_data.pixel_format == 7:
                    image = texture_4444(texture_data.texture_data,
                                        texture_data.width, texture_data.height)
                    
                elif texture_data.pixel_format == 14 or texture_data.pixel_format == 17:
                    image = texture_8888(texture_data.texture_data,
                                        texture_data.width, texture_data.height)
                else:
                    dds = BytesIO(NutTexture_to_DDS(texture_data))
                    try:
                        image = Image.open(dds)
                    except:
                        ErrorTex = tkinter.PhotoImage(data=Error_Texture)
                        image = Image.open('ErrorTexture.png')

            image = image.resize((370, 370), Image.Resampling.BICUBIC)

            # convert the image to a tkinter image
            image = ImageTk.PhotoImage(image)
            self.texture_preview.configure(image=image)
            self.texture_preview.image = image  
        else:
            # clear the texture preview
            self.texture_preview.configure(image='')

    def import_texture_nut(self):
        active = self.xfbin_list.focus()
        if active == '':
            # ask the user if they want to create a new xfbin
            if tkinter.messagebox.askyesno("Import Texture", "No XFBIN is selected, would you like to create a new XFBIN?"):
                xfbin = create_xfbin()
                xfbins.append(xfbin)
                self.xfbin_list.insert(
                    '', tkinter.END, text='TempXfbin')
                # select the new xfbin
                self.xfbin_list.selection_set(
                    self.xfbin_list.get_children()[-1])

            else:
                return
        else:
            index = self.xfbin_list.index(active)
            xfbin = xfbins[index]
        '''path = fd.askopenfilename(title='Select a texture to import',
                                  filetypes=[("NUT", "*.nut")],
                                  defaultextension=".nut")'''
        paths = fd.askopenfilenames(title='Select one or more textures in the following formats: NUT, DDS, PNG',
                                    filetypes=[("Images", "*.nut *.dds *.png")])
        for path in paths:

            if path != '':
                tex_type = check_texture(path)
                filename = path.split('/')[-1]
                if tex_type == "nut":
                    texture = read_nut(path, filename[:-4])
                    chunk = create_texture_chunk(texture)
                
                elif tex_type == "dds":
                    dds = read_dds_path(path)
                    nuttex = DDS_to_NutTexture(dds)
                    nut = Nut()
                    nut.magic = b'NUT\x00'
                    nut.version = 0x100
                    nut.texture_count = 1
                    nut.textures = [nuttex]
                    texture = nut_to_texture(nut, filename[:-4])

                    chunk = create_texture_chunk(texture)
                
                elif tex_type == "png":
                    image = Image.open(path)
                    image = image.convert('RGBA')
                    dds = BytesIO()
                    image.save(dds, format='DDS')
                    dds.seek(0)
                    dds = read_dds(dds.getvalue())
                    nuttex = DDS_to_NutTexture(dds)
                    nut = Nut()
                    nut.magic = b'NUT\x00'
                    nut.version = 0x100
                    nut.texture_count = 1
                    nut.textures = [nuttex]
                    texture = nut_to_texture(nut, filename[:-4])
                    chunk = create_texture_chunk(texture)
                xfbin.add_chunk_page(chunk)
                textures.append(texture)
                self.textures_list.insert(
                    '', tkinter.END, text=texture.name, values=(texture.data.texture_count))
                
            

                # refresh the texture chunks
                self.update_texture_chunks(None)
                # select the new texture
                self.textures_list.selection_set(
                    self.textures_list.get_children()[-1])

    def import_texture_png(self):
        active = self.xfbin_list.focus()
        if active == '':
            # ask the user if they want to create a new xfbin
            if tkinter.messagebox.askyesno("Import Texture", "No XFBIN is selected, would you like to create a new XFBIN?"):
                xfbin = create_xfbin()
                xfbins.append(xfbin)
                self.xfbin_list.insert(
                    '', tkinter.END, text='TempXfbin')
                
                # select the new xfbin
                self.xfbin_list.selection_set(
                    self.xfbin_list.get_children()[-1])

            else:
                return
        else:
            index = self.xfbin_list.index(active)
            xfbin = xfbins[index]
        path = fd.askopenfilenames(title='Select 1 or more textures to import',
                                  filetypes=[("PNG", "*.png")],
                                  defaultextension=".png")
        for filepath in path:
            if filepath != '':
                with open(filepath, 'rb') as f:
                    file = f.read()
                texture = png_to_texture(file, filepath.split('/')[-1][:-4])
                chunk = create_binary_chunk(texture)
                xfbin.add_chunk_page(chunk)
                textures.append(texture)
                self.textures_list.insert(
                    '', tkinter.END, text=texture.name, values=(1))
                

                # refresh the texture chunks
                self.update_texture_chunks(None)
                # select the new texture
                self.textures_list.selection_set(
                    self.textures_list.get_children()[-1])
                
        

    def import_texture_dds(self):
        active = self.xfbin_list.focus()
        if active == '':
            # ask the user if they want to create a new xfbin
            if tkinter.messagebox.askyesno("Import Texture", "No XFBIN is selected, would you like to create a new XFBIN?"):
                xfbin = create_xfbin()
                xfbins.append(xfbin)
                self.xfbin_list.insert(
                    '', tkinter.END, text='TempXfbin')
                # select the new xfbin
                self.xfbin_list.selection_set(
                    self.xfbin_list.get_children()[-1])
            else:
                return

        else:
            index = self.xfbin_list.index(active)
            xfbin = xfbins[index]
        path = fd.askopenfilenames(title='Select 1 or more textures to import',
                                  filetypes=[("DDS", "*.dds")],
                                  defaultextension=".dds")
        for file in path:
            if file != '':
                with open(file, 'rb') as f:
                    filedata = f.read()
                texture = dds_to_texture(filedata, file.split('/')[-1][:-4])
                chunk = create_binary_chunk(texture)
                xfbin.add_chunk_page(chunk)
                textures.append(texture)
                self.textures_list.insert(
                    '', tkinter.END, text=texture.name, values=(1))
                

                # refresh the texture chunks
                self.update_texture_chunks(None)
                # select the new texture
                self.textures_list.selection_set(
                    self.textures_list.get_children()[-1])

    def show_right_click_menu(self, event):
        selection = self.textures_list.selection()
        if len(selection) > 0:
            index = self.textures_list.index(selection[0])
            parent = self.textures_list.parent(selection[0])
            if parent == '':
                if textures[index].type == "nut":
                    self.nut_menu.tk_popup(event.x_root, event.y_root)
                elif textures[index].type == "dds" or textures[index].type == "png":
                    self.binary_menu.tk_popup(event.x_root, event.y_root)        

            elif parent != '':
                self.texture_menu.tk_popup(event.x_root, event.y_root)

    def add_nut_texture(self):
        pass

    def replace_nut_texture(self):
        pass

    def remove_nut_texture(self):
        # remove the texture from the xfbin
        selection = self.textures_list.selection()
        if len(selection) > 0:
            index = self.textures_list.index(selection[0])
            texture = textures[index]
            xfbin = xfbins[self.xfbin_list.index(
                self.xfbin_list.selection()[0])]
            xfbin.remove_chunk_page(texture.chunk)
            textures.remove(texture)
            self.textures_list.delete(selection[0])

            # select the next texture
            if len(self.textures_list.get_children()) > 0:
                self.textures_list.selection_set(
                    self.textures_list.get_children()[0])
            else:
                self.texture_name.delete(0, tkinter.END)
                self.texture_path.delete(0, tkinter.END)
                self.update_texture_preview(None)
                self.update_text_variables("", "", "", "")

    def add_texture(self):
        files = fd.askopenfilenames(title='Select one or more DDS textures',
                                    filetypes=[("DDS", "*.dds")], defaultextension=".dds")
        for file in files:
            if file != '':

                dds = read_dds_path(file)

                selected = self.textures_list.selection()
                index = self.textures_list.index(selected)
                texture = textures[index]
                texture.data.texture_count += 1
                nuttex = DDS_to_NutTexture(dds)
                texture.data.textures.append(nuttex)
                self.textures_list.insert(
                    index, 'end', text=f'Texture {len(texture.data.textures)}')
                # update texture count
                self.textures_list.item(
                    index, values=(texture.data.texture_count))
        

    def replace_dds_texture(self):
        file = fd.askopenfilename(title='Select one or more DDS textures',
                                  filetypes=[("DDS", "*.dds")], defaultextension=".dds")
        if file != '':
            dds = read_dds_path(file)

            selected = self.textures_list.selection()
            parent = self.textures_list.parent(selected)
            index = self.textures_list.index(parent)
            texture = textures[index]
            texture.data.textures[self.textures_list.index(
                selected)] = DDS_to_NutTexture(dds)
            self.update_texture_preview(texture, self.textures_list.index(selected))
            self.update_name_path(None)
            self.update_text_variables(dds.header.height, dds.header.width, "NUT", texture.data.textures[self.textures_list.index(
                selected)].pixel_format, dds.header.mipMapCount)
        print('done')
    
    def replace_png_texture(self):
        file = fd.askopenfilename(title='Select one or more PNG textures',
                                  filetypes=[("PNG", "*.png")], defaultextension=".png")
        if file != '':
            image = Image.open(file)
            image = image.convert('RGBA')
            dds = BytesIO()
            image.save(dds, format='DDS')
            dds.seek(0)
            dds = read_dds(dds.getvalue())
            selected = self.textures_list.selection()
            parent = self.textures_list.parent(selected)
            index = self.textures_list.index(parent)
            texture = textures[index]
            texture.data.textures[self.textures_list.index(
                selected)] = DDS_to_NutTexture(dds)
            self.update_texture_preview(texture, self.textures_list.index(selected))
            self.update_name_path(None)
            self.update_text_variables(dds.header.height, dds.header.width, "NUT", texture.data.textures[self.textures_list.index(
                selected)].pixel_format, dds.header.mipMapCount)
        print('done')
    

    def replace_binary_texture(self):
        file = fd.askopenfilename(title='Select one or more textures',
                                  filetypes=[("Image", "*.dds *.png")])
        if file != '':
            with open(file, 'rb') as f:
                filedata = f.read()
            filetype = check_texture(file)

            if filetype == "dds":   
                new_texture = dds_to_texture(filedata, file.split('/')[-1][:-4])
            elif filetype == "png":
                new_texture = png_to_texture(filedata, file.split('/')[-1][:-4])
            selected = self.textures_list.selection()
            parent = self.textures_list.parent(selected)
            index = self.textures_list.index(parent)
            old_texture = textures[index]

            new_texture.filePath = old_texture.filePath
            new_texture.name = old_texture.name

            chunk = create_binary_chunk(new_texture)
            new_texture.chunk = chunk
            

            xfbin = xfbins[self.xfbin_list.index(
                self.xfbin_list.selection()[0])]
            xfbin.remove_chunk_page(old_texture.chunk)
            xfbin.add_chunk_page(chunk)
            textures.remove(old_texture)
            textures.append(new_texture)
            self.update_texture_chunks(None)
            


    def remove_texture_(self):
        selected = self.textures_list.selection()
        print(selected)
        if len(selected) > 0:
            for i in selected[::-1]:
                parent = self.textures_list.parent(i)
                index = self.textures_list.index(parent)
                texture = textures[index]
                texture.data.textures.pop(self.textures_list.index(i))
                texture.data.texture_count -= 1
                self.textures_list.delete(i)

            self.textures_list.item(index, values=(texture.data.texture_count))
            print('done')
    
    def collapse_all(self):
        for i in self.textures_list.get_children():
            self.textures_list.item(i, open=False)
    
    def expand_all(self):
        for i in self.textures_list.get_children():
            self.textures_list.item(i, open=True)


if __name__ == "__main__":
    app = App()
    app.mainloop()
