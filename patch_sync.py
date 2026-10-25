from pathlib import Path
import ast
p=Path("source/SS_OIL_SMJENE.py")
s=p.read_text(encoding="utf-8")
s=s.replace("import sqlite3, os, json, urllib.request, urllib.parse, urllib.error, threading, uuid, sys","import sqlite3, os, json, urllib.request, urllib.parse, urllib.error, threading, uuid, sys, queue")
s=s.replace("        self.sync_running=False\\n        self.after(1200,self.poll_sync)","        self.sync_running=False\\n        self.sync_results=queue.Queue()\\n        self.after(250,self.drain_sync_results)\\n        self.after(1200,self.poll_sync)")
s=s.replace("    def poll_sync(self):",'''    def drain_sync_results(self):
        try:
            while True:
                date_key,results,error=self.sync_results.get_nowait()
                self._apply_sync(date_key,results,error)
        except queue.Empty:pass
        if self.winfo_exists():self.after(250,self.drain_sync_results)

    def poll_sync(self):''',1)
s=s.replace("args=(host,business_date,snapshot),daemon=True","args=(host,business_date,snapshot,center_token(self.db)),daemon=True")
a=s.index("    def _sync_thread(self,host,business_date,snapshot")
b=s.index("    def close(self):",a)
replacement="    def _sync_thread(self,host,business_date,snapshot,token):\n        results=[]\n        try:\n            if not token:raise RuntimeError(\"Merkez token eksik\")\n            base=f\"http://{host}:8767/vardiya/ssoil_shift_handoffs\"\n            headers={\"Content-Type\":\"application/json\",\"X-SSOIL-Token\":token}\n            def request(method,url,payload=None):\n                data=None if payload is None else json.dumps(payload).encode(\"utf-8\")\n                req=urllib.request.Request(url,data=data,headers=headers,method=method)\n                with urllib.request.urlopen(req,timeout=8) as response:\n                    raw=response.read()\n                    return json.loads(raw) if raw else None\n            query=urllib.parse.urlencode({\"business_date\":\"eq.\"+business_date})\n            existing=request(\"GET\",base+\"?\"+query)\n            if isinstance(existing,dict):existing=existing.get(\"data\",existing.get(\"records\",[]))\n            if not isinstance(existing,list):raise RuntimeError(\"Merkez GET yaniti gecersiz\")\n            by_shift={int(r.get(\"shift_number\") or 0):r for r in existing if isinstance(r,dict)}\n            for item in snapshot:\n                if not item[\"pending_send\"] or not item[\"confirmed_total\"]:continue\n                remote=by_shift.get(item[\"shift\"])\n                if remote:\n                    results.append((item,\"existing\",remote))\n                    continue\n                total=float(number(item[\"confirmed_total\"]))\n                payload={\"id\":item[\"remote_id\"] or str(uuid.uuid4()),\"business_date\":business_date,\n                         \"shift_number\":item[\"shift\"],\"employee_name\":item[\"locked_worker\"] or item[\"employee\"],\n                         \"snapshot\":{\"source\":\"v1_cash_counter\"},\"expected_cash\":0,\n                         \"delivered_cash\":total,\"difference\":total,\"status\":\"open\",\"revision\":1}\n                try:ack=request(\"POST\",base,payload)\n                except urllib.error.HTTPError as exc:\n                    if exc.code==409:\n                        latest=request(\"GET\",base+\"?\"+query)\n                        if isinstance(latest,dict):latest=latest.get(\"data\",latest.get(\"records\",[]))\n                        match=next((x for x in latest if isinstance(x,dict) and int(x.get(\"shift_number\") or 0)==item[\"shift\"]),None) if isinstance(latest,list) else None\n                        if match:\n                            results.append((item,\"existing\",match))\n                            continue\n                    raise\n                if isinstance(ack,list):ack=ack[0] if ack else None\n                if isinstance(ack,dict) and isinstance(ack.get(\"data\"),dict):ack=ack[\"data\"]\n                if not isinstance(ack,dict) or not ack.get(\"id\"):raise RuntimeError(\"Merkez kaydi dogrulamadi\")\n                results.append((item,\"sent\",ack))\n            self.sync_results.put((business_date,results,None))\n        except urllib.error.HTTPError as exc:\n            self.sync_results.put((business_date,results,f\"HTTP {exc.code}: \"+exc.read().decode(\"utf-8\",\"replace\")[:100]))\n        except Exception as exc:\n            self.sync_results.put((business_date,results,str(exc)[:160]))\n\n    def _apply_sync(self,business_date,results,error):\n        self.sync_running=False\n        if self.selected.isoformat()!=business_date:return\n        for item,state,ack in results:\n            panel=self.panels[item[\"shift\"]-1]\n            if panel.last_local_edit!=item[\"local_edit\"]:continue\n            with self.db:\n                self.db.execute(\"UPDATE shifts SET pending_send=0,remote_id=? WHERE business_date=? AND shift=? AND confirmed_total=?\",\n                    (str(ack.get(\"id\") or item[\"remote_id\"]),business_date,item[\"shift\"],item[\"confirmed_total\"]))\n            panel.remote_label.set(\"PRIMLJENO U PC CENTRU\" if state==\"sent\" else \"POSTOJEĆI ZAPIS U CENTRU • NIJE PREPISAN\")\n        self.status.set(\"8767 greška: \"+error[:90] if error else \"PC Merkez 8767 • povezano\")\n\n"
s=s[:a]+replacement+s[b:]
needle='            entry.grid(row=i,column=1,sticky="ew",padx=2,pady=0)'
assert needle in s
s=s.replace(needle,needle+'\n            entry.bind("<Return>",lambda e,w=entry: (w.tk_focusNext().focus_set(),"break")[-1])',1)

# Restore admin reset control without changing stored shift data.
if "def admin_reset(self):" not in s:
    s=s.replace("import tkinter as tk","import tkinter as tk\nimport hashlib, hmac",1)
    admin='''    def admin_reset(self):
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
    assert "    def poll_sync(self):" in s
    s=s.replace("    def poll_sync(self):",admin+"    def poll_sync(self):",1)
if 'text="ADMIN RESET"' not in s:
    anchor='        ttk.Button(head,text="MERKEZ 8767",command=self.server_settings).pack(side="right",padx=(7,0))'
    assert anchor in s
    s=s.replace(anchor,anchor+'\n        ttk.Button(head,text="ADMIN RESET",command=self.admin_reset).pack(side="right",padx=(7,0))',1)
ast.parse(s)
p.write_text(s,encoding="utf-8")
print("V1 send-only patch validated")
