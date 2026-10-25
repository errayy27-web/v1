from pathlib import Path
p=Path("source/SS_OIL_SMJENE.py")
s=p.read_text(encoding="utf-8")
needle='        ttk.Button(head,text="MERKEZ 8767",command=self.server_settings).pack(side="right",padx=(7,0))'
assert needle in s
s=s.replace(needle,needle+'\n        ttk.Button(head,text="SINHRONIZUJ",command=self.manual_sync).pack(side="right",padx=(7,0))')
needle='    def poll_sync(self):'
assert needle in s
s=s.replace(needle,'    def manual_sync(self):\n        self.status.set("Provjera veze sa PC centrom...")\n        self.poll_sync()\n\n'+needle)
needle='            self.status.set("8767 greška: "+error[:65])'
assert needle in s
s=s.replace(needle,needle+'\n            for panel in self.panels:\n                if panel.confirmed_total:\n                    panel.remote_label.set("LOKALNO SAČUVANO • slanje nije potvrđeno")')
# Administrator may reset the employee's two-save counter for one selected shift.
# This does not delete counts or change any center/phone record.
s=s.replace('from pathlib import Path','from pathlib import Path\\nimport hashlib, hmac',1)
needle='    def poll_sync(self):'
assert needle in s
s=s.replace(needle,'''    def admin_reset(self):
        from tkinter import simpledialog, messagebox
        selected=simpledialog.askinteger("Administrator", "Broj smjene (1-3):",
            parent=self,minvalue=1,maxvalue=3)
        if selected is None:return
        pin=simpledialog.askstring("Administrator", "Unesite PIN:",show="*",parent=self)
        if pin is None:return
        digest=lambda value:hashlib.sha256(value.encode("utf-8")).digest()
        if not hmac.compare_digest(digest(pin),digest("3729")):
            messagebox.showerror("Greška","Pogrešan PIN.",parent=self)
            return
        if not messagebox.askyesno("Potvrda",
                "Resetovati 2 prava čuvanja za smjenu "+str(selected)+"?\\\\n"
                "Postojeći iznosi i zapisi ostaju sačuvani.",parent=self):return
        day=self.selected.isoformat()
        with self.db:
            self.db.execute("UPDATE shifts SET save_count=0 WHERE business_date=? AND shift=?",
                            (day,selected))
        self.panels[selected-1].load()
        messagebox.showinfo("Gotovo","Prava čuvanja su resetovana (0/2).",parent=self)

'''+needle)
needle='        ttk.Button(head,text="SINHRONIZUJ",command=self.manual_sync).pack(side="right",padx=(7,0))'
assert needle in s
s=s.replace(needle,needle+'\\n        ttk.Button(head,text="ADMIN RESET",command=self.admin_reset).pack(side="right",padx=(7,0))')
# Tkinter must only be called on the UI thread; network workers return via Queue.
s=s.replace('import hashlib, hmac','import hashlib, hmac, queue',1)
needle='        self.sync_running=False'
assert needle in s
s=s.replace(needle,needle+'\\n        self.sync_results=queue.Queue()',1)
needle='    def poll_sync(self):'
assert needle in s
s=s.replace(needle,'''    def drain_sync_results(self):
        try:
            while True:
                day, results, error=self.sync_results.get_nowait()
                self._apply_sync(day,results,error)
        except queue.Empty:
            pass
        self.after(250,self.drain_sync_results)

'''+needle)
# schedule UI queue processor at startup without changing existing polling timer
needle='        self.sync_results=queue.Queue()'
assert needle in s
s=s.replace(needle,needle+'\\n        self.after(250,self.drain_sync_results)',1)
# Worker must never access Tk or SQLite. Resolve token before spawning.
needle='threading.Thread(target=self._sync_thread,args=(host,business_date,snapshot),daemon=True).start()'
assert needle in s
s=s.replace(needle,'threading.Thread(target=self._sync_thread,args=(host,business_date,snapshot,center_token(self.db)),daemon=True).start()')
s=s.replace('def _sync_thread(self,host,business_date,snapshot):','def _sync_thread(self,host,business_date,snapshot,token):')
s=s.replace('            token=center_token(self.db)\\n','')
s=s.replace('self.after(0,lambda:self._apply_sync(business_date,results,None))','self.sync_results.put((business_date,results,None))')
s=s.replace('try:self.after(0,lambda:self._apply_sync(business_date,[],msg))\\n            except RuntimeError:pass','self.sync_results.put((business_date,[],msg))')
assert 'self.sync_results.put((business_date,results,None))' in s
assert 'self.sync_results.put((business_date,[],msg))' in s
p.write_text(s,encoding="utf-8")
