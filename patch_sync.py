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
p.write_text(s,encoding="utf-8")
