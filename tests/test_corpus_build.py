import pandas as pd

from src.corpus.build_corpus import clean_title
from src.corpus.publishers import build_publisher_map, group_syndication, publisher_id


# --- Judul berita: akhiran sumber dari Google News dibuang ---
def test_clean_title_strips_source_suffix():
    t = "Pawai Ogoh-ogoh Meriah - Radar Cianjur - radarcianjur.com"
    assert clean_title(t, "Radar Cianjur", "www.radarcianjur.com") == "Pawai Ogoh-ogoh Meriah"


def test_clean_title_keeps_inner_dash():
    t = "Alun-Alun Suryakencana - Pendakian Ditutup - detikTravel"
    assert clean_title(t, "detikTravel", "travel.detik.com") == "Alun-Alun Suryakencana - Pendakian Ditutup"


# --- Penerbit: subdomain satu penerbit digabung, blog berbeda tidak ---
def test_publisher_id_merges_subdomains():
    assert publisher_id("travel.detik.com") == publisher_id("www.detik.com") == "detik.com"
    assert publisher_id("mediacenter.banjarbarukota.go.id") == "banjarbarukota.go.id"


def test_publisher_id_keeps_private_suffix_blogs_apart():
    assert publisher_id("a.blogspot.com") != publisher_id("b.blogspot.com")


def test_publisher_map_counts():
    m = build_publisher_map(pd.Series(["travel.detik.com", "www.detik.com", "www.detik.com", "kompas.tv"]))
    assert m.loc[m.domain == "www.detik.com", "n_articles"].item() == 2
    assert m.loc[m.domain == "travel.detik.com", "n_domains_in_publisher"].item() == 2


# --- Sindikasi: judul mirip DAN tanggal berdekatan ---
def test_syndication_groups_similar_titles_within_window():
    titles = pd.Series(["Bupati Biak membuka atraksi budaya menangkap ikan Snapmor",
                        "Bupati Biak buka atraksi budaya tangkap ikan Snapmor",
                        "Festival Danau Toba resmi dibuka"])
    dates = pd.Series(pd.to_datetime(["2026-08-01", "2026-08-02", "2026-08-01"]))
    ids = group_syndication(titles, dates, threshold=85, max_days=2)
    assert ids[0] == ids[1] != ids[2]


def test_syndication_respects_date_window():
    titles = pd.Series(["Judul yang persis sama", "Judul yang persis sama"])
    dates = pd.Series(pd.to_datetime(["2026-01-01", "2026-01-10"]))
    ids = group_syndication(titles, dates, max_days=2)
    assert ids[0] != ids[1]
