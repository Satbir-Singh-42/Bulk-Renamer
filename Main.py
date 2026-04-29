import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText
from pathlib import Path
import shutil
import re
import os
from PIL import Image, ImageTk

class FileRenamerPro(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Bulk Renamer")
        self.geometry("1100x700")               # Wider for preview panel
        self.current_folder = None
        self.file_objects = []
        self.overwrite_all = None
        self.current_preview_image = None       # keep reference to PhotoImage
        self.setup_ui()
        self.setup_bindings()
        self.set_default_values()

    def set_default_values(self):
        self.base_entry.insert(0, "")
        self.start_spin.set(1)
        self.padding_combo.current(1)           # "01"
        self.suffix_entry.insert(0, "")

    def setup_ui(self):
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Folder selection (unchanged)
        folder_frame = ttk.LabelFrame(main_frame, text="Folder Selection")
        folder_frame.pack(fill=tk.X, pady=5)

        self.btn_folder = ttk.Button(folder_frame, text="Select Folder", command=self.load_folder)
        self.btn_folder.pack(side=tk.LEFT, padx=5)
        self.btn_clear_folder = ttk.Button(folder_frame, text="Clear Folder", command=self.clear_folder)
        self.btn_clear_folder.pack(side=tk.LEFT, padx=5)
        self.lbl_folder = ttk.Label(folder_frame, text="No folder selected")
        self.lbl_folder.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Naming options (unchanged)
        options_frame = ttk.LabelFrame(main_frame, text="Naming Options")
        options_frame.pack(fill=tk.X, pady=5)

        ttk.Label(options_frame, text="Base Name:").grid(row=0, column=0, sticky=tk.W)
        self.base_entry = ttk.Entry(options_frame)
        self.base_entry.grid(row=0, column=1, padx=5, sticky=tk.EW)

        ttk.Label(options_frame, text="Start Number:").grid(row=0, column=2, sticky=tk.W)
        self.start_spin = ttk.Spinbox(options_frame, from_=1, to=9999, width=5, validate="key",
                                    validatecommand=(self.register(self.validate_number), '%P'))
        self.start_spin.grid(row=0, column=3, padx=5)

        ttk.Label(options_frame, text="Padding:").grid(row=0, column=4, sticky=tk.W)
        self.padding_combo = ttk.Combobox(options_frame, values=["1", "01", "001", "0001"], width=5)
        self.padding_combo.grid(row=0, column=5, padx=5)

        ttk.Label(options_frame, text="Text After Number:").grid(row=1, column=0, sticky=tk.W)
        self.suffix_entry = ttk.Entry(options_frame)
        self.suffix_entry.grid(row=1, column=1, columnspan=5, padx=5, sticky=tk.EW)

        options_frame.grid_columnconfigure(1, weight=1)

        # ---- Main area: file list + preview panel (PanedWindow) ----
        paned = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, pady=5)

        # Left: file list frame
        list_frame = ttk.LabelFrame(paned, text="Files (Drag to Reorder)")
        paned.add(list_frame, weight=2)

        self.file_list = tk.Listbox(list_frame, selectmode=tk.SINGLE, activestyle="none")
        self.file_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.file_list.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.file_list.config(yscrollcommand=scrollbar.set)

        # Right: preview panel
        preview_container = ttk.LabelFrame(paned, text="Preview")
        paned.add(preview_container, weight=1)

        # Canvas for image preview
        self.preview_canvas = tk.Canvas(preview_container, bg="#f0f0f0", height=200, relief=tk.SUNKEN)
        self.preview_canvas.pack(fill=tk.X, padx=5, pady=5)

        # Label for text info (folder contents, metadata, errors)
        self.preview_info = tk.Text(preview_container, wrap=tk.WORD, height=10, font=("TkFixedFont", 9))
        self.preview_info.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        scroll_info = ttk.Scrollbar(preview_container, orient=tk.VERTICAL, command=self.preview_info.yview)
        scroll_info.pack(side=tk.RIGHT, fill=tk.Y)
        self.preview_info.config(yscrollcommand=scroll_info.set)
        # ----------

        # Preview of new names (unchanged, but below PanedWindow)
        preview_frame = ttk.LabelFrame(main_frame, text="Rename Preview")
        preview_frame.pack(fill=tk.X, pady=5)

        text_frame = ttk.Frame(preview_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)

        self.preview_text = tk.Text(text_frame, height=4, wrap=tk.NONE)
        self.preview_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        v_scroll = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.preview_text.yview)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        h_scroll = ttk.Scrollbar(preview_frame, orient=tk.HORIZONTAL, command=self.preview_text.xview)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.preview_text.config(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

        # Status bar
        self.status_label = ttk.Label(main_frame, foreground="red")
        self.status_label.pack(pady=5)

        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=5)

        self.btn_rename = ttk.Button(btn_frame, text="Rename Files", command=self.rename_files)
        self.btn_rename.pack(side=tk.LEFT, padx=5)
        self.btn_refresh = ttk.Button(btn_frame, text="Refresh List", command=self.refresh_file_list)
        self.btn_refresh.pack(side=tk.LEFT, padx=5)
        self.btn_clear = ttk.Button(btn_frame, text="Clear All", command=self.reset_app)
        self.btn_clear.pack(side=tk.RIGHT, padx=5)

    def setup_bindings(self):
        self.file_list.bind("<Button-1>", self.start_drag)
        self.file_list.bind("<B1-Motion>", self.on_drag)
        self.file_list.bind("<<ListboxSelect>>", self.on_file_select)
        for entry in [self.base_entry, self.start_spin, self.padding_combo, self.suffix_entry]:
            entry.bind("<KeyRelease>", lambda e: self.update_preview())

    # -----------------------------------------------------------------
    # Existing methods (validators, drag&drop, generate names, etc.)
    # -----------------------------------------------------------------
    def validate_number(self, value):
        if value == "" or value.isdigit():
            self.clear_status()
            return True
        self.show_status("Only numbers allowed in start field!")
        return False

    def show_status(self, message):
        self.status_label.config(text=message)
        self.after(5000, self.clear_status)

    def clear_status(self):
        self.status_label.config(text="")

    def natural_sort_key(self, s):
        return [int(text) if text.isdigit() else text.lower()
                for text in re.split(r"(\d+)", str(s))]

    def load_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.current_folder = Path(folder)
            self.refresh_file_list()

    def refresh_file_list(self):
        if self.current_folder:
            try:
                self.file_objects = sorted(self.current_folder.iterdir(),
                                           key=lambda x: self.natural_sort_key(x.name))
                self.lbl_folder.config(text=str(self.current_folder))
                self.update_file_list()
            except PermissionError:
                self.show_status("Permission denied to access folder!")

    def clear_folder(self):
        self.current_folder = None
        self.file_objects = []
        self.lbl_folder.config(text="No folder selected")
        self.file_list.delete(0, tk.END)
        self.update_preview()
        self.clear_preview()

    def update_file_list(self):
        self.file_list.delete(0, tk.END)
        for f in self.file_objects:
            self.file_list.insert(tk.END, f.name)
        self.update_preview()

    def start_drag(self, event):
        self.drag_index = self.file_list.nearest(event.y)
        self.file_list.selection_clear(0, tk.END)
        self.file_list.selection_set(self.drag_index)

    def on_drag(self, event):
        new_index = self.file_list.nearest(event.y)
        if new_index != self.drag_index and 0 <= new_index < self.file_list.size():
            item = self.file_list.get(self.drag_index)
            self.file_list.delete(self.drag_index)
            self.file_list.insert(new_index, item)

            obj = self.file_objects.pop(self.drag_index)
            self.file_objects.insert(new_index, obj)

            self.drag_index = new_index
            self.file_list.selection_set(new_index)
            self.update_preview()

    def generate_new_name(self, index, path):
        base = self.base_entry.get().strip()
        padding_str = self.padding_combo.get()
        width = len(padding_str)
        start_num = int(self.start_spin.get() or 1)
        suffix = self.suffix_entry.get().strip()
        number = start_num + index
        formatted_num = f"{number:0{width}d}"
        return f"{base}{formatted_num}{suffix}{path.suffix}"

    def update_preview(self):
        self.preview_text.config(state=tk.NORMAL)
        self.preview_text.delete(1.0, tk.END)

        previews = []
        for i, path in enumerate(self.file_objects):
            new_name = self.generate_new_name(i, path)
            previews.append(f"{path.name} → {new_name}")

        new_names = [p.split(" → ")[1] for p in previews]
        duplicates = {name for name in new_names if new_names.count(name) > 1}

        for line in previews:
            if line.split(" → ")[1] in duplicates:
                self.preview_text.insert(tk.END, line + " ⚠\n", "warning")
            else:
                self.preview_text.insert(tk.END, line + "\n")

        self.preview_text.tag_config("warning", foreground="red")
        self.preview_text.see("1.0")
        self.preview_text.config(state=tk.DISABLED)

    # -----------------------------------------------------------------
    # NEW: Preview panel (image / folder / info)
    # -----------------------------------------------------------------
    def on_file_select(self, event):
        """Called when an item in the listbox is selected."""
        sel = self.file_list.curselection()
        if not sel:
            return
        index = sel[0]
        path = self.file_objects[index]
        self.show_preview(path)

    def show_preview(self, path):
        """Display preview based on file/directory type."""
        # Clear previous content
        self.preview_canvas.delete("all")
        self.preview_info.config(state=tk.NORMAL)
        self.preview_info.delete(1.0, tk.END)

        # 1. Directory preview
        if path.is_dir():
            self.preview_info.insert(tk.END, f"📁 FOLDER: {path.name}\n\n")
            try:
                items = list(path.iterdir())
                if not items:
                    self.preview_info.insert(tk.END, "(empty folder)")
                else:
                    for i, item in enumerate(items[:10]):
                        self.preview_info.insert(tk.END, f"• {item.name}\n")
                    if len(items) > 10:
                        self.preview_info.insert(tk.END, f"... and {len(items)-10} more")
            except PermissionError:
                self.preview_info.insert(tk.END, "Permission denied reading folder")
            self.preview_info.config(state=tk.DISABLED)
            return

        # 2. Image preview
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}
        if path.suffix.lower() in image_extensions:
            try:
                img = Image.open(path)
                # Resize to fit canvas (max 200x200)
                img.thumbnail((200, 200), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self.preview_canvas.create_image(100, 100, image=photo, anchor="center")
                self.current_preview_image = photo   # keep reference
                # show metadata
                info_text = (f"🖼️ IMAGE: {path.name}\n"
                             f"Dimensions: {img.width} × {img.height}\n"
                             f"Size: {path.stat().st_size:,} bytes")
                self.preview_info.insert(tk.END, info_text)
            except Exception as e:
                self.preview_info.insert(tk.END, f"Error loading image:\n{str(e)}")
            self.preview_info.config(state=tk.DISABLED)
            return

        # 3. Other files: show basic metadata
        try:
            stat = path.stat()
            info = (f"📄 FILE: {path.name}\n"
                    f"Type: {path.suffix or 'no extension'}\n"
                    f"Size: {stat.st_size:,} bytes\n"
                    f"Modified: {tk.Label().tk.call('clock', 'format', stat.st_mtime)}")
            self.preview_info.insert(tk.END, info)
        except Exception as e:
            self.preview_info.insert(tk.END, f"Cannot read file info:\n{str(e)}")
        self.preview_info.config(state=tk.DISABLED)

    def clear_preview(self):
        """Clear both canvas and text info."""
        self.preview_canvas.delete("all")
        self.preview_info.config(state=tk.NORMAL)
        self.preview_info.delete(1.0, tk.END)
        self.preview_info.insert(tk.END, "Select a file or folder to preview")
        self.preview_info.config(state=tk.DISABLED)
        self.current_preview_image = None

    # -----------------------------------------------------------------
    # Rename logic (with all previous fixes)
    # -----------------------------------------------------------------
    def rename_files(self):
        if not self.file_objects:
            self.show_status("No files selected!")
            return

        if len(self.file_objects) > 10:
            if not messagebox.askyesno("Confirm Rename",
                                       f"Are you sure you want to rename {len(self.file_objects)} files?"):
                return

        try:
            start_num = int(self.start_spin.get())
        except ValueError:
            self.show_status("Invalid start number! Using 1")
            start_num = 1
            self.start_spin.set(1)

        self.overwrite_all = None
        processed = 0
        errors = []
        cancel_operation = False

        for i, path in enumerate(self.file_objects):
            if cancel_operation:
                break

            new_name = self.generate_new_name(i, path)
            new_path = path.parent / new_name

            if new_path == path:
                continue

            if new_path.exists():
                if self.overwrite_all is None:
                    response = self.ask_overwrite(new_name)
                    if response == "cancel":
                        cancel_operation = True
                        continue
                    elif response == "no":
                        continue
                    elif response == "noall":
                        self.overwrite_all = False
                        continue
                    elif response == "yes":
                        pass
                    elif response == "yesall":
                        self.overwrite_all = True
                elif not self.overwrite_all:
                    continue

            try:
                shutil.move(str(path), str(new_path))
                processed += 1
            except Exception as e:
                errors.append(f"{path.name}: {str(e)}")

        if errors:
            self.show_error_dialog(errors)

        if processed > 0 and not cancel_operation:
            self.refresh_file_list()
            self.show_status(f"Successfully processed {processed} files")
        elif cancel_operation:
            self.show_status("Operation cancelled by user")

    def show_error_dialog(self, errors):
        dialog = tk.Toplevel(self)
        dialog.title("Processing Errors")
        dialog.geometry("600x400")

        wrapper = ttk.Frame(dialog)
        wrapper.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        lbl = ttk.Label(wrapper, text=f"Encountered {len(errors)} errors:")
        lbl.pack(anchor=tk.W)

        txt = ScrolledText(wrapper, wrap=tk.WORD, width=70, height=15)
        txt.pack(fill=tk.BOTH, expand=True)

        error_sample = "\n".join(errors[:20])
        if len(errors) > 20:
            error_sample += f"\n\n...and {len(errors)-20} more errors..."
        txt.insert(tk.END, error_sample)
        txt.config(state=tk.DISABLED)

        btn = ttk.Button(wrapper, text="OK", command=dialog.destroy)
        btn.pack(pady=5)

    def ask_overwrite(self, filename):
        dialog = tk.Toplevel(self)
        dialog.title("Overwrite File?")
        dialog.transient(self)
        dialog.grab_set()

        msg = ttk.Label(dialog, text=f"File '{filename}' already exists. Overwrite?")
        msg.pack(padx=20, pady=10)

        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=10)

        response = {"answer": "no"}

        def set_response(answer):
            response["answer"] = answer
            dialog.destroy()

        ttk.Button(btn_frame, text="Yes", command=lambda: set_response("yes")).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Yes to All", command=lambda: set_response("yesall")).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="No", command=lambda: set_response("no")).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="No to All", command=lambda: set_response("noall")).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=lambda: set_response("cancel")).pack(side=tk.LEFT, padx=5)

        dialog.wait_window()
        return response["answer"]

    def reset_app(self):
        self.clear_folder()
        self.base_entry.delete(0, tk.END)
        self.start_spin.set(1)
        self.padding_combo.current(1)
        self.suffix_entry.delete(0, tk.END)
        self.preview_text.config(state=tk.NORMAL)
        self.preview_text.delete(1.0, tk.END)
        self.preview_text.config(state=tk.DISABLED)
        self.clear_status()


if __name__ == "__main__":
    app = FileRenamerPro()
    app.mainloop()