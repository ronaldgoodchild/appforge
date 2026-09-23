"""
AppForge — Windows Package Manager
Professional GUI front-end for Winget and Chocolatey.

Developed by REGTeches · Ronald Goodchild
MIT License - see LICENSE.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import threading
import webbrowser
import re
import os


APP_NAME    = "AppForge"
APP_VERSION = "1.0.0"
APP_AUTHOR  = "Ronald Goodchild"
APP_COMPANY = "REGTeches"


# ──────────────────────────────────────────────────────────────────────
# Theme Engine
# ──────────────────────────────────────────────────────────────────────
class ThemeEngine:
    LIGHT = dict(
        bg="#f0f0f0", fg="#1a1a1a",
        text_bg="#ffffff", text_fg="#1a1a1a",
        hdr_bg="#003366", hdr_fg="#ffffff", hdr_sub="#99bbdd",
        sel_bg="#0078d4", sel_fg="#ffffff",
        tree_bg="#ffffff", tree_fg="#1a1a1a",
        tree_odd="#f7f9fc", checked_bg="#d4edda",
        frame_bg="#f0f0f0", entry_bg="#ffffff",
        border="#cccccc",
        btn_bg="#e1e1e1", btn_fg="#1a1a1a",
        status_bg="#e0e0e0", status_fg="#444444",
    )
    DARK = dict(
        bg="#1e1e1e", fg="#d4d4d4",
        text_bg="#252526", text_fg="#d4d4d4",
        hdr_bg="#0d0d1e", hdr_fg="#ffffff", hdr_sub="#6699cc",
        sel_bg="#094771", sel_fg="#ffffff",
        tree_bg="#252526", tree_fg="#d4d4d4",
        tree_odd="#2a2a2b", checked_bg="#1a3a1a",
        frame_bg="#1e1e1e", entry_bg="#3c3c3c",
        border="#555555",
        btn_bg="#3c3c3c", btn_fg="#d4d4d4",
        status_bg="#2d2d2d", status_fg="#aaaaaa",
    )

    def __init__(self):
        self.dark = False
        self._text_widgets  = []   # tk.Text instances
        self._header_frames = []   # (frame, label_list)
        self._status_labels = []
        self._root          = None
        self._style         = None

    def init(self, root, style):
        self._root  = root
        self._style = style
        self._apply(self.LIGHT)

    def register_text(self, widget):
        self._text_widgets.append(widget)

    def register_status(self, label):
        self._status_labels.append(label)

    def toggle(self):
        self.dark = not self.dark
        self._apply(self.DARK if self.dark else self.LIGHT)

    def colors(self):
        return self.DARK if self.dark else self.LIGHT

    def _apply(self, c):
        s = self._style
        s.theme_use("clam")

        # Base
        s.configure(".",
            background=c["bg"], foreground=c["fg"],
            fieldbackground=c["entry_bg"],
            bordercolor=c["border"], darkcolor=c["bg"], lightcolor=c["bg"],
            troughcolor=c["bg"], insertcolor=c["fg"])

        s.configure("TFrame",        background=c["bg"])
        s.configure("TLabel",        background=c["bg"],        foreground=c["fg"])
        s.configure("TLabelframe",   background=c["bg"],        foreground=c["fg"],
                    bordercolor=c["border"])
        s.configure("TLabelframe.Label", background=c["bg"],   foreground=c["fg"])
        s.configure("TPanedwindow",  background=c["bg"])
        s.configure("TSeparator",    background=c["border"])

        s.configure("TButton",
            background=c["btn_bg"], foreground=c["btn_fg"],
            bordercolor=c["border"], focuscolor=c["sel_bg"],
            padding=(8, 4))
        s.map("TButton",
            background=[("active", c["sel_bg"]), ("pressed", c["sel_bg"])],
            foreground=[("active", c["sel_fg"]), ("pressed", c["sel_fg"])])

        s.configure("TCheckbutton",  background=c["bg"], foreground=c["fg"],
                    focuscolor=c["sel_bg"])
        s.map("TCheckbutton",        background=[("active", c["bg"])])

        s.configure("TEntry",        fieldbackground=c["entry_bg"],
                    foreground=c["fg"], insertcolor=c["fg"],
                    bordercolor=c["border"])

        s.configure("TScrollbar",    background=c["btn_bg"],
                    troughcolor=c["bg"], bordercolor=c["border"],
                    arrowcolor=c["fg"])
        s.map("TScrollbar",          background=[("active", c["sel_bg"])])

        s.configure("TProgressbar",  troughcolor=c["bg"],
                    background=c["sel_bg"], bordercolor=c["border"])

        s.configure("TNotebook",     background=c["bg"],
                    bordercolor=c["border"], tabmargins=[2, 5, 2, 0])
        s.configure("TNotebook.Tab",
            background=c["btn_bg"], foreground=c["fg"],
            padding=[12, 6], focuscolor=c["sel_bg"])
        s.map("TNotebook.Tab",
            background=[("selected", c["bg"]), ("active", c["entry_bg"])],
            foreground=[("selected", c["sel_bg"])],
            expand=[("selected", [1, 1, 1, 0])])

        s.configure("Treeview",
            background=c["tree_bg"], foreground=c["tree_fg"],
            fieldbackground=c["tree_bg"], bordercolor=c["border"],
            rowheight=24)
        s.configure("Treeview.Heading",
            background=c["btn_bg"], foreground=c["fg"],
            bordercolor=c["border"], relief="flat", padding=[4, 4])
        s.map("Treeview",
            background=[("selected", c["sel_bg"])],
            foreground=[("selected", c["sel_fg"])])
        s.map("Treeview.Heading",
            background=[("active", c["entry_bg"])])

        # Checked row tag (applied directly on treeview widgets)
        for tw in self._text_widgets:
            try:
                tw.config(
                    bg=c["text_bg"], fg=c["text_fg"],
                    insertbackground=c["fg"],
                    selectbackground=c["sel_bg"],
                    selectforeground=c["sel_fg"])
            except Exception:
                pass

        for lbl in self._status_labels:
            try:
                lbl.config(bg=c["status_bg"], fg=c["status_fg"])
            except Exception:
                pass

        if self._root:
            self._root.config(bg=c["bg"])


# Module-level singleton — widgets register themselves here
theme = ThemeEngine()


# ──────────────────────────────────────────────────────────────────────
# Subprocess helpers
# ──────────────────────────────────────────────────────────────────────
SUBPROCESS_FLAGS = dict(
    capture_output=True, text=True,
    encoding="utf-8", errors="replace",
    creationflags=0x08000000,
)
ACTION_FLAGS = dict(
    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    text=True, encoding="utf-8", errors="replace",
)


def run_action(args, cmd="winget", timeout=600):
    proc = subprocess.Popen([cmd] + args, **ACTION_FLAGS)
    try:
        stdout, stderr = proc.communicate(timeout=timeout)
        output = (stdout or "") + ("\n" + stderr if stderr else "")
        return proc.returncode == 0, output.strip()
    except subprocess.TimeoutExpired:
        proc.kill()
        return False, "Timed out"


def parse_winget_table(lines):
    sep_idx = None
    for i, line in enumerate(lines):
        if re.match(r"^-{10,}", line.strip()):
            sep_idx = i
            break
    if sep_idx is None or sep_idx == 0:
        return [], []
    header_line = lines[sep_idx - 1]
    col_starts = [m.start() for m in re.finditer(r"\S+", header_line)]
    rows, seen = [], set()
    for line in lines[sep_idx + 1:]:
        if not line.strip():
            continue
        parts = []
        for j, start in enumerate(col_starts):
            end = col_starts[j + 1] if j + 1 < len(col_starts) else len(line)
            parts.append(line[start:end].strip())
        if len(parts) >= 2 and (parts[1].endswith("…") or parts[1].endswith("...")):
            continue
        key = parts[1] if len(parts) >= 2 else line.strip()
        if key in seen:
            continue
        seen.add(key)
        rows.append(parts)
    return [], rows


def run_winget(args, timeout=120):
    r = subprocess.run(["winget"] + args, timeout=timeout, **SUBPROCESS_FLAGS)
    return r.stdout


def run_choco(args, timeout=120):
    r = subprocess.run(["choco"] + args, timeout=timeout, **SUBPROCESS_FLAGS)
    return r.stdout


def run_choco_action(args, timeout=600):
    return run_action(args, cmd="choco", timeout=timeout)


def parse_choco_limit(output):
    rows, seen = [], set()
    for line in output.splitlines():
        line = line.strip()
        if not line or "|" not in line:
            continue
        parts = line.split("|")
        pkg_id = parts[0].strip()
        if not pkg_id or pkg_id in seen:
            continue
        seen.add(pkg_id)
        rows.append([pkg_id, parts[1].strip() if len(parts) > 1 else ""])
    return rows


def parse_choco_outdated(output):
    rows, seen = [], set()
    for line in output.splitlines():
        line = line.strip()
        if not line or "|" not in line:
            continue
        parts = line.split("|")
        if len(parts) < 3:
            continue
        pkg_id = parts[0].strip()
        if not pkg_id or pkg_id in seen:
            continue
        seen.add(pkg_id)
        rows.append([pkg_id, parts[1].strip(), parts[2].strip()])
    return rows


def parse_choco_sources(output):
    rows = []
    for line in output.splitlines():
        line = line.strip()
        if not line or " - " not in line:
            continue
        parts = line.split(" - ", 1)
        if len(parts) == 2:
            rows.append([parts[0].strip(), parts[1].split("|")[0].strip()])
    return rows


# ──────────────────────────────────────────────────────────────────────
# Progress Dialog
# ──────────────────────────────────────────────────────────────────────
class ProgressDialog(tk.Toplevel):
    def __init__(self, parent, title="Working..."):
        super().__init__(parent)
        self.title(title)
        self.geometry("520x340")
        self.resizable(True, True)
        self.transient(parent)

        c = theme.colors()
        self.config(bg=c["bg"])

        self.header_var = tk.StringVar(value="Starting...")
        ttk.Label(self, textvariable=self.header_var,
                  font=("Segoe UI", 11, "bold"), padding=(12, 8)).pack(fill=tk.X)

        self.progress = ttk.Progressbar(self, mode="determinate")
        self.progress.pack(fill=tk.X, padx=12, pady=(0, 4))

        self.counter_var = tk.StringVar(value="")
        ttk.Label(self, textvariable=self.counter_var, padding=(12, 2)).pack(fill=tk.X)

        log_frame = ttk.Frame(self, padding=(12, 4))
        log_frame.pack(fill=tk.BOTH, expand=True)

        self.log = tk.Text(log_frame, wrap=tk.WORD, state=tk.DISABLED,
                           font=("Consolas", 9), height=10)
        vsb = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log.yview)
        self.log.configure(yscrollcommand=vsb.set)
        self.log.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        theme.register_text(self.log)
        # Apply current theme immediately
        self.log.config(bg=c["text_bg"], fg=c["text_fg"],
                        insertbackground=c["fg"],
                        selectbackground=c["sel_bg"],
                        selectforeground=c["sel_fg"])

        self.protocol("WM_DELETE_WINDOW", lambda: None)

    def set_total(self, total):
        self.progress["maximum"] = total
        self.progress["value"]   = 0

    def update_progress(self, current, total, name):
        self.progress["value"] = current
        self.header_var.set(f"Processing: {name}")
        self.counter_var.set(f"{current} of {total} complete")

    def log_message(self, msg):
        self.log.config(state=tk.NORMAL)
        self.log.insert(tk.END, msg + "\n")
        self.log.see(tk.END)
        self.log.config(state=tk.DISABLED)

    def finish(self, message="Done!"):
        self.header_var.set(message)
        self.counter_var.set("")
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        ttk.Button(self, text="Close", command=self.destroy).pack(pady=8)


# ──────────────────────────────────────────────────────────────────────
# Package List Frame (shared by both managers)
# ──────────────────────────────────────────────────────────────────────
class PackageListFrame(ttk.Frame):
    def __init__(self, parent, columns, show_checks=True, detail_fn=None):
        super().__init__(parent)
        self.show_checks = show_checks
        self.check_vars  = {}
        self.description_cache   = {}
        self.loading_descriptions = set()
        self._detail_fn  = detail_fn

        paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        left = ttk.Frame(paned)
        paned.add(left, weight=3)

        tree_show = "tree headings" if show_checks else "headings"
        self.tree = ttk.Treeview(left, columns=columns, show=tree_show, selectmode="browse")
        for col in columns:
            self.tree.heading(col, text=col, command=lambda c=col: self._sort(c))
            self.tree.column(col, width=200)
        if show_checks:
            self.tree.column("#0", width=40, stretch=False)

        vsb = ttk.Scrollbar(left, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        if show_checks:
            self.tree.bind("<ButtonRelease-1>", self._on_click)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        right = ttk.LabelFrame(paned, text="Package Details", padding=8)
        paned.add(right, weight=2)

        self.detail_text = tk.Text(right, wrap=tk.WORD, state=tk.DISABLED,
                                   font=("Segoe UI", 10))
        d_vsb = ttk.Scrollbar(right, orient=tk.VERTICAL, command=self.detail_text.yview)
        self.detail_text.configure(yscrollcommand=d_vsb.set)
        self.detail_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        d_vsb.pack(side=tk.RIGHT, fill=tk.Y)

        theme.register_text(self.detail_text)
        c = theme.colors()
        self.detail_text.config(bg=c["text_bg"], fg=c["text_fg"],
                                insertbackground=c["fg"],
                                selectbackground=c["sel_bg"],
                                selectforeground=c["sel_fg"])

        self.tree.tag_configure("checked", background=c["checked_bg"])

    def set_rows(self, rows, id_col=1):
        self.tree.delete(*self.tree.get_children())
        self.check_vars.clear()
        seen = set()
        for row in rows:
            iid = row[id_col] if id_col < len(row) else ""
            if not iid or iid in seen:
                continue
            seen.add(iid)
            if self.show_checks:
                var = tk.BooleanVar(value=False)
                self.check_vars[iid] = var
                self.tree.insert("", tk.END, iid=iid, text="☐", values=tuple(row))
            else:
                self.tree.insert("", tk.END, iid=iid, values=tuple(row))

    def _on_click(self, event):
        if self.tree.identify_region(event.x, event.y) == "tree":
            iid = self.tree.identify_row(event.y)
            if iid:
                self._toggle(iid)

    def _toggle(self, iid):
        var = self.check_vars.get(iid)
        if not var:
            return
        var.set(not var.get())
        checked = var.get()
        self.tree.item(iid, text="☑" if checked else "☐",
                       tags=("checked",) if checked else ())
        self.event_generate("<<CheckChanged>>")

    def get_selected_ids(self):
        return [iid for iid, v in self.check_vars.items() if v.get()]

    def selected_count(self):
        return sum(1 for v in self.check_vars.values() if v.get())

    def _sort(self, col):
        data = [(self.tree.set(iid, col), iid) for iid in self.tree.get_children()]
        data.sort(key=lambda t: t[0].lower())
        for i, (_, iid) in enumerate(data):
            self.tree.move(iid, "", i)

    def _on_select(self, _e):
        sel = self.tree.selection()
        if not sel:
            return
        pkg_id = sel[0]
        if pkg_id in self.description_cache:
            self._show_detail(self.description_cache[pkg_id])
        else:
            self._show_detail("Loading details...")
            if pkg_id not in self.loading_descriptions:
                self.loading_descriptions.add(pkg_id)
                threading.Thread(target=self._fetch_detail,
                                 args=(pkg_id,), daemon=True).start()

    def _fetch_detail(self, pkg_id):
        try:
            desc = self._detail_fn(pkg_id) if self._detail_fn else \
                   run_winget(["show", pkg_id], timeout=30)
        except Exception as exc:
            desc = f"Error: {exc}"
        self.description_cache[pkg_id] = desc
        self.loading_descriptions.discard(pkg_id)
        self.after(0, lambda d=desc: self._show_if_still_selected(pkg_id, d))

    def _show_if_still_selected(self, pkg_id, desc):
        sel = self.tree.selection()
        if sel and sel[0] == pkg_id:
            self._show_detail(desc)

    def _show_detail(self, text):
        self.detail_text.config(state=tk.NORMAL)
        self.detail_text.delete("1.0", tk.END)
        self.detail_text.insert(tk.END, text)
        self.detail_text.config(state=tk.DISABLED)


# ──────────────────────────────────────────────────────────────────────
# Shared bulk-operation helpers (used by both WingetApp and ChocoApp)
# ──────────────────────────────────────────────────────────────────────
def _make_log_widget(parent):
    """Return a themed, scrollable Text+Scrollbar pair inside parent."""
    f = ttk.Frame(parent, padding=0)
    t = tk.Text(f, wrap=tk.WORD, state=tk.DISABLED, font=("Consolas", 9))
    sb = ttk.Scrollbar(f, orient=tk.VERTICAL, command=t.yview)
    t.configure(yscrollcommand=sb.set)
    t.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    sb.pack(side=tk.RIGHT, fill=tk.Y)
    theme.register_text(t)
    c = theme.colors()
    t.config(bg=c["text_bg"], fg=c["text_fg"],
             insertbackground=c["fg"],
             selectbackground=c["sel_bg"],
             selectforeground=c["sel_fg"])
    return f, t


# ──────────────────────────────────────────────────────────────────────
# Winget Application
# ──────────────────────────────────────────────────────────────────────
class WingetApp:
    def __init__(self, root):
        self.root = root
        self.status_var = tk.StringVar(value="Ready")
        status_lbl = tk.Label(root, textvariable=self.status_var,
                              relief=tk.SUNKEN, anchor=tk.W, padx=6, pady=3,
                              font=("Segoe UI", 9))
        status_lbl.pack(fill=tk.X, side=tk.BOTTOM)
        theme.register_status(status_lbl)
        c = theme.colors()
        status_lbl.config(bg=c["status_bg"], fg=c["status_fg"])

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        self._build_browse_tab()
        self._build_installed_tab()
        self._build_updates_tab()
        self._build_sources_tab()
        self._build_settings_tab()

        self._load_browse()
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

    # ── TAB 1 — Browse & Install ───────────────────────────────────────
    def _build_browse_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="  Browse & Install  ")

        bar = ttk.Frame(tab, padding=(8, 6))
        bar.pack(fill=tk.X)
        ttk.Label(bar, text="Search:").pack(side=tk.LEFT)
        self.browse_search = tk.StringVar()
        self.browse_search.trace_add("write", lambda *_: self._filter_browse())
        ttk.Entry(bar, textvariable=self.browse_search, width=40).pack(side=tk.LEFT, padx=(4, 12))
        self.browse_refresh_btn = ttk.Button(bar, text="↻ Refresh", command=self._load_browse)
        self.browse_refresh_btn.pack(side=tk.LEFT, padx=4)
        self.browse_install_btn = ttk.Button(bar, text="⬇ Install Selected", command=self._install_checked)
        self.browse_install_btn.pack(side=tk.RIGHT, padx=4)
        self.browse_uninstall_btn = ttk.Button(bar, text="✕ Uninstall Selected", command=self._uninstall_from_browse)
        self.browse_uninstall_btn.pack(side=tk.RIGHT, padx=4)
        self.browse_count = ttk.Label(bar, text="0 selected")
        self.browse_count.pack(side=tk.RIGHT, padx=8)

        self.browse_list = PackageListFrame(tab, columns=("Name", "ID", "Version"))
        self.browse_list.pack(fill=tk.BOTH, expand=True, padx=4, pady=(0, 4))
        self.browse_list.bind("<<CheckChanged>>",
            lambda *_: self.browse_count.config(
                text=f"{self.browse_list.selected_count()} selected"))
        self.browse_all_rows = []

    def _load_browse(self):
        self.browse_refresh_btn.config(state=tk.DISABLED)
        self.status_var.set("Loading available packages…")
        threading.Thread(target=self._fetch_browse, daemon=True).start()

    def _fetch_browse(self):
        try:
            out = run_winget(["search", ""], timeout=180)
            _, rows = parse_winget_table(out.splitlines())
            self.browse_all_rows = rows
            self.root.after(0, self._populate_browse, rows)
        except Exception as exc:
            msg = str(exc)
            self.root.after(0, lambda m=msg: self.status_var.set(f"Error: {m}"))
            self.root.after(0, lambda: self.browse_refresh_btn.config(state=tk.NORMAL))

    def _populate_browse(self, rows):
        self.browse_list.set_rows(rows, id_col=1)
        self.status_var.set(f"Loaded {len(rows)} packages")
        self.browse_refresh_btn.config(state=tk.NORMAL)

    def _filter_browse(self):
        q = self.browse_search.get().lower()
        filtered = [r for r in self.browse_all_rows
                    if q in r[0].lower() or q in r[1].lower()]
        self.browse_list.set_rows(filtered, id_col=1)

    def _install_checked(self):
        ids = self.browse_list.get_selected_ids()
        if not ids:
            messagebox.showinfo("Nothing selected",
                                "Check the boxes next to packages you want to install.")
            return
        preview = "\n".join(f"  • {p}" for p in ids[:25])
        if len(ids) > 25:
            preview += f"\n  … and {len(ids)-25} more"
        if not messagebox.askyesno("Confirm Install",
                                   f"Install {len(ids)} package(s)?\n\n{preview}"):
            return
        self.browse_install_btn.config(state=tk.DISABLED)
        threading.Thread(target=self._run_installs, args=(ids,), daemon=True).start()

    def _run_installs(self, ids):
        total = len(ids)
        progress = [None]
        self.root.after(0, lambda: _create_progress(self.root, progress, "Installing Packages", total))
        import time; time.sleep(0.2)
        errors = []
        for i, pid in enumerate(ids, 1):
            self.root.after(0, lambda p=pid, n=i, t=total: (
                self.status_var.set(f"Installing {n}/{t}: {p}…"),
                progress[0] and progress[0].update_progress(n, t, p),
                progress[0] and progress[0].log_message(f"[{n}/{t}] Installing {p}…"),
            ))
            ok, out = run_action(["install", "--id", pid, "-e",
                                  "--accept-source-agreements",
                                  "--accept-package-agreements"])
            if ok:
                self.root.after(0, lambda p=pid, o=out: progress[0] and
                    progress[0].log_message(f"  ✓ {p} installed\n{o}\n"))
            else:
                errors.append(pid)
                self.root.after(0, lambda p=pid, o=out: progress[0] and
                    progress[0].log_message(f"  ✗ Failed: {p}\n{o}\n"))
        done = f"Installed {total - len(errors)}/{total} package(s)"
        if errors:
            done += f"  ({len(errors)} failed)"
        self.root.after(0, lambda m=done: self.status_var.set(m))
        self.root.after(0, lambda: self.browse_install_btn.config(state=tk.NORMAL))
        self.root.after(0, lambda m=done: progress[0] and progress[0].finish(m))
        self.inst_loaded = False

    def _uninstall_from_browse(self):
        ids = self.browse_list.get_selected_ids()
        if not ids:
            messagebox.showinfo("Nothing selected",
                                "Check the boxes next to packages you want to uninstall.")
            return
        preview = "\n".join(f"  • {p}" for p in ids[:25])
        if not messagebox.askyesno("Confirm Uninstall",
                                   f"Uninstall {len(ids)} package(s)?\n\n{preview}"):
            return
        self.browse_uninstall_btn.config(state=tk.DISABLED)
        threading.Thread(target=self._run_uninstalls_from_browse,
                         args=(ids,), daemon=True).start()

    def _run_uninstalls_from_browse(self, ids):
        self._do_uninstall(ids, self.browse_uninstall_btn)
        self.inst_loaded = False

    # ── TAB 2 — Installed ──────────────────────────────────────────────
    def _build_installed_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="  Installed  ")
        bar = ttk.Frame(tab, padding=(8, 6))
        bar.pack(fill=tk.X)
        ttk.Label(bar, text="Search:").pack(side=tk.LEFT)
        self.inst_search = tk.StringVar()
        self.inst_search.trace_add("write", lambda *_: self._filter_installed())
        ttk.Entry(bar, textvariable=self.inst_search, width=40).pack(side=tk.LEFT, padx=(4, 12))
        self.inst_refresh_btn = ttk.Button(bar, text="↻ Refresh", command=self._load_installed)
        self.inst_refresh_btn.pack(side=tk.LEFT, padx=4)
        self.uninstall_btn = ttk.Button(bar, text="✕ Uninstall Selected", command=self._uninstall_checked)
        self.uninstall_btn.pack(side=tk.RIGHT, padx=4)
        self.inst_count = ttk.Label(bar, text="0 selected")
        self.inst_count.pack(side=tk.RIGHT, padx=8)
        self.inst_list = PackageListFrame(tab, columns=("Name", "ID", "Version"))
        self.inst_list.pack(fill=tk.BOTH, expand=True, padx=4, pady=(0, 4))
        self.inst_list.bind("<<CheckChanged>>",
            lambda *_: self.inst_count.config(
                text=f"{self.inst_list.selected_count()} selected"))
        self.inst_all_rows = []
        self.inst_loaded   = False

    def _load_installed(self):
        self.inst_refresh_btn.config(state=tk.DISABLED)
        self.status_var.set("Loading installed packages…")
        threading.Thread(target=self._fetch_installed, daemon=True).start()

    def _fetch_installed(self):
        try:
            out = run_winget(["list"], timeout=120)
            _, rows = parse_winget_table(out.splitlines())
            self.inst_all_rows = rows
            self.root.after(0, self._populate_installed, rows)
        except Exception as exc:
            msg = str(exc)
            self.root.after(0, lambda m=msg: self.status_var.set(f"Error: {m}"))
            self.root.after(0, lambda: self.inst_refresh_btn.config(state=tk.NORMAL))

    def _populate_installed(self, rows):
        self.inst_list.set_rows(rows, id_col=1)
        self.status_var.set(f"{len(rows)} packages installed")
        self.inst_refresh_btn.config(state=tk.NORMAL)
        self.inst_loaded = True

    def _filter_installed(self):
        q = self.inst_search.get().lower()
        filtered = [r for r in self.inst_all_rows
                    if q in r[0].lower() or (len(r) > 1 and q in r[1].lower())]
        self.inst_list.set_rows(filtered, id_col=1)

    def _uninstall_checked(self):
        ids = self.inst_list.get_selected_ids()
        if not ids:
            messagebox.showinfo("Nothing selected",
                                "Check the boxes next to packages you want to uninstall.")
            return
        preview = "\n".join(f"  • {p}" for p in ids[:25])
        if not messagebox.askyesno("Confirm Uninstall",
                                   f"Uninstall {len(ids)} package(s)?\n\n{preview}"):
            return
        self.uninstall_btn.config(state=tk.DISABLED)
        threading.Thread(target=self._run_uninstalls, args=(ids,), daemon=True).start()

    def _run_uninstalls(self, ids):
        self._do_uninstall(ids, self.uninstall_btn)
        self.root.after(0, self._load_installed)

    def _do_uninstall(self, ids, btn):
        total = len(ids)
        progress = [None]
        self.root.after(0, lambda: _create_progress(self.root, progress, "Uninstalling Packages", total))
        import time; time.sleep(0.2)
        errors = []
        for i, pid in enumerate(ids, 1):
            self.root.after(0, lambda p=pid, n=i, t=total: (
                self.status_var.set(f"Uninstalling {n}/{t}: {p}…"),
                progress[0] and progress[0].update_progress(n, t, p),
                progress[0] and progress[0].log_message(f"[{n}/{t}] Uninstalling {p}…"),
            ))
            ok, out = run_action(["uninstall", "--id", pid, "-e",
                                  "--accept-source-agreements"])
            if ok:
                self.root.after(0, lambda p=pid, o=out: progress[0] and
                    progress[0].log_message(f"  ✓ {p} removed\n{o}\n"))
            else:
                errors.append(pid)
                self.root.after(0, lambda p=pid, o=out: progress[0] and
                    progress[0].log_message(f"  ✗ Failed: {p}\n{o}\n"))
        done = f"Uninstalled {total - len(errors)}/{total} package(s)"
        self.root.after(0, lambda m=done: self.status_var.set(m))
        self.root.after(0, lambda: btn.config(state=tk.NORMAL))
        self.root.after(0, lambda m=done: progress[0] and progress[0].finish(m))

    # ── TAB 3 — Updates ───────────────────────────────────────────────
    def _build_updates_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="  Updates  ")
        bar = ttk.Frame(tab, padding=(8, 6))
        bar.pack(fill=tk.X)
        self.upd_refresh_btn = ttk.Button(bar, text="↻ Check for Updates", command=self._load_updates)
        self.upd_refresh_btn.pack(side=tk.LEFT, padx=4)
        self.upd_all_btn = ttk.Button(bar, text="⬆ Update ALL", command=self._update_all)
        self.upd_all_btn.pack(side=tk.LEFT, padx=4)
        self.upd_selected_btn = ttk.Button(bar, text="⬆ Update Selected", command=self._update_checked)
        self.upd_selected_btn.pack(side=tk.RIGHT, padx=4)
        self.upd_count = ttk.Label(bar, text="0 selected")
        self.upd_count.pack(side=tk.RIGHT, padx=8)
        self.upd_list = PackageListFrame(tab, columns=("Name", "ID", "Installed", "Available"))
        self.upd_list.pack(fill=tk.BOTH, expand=True, padx=4, pady=(0, 4))
        self.upd_list.bind("<<CheckChanged>>",
            lambda *_: self.upd_count.config(
                text=f"{self.upd_list.selected_count()} selected"))
        self.upd_loaded = False

    def _load_updates(self):
        self.upd_refresh_btn.config(state=tk.DISABLED)
        self.status_var.set("Checking for updates…")
        threading.Thread(target=self._fetch_updates, daemon=True).start()

    def _fetch_updates(self):
        try:
            out = run_winget(["upgrade"], timeout=120)
            _, rows = parse_winget_table(out.splitlines())
            self.root.after(0, self._populate_updates, rows)
        except Exception as exc:
            msg = str(exc)
            self.root.after(0, lambda m=msg: self.status_var.set(f"Error: {m}"))
            self.root.after(0, lambda: self.upd_refresh_btn.config(state=tk.NORMAL))

    def _populate_updates(self, rows):
        self.upd_list.set_rows(rows, id_col=1)
        self.status_var.set(f"{len(rows)} update(s) available")
        self.upd_refresh_btn.config(state=tk.NORMAL)
        self.upd_loaded = True

    def _update_all(self):
        if not messagebox.askyesno("Update All", "Update ALL packages with available updates?"):
            return
        self.upd_all_btn.config(state=tk.DISABLED)
        threading.Thread(target=self._run_update_all, daemon=True).start()

    def _run_update_all(self):
        progress = [None]
        def create():
            progress[0] = ProgressDialog(self.root, "Updating All Packages")
            progress[0].progress.config(mode="indeterminate")
            progress[0].progress.start(20)
            progress[0].log_message("Running: winget upgrade --all")
        self.root.after(0, create)
        import time; time.sleep(0.2)
        ok, out = run_action(["upgrade", "--all",
                              "--accept-source-agreements",
                              "--accept-package-agreements"], timeout=1800)
        self.root.after(0, lambda o=out: progress[0] and
            progress[0].log_message(f"\n--- Output ---\n{o}"))
        done = "Update all complete" if ok else "Update all finished with errors"
        self.root.after(0, lambda m=done: self.status_var.set(m))
        self.root.after(0, lambda: self.upd_all_btn.config(state=tk.NORMAL))
        self.root.after(0, lambda m=done: (
            progress[0] and progress[0].progress.stop(),
            progress[0] and progress[0].finish(m)))
        self.root.after(500, self._load_updates)

    def _update_checked(self):
        ids = self.upd_list.get_selected_ids()
        if not ids:
            messagebox.showinfo("Nothing selected",
                                "Check the boxes next to packages you want to update.")
            return
        self.upd_selected_btn.config(state=tk.DISABLED)
        threading.Thread(target=self._run_update_selected, args=(ids,), daemon=True).start()

    def _run_update_selected(self, ids):
        total = len(ids)
        progress = [None]
        self.root.after(0, lambda: _create_progress(self.root, progress, "Updating Packages", total))
        import time; time.sleep(0.2)
        errors = []
        for i, pid in enumerate(ids, 1):
            self.root.after(0, lambda p=pid, n=i, t=total: (
                self.status_var.set(f"Updating {n}/{t}: {p}…"),
                progress[0] and progress[0].update_progress(n, t, p),
                progress[0] and progress[0].log_message(f"[{n}/{t}] Updating {p}…"),
            ))
            ok, out = run_action(["upgrade", "--id", pid, "-e",
                                  "--accept-source-agreements",
                                  "--accept-package-agreements"])
            if ok:
                self.root.after(0, lambda p=pid, o=out: progress[0] and
                    progress[0].log_message(f"  ✓ {p} updated\n{o}\n"))
            else:
                errors.append(pid)
                self.root.after(0, lambda p=pid, o=out: progress[0] and
                    progress[0].log_message(f"  ✗ Failed: {p}\n{o}\n"))
        done = f"Updated {total - len(errors)}/{total} package(s)"
        self.root.after(0, lambda m=done: self.status_var.set(m))
        self.root.after(0, lambda: self.upd_selected_btn.config(state=tk.NORMAL))
        self.root.after(0, lambda m=done: progress[0] and progress[0].finish(m))
        self.root.after(500, self._load_updates)

    # ── TAB 4 — Sources ───────────────────────────────────────────────
    def _build_sources_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="  Sources  ")
        bar = ttk.Frame(tab, padding=(8, 6))
        bar.pack(fill=tk.X)
        self.src_refresh_btn = ttk.Button(bar, text="↻ Refresh Sources", command=self._load_sources)
        self.src_refresh_btn.pack(side=tk.LEFT, padx=4)
        self.src_reset_btn = ttk.Button(bar, text="⚠ Reset Sources", command=self._reset_sources)
        self.src_reset_btn.pack(side=tk.LEFT, padx=4)
        add_frame = ttk.LabelFrame(tab, text="Add a Source", padding=8)
        add_frame.pack(fill=tk.X, padx=8, pady=(4, 0))
        ttk.Label(add_frame, text="Name:").grid(row=0, column=0, sticky=tk.W, padx=4)
        self.src_name_var = tk.StringVar()
        ttk.Entry(add_frame, textvariable=self.src_name_var, width=28).grid(row=0, column=1, padx=4)
        ttk.Label(add_frame, text="URL:").grid(row=0, column=2, sticky=tk.W, padx=4)
        self.src_url_var = tk.StringVar()
        ttk.Entry(add_frame, textvariable=self.src_url_var, width=48).grid(row=0, column=3, padx=4)
        ttk.Button(add_frame, text="Add Source", command=self._add_source).grid(row=0, column=4, padx=8)
        self.src_list = PackageListFrame(tab, columns=("Name", "Argument"), show_checks=False)
        self.src_list.pack(fill=tk.BOTH, expand=True, padx=4, pady=(4, 4))
        self.src_loaded = False

    def _load_sources(self):
        self.src_refresh_btn.config(state=tk.DISABLED)
        self.status_var.set("Loading sources…")
        threading.Thread(target=self._fetch_sources, daemon=True).start()

    def _fetch_sources(self):
        try:
            out = run_winget(["source", "list"], timeout=30)
            _, rows = parse_winget_table(out.splitlines())
            self.root.after(0, self._populate_sources, rows)
        except Exception as exc:
            msg = str(exc)
            self.root.after(0, lambda m=msg: self.status_var.set(f"Error: {m}"))
            self.root.after(0, lambda: self.src_refresh_btn.config(state=tk.NORMAL))

    def _populate_sources(self, rows):
        self.src_list.set_rows(rows, id_col=0)
        self.status_var.set(f"{len(rows)} source(s)")
        self.src_refresh_btn.config(state=tk.NORMAL)
        self.src_loaded = True

    def _add_source(self):
        name = self.src_name_var.get().strip()
        url  = self.src_url_var.get().strip()
        if not name or not url:
            messagebox.showwarning("Missing info", "Enter both a name and URL.")
            return
        threading.Thread(target=self._run_add_source, args=(name, url), daemon=True).start()

    def _run_add_source(self, name, url):
        try:
            subprocess.run(
                ["winget", "source", "add", "--name", name, "--arg", url,
                 "--accept-source-agreements"],
                timeout=60, **SUBPROCESS_FLAGS)
            self.root.after(0, lambda n=name: self.status_var.set(f"Source '{n}' added"))
            self.root.after(0, self._load_sources)
        except Exception as exc:
            msg = str(exc)
            self.root.after(0, lambda m=msg: messagebox.showerror("Error", m))

    def _reset_sources(self):
        if not messagebox.askyesno("Reset Sources", "Reset all sources to defaults?"):
            return
        threading.Thread(target=self._run_reset_sources, daemon=True).start()

    def _run_reset_sources(self):
        try:
            subprocess.run(["winget", "source", "reset", "--force"],
                           timeout=60, **SUBPROCESS_FLAGS)
            self.root.after(0, lambda: self.status_var.set("Sources reset to defaults"))
            self.root.after(0, self._load_sources)
        except Exception as exc:
            msg = str(exc)
            self.root.after(0, lambda m=msg: messagebox.showerror("Error", m))

    # ── TAB 5 — Settings & Info ────────────────────────────────────────
    def _build_settings_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="  Settings & Info  ")
        frame = ttk.Frame(tab, padding=16)
        frame.pack(fill=tk.BOTH, expand=True)
        info_frame = ttk.LabelFrame(frame, text="Winget Info", padding=12)
        info_frame.pack(fill=tk.X, pady=(0, 12))
        self.info_text = tk.Text(info_frame, height=6, wrap=tk.WORD,
                                 state=tk.DISABLED, font=("Consolas", 10))
        self.info_text.pack(fill=tk.X)
        theme.register_text(self.info_text)
        c = theme.colors()
        self.info_text.config(bg=c["text_bg"], fg=c["text_fg"],
                              insertbackground=c["fg"],
                              selectbackground=c["sel_bg"],
                              selectforeground=c["sel_fg"])

        btn_frame = ttk.LabelFrame(frame, text="Quick Actions", padding=12)
        btn_frame.pack(fill=tk.X, pady=(0, 12))
        actions = [
            ("Open Winget Settings",       self._open_settings),
            ("Export Installed Packages",  self._export_packages),
            ("Import Packages from File",  self._import_packages),
            ("Repair Winget",              self._repair_winget),
        ]
        for i, (label, cmd) in enumerate(actions):
            ttk.Button(btn_frame, text=label, command=cmd, width=28).grid(
                row=i // 2, column=i % 2, padx=8, pady=4, sticky=tk.W)

        log_frame = ttk.LabelFrame(frame, text="Command Output", padding=8)
        log_frame.pack(fill=tk.BOTH, expand=True)
        inner, self.log_text = _make_log_widget(log_frame)
        inner.pack(fill=tk.BOTH, expand=True)
        self.settings_loaded = False

    def _log(self, text):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, text + "\n\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def _load_settings_info(self):
        threading.Thread(target=self._fetch_info, daemon=True).start()

    def _fetch_info(self):
        try:
            out = run_winget(["--info"], timeout=15)
        except Exception as exc:
            out = f"Error: {exc}"
        self.root.after(0, lambda o=out: self._show_info(o))

    def _show_info(self, text):
        self.info_text.config(state=tk.NORMAL)
        self.info_text.delete("1.0", tk.END)
        self.info_text.insert(tk.END, text)
        self.info_text.config(state=tk.DISABLED)
        self.settings_loaded = True

    def _open_settings(self):
        threading.Thread(target=lambda: (
            run_winget(["settings"], timeout=15),
            self.root.after(0, lambda: self._log("Opened winget settings file.")),
            self.root.after(0, lambda: self.status_var.set("Settings file opened")),
        ), daemon=True).start()

    def _export_packages(self):
        from tkinter import filedialog
        path = filedialog.asksaveasfilename(defaultextension=".json",
            filetypes=[("JSON files", "*.json")], title="Export packages to…")
        if not path:
            return
        threading.Thread(target=self._run_export, args=(path,), daemon=True).start()

    def _run_export(self, path):
        try:
            out = run_winget(["export", "-o", path, "--accept-source-agreements"], timeout=60)
            self.root.after(0, lambda p=path, o=out: self._log(f"Exported to: {p}\n{o}"))
            self.root.after(0, lambda p=path: self.status_var.set(f"Exported to {p}"))
        except Exception as exc:
            msg = str(exc)
            self.root.after(0, lambda m=msg: messagebox.showerror("Export Error", m))

    def _import_packages(self):
        from tkinter import filedialog
        path = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json")], title="Import packages from…")
        if not path:
            return
        if not messagebox.askyesno("Confirm Import",
                                   f"Import and install all packages from:\n{path}?"):
            return
        threading.Thread(target=self._run_import, args=(path,), daemon=True).start()

    def _run_import(self, path):
        progress = [None]
        def create():
            progress[0] = ProgressDialog(self.root, "Importing Packages")
            progress[0].progress.config(mode="indeterminate")
            progress[0].progress.start(20)
            progress[0].log_message(f"Importing from: {path}")
        self.root.after(0, create)
        import time; time.sleep(0.2)
        ok, out = run_action(["import", "-i", path,
                              "--accept-source-agreements",
                              "--accept-package-agreements"], timeout=1800)
        done = "Import complete" if ok else "Import finished with errors"
        self.root.after(0, lambda o=out: self._log(f"{done}:\n{o}"))
        self.root.after(0, lambda m=done: self.status_var.set(m))
        self.root.after(0, lambda o=out, m=done: (
            progress[0] and progress[0].progress.stop(),
            progress[0] and progress[0].log_message(o),
            progress[0] and progress[0].finish(m)))
        self.inst_loaded = False

    def _repair_winget(self):
        if not messagebox.askyesno("Repair", "Run winget repair?"):
            return
        threading.Thread(target=self._run_repair, daemon=True).start()

    def _run_repair(self):
        try:
            out = run_winget(["repair"], timeout=120)
            self.root.after(0, lambda o=out: self._log(f"Repair output:\n{o}"))
            self.root.after(0, lambda: self.status_var.set("Repair complete"))
        except Exception as exc:
            msg = str(exc)
            self.root.after(0, lambda m=msg: self._log(f"Repair error: {m}"))

    # ── Tab switching ──────────────────────────────────────────────────
    def _on_tab_changed(self, _e):
        idx = self.notebook.index("current")
        if   idx == 1 and not self.inst_loaded:     self._load_installed()
        elif idx == 2 and not self.upd_loaded:      self._load_updates()
        elif idx == 3 and not self.src_loaded:      self._load_sources()
        elif idx == 4 and not self.settings_loaded: self._load_settings_info()


# ──────────────────────────────────────────────────────────────────────
# Chocolatey Application
# ──────────────────────────────────────────────────────────────────────
class ChocoApp:
    def __init__(self, root):
        self.root = root
        self.status_var = tk.StringVar(value="Ready")
        status_lbl = tk.Label(root, textvariable=self.status_var,
                              relief=tk.SUNKEN, anchor=tk.W, padx=6, pady=3,
                              font=("Segoe UI", 9))
        status_lbl.pack(fill=tk.X, side=tk.BOTTOM)
        theme.register_status(status_lbl)
        c = theme.colors()
        status_lbl.config(bg=c["status_bg"], fg=c["status_fg"])

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        self._build_browse_tab()
        self._build_installed_tab()
        self._build_updates_tab()
        self._build_sources_tab()
        self._build_settings_tab()

        self._load_browse()
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

    # ── TAB 1 — Browse & Install ───────────────────────────────────────
    def _build_browse_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="  Browse & Install  ")
        bar = ttk.Frame(tab, padding=(8, 6))
        bar.pack(fill=tk.X)
        ttk.Label(bar, text="Search:").pack(side=tk.LEFT)
        self.browse_search = tk.StringVar()
        self.browse_search.trace_add("write", lambda *_: self._filter_browse())
        ttk.Entry(bar, textvariable=self.browse_search, width=40).pack(side=tk.LEFT, padx=(4, 12))
        self.browse_refresh_btn = ttk.Button(bar, text="↻ Refresh", command=self._load_browse)
        self.browse_refresh_btn.pack(side=tk.LEFT, padx=4)
        self.browse_install_btn = ttk.Button(bar, text="⬇ Install Selected", command=self._install_checked)
        self.browse_install_btn.pack(side=tk.RIGHT, padx=4)
        self.browse_uninstall_btn = ttk.Button(bar, text="✕ Uninstall Selected", command=self._uninstall_from_browse)
        self.browse_uninstall_btn.pack(side=tk.RIGHT, padx=4)
        self.browse_count = ttk.Label(bar, text="0 selected")
        self.browse_count.pack(side=tk.RIGHT, padx=8)

        self.browse_list = PackageListFrame(
            tab, columns=("ID", "Version"),
            detail_fn=lambda pkg_id: run_choco(["info", pkg_id], timeout=30))
        self.browse_list.pack(fill=tk.BOTH, expand=True, padx=4, pady=(0, 4))
        self.browse_list.bind("<<CheckChanged>>",
            lambda *_: self.browse_count.config(
                text=f"{self.browse_list.selected_count()} selected"))
        self.browse_all_rows = []

    def _load_browse(self):
        self.browse_refresh_btn.config(state=tk.DISABLED)
        self.status_var.set("Loading Chocolatey packages…")
        threading.Thread(target=self._fetch_browse, daemon=True).start()

    def _fetch_browse(self):
        try:
            out = run_choco(["search", "--limit-output"], timeout=300)
            rows = parse_choco_limit(out)
            self.browse_all_rows = rows
            self.root.after(0, self._populate_browse, rows)
        except Exception as exc:
            msg = str(exc)
            self.root.after(0, lambda m=msg: self.status_var.set(f"Error: {m}"))
            self.root.after(0, lambda: self.browse_refresh_btn.config(state=tk.NORMAL))

    def _populate_browse(self, rows):
        self.browse_list.set_rows(rows, id_col=0)
        self.status_var.set(
            f"Loaded {len(rows)} packages — type to search the full repo")
        self.browse_refresh_btn.config(state=tk.NORMAL)

    def _filter_browse(self):
        q = self.browse_search.get().strip()
        if not q:
            self.browse_list.set_rows(self.browse_all_rows, id_col=0)
            return
        if hasattr(self, "_search_after_id"):
            self.root.after_cancel(self._search_after_id)
        self._search_after_id = self.root.after(400, lambda: self._remote_search(q))

    def _remote_search(self, q):
        self.status_var.set(f"Searching for '{q}'…")
        threading.Thread(target=self._fetch_remote_search, args=(q,), daemon=True).start()

    def _fetch_remote_search(self, q):
        try:
            out = run_choco(["search", q, "--limit-output"], timeout=30)
            rows = parse_choco_limit(out)
            if self.browse_search.get().strip() == q:
                self.root.after(0, lambda r=rows: self.browse_list.set_rows(r, id_col=0))
                self.root.after(0, lambda: self.status_var.set(
                    f"{len(rows)} result(s) for '{q}'"))
        except Exception:
            pass

    def _install_checked(self):
        ids = self.browse_list.get_selected_ids()
        if not ids:
            messagebox.showinfo("Nothing selected",
                                "Check the boxes next to packages you want to install.")
            return
        preview = "\n".join(f"  • {p}" for p in ids[:25])
        if not messagebox.askyesno("Confirm Install",
                                   f"Install {len(ids)} package(s)?\n\n{preview}"):
            return
        self.browse_install_btn.config(state=tk.DISABLED)
        threading.Thread(target=self._run_installs, args=(ids,), daemon=True).start()

    def _run_installs(self, ids):
        total = len(ids)
        progress = [None]
        self.root.after(0, lambda: _create_progress(self.root, progress, "Installing Packages", total))
        import time; time.sleep(0.2)
        errors = []
        for i, pid in enumerate(ids, 1):
            self.root.after(0, lambda p=pid, n=i, t=total: (
                self.status_var.set(f"Installing {n}/{t}: {p}…"),
                progress[0] and progress[0].update_progress(n, t, p),
                progress[0] and progress[0].log_message(f"[{n}/{t}] Installing {p}…"),
            ))
            ok, out = run_choco_action(["install", pid, "-y", "--no-progress"])
            if ok:
                self.root.after(0, lambda p=pid, o=out: progress[0] and
                    progress[0].log_message(f"  ✓ {p} installed\n{o}\n"))
            else:
                errors.append(pid)
                self.root.after(0, lambda p=pid, o=out: progress[0] and
                    progress[0].log_message(f"  ✗ Failed: {p}\n{o}\n"))
        done = f"Installed {total - len(errors)}/{total} package(s)"
        self.root.after(0, lambda m=done: self.status_var.set(m))
        self.root.after(0, lambda: self.browse_install_btn.config(state=tk.NORMAL))
        self.root.after(0, lambda m=done: progress[0] and progress[0].finish(m))
        self.inst_loaded = False

    def _uninstall_from_browse(self):
        ids = self.browse_list.get_selected_ids()
        if not ids:
            messagebox.showinfo("Nothing selected",
                                "Check the boxes next to packages you want to uninstall.")
            return
        preview = "\n".join(f"  • {p}" for p in ids[:25])
        if not messagebox.askyesno("Confirm Uninstall",
                                   f"Uninstall {len(ids)} package(s)?\n\n{preview}"):
            return
        self.browse_uninstall_btn.config(state=tk.DISABLED)
        threading.Thread(target=self._run_uninstalls_from_browse,
                         args=(ids,), daemon=True).start()

    def _run_uninstalls_from_browse(self, ids):
        self._do_uninstall(ids, self.browse_uninstall_btn)
        self.inst_loaded = False

    # ── TAB 2 — Installed ──────────────────────────────────────────────
    def _build_installed_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="  Installed  ")
        bar = ttk.Frame(tab, padding=(8, 6))
        bar.pack(fill=tk.X)
        ttk.Label(bar, text="Search:").pack(side=tk.LEFT)
        self.inst_search = tk.StringVar()
        self.inst_search.trace_add("write", lambda *_: self._filter_installed())
        ttk.Entry(bar, textvariable=self.inst_search, width=40).pack(side=tk.LEFT, padx=(4, 12))
        self.inst_refresh_btn = ttk.Button(bar, text="↻ Refresh", command=self._load_installed)
        self.inst_refresh_btn.pack(side=tk.LEFT, padx=4)
        self.uninstall_btn = ttk.Button(bar, text="✕ Uninstall Selected", command=self._uninstall_checked)
        self.uninstall_btn.pack(side=tk.RIGHT, padx=4)
        self.inst_count = ttk.Label(bar, text="0 selected")
        self.inst_count.pack(side=tk.RIGHT, padx=8)
        self.inst_list = PackageListFrame(
            tab, columns=("ID", "Version"),
            detail_fn=lambda pkg_id: run_choco(["info", pkg_id], timeout=30))
        self.inst_list.pack(fill=tk.BOTH, expand=True, padx=4, pady=(0, 4))
        self.inst_list.bind("<<CheckChanged>>",
            lambda *_: self.inst_count.config(
                text=f"{self.inst_list.selected_count()} selected"))
        self.inst_all_rows = []
        self.inst_loaded   = False

    def _load_installed(self):
        self.inst_refresh_btn.config(state=tk.DISABLED)
        self.status_var.set("Loading installed Chocolatey packages…")
        threading.Thread(target=self._fetch_installed, daemon=True).start()

    def _fetch_installed(self):
        try:
            out = run_choco(["list", "--limit-output"], timeout=60)
            rows = parse_choco_limit(out)
            self.inst_all_rows = rows
            self.root.after(0, self._populate_installed, rows)
        except Exception as exc:
            msg = str(exc)
            self.root.after(0, lambda m=msg: self.status_var.set(f"Error: {m}"))
            self.root.after(0, lambda: self.inst_refresh_btn.config(state=tk.NORMAL))

    def _populate_installed(self, rows):
        self.inst_list.set_rows(rows, id_col=0)
        self.status_var.set(f"{len(rows)} packages installed via Chocolatey")
        self.inst_refresh_btn.config(state=tk.NORMAL)
        self.inst_loaded = True

    def _filter_installed(self):
        q = self.inst_search.get().lower()
        filtered = [r for r in self.inst_all_rows if q in r[0].lower()]
        self.inst_list.set_rows(filtered, id_col=0)

    def _uninstall_checked(self):
        ids = self.inst_list.get_selected_ids()
        if not ids:
            messagebox.showinfo("Nothing selected",
                                "Check the boxes next to packages you want to uninstall.")
            return
        preview = "\n".join(f"  • {p}" for p in ids[:25])
        if not messagebox.askyesno("Confirm Uninstall",
                                   f"Uninstall {len(ids)} package(s)?\n\n{preview}"):
            return
        self.uninstall_btn.config(state=tk.DISABLED)
        threading.Thread(target=self._run_uninstalls, args=(ids,), daemon=True).start()

    def _run_uninstalls(self, ids):
        self._do_uninstall(ids, self.uninstall_btn)
        self.root.after(0, self._load_installed)

    def _do_uninstall(self, ids, btn):
        total = len(ids)
        progress = [None]
        self.root.after(0, lambda: _create_progress(self.root, progress, "Uninstalling Packages", total))
        import time; time.sleep(0.2)
        errors = []
        for i, pid in enumerate(ids, 1):
            self.root.after(0, lambda p=pid, n=i, t=total: (
                self.status_var.set(f"Uninstalling {n}/{t}: {p}…"),
                progress[0] and progress[0].update_progress(n, t, p),
                progress[0] and progress[0].log_message(f"[{n}/{t}] Uninstalling {p}…"),
            ))
            ok, out = run_choco_action(["uninstall", pid, "-y"])
            if ok:
                self.root.after(0, lambda p=pid, o=out: progress[0] and
                    progress[0].log_message(f"  ✓ {p} removed\n{o}\n"))
            else:
                errors.append(pid)
                self.root.after(0, lambda p=pid, o=out: progress[0] and
                    progress[0].log_message(f"  ✗ Failed: {p}\n{o}\n"))
        done = f"Uninstalled {total - len(errors)}/{total} package(s)"
        self.root.after(0, lambda m=done: self.status_var.set(m))
        self.root.after(0, lambda: btn.config(state=tk.NORMAL))
        self.root.after(0, lambda m=done: progress[0] and progress[0].finish(m))

    # ── TAB 3 — Updates ───────────────────────────────────────────────
    def _build_updates_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="  Updates  ")
        bar = ttk.Frame(tab, padding=(8, 6))
        bar.pack(fill=tk.X)
        self.upd_refresh_btn = ttk.Button(bar, text="↻ Check for Updates", command=self._load_updates)
        self.upd_refresh_btn.pack(side=tk.LEFT, padx=4)
        self.upd_all_btn = ttk.Button(bar, text="⬆ Update ALL", command=self._update_all)
        self.upd_all_btn.pack(side=tk.LEFT, padx=4)
        self.upd_selected_btn = ttk.Button(bar, text="⬆ Update Selected", command=self._update_checked)
        self.upd_selected_btn.pack(side=tk.RIGHT, padx=4)
        self.upd_count = ttk.Label(bar, text="0 selected")
        self.upd_count.pack(side=tk.RIGHT, padx=8)
        self.upd_list = PackageListFrame(
            tab, columns=("ID", "Installed", "Available"),
            detail_fn=lambda pkg_id: run_choco(["info", pkg_id], timeout=30))
        self.upd_list.pack(fill=tk.BOTH, expand=True, padx=4, pady=(0, 4))
        self.upd_list.bind("<<CheckChanged>>",
            lambda *_: self.upd_count.config(
                text=f"{self.upd_list.selected_count()} selected"))
        self.upd_loaded = False

    def _load_updates(self):
        self.upd_refresh_btn.config(state=tk.DISABLED)
        self.status_var.set("Checking for Chocolatey updates…")
        threading.Thread(target=self._fetch_updates, daemon=True).start()

    def _fetch_updates(self):
        try:
            out = run_choco(["outdated", "--limit-output"], timeout=120)
            rows = parse_choco_outdated(out)
            self.root.after(0, self._populate_updates, rows)
        except Exception as exc:
            msg = str(exc)
            self.root.after(0, lambda m=msg: self.status_var.set(f"Error: {m}"))
            self.root.after(0, lambda: self.upd_refresh_btn.config(state=tk.NORMAL))

    def _populate_updates(self, rows):
        self.upd_list.set_rows(rows, id_col=0)
        self.status_var.set(f"{len(rows)} update(s) available")
        self.upd_refresh_btn.config(state=tk.NORMAL)
        self.upd_loaded = True

    def _update_all(self):
        if not messagebox.askyesno("Update All", "Update ALL Chocolatey packages?"):
            return
        self.upd_all_btn.config(state=tk.DISABLED)
        threading.Thread(target=self._run_update_all, daemon=True).start()

    def _run_update_all(self):
        progress = [None]
        def create():
            progress[0] = ProgressDialog(self.root, "Updating All Packages")
            progress[0].progress.config(mode="indeterminate")
            progress[0].progress.start(20)
            progress[0].log_message("Running: choco upgrade all -y")
        self.root.after(0, create)
        import time; time.sleep(0.2)
        ok, out = run_choco_action(["upgrade", "all", "-y", "--no-progress"], timeout=1800)
        self.root.after(0, lambda o=out: progress[0] and
            progress[0].log_message(f"\n--- Output ---\n{o}"))
        done = "Update all complete" if ok else "Update all finished with errors"
        self.root.after(0, lambda m=done: self.status_var.set(m))
        self.root.after(0, lambda: self.upd_all_btn.config(state=tk.NORMAL))
        self.root.after(0, lambda m=done: (
            progress[0] and progress[0].progress.stop(),
            progress[0] and progress[0].finish(m)))
        self.root.after(500, self._load_updates)

    def _update_checked(self):
        ids = self.upd_list.get_selected_ids()
        if not ids:
            messagebox.showinfo("Nothing selected",
                                "Check the boxes next to packages you want to update.")
            return
        self.upd_selected_btn.config(state=tk.DISABLED)
        threading.Thread(target=self._run_update_selected, args=(ids,), daemon=True).start()

    def _run_update_selected(self, ids):
        total = len(ids)
        progress = [None]
        self.root.after(0, lambda: _create_progress(self.root, progress, "Updating Packages", total))
        import time; time.sleep(0.2)
        errors = []
        for i, pid in enumerate(ids, 1):
            self.root.after(0, lambda p=pid, n=i, t=total: (
                self.status_var.set(f"Updating {n}/{t}: {p}…"),
                progress[0] and progress[0].update_progress(n, t, p),
                progress[0] and progress[0].log_message(f"[{n}/{t}] Updating {p}…"),
            ))
            ok, out = run_choco_action(["upgrade", pid, "-y", "--no-progress"])
            if ok:
                self.root.after(0, lambda p=pid, o=out: progress[0] and
                    progress[0].log_message(f"  ✓ {p} updated\n{o}\n"))
            else:
                errors.append(pid)
                self.root.after(0, lambda p=pid, o=out: progress[0] and
                    progress[0].log_message(f"  ✗ Failed: {p}\n{o}\n"))
        done = f"Updated {total - len(errors)}/{total} package(s)"
        self.root.after(0, lambda m=done: self.status_var.set(m))
        self.root.after(0, lambda: self.upd_selected_btn.config(state=tk.NORMAL))
        self.root.after(0, lambda m=done: progress[0] and progress[0].finish(m))
        self.root.after(500, self._load_updates)

    # ── TAB 4 — Sources ───────────────────────────────────────────────
    def _build_sources_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="  Sources  ")
        bar = ttk.Frame(tab, padding=(8, 6))
        bar.pack(fill=tk.X)
        self.src_refresh_btn = ttk.Button(bar, text="↻ Refresh Sources", command=self._load_sources)
        self.src_refresh_btn.pack(side=tk.LEFT, padx=4)
        add_frame = ttk.LabelFrame(tab, text="Add a Source", padding=8)
        add_frame.pack(fill=tk.X, padx=8, pady=(4, 0))
        ttk.Label(add_frame, text="Name:").grid(row=0, column=0, sticky=tk.W, padx=4)
        self.src_name_var = tk.StringVar()
        ttk.Entry(add_frame, textvariable=self.src_name_var, width=28).grid(row=0, column=1, padx=4)
        ttk.Label(add_frame, text="URL:").grid(row=0, column=2, sticky=tk.W, padx=4)
        self.src_url_var = tk.StringVar()
        ttk.Entry(add_frame, textvariable=self.src_url_var, width=48).grid(row=0, column=3, padx=4)
        ttk.Button(add_frame, text="Add Source", command=self._add_source).grid(row=0, column=4, padx=8)
        self.src_list = PackageListFrame(tab, columns=("Name", "URL"), show_checks=False)
        self.src_list.pack(fill=tk.BOTH, expand=True, padx=4, pady=(4, 4))
        self.src_loaded = False

    def _load_sources(self):
        self.src_refresh_btn.config(state=tk.DISABLED)
        self.status_var.set("Loading Chocolatey sources…")
        threading.Thread(target=self._fetch_sources, daemon=True).start()

    def _fetch_sources(self):
        try:
            out = run_choco(["source", "list"], timeout=30)
            rows = parse_choco_sources(out)
            self.root.after(0, self._populate_sources, rows)
        except Exception as exc:
            msg = str(exc)
            self.root.after(0, lambda m=msg: self.status_var.set(f"Error: {m}"))
            self.root.after(0, lambda: self.src_refresh_btn.config(state=tk.NORMAL))

    def _populate_sources(self, rows):
        self.src_list.set_rows(rows, id_col=0)
        self.status_var.set(f"{len(rows)} source(s)")
        self.src_refresh_btn.config(state=tk.NORMAL)
        self.src_loaded = True

    def _add_source(self):
        name = self.src_name_var.get().strip()
        url  = self.src_url_var.get().strip()
        if not name or not url:
            messagebox.showwarning("Missing info", "Enter both a name and URL.")
            return
        threading.Thread(target=self._run_add_source, args=(name, url), daemon=True).start()

    def _run_add_source(self, name, url):
        try:
            subprocess.run(["choco", "source", "add",
                            f"--name={name}", f"--source={url}"],
                           timeout=30, **SUBPROCESS_FLAGS)
            self.root.after(0, lambda n=name: self.status_var.set(f"Source '{n}' added"))
            self.root.after(0, self._load_sources)
        except Exception as exc:
            msg = str(exc)
            self.root.after(0, lambda m=msg: messagebox.showerror("Error", m))

    # ── TAB 5 — Settings & Info ────────────────────────────────────────
    def _build_settings_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="  Settings & Info  ")
        frame = ttk.Frame(tab, padding=16)
        frame.pack(fill=tk.BOTH, expand=True)

        info_frame = ttk.LabelFrame(frame, text="Chocolatey Info", padding=12)
        info_frame.pack(fill=tk.X, pady=(0, 12))
        self.info_text = tk.Text(info_frame, height=6, wrap=tk.WORD,
                                 state=tk.DISABLED, font=("Consolas", 10))
        self.info_text.pack(fill=tk.X)
        theme.register_text(self.info_text)
        c = theme.colors()
        self.info_text.config(bg=c["text_bg"], fg=c["text_fg"],
                              insertbackground=c["fg"],
                              selectbackground=c["sel_bg"],
                              selectforeground=c["sel_fg"])

        btn_frame = ttk.LabelFrame(frame, text="Quick Actions", padding=12)
        btn_frame.pack(fill=tk.X, pady=(0, 12))
        actions = [
            ("Show Choco Config",         self._show_config),
            ("Upgrade Chocolatey",        self._upgrade_choco),
            ("Open Choco Config File",    self._open_config_file),
            ("Check Outdated (verbose)",  self._check_outdated_verbose),
        ]
        for i, (label, cmd) in enumerate(actions):
            ttk.Button(btn_frame, text=label, command=cmd, width=28).grid(
                row=i // 2, column=i % 2, padx=8, pady=4, sticky=tk.W)

        log_frame = ttk.LabelFrame(frame, text="Command Output", padding=8)
        log_frame.pack(fill=tk.BOTH, expand=True)
        inner, self.log_text = _make_log_widget(log_frame)
        inner.pack(fill=tk.BOTH, expand=True)
        self.settings_loaded = False

    def _log(self, text):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, text + "\n\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def _load_settings_info(self):
        threading.Thread(target=self._fetch_info, daemon=True).start()

    def _fetch_info(self):
        try:
            version = run_choco(["--version"], timeout=10)
            config  = run_choco(["config", "list"], timeout=15)
            out = f"Chocolatey Version: {version.strip()}\n\n{config}"
        except Exception as exc:
            out = f"Error: {exc}"
        self.root.after(0, lambda o=out: self._show_info(o))

    def _show_info(self, text):
        self.info_text.config(state=tk.NORMAL)
        self.info_text.delete("1.0", tk.END)
        self.info_text.insert(tk.END, text)
        self.info_text.config(state=tk.DISABLED)
        self.settings_loaded = True

    def _show_config(self):
        threading.Thread(target=lambda: (
            self.root.after(0, lambda: self._log(
                "Choco config:\n" + run_choco(["config", "list"], timeout=15))),
            self.root.after(0, lambda: self.status_var.set("Config loaded")),
        ), daemon=True).start()

    def _upgrade_choco(self):
        if not messagebox.askyesno("Upgrade Chocolatey",
                                   "Upgrade Chocolatey itself to the latest version?"):
            return
        threading.Thread(target=self._run_upgrade_choco, daemon=True).start()

    def _run_upgrade_choco(self):
        ok, out = run_choco_action(["upgrade", "chocolatey", "-y"])
        msg = "Chocolatey upgraded" if ok else "Upgrade finished with errors"
        self.root.after(0, lambda o=out, m=msg: self._log(f"{m}:\n{o}"))
        self.root.after(0, lambda m=msg: self.status_var.set(m))

    def _open_config_file(self):
        path = os.path.expandvars(r"%ChocolateyInstall%\config\chocolatey.config")
        try:
            os.startfile(path)
            self.root.after(0, lambda: self.status_var.set("Opened config file"))
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    def _check_outdated_verbose(self):
        threading.Thread(target=lambda: (
            self.root.after(0, lambda: self.status_var.set("Checking outdated…")),
            self.root.after(0, lambda: self._log(
                "Outdated packages:\n" + run_choco(["outdated"], timeout=120))),
            self.root.after(0, lambda: self.status_var.set("Outdated check complete")),
        ), daemon=True).start()

    # ── Tab switching ──────────────────────────────────────────────────
    def _on_tab_changed(self, _e):
        idx = self.notebook.index("current")
        if   idx == 1 and not self.inst_loaded:     self._load_installed()
        elif idx == 2 and not self.upd_loaded:      self._load_updates()
        elif idx == 3 and not self.src_loaded:      self._load_sources()
        elif idx == 4 and not self.settings_loaded: self._load_settings_info()


# ──────────────────────────────────────────────────────────────────────
# Shared progress helper
# ──────────────────────────────────────────────────────────────────────
def _create_progress(root, holder, title, total):
    holder[0] = ProgressDialog(root, title)
    holder[0].set_total(total)


# ──────────────────────────────────────────────────────────────────────
# Setup Tab
# ──────────────────────────────────────────────────────────────────────
def build_setup_tab(notebook):
    tab = ttk.Frame(notebook)
    notebook.add(tab, text="   Setup   ")

    canvas = tk.Canvas(tab, highlightthickness=0)
    vsb = ttk.Scrollbar(tab, orient=tk.VERTICAL, command=canvas.yview)
    canvas.configure(yscrollcommand=vsb.set)
    vsb.pack(side=tk.RIGHT, fill=tk.Y)
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    inner = ttk.Frame(canvas)
    win_id = canvas.create_window((0, 0), window=inner, anchor="nw")

    def _on_resize(e):
        canvas.itemconfig(win_id, width=e.width)
    canvas.bind("<Configure>", _on_resize)
    inner.bind("<Configure>",
               lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

    pad = dict(padx=20, pady=10)

    # ── Winget section ────────────────────────────────────────────────
    wg = ttk.LabelFrame(inner, text="  Winget  ", padding=16)
    wg.pack(fill=tk.X, **pad)

    ttk.Label(wg, text="Windows Package Manager (Winget)",
              font=("Segoe UI", 12, "bold")).pack(anchor=tk.W)
    ttk.Label(wg, wraplength=700, justify=tk.LEFT, text=(
        "Winget is Microsoft's official command-line package manager for Windows. "
        "It lets you discover, install, upgrade, remove, and configure applications. "
        "Winget is built into Windows 11 and available for Windows 10 via the "
        "Microsoft Store (App Installer)."
    )).pack(anchor=tk.W, pady=(4, 10))

    wg_status = tk.StringVar(value="Checking…")
    ttk.Label(wg, text="Status:", font=("Segoe UI", 9, "bold")).pack(anchor=tk.W)
    ttk.Label(wg, textvariable=wg_status).pack(anchor=tk.W, pady=(0, 8))

    btn_row = ttk.Frame(wg)
    btn_row.pack(anchor=tk.W)
    ttk.Button(btn_row, text="⬇  Get Winget (Microsoft Store)",
               command=lambda: webbrowser.open("https://aka.ms/getwinget")
               ).pack(side=tk.LEFT, padx=(0, 8))
    ttk.Button(btn_row, text="  GitHub Releases",
               command=lambda: webbrowser.open(
                   "https://github.com/microsoft/winget-cli/releases")
               ).pack(side=tk.LEFT, padx=(0, 8))
    ttk.Button(btn_row, text="↻ Check Status",
               command=lambda: _check_tool("winget", ["--version"], wg_status)
               ).pack(side=tk.LEFT)

    ttk.Separator(inner, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=20, pady=4)

    # ── Chocolatey section ────────────────────────────────────────────
    ch = ttk.LabelFrame(inner, text="  Chocolatey  ", padding=16)
    ch.pack(fill=tk.X, **pad)

    ttk.Label(ch, text="Chocolatey Package Manager",
              font=("Segoe UI", 12, "bold")).pack(anchor=tk.W)
    ttk.Label(ch, wraplength=700, justify=tk.LEFT, text=(
        "Chocolatey is the largest repository of Windows software packages, "
        "with over 9,000 community-maintained packages. It automates software "
        "management using a NuGet-based infrastructure and PowerShell. "
        "Chocolatey works great alongside Winget for packages not available in "
        "the Microsoft Store ecosystem."
    )).pack(anchor=tk.W, pady=(4, 10))

    ch_status = tk.StringVar(value="Checking…")
    ttk.Label(ch, text="Status:", font=("Segoe UI", 9, "bold")).pack(anchor=tk.W)
    ttk.Label(ch, textvariable=ch_status).pack(anchor=tk.W, pady=(0, 4))

    ttk.Label(ch, text="PowerShell install command:",
              font=("Segoe UI", 9, "bold")).pack(anchor=tk.W, pady=(6, 2))

    cmd_frame = ttk.Frame(ch)
    cmd_frame.pack(fill=tk.X, pady=(0, 8))
    ps_cmd = (
        "Set-ExecutionPolicy Bypass -Scope Process -Force; "
        "[System.Net.ServicePointManager]::SecurityProtocol = "
        "[System.Net.SecurityProtocolType]::Tls12; "
        "iex ((New-Object System.Net.WebClient).DownloadString("
        "'https://community.chocolatey.org/install.ps1'))"
    )
    c = theme.colors()
    cmd_text = tk.Text(cmd_frame, height=3, wrap=tk.WORD,
                       font=("Consolas", 9), state=tk.NORMAL)
    cmd_text.insert(tk.END, ps_cmd)
    cmd_text.config(state=tk.DISABLED)
    cmd_text.pack(fill=tk.X)
    theme.register_text(cmd_text)
    cmd_text.config(bg=c["text_bg"], fg=c["text_fg"],
                    selectbackground=c["sel_bg"], selectforeground=c["sel_fg"])

    btn_row2 = ttk.Frame(ch)
    btn_row2.pack(anchor=tk.W, pady=(4, 0))
    ttk.Button(btn_row2, text="⬇  Chocolatey Website",
               command=lambda: webbrowser.open("https://chocolatey.org/install")
               ).pack(side=tk.LEFT, padx=(0, 8))
    ttk.Button(btn_row2, text="↻ Check Status",
               command=lambda: _check_tool("choco", ["--version"], ch_status)
               ).pack(side=tk.LEFT)

    # Run initial status checks
    threading.Thread(target=lambda: _check_tool("winget", ["--version"], wg_status),
                     daemon=True).start()
    threading.Thread(target=lambda: _check_tool("choco", ["--version"], ch_status),
                     daemon=True).start()


def _check_tool(cmd, args, status_var):
    try:
        r = subprocess.run([cmd] + args, timeout=10, **SUBPROCESS_FLAGS)
        ver = r.stdout.strip().splitlines()[0] if r.stdout.strip() else "unknown"
        status_var.set(f"✓  Installed — {ver}")
    except FileNotFoundError:
        status_var.set("✗  Not installed")
    except Exception as exc:
        status_var.set(f"✗  Error: {exc}")


# ──────────────────────────────────────────────────────────────────────
# About Tab
# ──────────────────────────────────────────────────────────────────────
def build_about_tab(notebook):
    tab = ttk.Frame(notebook)
    notebook.add(tab, text="   About   ")

    outer = ttk.Frame(tab, padding=40)
    outer.place(relx=0.5, rely=0.5, anchor="center")

    # App name banner
    ttk.Label(outer, text=APP_NAME,
              font=("Segoe UI", 36, "bold")).pack()
    ttk.Label(outer, text=f"Version {APP_VERSION}",
              font=("Segoe UI", 11)).pack(pady=(0, 4))

    ttk.Separator(outer, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=12)

    ttk.Label(outer, text="Windows Package Manager",
              font=("Segoe UI", 13, "bold")).pack()
    ttk.Label(outer,
              text="A professional GUI front-end for Winget and Chocolatey.\n"
                   "Browse, install, update, and remove software with ease.",
              font=("Segoe UI", 10), justify=tk.CENTER).pack(pady=(4, 16))

    ttk.Separator(outer, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=4)

    info = ttk.Frame(outer)
    info.pack(pady=12)
    for label, value in [
        ("Developed by", APP_AUTHOR),
        ("Company",      APP_COMPANY),
        ("Year",         "2026"),
        ("License",      "MIT License"),
    ]:
        row = ttk.Frame(info)
        row.pack(anchor=tk.W, pady=2)
        ttk.Label(row, text=f"{label}:", font=("Segoe UI", 10, "bold"),
                  width=14, anchor=tk.E).pack(side=tk.LEFT)
        ttk.Label(row, text=value, font=("Segoe UI", 10)).pack(side=tk.LEFT, padx=(8, 0))

    ttk.Separator(outer, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=12)

    links = ttk.Frame(outer)
    links.pack()
    ttk.Label(links, text="Package manager downloads:",
              font=("Segoe UI", 9, "bold")).pack()

    lnk_row = ttk.Frame(links)
    lnk_row.pack(pady=4)
    ttk.Button(lnk_row, text="Get Winget",
               command=lambda: webbrowser.open("https://aka.ms/getwinget")
               ).pack(side=tk.LEFT, padx=6)
    ttk.Button(lnk_row, text="Get Chocolatey",
               command=lambda: webbrowser.open("https://chocolatey.org/install")
               ).pack(side=tk.LEFT, padx=6)

    ttk.Label(outer,
              text=f"© 2026 {APP_COMPANY}  ·  {APP_NAME}  ·  MIT License",
              font=("Segoe UI", 8), foreground="gray").pack(pady=(16, 0))


# ──────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────
def main():
    root = tk.Tk()
    root.title(f"{APP_NAME} — Windows Package Manager  |  {APP_COMPANY}")
    root.geometry("1200x820")
    root.minsize(980, 620)

    style = ttk.Style()
    theme.init(root, style)

    # ── Header bar ────────────────────────────────────────────────────
    c = theme.colors()
    header = tk.Frame(root, bg=c["hdr_bg"], height=54)
    header.pack(fill=tk.X, side=tk.TOP)
    header.pack_propagate(False)

    tk.Label(header, text=APP_NAME,
             font=("Segoe UI", 20, "bold"),
             bg=c["hdr_bg"], fg=c["hdr_fg"]).pack(side=tk.LEFT, padx=(18, 6), pady=10)
    tk.Label(header,
             text=f"by {APP_COMPANY}  ·  {APP_AUTHOR}",
             font=("Segoe UI", 9),
             bg=c["hdr_bg"], fg=c["hdr_sub"]).pack(side=tk.LEFT, pady=16)

    # Dark mode toggle (right side of header)
    dark_var = tk.BooleanVar(value=False)

    def _toggle_dark():
        theme.toggle()
        nc = theme.colors()
        header.config(bg=nc["hdr_bg"])
        for w in header.winfo_children():
            if isinstance(w, tk.Label):
                w.config(bg=nc["hdr_bg"])
                if w.cget("font") and "20" in str(w.cget("font")):
                    w.config(fg=nc["hdr_fg"])
                else:
                    w.config(fg=nc["hdr_sub"])
        # Re-tag checked rows on all visible treeviews
        for w in root.winfo_children():
            _retag_treeviews(w, nc["checked_bg"])

    toggle_btn = tk.Checkbutton(
        header, text="  🌙  Dark Mode",
        variable=dark_var, command=_toggle_dark,
        font=("Segoe UI", 10),
        bg=c["hdr_bg"], fg=c["hdr_fg"],
        selectcolor=c["hdr_bg"],
        activebackground=c["hdr_bg"], activeforeground=c["hdr_fg"],
        cursor="hand2", bd=0, relief=tk.FLAT)
    toggle_btn.pack(side=tk.RIGHT, padx=20)

    # ── Manager notebook ──────────────────────────────────────────────
    manager_nb = ttk.Notebook(root)
    manager_nb.pack(fill=tk.BOTH, expand=True)

    winget_frame = ttk.Frame(manager_nb)
    manager_nb.add(winget_frame, text="     Winget     ")
    WingetApp(winget_frame)

    choco_frame = ttk.Frame(manager_nb)
    manager_nb.add(choco_frame, text="   Chocolatey   ")
    ChocoApp(choco_frame)

    build_setup_tab(manager_nb)
    build_about_tab(manager_nb)

    root.mainloop()


def _retag_treeviews(widget, checked_color):
    """Recursively update the 'checked' tag background on all Treeview widgets."""
    if isinstance(widget, ttk.Treeview):
        widget.tag_configure("checked", background=checked_color)
    for child in widget.winfo_children():
        _retag_treeviews(child, checked_color)


if __name__ == "__main__":
    main()
