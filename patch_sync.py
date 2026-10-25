from pathlib import Path
p=Path("source/SS_OIL_SMJENE.py")
s=p.read_text(encoding="utf-8")
if "import hashlib, hmac" not in s:
    s=s.replace("import sqlite3, os, json,", "import hashlib, hmac\nimport sqlite3, os, json,", 1)
if 'import queue' not in s:
    s=s.replace('import hashlib, hmac','import hashlib, hmac, queue',1)
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

# VERIFIED FIX: SQLite and Tkinter may only be used on the UI thread.
needle='threading.Thread(target=self._sync_thread,args=(host,business_date,snapshot),daemon=True).start()'
assert needle in s
s=s.replace(needle,'threading.Thread(target=self._sync_thread,args=(host,business_date,snapshot,center_token(self.db)),daemon=True).start()',1)
assert 'def _sync_thread(self,host,business_date,snapshot):' in s
s=s.replace('def _sync_thread(self,host,business_date,snapshot):','def _sync_thread(self,host,business_date,snapshot,token):',1)
assert '            token=center_token(self.db)\\n' in s
s=s.replace('            token=center_token(self.db)\\n','',1)
assert 'self.after(0,lambda:self._apply_sync(business_date,results,None))' in s
s=s.replace('self.after(0,lambda:self._apply_sync(business_date,results,None))','self.sync_results.put((business_date,results,None))',1)
needle='try:self.after(0,lambda:self._apply_sync(business_date,[],msg))\\n            except RuntimeError:pass'
assert needle in s
s=s.replace(needle,'self.sync_results.put((business_date,[],msg))')
assert '        self.sync_running=False\\n        self.after(1200,self.poll_sync)' in s
s=s.replace('        self.sync_running=False\\n        self.after(1200,self.poll_sync)','        self.sync_running=False\\n        self.sync_results=queue.Queue()\\n        self.after(250,self.drain_sync_results)\\n        self.after(1200,self.poll_sync)',1)
code='''    def drain_sync_results(self):
        try:
            while True:
                day,results,error=self.sync_results.get_nowait()
                self._apply_sync(day,results,error)
        except queue.Empty:
            pass
        self.after(250,self.drain_sync_results)

'''
s=s.replace('    def poll_sync(self):',code+'    def poll_sync(self):',1)
# Existing phone values win over unsynced stale PC data.
needle='                if item["pending_send"] and item["confirmed_total"]:\\n                    # If the remote was changed since the last successful sync,'
assert needle in s
s=s.replace(needle,'                if item["pending_send"] and item["confirmed_total"]:\\n                    if not baseline and number(remote_total)!=number(item["confirmed_total"]):\\n                        results.append((item,"remote",remote))\\n                        continue\\n                    # If the remote was changed since the last successful sync,',1)
needle='                elif baseline and number(remote_total)!=number(baseline):'
assert needle in s
s=s.replace(needle,'                elif (not baseline and not item["pending_send"]) or (baseline and number(remote_total)!=number(baseline)):',1)
worker=s.split('    def _sync_thread(',1)[1].split('    def _apply_sync(',1)[0]
assert 'self.db' not in worker and 'self.after(' not in worker

# Responsive layout: bottom controls are packed first, so SAVE stays visible.
start=s.index('        tbl=tk.Frame(self,bg="white",padx=6)')
end=s.index('    def summary(self,parent,label,var,strong=False):',start)
section=s[start:end]
foot_at=section.index('        foot=tk.Frame(self,bg="#f5f8fc",padx=6,pady=3)')
tbl_part=section[:foot_at]
foot_part=section[foot_at:]
# Add the footer before the expanding table; preserve all existing controls.
foot_part=foot_part.replace('foot.pack(fill="x",side="bottom")','foot.pack(side="bottom",fill="x")')
tbl_part=tbl_part.replace('tbl.pack(fill="both",expand=True)','tbl.pack(side="top",fill="both",expand=True)')
# Scrollable table for narrow/short windows.
tbl_part=tbl_part.replace('        tbl=tk.Frame(self,bg="white",padx=6)\n        tbl.pack(side="top",fill="both",expand=True)',
'''        table_host=tk.Frame(self,bg="white")
        table_host.pack(side="top",fill="both",expand=True)
        canvas=tk.Canvas(table_host,bg="white",highlightthickness=0)
        scrollbar=ttk.Scrollbar(table_host,orient="vertical",command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right",fill="y")
        canvas.pack(side="left",fill="both",expand=True)
        tbl=tk.Frame(canvas,bg="white",padx=4)
        table_window=canvas.create_window((0,0),window=tbl,anchor="nw")
        tbl.bind("<Configure>",lambda e:canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>",lambda e:canvas.itemconfigure(table_window,width=e.width))''')
assert 'table_window=canvas.create_window' in tbl_part
s=s[:start]+foot_part+tbl_part+s[end:]
# More compact window and flexible width; no clipped Save buttons.
s=s.replace('self.geometry("950x590")','self.geometry("1100x710")')
s=s.replace('self.minsize(760,540)','self.minsize(690,390)')
s=s.replace('font=("Segoe UI",15,"bold")','font=("Segoe UI",12,"bold")')
s=s.replace('padx=(18,3)','padx=(5,2)')
s=s.replace('padx=10,pady=7','padx=5,pady=3')
s=s.replace('padx=8,pady=4','padx=3,pady=2')
# Avoid long status taking away room from date/action buttons.
s=s.replace('tk.Label(head,textvariable=self.status,bg="#eef2f7",fg="#63758b",font=("Segoe UI",8)).pack(side="right")',
'''statusbar=tk.Label(self,textvariable=self.status,bg="#eef2f7",fg="#63758b",font=("Segoe UI",8),anchor="w")
        statusbar.pack(side="bottom",fill="x",padx=5)''')

p.write_text(s,encoding="utf-8")
print("V1 sync thread patch applied")

print("Patch applied successfully")
