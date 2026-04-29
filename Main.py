import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText
from pathlib import Path
import shutil
import re
from datetime import datetime
from PIL import Image, ImageTk

class FileRenamerPro(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("File Renamer Pro")
        self.geometry("1300x800")
        self.current_folder = None
        self.file_objects = []          # list of Path objects
        self.file_vars = []             # list of BooleanVar for checkboxes
        self.overwrite_all = None
        self.current_preview_image = None
        self.sort_column = "name"
        self.sort_reverse = False
        self.setup_ui()
        self.setup_bindings()
        self.set_default_values()

    def set_default_values(self):
        self.base_entry.delete(0, tk.END)
        self.base_entry.insert(0, "")
        self.start_spin.set(1)
        self.padding_combo.current(1)   # "01"
        self.suffix_entry.delete(0, tk.END)
        self.suffix_entry.insert(0, "")
        self.case_combo.current(0)      # "Keep original"
        self.apply_ext_var.set(True)

    def setup_ui(self):
        # ---- Main vertical PanedWindow (top + bottom) ----
        main_vpaned = ttk.PanedWindow(self, orient=tk.VERTICAL)
        main_vpaned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # ========== TOP PART: File list (left) + Naming options & preview (right) ==========
        top_paned = ttk.PanedWindow(main_vpaned, orient=tk.HORIZONTAL)
        main_vpaned.add(top_paned, weight=3)

        # ----- LEFT: File list with metadata + reorder buttons -----
        left_container = ttk.Frame(top_paned)
        top_paned.add(left_container, weight=2)

        file_frame = ttk.LabelFrame(left_container, text="Files (click to preview)")
        file_frame.pack(fill=tk.BOTH, expand=True)

        # Treeview with checkboxes
        columns = ("select", "name", "type", "modified", "size")
        self.file_tree = ttk.Treeview(file_frame, columns=columns, show="headings", height=20)
        self.file_tree.heading("select", text="✓", command=lambda: self.toggle_all())
        self.file_tree.heading("name", text="Name", command=lambda: self.sort_by_column("name"))
        self.file_tree.heading("type", text="Type", command=lambda: self.sort_by_column("type"))
        self.file_tree.heading("modified", text="Modified", command=lambda: self.sort_by_column("modified"))
        self.file_tree.heading("size", text="Size", command=lambda: self.sort_by_column("size"))
        self.file_tree.column("select", width=40, anchor="center")
        self.file_tree.column("name", width=200)
        self.file_tree.column("type", width=80)
        self.file_tree.column("modified", width=120)
        self.file_tree.column("size", width=100)

        tree_scroll = ttk.Scrollbar(file_frame, orient=tk.VERTICAL, command=self.file_tree.yview)
        self.file_tree.configure(yscrollcommand=tree_scroll.set)
        self.file_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Reorder buttons frame
        btn_order_frame = ttk.Frame(left_container)
        btn_order_frame.pack(fill=tk.X, pady=5)
        ttk.Button(btn_order_frame, text="⬆ Move Up", command=self.move_up).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_order_frame, text="⬇ Move Down", command=self.move_down).pack(side=tk.LEFT, padx=2)
        ttk.Label(btn_order_frame, text="Double-click to move", foreground="gray").pack(side=tk.RIGHT, padx=2)

        # ----- RIGHT: Naming options + side-by-side preview -----
        right_paned = ttk.PanedWindow(top_paned, orient=tk.VERTICAL)
        top_paned.add(right_paned, weight=1)

        # Naming options frame
        options_frame = ttk.LabelFrame(right_paned, text="Naming Options")
        right_paned.add(options_frame, weight=1)

        ttk.Label(options_frame, text="Rename Mode:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.mode_label = ttk.Label(options_frame, text="Sequential Naming", font=("", 10, "bold"))
        self.mode_label.grid(row=0, column=1, sticky=tk.W, padx=5)

        ttk.Label(options_frame, text="Base Name:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.base_entry = ttk.Entry(options_frame, width=25)
        self.base_entry.grid(row=1, column=1, padx=5, pady=2, sticky=tk.EW)

        ttk.Label(options_frame, text="Start Number:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        self.start_spin = ttk.Spinbox(options_frame, from_=1, to=9999, width=8, validate="key",
                                      validatecommand=(self.register(self.validate_number), '%P'))
        self.start_spin.grid(row=2, column=1, sticky=tk.W, padx=5)

        ttk.Label(options_frame, text="Padding:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=2)
        self.padding_combo = ttk.Combobox(options_frame, values=["1", "01", "001", "0001"], width=8)
        self.padding_combo.grid(row=3, column=1, sticky=tk.W, padx=5)

        ttk.Label(options_frame, text="Suffix:").grid(row=4, column=0, sticky=tk.W, padx=5, pady=2)
        self.suffix_entry = ttk.Entry(options_frame, width=25)
        self.suffix_entry.grid(row=4, column=1, padx=5, pady=2, sticky=tk.EW)

        ttk.Label(options_frame, text="Case:").grid(row=5, column=0, sticky=tk.W, padx=5, pady=2)
        self.case_combo = ttk.Combobox(options_frame, values=["Keep original", "lowercase", "UPPERCASE", "Capitalize"], width=15)
        self.case_combo.grid(row=5, column=1, sticky=tk.W, padx=5)
        self.case_combo.current(0)

        self.apply_ext_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Apply to Filename & Extension", variable=self.apply_ext_var).grid(row=6, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)

        options_frame.grid_columnconfigure(1, weight=1)

        # Side‑by‑side preview (canvas + info text)
        preview_frame = ttk.LabelFrame(right_paned, text="Preview (click any file)")
        right_paned.add(preview_frame, weight=1)

        preview_paned = ttk.PanedWindow(preview_frame, orient=tk.HORIZONTAL)
        preview_paned.pack(fill=tk.BOTH, expand=True)

        self.preview_canvas = tk.Canvas(preview_paned, bg="#f0f0f0", width=150, height=150, relief=tk.SUNKEN)
        preview_paned.add(self.preview_canvas, weight=1)

        self.preview_info = tk.Text(preview_paned, wrap=tk.WORD, font=("TkFixedFont", 8))
        preview_paned.add(self.preview_info, weight=2)
        info_scroll = ttk.Scrollbar(self.preview_info, orient=tk.VERTICAL, command=self.preview_info.yview)
        self.preview_info.configure(yscrollcommand=info_scroll.set)
        info_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # ========== BOTTOM PART: Live preview table + status bar ==========
        bottom_frame = ttk.LabelFrame(main_vpaned, text="Live Preview (original → new)")
        main_vpaned.add(bottom_frame, weight=1)

        # Preview table
        columns = ("original", "new")
        self.preview_table = ttk.Treeview(bottom_frame, columns=columns, show="headings", height=6)
        self.preview_table.heading("original", text="Original Name")
        self.preview_table.heading("new", text="New Name")
        self.preview_table.column("original", width=300)
        self.preview_table.column("new", width=300)
        self.preview_table.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        table_scroll = ttk.Scrollbar(bottom_frame, orient=tk.VERTICAL, command=self.preview_table.yview)
        table_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.preview_table.configure(yscrollcommand=table_scroll.set)

        # Status bar + control buttons
        status_frame = ttk.Frame(bottom_frame)
        status_frame.pack(fill=tk.X, pady=5)
        self.status_label = ttk.Label(status_frame, text="No folder selected", foreground="blue")
        self.status_label.pack(side=tk.LEFT)
        self.progress_label = ttk.Label(status_frame, text="", foreground="green")
        self.progress_label.pack(side=tk.RIGHT)

        btn_frame = ttk.Frame(bottom_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        ttk.Button(btn_frame, text="📂 Select Folder", command=self.load_folder).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🔄 Refresh", command=self.refresh_file_list).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🏷️ Rename Selected", command=self.rename_files).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🗑️ Clear All", command=self.reset_app).pack(side=tk.RIGHT, padx=5)

    def setup_bindings(self):
        self.base_entry.bind("<KeyRelease>", lambda e: self.update_preview())
        self.start_spin.bind("<KeyRelease>", lambda e: self.update_preview())
        self.padding_combo.bind("<<ComboboxSelected>>", lambda e: self.update_preview())
        self.suffix_entry.bind("<KeyRelease>", lambda e: self.update_preview())
        self.case_combo.bind("<<ComboboxSelected>>", lambda e: self.update_preview())
        self.apply_ext_var.trace_add("write", lambda *_: self.update_preview())
        # Click on tree row -> show preview
        self.file_tree.bind("<ButtonRelease-1>", self.on_tree_click)
        # Double-click on tree row -> move up (optional reorder)
        self.file_tree.bind("<Double-1>", self.double_click_move)

    # ---------------------------- Sorting & Reordering ----------------------------
    def sort_by_column(self, col):
        """Sort file_objects and file_vars by column and refresh list."""
        self.sort_reverse = (self.sort_column == col and not self.sort_reverse)
        self.sort_column = col
        
        # Zip them to keep selection states with the files
        combined = list(zip(self.file_objects, self.file_vars))
        
        if col == "name":
            combined.sort(key=lambda pair: self.natural_sort_key(pair[0].name), reverse=self.sort_reverse)
        elif col == "type":
            combined.sort(key=lambda pair: pair[0].suffix.lower(), reverse=self.sort_reverse)
        elif col == "modified":
            combined.sort(key=lambda pair: pair[0].stat().st_mtime, reverse=self.sort_reverse)
        elif col == "size":
            combined.sort(key=lambda pair: pair[0].stat().st_size, reverse=self.sort_reverse)
            
        # Unzip back
        self.file_objects, self.file_vars = map(list, zip(*combined)) if combined else ([], [])
        
        # Re-render UI (do not fetch from disk as we just sorted the existing list)
        self.refresh_file_list(fetch_from_disk=False)

    def move_up(self):
        """Move selected file one position up in the list."""
        selected = self.file_tree.selection()
        if not selected:
            return
        # Get the index from the tag
        idx = int(self.file_tree.item(selected[0], "tags")[0])
        if idx > 0:
            # Swap in data lists
            self.file_objects[idx], self.file_objects[idx-1] = self.file_objects[idx-1], self.file_objects[idx]
            self.file_vars[idx], self.file_vars[idx-1] = self.file_vars[idx-1], self.file_vars[idx]
            # Update UI without re-fetching from disk
            self.refresh_file_list(fetch_from_disk=False, select_idx=idx-1)

    def move_down(self):
        selected = self.file_tree.selection()
        if not selected:
            return
        idx = int(self.file_tree.item(selected[0], "tags")[0])
        if idx < len(self.file_objects)-1:
            self.file_objects[idx], self.file_objects[idx+1] = self.file_objects[idx+1], self.file_objects[idx]
            self.file_vars[idx], self.file_vars[idx+1] = self.file_vars[idx+1], self.file_vars[idx]
            self.refresh_file_list(fetch_from_disk=False, select_idx=idx+1)

    def double_click_move(self, event):
        """Double-click moves file up."""
        self.move_up()

    def toggle_all(self):
        """Select/deselect all files."""
        select_all = not all(var.get() for var in self.file_vars)
        for var in self.file_vars:
            var.set(select_all)
        self.refresh_file_list(keep_selection=True)
        self.update_preview()

    # ---------------------------- File loading & display ----------------------------
    def validate_number(self, value):
        return value == "" or value.isdigit()

    def natural_sort_key(self, s):
        return [int(text) if text.isdigit() else text.lower() for text in re.split(r"(\d+)", str(s))]

    def human_readable_size(self, size_bytes):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"

    def load_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.current_folder = Path(folder)
            self.refresh_file_list()

    def refresh_file_list(self, fetch_from_disk=True, select_idx=None):
        if not self.current_folder:
            return
        try:
            if fetch_from_disk:
                all_files = sorted(self.current_folder.iterdir(), key=lambda x: self.natural_sort_key(x.name))
                self.file_objects = [f for f in all_files if f.is_file()]
                self.file_vars = [tk.BooleanVar(value=True) for _ in self.file_objects]

            self.file_tree.delete(*self.file_tree.get_children())
            total_size = 0
            for i, f in enumerate(self.file_objects):
                total_size += f.stat().st_size
                mod_time = datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
                size_str = self.human_readable_size(f.stat().st_size)
                ext = f.suffix[1:] if f.suffix else "file"
                check_mark = "✓" if (i < len(self.file_vars) and self.file_vars[i].get()) else " "
                
                # Determine icon based on type
                icon = "📄 " if f.is_file() else "📁 "
                display_name = icon + f.name
                
                self.file_tree.insert("", "end", values=(check_mark, display_name, ext, mod_time, size_str), tags=(str(i),))
            
            self.status_label.config(text=f"Selected Folder: {self.current_folder}  |  {len(self.file_objects)} files, {self.human_readable_size(total_size)}")
            
            if select_idx is not None and select_idx < len(self.file_objects):
                children = self.file_tree.get_children()
                if children:
                    item = children[select_idx]
                    self.file_tree.selection_set(item)
                    self.file_tree.see(item)
            self.update_preview()
        except PermissionError:
            messagebox.showerror("Error", "Permission denied to access folder")

    def on_tree_click(self, event):
        region = self.file_tree.identify_region(event.x, event.y)
        if region == "cell":
            column = self.file_tree.identify_column(event.x)
            if column == "#1":   # checkbox column
                item = self.file_tree.identify_row(event.y)
                if item:
                    idx = int(self.file_tree.item(item, "tags")[0])
                    new_val = not self.file_vars[idx].get()
                    self.file_vars[idx].set(new_val)
                    self.file_tree.set(item, "select", "✓" if new_val else " ")
                    self.update_preview()
                return
        # Click on any other part of the row -> show preview
        item = self.file_tree.identify_row(event.y)
        if item:
            idx = int(self.file_tree.item(item, "tags")[0])
            self.show_preview(self.file_objects[idx])

    # ---------------------------- Preview (image / folder / file) ----------------------------
    def show_preview(self, path):
        self.preview_canvas.delete("all")
        self.preview_info.config(state=tk.NORMAL)
        self.preview_info.delete(1.0, tk.END)

        if path.is_dir():
            self.preview_info.insert(tk.END, f"📁 FOLDER: {path.name}\n\n")
            try:
                items = list(path.iterdir())[:15]
                for i in items:
                    self.preview_info.insert(tk.END, f"• {i.name}\n")
                if len(list(path.iterdir())) > 15:
                    self.preview_info.insert(tk.END, "...")
            except:
                self.preview_info.insert(tk.END, "Permission denied")
        elif path.suffix.lower() in {'.jpg','.jpeg','.png','.gif','.bmp','.tiff','.webp'}:
            try:
                img = Image.open(path)
                img.thumbnail((140, 140), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self.preview_canvas.create_image(70, 70, image=photo, anchor="center")
                self.current_preview_image = photo
                self.preview_info.insert(tk.END, f"🖼️ IMAGE: {path.name}\n")
                self.preview_info.insert(tk.END, f"Dimensions: {img.width}×{img.height}\n")
                self.preview_info.insert(tk.END, f"Size: {self.human_readable_size(path.stat().st_size)}")
            except Exception as e:
                self.preview_info.insert(tk.END, f"Error: {e}")
        else:
            stat = path.stat()
            self.preview_info.insert(tk.END, f"📄 FILE: {path.name}\n")
            self.preview_info.insert(tk.END, f"Type: {path.suffix or 'none'}\n")
            self.preview_info.insert(tk.END, f"Size: {self.human_readable_size(stat.st_size)}\n")
            self.preview_info.insert(tk.END, f"Modified: {datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M')}")
        self.preview_info.config(state=tk.DISABLED)

    def clear_preview(self):
        self.preview_canvas.delete("all")
        self.preview_info.config(state=tk.NORMAL)
        self.preview_info.delete(1.0, tk.END)
        self.preview_info.insert(tk.END, "Select a file to preview")
        self.preview_info.config(state=tk.DISABLED)

    # ---------------------------- Naming & Live Preview ----------------------------
    def apply_case(self, name):
        case = self.case_combo.get()
        if case == "lowercase":
            return name.lower()
        elif case == "UPPERCASE":
            return name.upper()
        elif case == "Capitalize":
            return name.capitalize()
        return name

    def generate_new_name(self, index, path):
        base = self.base_entry.get().strip()
        padding_str = self.padding_combo.get()
        width = len(padding_str)
        start_num = int(self.start_spin.get() or 1)
        suffix = self.suffix_entry.get().strip()
        number = start_num + index
        formatted_num = f"{number:0{width}d}"
        stem = f"{base}{formatted_num}{suffix}"
        new_name = stem + path.suffix
        return self.apply_case(new_name)

    def update_preview(self):
        for item in self.preview_table.get_children():
            self.preview_table.delete(item)
        selected_indices = [i for i, var in enumerate(self.file_vars) if var.get()]
        total_selected = len(selected_indices)
        if total_selected > 50:
            self.preview_table.insert("", "end", values=(f"... {total_selected} files selected (preview limited to 50)", ""))
            selected_indices = selected_indices[:50]
        new_names = []
        for seq, i in enumerate(selected_indices):
            new_name = self.generate_new_name(seq, self.file_objects[i])
            new_names.append(new_name)
            self.preview_table.insert("", "end", values=(self.file_objects[i].name, new_name))
        for item in self.preview_table.get_children():
            new = self.preview_table.item(item, "values")[1]
            if new_names.count(new) > 1:
                self.preview_table.tag_configure("duplicate", background="#ffcccc")
                self.preview_table.item(item, tags=("duplicate",))
        total_size = sum(self.file_objects[i].stat().st_size for i in selected_indices)
        self.progress_label.config(text=f"{total_selected} files selected ({self.human_readable_size(total_size)}) | Processed: 0 | Errors: 0")

    # ---------------------------- Renaming Logic ----------------------------
    def rename_files(self):
        selected = [(i, self.file_objects[i]) for i, var in enumerate(self.file_vars) if var.get()]
        if not selected:
            self.show_status("No files selected to rename")
            return
        if len(selected) > 10:
            if not messagebox.askyesno("Confirm Rename", f"Rename {len(selected)} files?"):
                return
        self.overwrite_all = None
        processed = 0
        errors = []
        cancel = False
        for seq, (orig_idx, path) in enumerate(selected):
            if cancel:
                break
            new_name = self.generate_new_name(seq, path)
            new_path = path.parent / new_name
            if new_path == path:
                continue
            if new_path.exists():
                if self.overwrite_all is None:
                    resp = self.ask_overwrite(new_name)
                    if resp == "cancel":
                        cancel = True
                        continue
                    elif resp == "no":
                        continue
                    elif resp == "noall":
                        self.overwrite_all = False
                        continue
                    elif resp == "yes":
                        pass
                    elif resp == "yesall":
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
        if processed:
            self.refresh_file_list()
            self.show_status(f"Renamed {processed} files")
            self.progress_label.config(text=f"{len(selected)} files selected | Processed: {processed} | Errors: {len(errors)}")
        else:
            self.show_status("No files were renamed")

    def ask_overwrite(self, filename):
        d = tk.Toplevel(self)
        d.title("Overwrite")
        d.transient(self)
        d.grab_set()
        tk.Label(d, text=f"'{filename}' exists. Overwrite?").pack(padx=20, pady=10)
        btn_frame = ttk.Frame(d)
        btn_frame.pack(pady=10)
        resp = {"val": "no"}
        def set_res(v): resp["val"] = v; d.destroy()
        ttk.Button(btn_frame, text="Yes", command=lambda: set_res("yes")).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Yes to All", command=lambda: set_res("yesall")).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="No", command=lambda: set_res("no")).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="No to All", command=lambda: set_res("noall")).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=lambda: set_res("cancel")).pack(side=tk.LEFT, padx=5)
        d.wait_window()
        return resp["val"]

    def show_error_dialog(self, errors):
        d = tk.Toplevel(self)
        d.title("Errors")
        txt = ScrolledText(d, width=70, height=15)
        txt.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        txt.insert(tk.END, "\n".join(errors[:50]))
        txt.config(state=tk.DISABLED)
        ttk.Button(d, text="OK", command=d.destroy).pack(pady=5)

    def show_status(self, msg):
        self.status_label.config(text=msg)
        self.after(4000, lambda: self.status_label.config(text=f"Selected Folder: {self.current_folder or 'None'}"))

    def reset_app(self):
        self.current_folder = None
        self.file_objects.clear()
        self.file_vars.clear()
        self.file_tree.delete(*self.file_tree.get_children())
        self.preview_table.delete(*self.preview_table.get_children())
        self.set_default_values()
        self.clear_preview()
        self.status_label.config(text="No folder selected")
        self.progress_label.config(text="")

if __name__ == "__main__":
    app = FileRenamerPro()
    app.mainloop()