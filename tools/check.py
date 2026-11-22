#!/usr/bin/env python3
"""로컬 검사: Pages처럼 서비스하는 서버로 모든 주소를 받아 200·구조를 확인한다. 사용: python3 tools/check.py"""
import http.server, threading, pathlib, urllib.request, json, re, sys
R = pathlib.Path(__file__).resolve().parent.parent
L = json.load(open(R/'tools/langs.json')); ORDER = L['order']
class H(http.server.SimpleHTTPRequestHandler):
    def translate_path(self, p):
        p = p.split('?')[0].split('#')[0]; f = R/p.lstrip('/')
        for c in (f, f.with_name(f.name+'.html'), f/'index.html'):
            if c.is_file(): return str(c)
        return str(R/'__none__')
    def log_message(self,*a): pass
srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), H); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
bad = []; n = 0
def get(u):
    try:
        with urllib.request.urlopen(f'http://127.0.0.1:{port}{u}') as r: return r.status, r.read().decode()
    except Exception as e: return getattr(e,'code',0), ''
tags = ['<h2','<li','<tr','<td','<p','<a ','<ul','<ol']
def counts(s): return [s.count(t) for t in tags]
ref = {p: counts(get(f'/en/{p}')[1]) for p in ('privacy','terms','license')}
for l in ORDER:
    pre = '/' if l == 'ko' else f'/{l}/'
    for p in ('', 'privacy', 'terms', 'license'):
        u = pre + p; c, s = get(u); n += 1
        if c != 200: bad.append((u, c)); continue
        if l not in ('ko','en') and p:
            if counts(s) != ref[p]: bad.append((u, 'count', counts(s), ref[p]))
        if '○○' in s: bad.append((u,'date-placeholder'))
        if '{{' in s or ('word'+'le') in s.lower() or ('워'+'들') in s: bad.append((u, 'forbidden/placeholder'))
        if '7 days before' in s or '시행 7일' in s: bad.append((u,'7day'))
        for h in re.findall(r'href="(/[^"#]*)"', s):
            if h.startswith('/assets') or h in ('/app-ads.txt',): continue
            if get(h)[0] != 200: bad.append((u, 'link', h))
        if p in ('privacy','terms') and l != 'ko' and '한국어 원문' not in s: bad.append((u,'no-priority-link'))
for u in ('/privacy-en.html','/terms-en.html','/terms.html','/sitemap.xml','/robots.txt','/app-ads.txt'):
    c,_ = get(u); n += 1
    if c != 200: bad.append((u,c))
print('checked', n, 'bad', len(bad)); [print(b) for b in bad[:40]]
sys.exit(1 if bad else 0)
