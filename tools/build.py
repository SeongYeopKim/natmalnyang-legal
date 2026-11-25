#!/usr/bin/env python3
"""src/<lang>/{index,license,privacy,terms}.html (조각) → <lang>/*.html 생성 + 한국어 페이지에 언어 막대 주입 + sitemap.
한국어 원문(루트의 index/privacy/terms/license.html)이 원본이다. 바뀌면 src/en 부터 갱신하고 다시 번역한다."""
import json, re, pathlib, sys
R = pathlib.Path(__file__).resolve().parent.parent
L = json.load(open(R/'tools/langs.json'))
ORDER, OWN, NAME = L['order'], L['own'], L['name']
SITE = 'https://natmalnyang.soarus.dev'
PAGES = ['index', 'privacy', 'terms', 'license']
NOLEGAL = {'ja'}   # 소개만 있는 언어: 방침·약관·출처 링크는 영어판으로 잇는다(새 법률 번역을 만들지 않음)
SLUG = {'index': '', 'privacy': 'privacy', 'terms': 'terms', 'license': 'license'}

def path(lang, page):          # 주소 경로
    if lang in NOLEGAL and page != 'index': lang = 'en'
    base = '/' if lang == 'ko' else f'/{lang}/'
    return base + SLUG[page]
def url(lang, page): return SITE + path(lang, page)
def swap(l, page):             # 언어 바꿈 링크: 그 언어에 이 쪽이 없으면 그 언어 소개로
    return path(l, 'index') if (l in NOLEGAL and page != 'index') else path(l, page)

BAR_CSS = ('<style id="i18n-css">.langbar{display:flex;justify-content:flex-end;max-width:720px;margin:0 auto;padding:10px 16px 0}'
 '.langbar details{position:relative}.langbar summary{list-style:none;cursor:pointer;border:1px solid #e4e1d9;background:#fff;border-radius:999px;padding:6px 14px;font-size:13px;color:#2F3A4A;font-weight:600}'
 '.langbar summary::-webkit-details-marker{display:none}.langbar ul{position:absolute;right:0;top:36px;z-index:9;list-style:none;margin:0;padding:6px 0;background:#fff;border:1px solid #e4e1d9;border-radius:12px;max-height:60vh;overflow:auto;min-width:200px;box-shadow:0 4px 16px rgba(0,0,0,.12)}'
 '.langbar li a{display:block;padding:8px 16px;font-size:14px;color:#1C1F24;text-decoration:none}.langbar li a.cur{background:#EDF3EA;font-weight:700}'
 '.langfoot{font-size:12px;color:#6a6f76;line-height:2}.langfoot a{color:#6a6f76;margin-right:8px;white-space:nowrap}'
 '.langnote{max-width:720px;margin:6px auto 0;padding:8px 16px;font-size:13px;background:#fff7d6;display:none}</style>')
BAR_JS = ('<script>try{document.addEventListener("click",function(e){var a=e.target.closest&&e.target.closest("a[data-l]");'
 'if(a)localStorage.setItem("natmal_lang",a.getAttribute("data-l"))});'
 'if(sessionStorage.getItem("natmal_auto")){sessionStorage.removeItem("natmal_auto");var n=document.getElementById("langnote");if(n)n.style.display="block"}}catch(e){}</script>')

def hreflang(page):
    out = [f'<link rel="alternate" hreflang="{l}" href="{url(l,page)}">' for l in ORDER if not (l in NOLEGAL and page != 'index')]
    out.append(f'<link rel="alternate" hreflang="x-default" href="{url("ko",page)}">')
    return '\n'.join(out)

def langbar(cur, page):
    items = ''.join(f'<li><a data-l="{l}" lang="{l}" href="{swap(l,page)}"{" class=cur" if l==cur else ""}>{OWN[l]}</a></li>' for l in ORDER)
    note = '<div class="langnote" id="langnote">🌐 <a data-l="ko" href="/">한국어 (Korean)</a></div>'
    return f'<nav class="langbar" aria-label="Language"><details><summary>🌐 {OWN[cur]} ▾</summary><ul>{items}</ul></details></nav>\n{note}'

def langfoot(cur, page):
    return '<p class="langfoot">' + ' '.join(f'<a data-l="{l}" lang="{l}" href="{swap(l,page)}">{OWN[l]}</a>' for l in ORDER) + '</p>'

def esc(s): return s.replace('&', '&amp;').replace('"', '&quot;')

def rewrite_links(body, lang):
    def f(m):
        h = m.group(1)
        pg = {'/': 'index', '/privacy': 'privacy', '/terms': 'terms', '/license': 'license'}.get(h)
        return f'href="{path(lang,pg)}"' if pg else m.group(0)
    return re.sub(r'href="(/[a-z]*)"', f, body)

def build_lang(lang, root_styles):
    for page in PAGES:
        if lang in NOLEGAL and page != 'index': continue
        src = (R/'src'/lang/f'{page}.html').read_text()
        src = src.replace('{{NAME}}', NAME[lang])
        m = re.match(r'<title>(.*?)</title>\n', src); title = m.group(1); body = src[m.end():]
        desc = ''
        md = re.match(r'<meta name="description" content="(.*?)">\n', body)
        if md: desc = md.group(1); body = body[md.end():]
        body = rewrite_links(body, lang)
        if page in ('privacy', 'terms'):   # 「한국어 원문」 링크를 번역 안내 줄에 붙인다
            ps = list(re.finditer(r'<p class="m">.*?</p>', body, re.S))
            assert len(ps) >= 2, (lang, page)
            p = ps[1]; assert '<b>' in p.group(0), (lang, page)
            new = p.group(0)[:-4] + f' <a href="/{SLUG[page]}">한국어 원문 →</a></p>'
            body = body[:p.start()] + new + body[p.end():]
        pre = f'<!doctype html><html lang="{lang}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
        pre += root_styles['index' if page == 'index' else 'legal']
        pre += f'<title>{title}</title>\n<link rel="canonical" href="{url(lang,page)}">\n{hreflang(page)}\n'
        if page == 'index':
            pre += f'<meta name="description" content="{desc}">\n<meta property="og:type" content="website"><meta property="og:site_name" content="{esc(NAME[lang])}">'
            pre += f'<meta property="og:title" content="{esc(re.sub("<[^>]+>","",title))}"><meta property="og:description" content="{desc}"><meta property="og:url" content="{url(lang,page)}">'
            pre += f'<meta property="og:image" content="{SITE}/assets/og.jpg"><meta name="twitter:card" content="summary_large_image">\n'
            pre += '<link rel="icon" href="/assets/icon-192.png"><link rel="apple-touch-icon" href="/assets/icon-192.png">\n'
        pre += BAR_CSS + '</head><body>\n' + langbar(lang, page) + '\n'
        if page == 'index':
            body = '<div class="wrap">\n' + body
            body = body.replace('<h1>' + NAME[lang] + '</h1>', f'<h1>{NAME[lang]}</h1>\n  <p class="sub">Natmalnyang · 낱말냥</p>', 1)
            body = re.sub(r'(<footer>.*?)</footer>', lambda m: m.group(1) + langfoot(lang, page) + '</footer>', body, flags=re.S)
            body += '\n</div>'
        else:
            body = body.rstrip() + '\n' + langfoot(lang, page).replace('class="langfoot"', 'class="m langfoot"')
        out = R/lang/('index.html' if page == 'index' else f'{page}.html')
        out.parent.mkdir(exist_ok=True)
        out.write_text(pre + body + '\n' + BAR_JS + '</body></html>\n')

def inject_ko():
    for page in PAGES:
        f = R/('index.html' if page == 'index' else f'{page}.html')
        s = f.read_text()
        s = re.sub(r'<!--i18n-head-->.*?<!--/i18n-head-->\n?', '', s, flags=re.S)
        s = re.sub(r'<!--i18n-body-->.*?<!--/i18n-body-->\n?', '', s, flags=re.S)
        s = s.replace('</head>', f'<!--i18n-head-->{hreflang(page)}\n{BAR_CSS}<!--/i18n-head-->\n</head>', 1)
        extra = langbar('ko', page)
        if page == 'index':   # 한국어 소개(/)만 브라우저 언어로 이동
            extra += ('\n<script>try{var c=localStorage.getItem("natmal_lang");if(!c){var ok=%s;var ls=navigator.languages||[navigator.language||""];'
                      'for(var i=0;i<ls.length;i++){var p=(ls[i]||"").toLowerCase().split("-")[0];if(p=="nb"||p=="nn")p="no";'
                      'if(p=="ko")break;if(ok.indexOf(p)>=0){sessionStorage.setItem("natmal_auto","1");location.replace("/"+p+"/");break}}}}catch(e){}</script>') % json.dumps(ORDER[1:])
        s = re.sub(r'(<body[^>]*>)', lambda m: m.group(1) + f'\n<!--i18n-body-->{extra}<!--/i18n-body-->', s, count=1)
        s = re.sub(r'<!--i18n-js-->.*?<!--/i18n-js-->\n?', '', s, flags=re.S)
        s = s.replace('</body>', '<!--i18n-js-->' + BAR_JS + '<!--/i18n-js-->\n</body>', 1)
        f.write_text(s)

def main():
    ko_legal = (R/'license.html').read_text(); ko_index = (R/'index.html').read_text()
    legal_style = re.search(r'<style>.*?</style>', ko_legal, re.S).group(0)
    idx_style = re.search(r'<style>.*?</style>', ko_index, re.S).group(0)
    styles = {'legal': legal_style, 'index': idx_style}
    for lang in ORDER[1:]:
        if not (R/'src'/lang/('index.html' if lang in NOLEGAL else 'terms.html')).exists(): print('skip',lang); continue
        build_lang(lang, styles)
    inject_ko()
    # 옛 영문 주소 → 새 주소
    for old, new in (('privacy-en', 'privacy'), ('terms-en', 'terms')):
        (R/f'{old}.html').write_text(f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Redirect</title><link rel="canonical" href="{SITE}/en/{new}"><meta http-equiv="refresh" content="0; url=/en/{new}"></head><body><a href="/en/{new}">/en/{new}</a></body></html>\n')
    lastmod = {'index': '2026-11-21', 'privacy': '2026-11-21', 'terms': '2026-11-21', 'license': '2026-11-21'}
    urls = ''.join(f'  <url>\n    <loc>{url(l,p)}</loc>\n    <lastmod>{lastmod[p]}</lastmod>\n    <priority>{1.0 if p=="index" else 0.5}</priority>\n  </url>\n' for l in ORDER for p in PAGES if not (l in NOLEGAL and p != 'index'))
    (R/'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + urls + '</urlset>\n')
main()
