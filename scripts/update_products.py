"""Nightly: add new Cheaperzone products (home page 'New Arrivals') to products.json.
Run: python3 scripts/update_products.py  -> prints added names. Uses only public pages."""
import re, json, urllib.request, datetime, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
F = os.path.join(ROOT, 'products.json')
def get(u):
    return urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0'}), timeout=30).read().decode()
def main():
    data = json.load(open(F))
    P = data['products']
    names = {p[0].strip().upper(): i for i, p in enumerate(P)}
    h = get('https://cheaperzone.in/')
    nd = json.loads(re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', h, re.S).group(1))
    build = nd['buildId']
    arr = nd['props']['pageProps']['data'].get('newArrivalProductsResult', [])
    added, updated = [], []
    for w in reversed(arr):
        p = w.get('Product') or w
        name = (p.get('name') or '').strip()
        if not name: continue
        path = ((p.get('attatchments') or p.get('Attachments') or [{}])[0] or {}).get('path', '')
        m = re.search(r'[a-f0-9]{32}\.\w+', path); img = m.group(0) if m else ''
        qty = sum((x.get('totalQty') or 0) for x in (p.get('warehouseStock') or []))
        price = p.get('displayPrice')
        if name.upper() in names:
            row = P[names[name.upper()]]
            if price is not None and row[1] != price: row[1] = price; updated.append(name)
            row[4] = 1 if qty > 0 else 0
            continue
        carton, cat = '', ''
        try:
            j = get(f'https://cheaperzone.in/_next/data/{build}/product/{p["id"]}.json?id={p["id"]}')
            mm = re.search(r'"cartonQty":\s*(\d+)', j); carton = int(mm.group(1)) if mm else ''
            mm = re.search(r'"ProductCategory":\s*\{[^}]*?"name":\s*"([^"]+)"', j); cat = mm.group(1) if mm else ''
        except Exception:
            pass
        P.insert(0, [name, price, carton, img, 1 if qty > 0 else 0, cat])
        names[name.upper()] = 0
        added.append(name)
    if added or updated:
        data['updated'] = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=5, minutes=30))).strftime('%d-%m-%Y %H:%M')
        json.dump(data, open(F, 'w'), ensure_ascii=False, separators=(',', ':'))
    print(json.dumps({'added': added, 'price_updated': updated, 'total': len(P)}, ensure_ascii=False))
if __name__ == '__main__':
    main()
