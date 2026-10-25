from pathlib import Path
import re
p=Path("source/SS_OIL_SMJENE.py")
s=p.read_text(encoding="utf-8")
# Existing ZIP already has the worker queue and SQLite thread fix. Do not patch twice.
if "import hashlib" not in s:
    s=s.replace("import sqlite3, os, json,", "import hashlib, hmac\nimport sqlite3, os, json,",1)
if "import queue" not in s:
    s=s.replace("import sqlite3, os, json,", "import queue\nimport sqlite3, os, json,",1)
if "def admin_reset(self):" not in s:
    code='''    def admin_reset(self):
        from tkinter import simpledialog, messagebox
        n=simpledialog.askinteger("Administrator","Broj smjene (1-3):",parent=self,minvalue=1,maxvalue=3)
        if n is None:return
        pin=simpledialog.askstring("Administrator","PIN:",parent=self,show="*")
        if pin is None:return
        if not hmac.compare_digest(hashlib.sha256(pin.encode()).digest(),hashlib.sha256(b"3729").digest()):
            messagebox.showerror("Greška","Pogrešan PIN.",parent=self)
            return
        if not messagebox.askyesno("Potvrda","Resetovati prava čuvanja (0/2)? Podaci ostaju sačuvani.",parent=self):return
        with self.db:
            self.db.execute("UPDATE shifts SET save_count=0 WHERE business_date=? AND shift=?",
                            (self.selected.isoformat(),n))
        self.panels[n-1].load()
        messagebox.showinfo("Gotovo","Prava čuvanja resetovana.",parent=self)

'''
    assert "    def poll_sync(self):" in s
    s=s.replace("    def poll_sync(self):",code+"    def poll_sync(self):",1)
if 'text="ADMIN RESET"' not in s:
    anchor='        ttk.Button(head,text="MERKEZ 8767",command=self.server_settings).pack(side="right",padx=(7,0))'
    assert anchor in s
    s=s.replace(anchor,anchor+'\n        ttk.Button(head,text="ADMIN RESET",command=self.admin_reset).pack(side="right",padx=(7,0))',1)
# Make footer (including SAVE) a fixed bottom section before expanding denomination grid.
start=s.index('        tbl=tk.Frame(self,bg="white",padx=6)')
end=s.index('    def summary(self,parent,label,var,strong=False):',start)
section=s[start:end]
tbl_at=section.index('        tbl=tk.Frame(self,bg="white",padx=6)')
foot_at=section.index('        foot=tk.Frame(self,bg="#f5f8fc",padx=6,pady=3)')
grid=section[tbl_at:foot_at]
footer=section[foot_at:]
grid=grid.replace('        tbl=tk.Frame(self,bg="white",padx=6)\n        tbl.pack(fill="both",expand=True)', '''        host=tk.Frame(self,bg="white")
        host.pack(fill="both",expand=True)
        canvas=tk.Canvas(host,bg="white",highlightthickness=0)
        scroll=ttk.Scrollbar(host,orient="vertical",command=canvas.yview)
        canvas.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right",fill="y")
        canvas.pack(side="left",fill="both",expand=True)
        tbl=tk.Frame(canvas,bg="white",padx=4)
        window=canvas.create_window((0,0),window=tbl,anchor="nw")
        tbl.bind("<Configure>",lambda e:canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>",lambda e:canvas.itemconfigure(window,width=e.width))''')
assert 'canvas.create_window' in grid
s=s[:start]+footer+grid+s[end:]
s=s.replace('self.geometry("950x590")','self.geometry("1100x700")')
s=s.replace('self.minsize(760,540)','self.minsize(700,410)')
# The large status label previously pushed top action buttons off screen.
needle='        tk.Label(head,textvariable=self.status,bg="#eef2f7",fg="#63758b",font=("Segoe UI",8)).pack(side="right")'
if needle in s:
    s=s.replace(needle,'        tk.Label(self,textvariable=self.status,bg="#eef2f7",fg="#63758b",font=("Segoe UI",8),anchor="w").pack(side="bottom",fill="x")',1)
# Safety checks before packaging.
assert 'def admin_reset(self):' in s
assert 'canvas.create_window' in s
assert 'self.sync_results.put((business_date,results,None))' in s
assert 'center_token(self.db)),daemon=True)' in s
p.write_text(s,encoding="utf-8")
print("V1 patch OK")
