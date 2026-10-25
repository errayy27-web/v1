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


# Sync employee names and totals, including zero. Do not alter counted denominations.
if 'synced_employee' not in s:
    s=s.replace('"pending_send":"INTEGER NOT NULL DEFAULT 0"}.items()', '"pending_send":"INTEGER NOT NULL DEFAULT 0","synced_employee":"TEXT DEFAULT \'\'"}.items()',1)
    s=s.replace('SELECT remote_revision,remote_id,synced_total,remote_override,confirmed_total,locked_worker,pending_send FROM shifts', 'SELECT remote_revision,remote_id,synced_total,remote_override,confirmed_total,locked_worker,pending_send,synced_employee FROM shifts',1)
    s=s.replace('pending_send=bool(r[6]) if r else False))', 'pending_send=bool(r[6]) if r else False,synced_employee=r[7] if r else ""))',1)
    s=s.replace('if baseline and number(remote_total)!=number(baseline):', 'if baseline and (number(remote_total)!=number(baseline) or (item["synced_employee"] and str(remote.get("employee_name") or "")!=item["synced_employee"])):',1)
    s=s.replace('if number(remote_total)==number(item["confirmed_total"]):', 'if number(remote_total)==number(item["confirmed_total"]) and str(remote.get("employee_name") or "")==(item["locked_worker"] or item["employee"]):',1)
    s=s.replace('patch={"delivered_cash":float(number(item["confirmed_total"])),', 'patch={"employee_name":item["locked_worker"] or item["employee"],"delivered_cash":float(number(item["confirmed_total"])),',1)
    s=s.replace('elif baseline and number(remote_total)!=number(baseline):','elif baseline and (number(remote_total)!=number(baseline) or (item["synced_employee"] and str(remote.get("employee_name") or "")!=item["synced_employee"])):',1)
    s=s.replace('            if state=="remote":\n                panel.remote_label', '''            remote_worker=str(remote.get("employee_name") or "").strip()
            if state in ("remote","ok","sent") and not item["pending_send"]:
                panel.loading=True
                try: panel.employee.set(remote_worker)
                finally: panel.loading=False
                panel.locked_worker=remote_worker
            if state=="remote":
                panel.remote_label''',1)
    s=s.replace('synced_total,remote_override,pending_send)\n                    VALUES(?,?,?,?,?,?,?,?)', 'synced_total,remote_override,pending_send,synced_employee)\n                    VALUES(?,?,?,?,?,?,?,?,?)',1)
    s=s.replace('pending_send=excluded.pending_send"""','pending_send=excluded.pending_send,synced_employee=excluded.synced_employee,\n                    employee=CASE WHEN excluded.pending_send=0 THEN excluded.synced_employee ELSE shifts.employee END,\n                    locked_worker=CASE WHEN excluded.pending_send=0 THEN excluded.synced_employee ELSE shifts.locked_worker END"""',1)
    s=s.replace('0 if state in ("sent","remote") else int(item["pending_send"])))', '0 if state in ("sent","remote") else int(item["pending_send"]),remote_worker))',1)
p.write_text(s,encoding="utf-8")
print("Patch completed")

# On an HTTP 409, refresh the authoritative center state rather than showing
# a permanent startup error or retrying the same stale revision blindly.
# The center is the only write path; no SQL/Supabase direct access.
p=Path("source/SS_OIL_SMJENE.py")
s=p.read_text(encoding="utf-8")
needle='''        except urllib.error.HTTPError as exc:
            msg=("401: token yanlış veya merkez tokenı değişmiş" if exc.code==401 else f"HTTP {exc.code}")
            try:self.after(0,lambda:self._apply_sync(business_date,[],msg))
            except RuntimeError:pass'''
replacement='''        except urllib.error.HTTPError as exc:
            if exc.code==409:
                try:
                    latest=request("GET",base+"?"+query)
                    if not isinstance(latest,list):
                        raise ValueError("Neispravan odgovor centra")
                    by_number={int(x.get("shift_number",0)):x for x in latest if isinstance(x,dict)}
                    refreshed=[(item,"remote",by_number[item["shift"]]) for item in snapshot if item["shift"] in by_number]
                    refreshed += [(item,"waiting",None) for item in snapshot if item["shift"] not in by_number]
                    self.after(0,lambda results=refreshed:self._apply_sync(business_date,results,None))
                except Exception as conflict_exc:
                    msg="409: "+str(conflict_exc)[:110]
                    try:self.after(0,lambda msg=msg:self._apply_sync(business_date,[],msg))
                    except RuntimeError:pass
            else:
                msg=("401: token yanlış veya merkez tokenı değişmiş" if exc.code==401 else f"HTTP {exc.code}")
                try:self.after(0,lambda msg=msg:self._apply_sync(business_date,[],msg))
                except RuntimeError:pass'''
assert s.count(needle)==1,"409 handler source mismatch"
s=s.replace(needle,replacement)
import ast
ast.parse(s)
p.write_text(s,encoding="utf-8")
print("V1 409 conflict refresh installed; local history retained")

# V1 SEND-ONLY: never import phone/center values into the cash counter.
p=Path("source/SS_OIL_SMJENE.py")
s=p.read_text(encoding="utf-8")
# Enter moves to the next denomination in the same shift.
s=s.replace('        for i,d in enumerate(DENOMS,1):','        entry_order=[]\n        for i,d in enumerate(DENOMS,1):',1)
s=s.replace('            entry.grid(row=i,column=1,sticky="ew",padx=2,pady=0)','            entry.grid(row=i,column=1,sticky="ew",padx=2,pady=0)\n            entry_order.append(entry)',1)
s=s.replace('        foot=tk.Frame(self,bg="#f5f8fc",padx=6,pady=3)','        for i,entry in enumerate(entry_order[:-1]):\n            entry.bind("<Return>",lambda e,next_entry=entry_order[i+1]: (next_entry.focus_set(),next_entry.select_range(0,"end"),"break")[-1])\n        foot=tk.Frame(self,bg="#f5f8fc",padx=6,pady=3)',1)
# No remote fetch, no remote corrections, no backflow to V1. Only send confirmed saves.
start=s.index('    def _sync_thread(self,host,business_date,snapshot):')
end=s.index('    def close(self):',start)
replacement='''    def _sync_thread(self,host,business_date,snapshot,token):
        """Send-only V1. Center receives name + counted cash; never read into V1."""
        try:
            if not token: raise RuntimeError("Merkez token nije podešen")
            base=f"http://{host}:8767/vardiya/ssoil_shift_handoffs"
            def request(method,url,payload):
                data=json.dumps(payload,ensure_ascii=False).encode("utf-8")
                req=urllib.request.Request(url,data=data,headers={"Content-Type":"application/json","X-SSOIL-Token":token},method=method)
                with urllib.request.urlopen(req,timeout=8) as response:
                    return json.load(response)
            results=[]
            for item in snapshot:
                if not item["pending_send"] or not item["confirmed_total"]:continue
                payload={"id":item["remote_id"] or str(uuid.uuid5(uuid.NAMESPACE_URL,f"ssoil-v1:{business_date}:{item['shift']}")),
                         "business_date":business_date,"shift_number":item["shift"],
                         "employee_name":item["locked_worker"] or item["employee"],
                         "delivered_cash":float(number(item["confirmed_total"])),
                         "snapshot":{"source":"v1_cash_counter"},"status":"closed"}
                # Center handles upsert and Supabase delivery.
                response=request("POST",base,payload)
                if not isinstance(response,list) or not response:raise RuntimeError("Centar nije potvrdio unos")
                results.append((item,response[0]))
            self.after(0,lambda:self._apply_sync(business_date,results,None))
        except Exception as exc:
            msg=str(exc)[:180]
            try:self.after(0,lambda:self._apply_sync(business_date,[],msg))
            except RuntimeError:pass

    def _apply_sync(self,business_date,results,error):
        self.sync_running=False
        if error:
            self.status.set("8767 greška: "+error[:90])
            return
        if self.selected.isoformat()!=business_date:return
        self.status.set("PC Merkez 8767 • povezano")
        for item,ack in results:
            panel=self.panels[item["shift"]-1]
            if panel.last_local_edit!=item["local_edit"]:continue
            with self.db:
                self.db.execute("UPDATE shifts SET pending_send=0,remote_id=? WHERE business_date=? AND shift=? AND confirmed_total=?",
                    (str(ack.get("id") or item["remote_id"]),business_date,item["shift"],item["confirmed_total"]))
            panel.remote_label.set("Primljeno u PC centar • čeka Supabase")
'''
s=s[:start]+replacement+s[end:]
s=s.replace('args=(host,business_date,snapshot,center_token(self.db)),daemon=True','args=(host,business_date,snapshot,center_token(self.db)),daemon=True')
# Suppress legacy remote corrections when loading local saved counts.
s=s.replace('self.remote_label.set(("ISPRAVKA S TELEFONA: "+fmt(number(r[3]))+" KM • važeći iznos") if r and r[3] else "")','self.remote_label.set("")')
# Avoid background SQLite calls and retain the old 2-save lock.
import ast
ast.parse(s)
p.write_text(s,encoding="utf-8")
print("Send-only V1 patch complete")
