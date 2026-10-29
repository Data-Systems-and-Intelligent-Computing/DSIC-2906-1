import json, glob, csv, io, re, sys
APPLY = len(sys.argv) > 1 and sys.argv[1] == 'apply'
m = json.load(open('/Users/angels/.gemini/antigravity/brain/45162689-0933-443f-9745-a2ace0557ff8/scratch_map.json'))

def title(p):
    t = p.title()
    t = t.replace('Dki ', 'DKI ').replace('Di Yogyakarta', 'DI Yogyakarta')
    return t

def norm(s):
    s = s.upper().strip()
    s = re.sub(r'^(KABUPATEN|KOTA)\s+', '', s)
    return re.sub(r'[^A-Z]', '', s)

K = {(norm(k), k.startswith('KOTA')): title(v) for k, v in m.items()}

# Papua split (2022) by regency
PAPUA = {
 'Papua Barat Daya': ['RAJAAMPAT', 'SORONG', 'SORONGSELATAN', 'MAYBRAT', 'TAMBRAUW'],
 'Papua Selatan': ['MERAUKE', 'MAPPI', 'ASMAT', 'BOVENDIGOEL'],
 'Papua Tengah': ['NABIRE', 'MIMIKA', 'PANIAI', 'PUNCAKJAYA', 'PUNCAK', 'DOGIYAI', 'DEIYAI', 'INTANJAYA'],
 'Papua Pegunungan': ['JAYAWIJAYA', 'YAHUKIMO', 'YALIMO', 'PEGUNUNGANBINTANG', 'TOLIKARA', 'MAMBERAMOTENGAH', 'LANNYJAYA', 'NDUGA'],
}
for prov_, names in PAPUA.items():
    for n in names:
        for kota in (False, True):
            if (n, kota) in K and K[(n, kota)] in ('Papua', 'Papua Barat'):
                K[(n, kota)] = prov_

EXTRA = {
 'Kabupaten Gayo Luwes': 'Aceh', 'Kabupaten Kepulauan Tanimbar': 'Maluku',
 'Kabupaten Pasangkayu': 'Sulawesi Barat', 'Kabupaten Toba': 'Sumatera Utara',
 # kabupaten field is corrupted in the source; inferred from desa/alamat
 'Pantai Ina Burak': 'Maluku', 'Pulau Osi': 'Maluku', 'Baqbatoa Beach': 'Sulawesi Barat',
 'Oboss': 'Gorontalo', 'berwawasan': 'Jawa Timur', 'udang merah': 'Sulawesi Tenggara',
 'Saribattang': 'Sulawesi Selatan', 'Sendangmulyo': 'DI Yogyakarta', 'Sengkol': 'Nusa Tenggara Barat',
 'Antraksi': 'Sumatera Barat', '': 'Sulawesi Utara',
}

def prov(kab):
    if kab in EXTRA: return EXTRA[kab]
    return K[(norm(kab), kab.startswith('Kota '))]

for f in sorted(glob.glob('*.jsonl')):
    raw = open(f, encoding='utf-8', newline='').read()
    lines = [x+'\n' for x in raw.split('\n')]
    if lines[-1]=='\n': lines.pop()
    elif not raw.endswith('\n'): lines[-1]=lines[-1][:-1]
    out = []
    for l in lines:
        body = l.rstrip('\r\n'); end = l[len(body):]
        if not body.strip():
            out.append(l); continue
        d = json.loads(body)
        assert json.dumps(d, ensure_ascii=False) == body, (f, body[:80])
        p = prov(d.get('kabupaten', ''))
        nd = {}
        for k, v in d.items():
            if k == 'provinsi': continue
            nd[k] = v
            if k == 'kabupaten': nd['provinsi'] = p
        if 'provinsi' not in nd: nd['provinsi'] = p
        out.append(json.dumps(nd, ensure_ascii=False) + end)
    if APPLY: open(f, 'w', encoding='utf-8', newline='').write(''.join(out))
    print(f, len(lines))

for f in sorted(glob.glob('*.csv')):
    raw = open(f, encoding='utf-8', newline='').read()
    rows = list(csv.reader(io.StringIO(raw, newline='')))
    h = rows[0]; ik = h.index('kabupaten'); ip = h.index('provinsi')
    buf = io.StringIO(newline='')
    csv.writer(buf, lineterminator='\r\n').writerows(rows)
    print(f, 'roundtrip identical:', buf.getvalue() == raw)
    for r in rows[1:]:
        r[ip] = prov(r[ik])
    buf = io.StringIO(newline='')
    csv.writer(buf, lineterminator='\r\n').writerows(rows)
    if APPLY: open(f, 'w', encoding='utf-8', newline='').write(buf.getvalue())
