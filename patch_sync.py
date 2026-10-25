from pathlib import Path
import re
p=Path("source/SS_OIL_SMJENE.py")
s=p.read_text(encoding="utf-8")
# Fix background SQLite access only when older source still has it.
if 'args=(host,business_date,snapshot),daemon=True' in s:
    s=s.replace('args=(host,business_date,snapshot),daemon=True','args=(host,business_date,snapshot,center_token(self.db)),daemon=True')
    s=s.replace('def _sync_thread(self,host,business_date,snapshot):','def _sync_thread(self,host,business_date,snapshot,token):')
    s=s.replace('            token=center_token(self.db)\n','')
# Make footer visible: pack footer before expanding table.
a=s.find('        tbl=tk.Frame(self,bg="white",padx=6)')
b=s.find('    def summary(self,parent,label,var,strong=False):',a)
if a>=0 and b>a:
    part=s[a:b]
    f=part.find('        foot=tk.Frame(self,bg="#f5f8fc",padx=6,pady=3)')
    if f>=0:
        table=part[:f]
        footer=part[f:]
        table=table.replace('        tbl=tk.Frame(self,bg="white",padx=6)\n        tbl.pack(fill="both",expand=True)', '''        host=tk.Frame(self,bg="white")
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
        s=s[:a]+footer+table+s[b:]
s=s.replace('self.geometry("950x590")','self.geometry("1100x700")')
s=s.replace('self.minsize(760,540)','self.minsize(700,410)')
# Admin reset without deleting any records.
if 'def admin_reset(self):' not in s:
    s=s.replace('from pathlib import Path','from pathlib import Path\nimport hashlib, hmac',1)
    code='''    def admin_reset(self):
        from tkinter import simpledialog, messagebox
        n=simpledialog.askinteger("Administrator","Broj smjene (1-3):",parent=self,minvalue=1,maxvalue=3)
        if n is None:return
        pin=simpledialog.askstring("Administrator","PIN:",parent=self,show="*")
        if pin is None:return
        if not hmac.compare_digest(hashlib.sha256(pin.encode()).digest(),hashlib.sha256(b"3729").digest()):
            messagebox.showerror("Greška","Pogrešan PIN.",parent=self)
            return
        if not messagebox.askyesno("Potvrda","Resetovati prava čuvanja (0/2)? Podaci ostaju.",parent=self):return
        with self.db:
            self.db.execute("UPDATE shifts SET save_count=0 WHERE business_date=? AND shift=?",(self.selected.isoformat(),n))
        self.panels[n-1].load()

'''
    s=s.replace('    def poll_sync(self):',code+'    def poll_sync(self):',1)
if 'text="ADMIN RESET"' not in s:
    anchor='        ttk.Button(head,text="MERKEZ 8767",command=self.server_settings).pack(side="right",padx=(7,0))'
    s=s.replace(anchor,anchor+'\n        ttk.Button(head,text="ADMIN RESET",command=self.admin_reset).pack(side="right",padx=(7,0))',1)
p.write_text(s,encoding="utf-8")
print("Patch completed")
