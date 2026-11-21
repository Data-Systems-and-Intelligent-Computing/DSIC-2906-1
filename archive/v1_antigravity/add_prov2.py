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
 'Antraksi': 'Sumatera Barat', 
}

def prov(kab):
    if kab in EXTRA: return EXTRA[kab]
    return K[(norm(kab), kab.startswith('Kota '))]


import collections
apply_=APPLY
for f in sorted(glob.glob('*.csv')):
    if 'Metadata' in f: continue
    raw = open(f, encoding='utf-8', newline='').read()
    rows = list(csv.reader(io.StringIO(raw, newline='')))
    h = rows[0]; ik = h.index('Kabupaten'); ip = h.index('Provinsi')
    buf = io.StringIO(newline='')
    csv.writer(buf, lineterminator='\r\n').writerows(rows)
    same = buf.getvalue().rstrip('\r\n') == raw.rstrip('\r\n')
    if not same:
        buf2 = io.StringIO(newline=''); csv.writer(buf2, lineterminator='\n').writerows(rows); same2 = buf2.getvalue()==raw
    print(f, 'roundtrip', same, 'lf-variant', None if same else same2, 'nonempty prov before', sum(1 for r in rows[1:] if r[ip]))
    miss = collections.Counter()
    for r in rows[1:]:
        try: r[ip] = prov(r[ik])
        except KeyError: miss[r[ik]] += 1
    print(' unmatched', dict(miss))
    term = '\r\n' if same else '\n'
    buf = io.StringIO(newline='')
    csv.writer(buf, lineterminator=term).writerows(rows)
    if APPLY and not miss and (same or same2): open(f, 'w', encoding='utf-8', newline='').write(buf.getvalue().rstrip('\r\n'))
