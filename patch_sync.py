from pathlib import Path
p=Path("source/SS_OIL_SMJENE.py")
s=p.read_text(encoding="utf-8")
if "import hashlib, hmac" not in s:
    s=s.replace("import sqlite3, os, json,", "import hashlib, hmac\nimport sqlite3, os, json,", 1)
if "def manual_sync(self):" not in s:
    s=s.replace("    def poll_sync(self):", '    def manual_sync(self):\n        self.status.set("Provjera veze sa PC centrom...")\n        self.poll_sync()\n\n    def poll_sync(self):', 1)
if 'text="SINHRONIZUJ"' not in s:
    anchor='        ttk.Button(head,text="MERKEZ 8767",command=self.server_settings).pack(side="right",padx=(7,0))'
    if anchor not in s: raise RuntimeError("Cannot locate toolbar: "+anchor)
    s=s.replace(anchor,anchor+'\n        ttk.Button(head,text="SINHRONIZUJ",command=self.manual_sync).pack(side="right",padx=(7,0))',1)
if "def admin_reset(self):" not in s:
    code='''    def admin_reset(self):
        from tkinter import simpledialog, messagebox
        selected=simpledialog.askinteger("Administrator", "Broj smjene (1-3):",parent=self,minvalue=1,maxvalue=3)
        if selected is None:return
        pin=simpledialog.askstring("Administrator", "Unesite PIN:",show="*",parent=self)
        if pin is None:return
        hashed=lambda x:hashlib.sha256(x.encode("utf-8")).digest()
        if not hmac.compare_digest(hashed(pin),hashed("3729")):
            messagebox.showerror("Greška","Pogrešan PIN.",parent=self)
            return
        if not messagebox.askyesno("Potvrda","Resetovati prava čuvanja (0/2)? Postojeći zapisi ostaju.",parent=self):
            return
        with self.db:
            self.db.execute("UPDATE shifts SET save_count=0 WHERE business_date=? AND shift=?",
                            (self.selected.isoformat(),selected))
        self.panels[selected-1].load()
        messagebox.showinfo("Gotovo","Prava čuvanja resetovana (0/2).",parent=self)

'''
    s=s.replace("    def poll_sync(self):",code+"    def poll_sync(self):",1)
if 'text="ADMIN RESET"' not in s:
    anchor='        ttk.Button(head,text="SINHRONIZUJ",command=self.manual_sync).pack(side="right",padx=(7,0))'
    s=s.replace(anchor,anchor+'\n        ttk.Button(head,text="ADMIN RESET",command=self.admin_reset).pack(side="right",padx=(7,0))',1)
# Legacy worker-thread Tk calls, if present, are replaced by a queue bridge.
if "self.after(0,lambda:self._apply_sync(" in s:
    if "import queue" not in s:s=s.replace("import hashlib, hmac","import hashlib, hmac, queue",1)
    s=s.replace("self.after(0,lambda:self._apply_sync(business_date,results,None))","self.sync_results.put((business_date,results,None))")
    s=s.replace("try:self.after(0,lambda:self._apply_sync(business_date,[],msg))\n            except RuntimeError:pass","self.sync_results.put((business_date,[],msg))")
    if "def drain_sync_results(self):" not in s:
        code='''    def drain_sync_results(self):
        try:
            while True:
                day,results,error=self.sync_results.get_nowait()
                self._apply_sync(day,results,error)
        except queue.Empty:
            pass
        self.after(250,self.drain_sync_results)

'''
        s=s.replace("    def poll_sync(self):",code+"    def poll_sync(self):",1)
        s=s.replace("        self.sync_running=False\n        self.after(1200,self.poll_sync)","        self.sync_running=False\n        self.sync_results=queue.Queue()\n        self.after(250,self.drain_sync_results)\n        self.after(1200,self.poll_sync)",1)
p.write_text(s,encoding="utf-8")
print("Patch applied successfully")
