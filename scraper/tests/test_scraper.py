"""Offline tests for the FemtoNews scraper (no network: HTTP is faked)."""
import io
import json
import shutil
import sys
from pathlib import Path

import pytest
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import femtonews_scraper as vs  # noqa: E402

CFG = vs.load_config(HERE.parent / "config.yaml")


# ----------------------------------------------------------------- fixtures

EPMC_RESULT = {
    "id": "40000001", "source": "MED", "pmid": "40000001", "doi": "10.1038/s41467-026-00001-x",
    "title": "Femtosecond laser writing of three-dimensional photonic lattices in fused silica for quantum walks.",
    "authorString": "Tan A, Lim B, Huang Z.",
    "authorList": {"author": [
        {"fullName": "Tan A", "authorAffiliationDetailsList": {"authorAffiliation": [{"affiliation": "Department of Biomedical Engineering, National University of Singapore, Singapore 117576. a.tan@nus.edu.sg"}]}},
        {"fullName": "Lim B", "authorAffiliationDetailsList": {"authorAffiliation": [{"affiliation": "Institute of Bioengineering and Bioimaging, A*STAR, Singapore"}]}},
        {"fullName": "Huang Z", "authorAffiliationDetailsList": {"authorAffiliation": [{"affiliation": "Department of Biomedical Engineering, National University of Singapore, Singapore"}]}},
    ]},
    "journalInfo": {"journal": {"title": "Nature Communications", "essn": "2041-1723"}},
    "firstPublicationDate": "2026-11-04",
    "abstractText": "<h4>Abstract</h4>Photonic lattices enable quantum simulation. We use femtosecond laser direct writing to inscribe waveguide lattices in fused silica. A deep learning model predicts the coupling constants.",
    "isOpenAccess": "Y", "license": "cc by",
    "pubTypeList": {"pubType": ["research-article", "Journal Article"]},
}

EPMC_NOISE = {  # ultrafast magnetism, not fabrication: must be excluded
    "id": "40000002", "source": "MED", "doi": "10.1000/magn.1",
    "title": "Ultrafast demagnetization dynamics in iron thin films",
    "authorList": {"author": [{"fullName": "Doe J"}]},
    "journalInfo": {"journal": {"title": "NeuroImage"}},
    "firstPublicationDate": "2026-11-03", "abstractText": "Femtosecond laser pulses excite spin dynamics probed by time-resolved spectroscopy.", "isOpenAccess": "N",
}

CROSSREF_ITEM = {
    "DOI": "10.2961/JLMN.2026.03.2001",
    "title": ["Femtosecond laser dicing of sapphire wafers with Bessel beams"],
    "author": [{"given": "Maria", "family": "Rossi", "affiliation": [{"name": "Dipartimento di Fisica, Politecnico di Milano, Milan, Italy"}]}],
    "container-title": ["Journal of Laser Micro/Nanoengineering"], "ISSN": ["1880-0688"],
    "created": {"date-parts": [[2026, 11, 5]]}, "published-online": {"date-parts": [[2026, 11, 5]]},
    "abstract": "<jats:p>We report crack-free Bessel-beam dicing of 430 µm sapphire wafers.</jats:p>",
    "license": [{"URL": "http://onlinelibrary.wiley.com/termsAndConditions"}],
}
CROSSREF_DUP = {  # same DOI as the Europe PMC record, should merge away
    "DOI": "10.1038/s41467-026-00001-x", "title": ["Femtosecond laser writing of three-dimensional photonic lattices in fused silica for quantum walks"],
    "author": [], "container-title": ["Nature Communications"], "created": {"date-parts": [[2026, 11, 4]]},
    "license": [{"URL": "https://creativecommons.org/licenses/by/4.0/"}],
}

def oa_work(doi, title, abstract, journal="Light: Science & Applications", date="2026-11-05", insts=("Zhejiang University",)):
    words = abstract.split()
    return {"id": "https://openalex.org/W" + doi[-4:], "doi": "https://doi.org/" + doi, "display_name": title, "publication_date": date, "type": "article",
            "authorships": [{"author": {"display_name": "Li Wei"}, "institutions": [{"display_name": i} for i in insts]}],
            "primary_location": {"source": {"display_name": journal, "issn_l": "2047-7538", "issn": ["2047-7538"], "type": "journal", "id": "https://openalex.org/S1"}},
            "open_access": {"oa_status": "gold"}, "best_oa_location": {"license": "cc-by"},
            "abstract_inverted_index": {w: [i] for i, w in enumerate(words)} if abstract else None}


OPENALEX_RESULTS = [
    # 2PP paper whose title never names the process: must be kept (strong term once in abstract)
    oa_work("10.1038/s41377-026-00001-a", "Bend-insensitive image relay through a hollow-core fibre",
            "A diffractive network was fabricated by two-photon polymerization on the fibre facet."),
    # the same DOI as the Crossref JLMN record; OpenAlex supplies its own abstract
    oa_work("10.2961/jlmn.2026.03.2001", "Femtosecond laser dicing of sapphire wafers with Bessel beams", "Bessel-beam dicing of sapphire wafers.", journal="Journal of Laser Micro/Nanoengineering"),
    # materials paper that mentions a femtosecond laser only in passing: must be dropped
    oa_work("10.1016/j.mat.2026.0001", "High-entropy oxide cathodes for sodium batteries",
            "Samples were cleaned with a femtosecond laser and characterised by XRD, SEM and XPS; capacity retention reached 92%."),
    # old paper re-indexed: must be dropped by the age guard
    oa_work("10.1000/old.fs.1", "Femtosecond laser writing of waveguides in glass", "Waveguides.", date="2025-01-10"),
]

CORE_JRS_ITEM = {  # core journal: kept although the title has no keyword
    "DOI": "10.2961/JLMN.2026.03.2002", "title": ["Thermal lensing in high-power galvanometer scanners"],
    "author": [{"given": "Ana", "family": "Costa"}], "container-title": ["Journal of Laser Micro/Nanoengineering"], "ISSN": ["1880-0688"],
    "created": {"date-parts": [[2026, 11, 5]]}, "license": [],
}

ARXIV_XML = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom">
  <entry>
    <id>http://arxiv.org/abs/2611.01234v1</id>
    <published>2026-11-06T10:00:00Z</published>
    <title>Spatiotemporal focusing enables aberration-free femtosecond writing deep in glass</title>
    <summary>We demonstrate femtosecond laser writing at 5 mm depth with simultaneous spatial and temporal focusing.</summary>
    <author><name>Ana Silva</name><arxiv:affiliation>University of Queensland</arxiv:affiliation></author>
  </entry>
  <entry>
    <id>http://arxiv.org/abs/2610.00001v2</id>
    <published>2026-10-01T10:00:00Z</published>
    <title>Old femtosecond laser writing paper outside the window</title>
    <summary>Writing.</summary>
    <author><name>X Y</name></author>
  </entry>
</feed>"""

ARTICLE_HTML = """<html><head>
<meta property="og:title" content="paper">
<meta property="og:image" content="/figures/fig1.png">
</head><body></body></html>"""
COVER_HTML = """<html><head><meta name="twitter:image" content="https://cdn.example.org/jrs/cover_image.jpg"></head></html>"""


def png_bytes(w=600, h=400, color=(30, 120, 160)):
    buf = io.BytesIO()
    Image.new("RGB", (w, h), color).save(buf, "PNG")
    return buf.getvalue()


class FakeResp:
    def __init__(self, url, body=b"", ctype="text/html", status=200):
        self.url, self.status_code = url, status
        self.content = body if isinstance(body, bytes) else body.encode()
        self.text = self.content.decode("utf-8", "ignore")
        self.headers = {"Content-Type": ctype}

    def json(self):
        return json.loads(self.text)


class FakeHttp:
    calls: list = []

    def __init__(self, cfg):
        self.cfg = cfg

    def get(self, url, check_robots=False, params=None, **kw):
        FakeHttp.calls.append((url, params))
        if "europepmc" in url:
            q = (params or {}).get("query", "")
            if q.startswith("DOI:"):
                return FakeResp(url, json.dumps({"resultList": {"result": []}}), "application/json")
            if (params or {}).get("cursorMark") == "*":
                return FakeResp(url, json.dumps({"nextCursorMark": "AAA", "resultList": {"result": [EPMC_RESULT, EPMC_NOISE]}}), "application/json")
            return FakeResp(url, json.dumps({"nextCursorMark": "AAA", "resultList": {"result": []}}), "application/json")
        if url == "https://api.openalex.org/works":
            if "cursor" in (params or {}) and params["cursor"] != "*":
                return FakeResp(url, json.dumps({"meta": {"next_cursor": None}, "results": []}), "application/json")
            return FakeResp(url, json.dumps({"meta": {"next_cursor": "NEXT"}, "results": OPENALEX_RESULTS}), "application/json")
        if "api.crossref.org/works" in url and "issn:" in (params or {}).get("filter", ""):
            return FakeResp(url, json.dumps({"message": {"items": [CORE_JRS_ITEM]}}), "application/json")
        if "api.crossref.org/works/" in url:   # single-DOI lookup (inbox)
            item = dict(CROSSREF_ITEM, DOI="10.1364/OE.999999", title=["Inbox paper: laser-written photonic lantern"])
            return FakeResp(url, json.dumps({"message": item}), "application/json")
        if "api.crossref.org/works" in url:
            return FakeResp(url, json.dumps({"message": {"items": [CROSSREF_ITEM, CROSSREF_DUP]}}), "application/json")
        if "arxiv.org/api" in url:
            return FakeResp(url, ARXIV_XML, "application/atom+xml")
        if url == "https://doi.org/10.1038/s41467-026-00001-x":
            return FakeResp("https://www.nature.com/articles/s41467-026-00001-x", ARTICLE_HTML)
        if url == "https://www.nature.com/figures/fig1.png":
            return FakeResp(url, png_bytes(), "image/png")
        if url == "https://doi.org/10.2961/jlmn.2026.03.2001":
            return FakeResp("https://www.jlps.gr.jp/jlmn/10.2961/jlmn.2026.03.2001", COVER_HTML)
        if url == "https://cdn.example.org/jrs/cover_image.jpg":
            return FakeResp(url, png_bytes(300, 400, (200, 60, 60)), "image/jpeg")
        return None


@pytest.fixture
def repo(tmp_path, monkeypatch):
    (tmp_path / "data" / "issues").mkdir(parents=True)
    (tmp_path / "data" / "inbox.txt").write_text("# submissions\n10.1364/OE.999999\n", encoding="utf-8")
    monkeypatch.setattr(vs, "Http", FakeHttp)
    FakeHttp.calls = []
    return tmp_path


# ----------------------------------------------------------------- unit tests

def test_parse_europepmc_fields():
    r = vs.parse_europepmc(EPMC_RESULT)
    assert r["title"].endswith("quantum walks")
    assert r["doi"] == "10.1038/s41467-026-00001-x"
    assert r["oa"] is True and r["license"] == "CC BY"
    assert r["journal"] == "Nature Communications"
    assert "Photonic lattices enable" in r["abstract"] and "Abstract" not in r["abstract"][:9]


def test_institutions_strip_departments_and_emails():
    r = vs.parse_europepmc(EPMC_RESULT)
    inst = vs.institutions_from(r["affiliations"])
    assert inst[0] == "National University of Singapore"
    assert any("A*STAR" in i or "Institute of Bioengineering" in i for i in inst)
    assert len(inst) == 2  # NUS de-duplicated


def test_relevance_filters():
    assert vs.is_relevant(vs.parse_europepmc(EPMC_RESULT), CFG)
    assert not vs.is_relevant(vs.parse_europepmc(EPMC_NOISE), CFG)
    assert not vs.is_relevant({"title": "Correction to: Femtosecond laser writing of waveguides", "abstract": ""}, CFG)
    # a generic mention in the abstract does not count; a process name does; other terms need two hits
    assert not vs.is_relevant({"title": "Cell mechanics", "abstract": "Cells were cut with a femtosecond laser."}, CFG)
    assert vs.is_relevant({"title": "Cell mechanics", "abstract": "Laser-induced periodic surface structures guide cell alignment."}, CFG)
    assert not vs.is_relevant({"title": "Stent coatings", "abstract": "Tubes were cut by laser micromachining."}, CFG)
    assert vs.is_relevant({"title": "Stent manufacturing", "abstract": "Laser micromachining of nitinol tubes. Laser micromachining parameters were varied."}, CFG)


def test_categories_and_glyph():
    r = vs.parse_europepmc(EPMC_RESULT)
    cats = vs.categorize(r, CFG)
    assert "Waveguides & Photonic Chips" in cats and "Glass & Silica" in cats and "Quantum Photonics & Color Centers" in cats
    assert vs.glyph_for(cats, CFG) == "quantum"
    assert cats.index("Waveguides & Photonic Chips") < cats.index("Glass & Silica")  # directions listed first


def test_crossref_and_arxiv_parsing():
    c = vs.parse_crossref(CROSSREF_ITEM)
    assert c["doi"] == "10.2961/jlmn.2026.03.2001" and c["date"] == "2026-11-05" and not c["oa"]
    assert vs.parse_crossref(CROSSREF_DUP)["license"] == "CC BY 4.0"
    a = vs.parse_arxiv(ARXIV_XML, "2026-11-02", "2026-11-08")
    assert len(a) == 1 and a[0]["url"] == "https://arxiv.org/abs/2611.01234"


def test_merge_dedupes_by_doi_and_fills_license():
    recs = [vs.parse_crossref(CROSSREF_DUP), vs.parse_europepmc(EPMC_RESULT), vs.parse_crossref(CROSSREF_ITEM)]
    merged = vs.merge_records(recs)
    assert len(merged) == 2
    assert merged[0]["source"] == "europepmc"


def test_trim_summary_sentence_boundary():
    s = "First sentence is here. " * 60
    t = vs.trim_summary(s, 200)
    assert len(t) <= 205 and t.endswith("…") and ". …" in t


def test_preview_image_extraction_and_cover_detection():
    assert vs.extract_preview_image(ARTICLE_HTML, "https://www.nature.com/articles/x") == "https://www.nature.com/figures/fig1.png"
    url = vs.extract_preview_image(COVER_HTML, "https://onlinelibrary.wiley.com/doi/x")
    assert vs.looks_like_cover(url)
    assert vs.extract_preview_image("<html></html>", "https://x.org") is None


def test_save_thumbnail_rejects_logos(tmp_path):
    assert not vs.save_thumbnail(png_bytes(64, 64), tmp_path / "a.jpg", CFG)
    assert vs.save_thumbnail(png_bytes(1600, 1000), tmp_path / "b.jpg", CFG)
    im = Image.open(tmp_path / "b.jpg")
    assert im.size[0] <= 400 and im.size[1] <= 280


# ----------------------------------------------------------------- end-to-end (fake network)

def run_cli(repo, *extra):
    return vs.main(["--root", str(repo), "--issue-date", "2026-11-09", *extra])


def test_end_to_end_issue_with_figure_cover_and_inbox(repo):
    assert run_cli(repo) == 0
    issue = json.loads((repo / "data/issues/2026-11-09.json").read_text())
    assert issue["window"] == ["2026-11-02", "2026-11-08"]
    titles = [a["title"] for a in issue["articles"]]
    assert any("photonic lattices" in t for t in titles)
    assert any("Bessel beams" in t for t in titles)
    assert any("Spatiotemporal focusing" in t for t in titles)   # arXiv
    assert any("Inbox paper" in t for t in titles)          # submitted DOI
    assert not any("demagnetization" in t for t in titles)
    by = {a["title"][:20]: a for a in issue["articles"]}
    srs = next(a for a in issue["articles"] if "photonic lattices" in a["title"])
    assert srs["fig"]["kind"] == "figure" and (repo / srs["fig"]["src"]).exists()
    assert "CC BY" in srs["fig"]["credit"]
    ters = next(a for a in issue["articles"] if "Bessel beams" in a["title"])
    assert ters["fig"]["kind"] == "cover" and ters["fig"]["src"].startswith("covers/")
    qe = next(a for a in issue["articles"] if "Spatiotemporal focusing" in a["title"])
    assert qe["fig"] is None and qe["glyph"] == "burst"
    idx = json.loads((repo / "data/issues/index.json").read_text())
    assert idx["issues"][0]["id"] == "2026-11-09" and idx["issues"][0]["number"] == 1
    assert "10.1364" not in (repo / "data/inbox.txt").read_text()   # processed DOI removed
    assert json.loads((repo / "covers/index.json").read_text())["journal of laser micro/nanoengineering"]["kind"] == "cover"


def test_rerun_keeps_editor_changes_and_removed(repo):
    run_cli(repo, "--no-figures")
    p = repo / "data/issues/2026-11-09.json"
    issue = json.loads(p.read_text())
    srs = next(a for a in issue["articles"] if "photonic lattices" in a["title"])
    srs["feature"] = True
    srs["summary"] = "Editor's own summary."
    victim = next(a for a in issue["articles"] if "Bessel beams" in a["title"])
    issue["articles"].remove(victim)
    issue["removed"].append(victim["id"])
    p.write_text(json.dumps(issue))
    run_cli(repo, "--no-figures")
    again = json.loads(p.read_text())
    srs2 = next(a for a in again["articles"] if "photonic lattices" in a["title"])
    assert srs2["feature"] and srs2["summary"] == "Editor's own summary."
    assert not any("Bessel beams" in a["title"] for a in again["articles"])
    assert again["articles"][0]["id"] == srs2["id"]  # feature sorts first


class PolicyHttp(FakeHttp):
    """Extra routes for the OA-figure / paywalled-cover policy."""

    def get(self, url, check_robots=False, params=None, **kw):
        routes = {
            # paywalled ACS paper: landing image is a landscape TOC graphic (must NOT be used)
            "https://doi.org/10.1021/acs.analchem.6c99999": ("https://pubs.acs.org/doi/10.1021/acs.analchem.6c99999", '<meta property="og:image" content="https://pubs.acs.org/cms/toc.jpg">', "text/html"),
            "https://pubs.acs.org/cms/toc.jpg": (url, png_bytes(600, 300), "image/jpeg"),
            "https://api.openalex.org/works/doi:10.1021/acs.analchem.6c99999": (url, json.dumps({"open_access": {"is_oa": False, "oa_status": "closed"}, "primary_location": {"source": {"id": "https://openalex.org/S123", "issn_l": "0003-2700"}}}), "application/json"),
            "https://api.openalex.org/sources/S123": (url, json.dumps({"homepage_url": "https://pubs.acs.org/journal/ancham"}), "application/json"),
            "https://pubs.acs.org/journal/ancham": (url, '<meta property="og:image" content="https://pubs.acs.org/ancham-img.jpg">', "text/html"),
            "https://pubs.acs.org/ancham-img.jpg": (url, png_bytes(300, 400, (10, 60, 120)), "image/jpeg"),
            # OA status discovered only through OpenAlex
            "https://api.openalex.org/works/doi:10.1038/s41467-026-00001-x": (url, json.dumps({"open_access": {"is_oa": True, "oa_status": "gold"}, "best_oa_location": {"license": "cc-by"}, "primary_location": {"source": {"id": "https://openalex.org/S9", "issn_l": "2041-1723"}}}), "application/json"),
            # OA page without og:image but with figures in the HTML (Light: Advanced Manufacturing style)
            "https://doi.org/10.37188/lam.2026.999": ("https://www.light-am.com/article/doi/10.37188/lam.2026.999", '<html><body><img src="/img/logo.png"><div class="figure"><img class="figure_img" src="/files/LAM-1.jpg"></div></body></html>', "text/html"),
            "https://www.light-am.com/files/LAM-1.jpg": (url, png_bytes(800, 500), "image/jpeg"),
            # paywalled Springer paper: landscape figure on the article page; cover on the journal homepage is a 92-px og:image
            "https://doi.org/10.1007/s10439-026-99999-x": ("https://link.springer.com/article/10.1007/s10439-026-99999-x", '<meta property="og:image" content="https://media.springernature.com/lw685/springer-static/image/art/fig1.png">', "text/html"),
            "https://media.springernature.com/lw685/springer-static/image/art/fig1.png": (url, png_bytes(685, 400), "image/png"),
            "https://api.openalex.org/works/doi:10.1007/s10439-026-99999-x": (url, json.dumps({"open_access": {"is_oa": False, "oa_status": "closed"}, "primary_location": {"source": {"id": "https://openalex.org/S77", "issn_l": "0090-6964"}}}), "application/json"),
            "https://api.openalex.org/sources/S77": (url, json.dumps({"homepage_url": "https://link.springer.com/journal/10439"}), "application/json"),
            "https://link.springer.com/journal/10439": (url, '<meta property="og:image" content="https://media.springernature.com/w92/springer-static/cover/journal/10439.jpg">', "text/html"),
            "https://media.springernature.com/w316/springer-static/cover/journal/10439.jpg": (url, png_bytes(316, 420, (90, 20, 20)), "image/jpeg"),
            # paywalled paper with no cover anywhere
            "https://doi.org/10.9999/nocover": ("https://example.org/nocover", "<html></html>", "text/html"),
        }
        if url in routes:
            final, body, ctype = routes[url]
            return FakeResp(final, body, ctype)
        return super().get(url, check_robots, params, **kw)


def paywalled_acs():
    return {"source": "crossref", "title": "SERS assay", "doi": "10.1021/acs.analchem.6c99999", "url": "https://doi.org/10.1021/acs.analchem.6c99999",
            "journal": "Analytical Chemistry", "oa": False, "license": ""}


def test_paywalled_paper_gets_journal_cover_never_its_figure(tmp_path):
    f = vs.FigureFetcher(PolicyHttp(CFG), CFG, tmp_path)
    rec = vs.enrich_oa(f.http, paywalled_acs())
    assert rec["oa"] is False and rec["_openalex_source"] == "S123"
    fig = f.fetch(rec, "acs1")
    assert fig["kind"] == "cover" and fig["src"].startswith("covers/analytical-chemistry")
    assert not (tmp_path / "figs" / "acs1.jpg").exists()
    # second paper from the same journal reuses the cached cover without new requests
    FakeHttp.calls = []
    again = f.fetch(dict(paywalled_acs(), doi="10.1021/x", url=""), "acs2")
    assert again["src"] == fig["src"] and not any("ancham-img" in c[0] for c in FakeHttp.calls)


def test_paywalled_paper_without_any_cover_falls_back_to_glyph(tmp_path):
    f = vs.FigureFetcher(PolicyHttp(CFG), CFG, tmp_path)
    rec = {"source": "crossref", "title": "x", "doi": "10.9999/nocover", "url": "https://doi.org/10.9999/nocover", "journal": "Obscure Letters", "oa": False}
    assert f.fetch(rec, "n1") is None


def test_open_access_paper_gets_its_own_figure_and_openalex_upgrades_oa(tmp_path):
    f = vs.FigureFetcher(PolicyHttp(CFG), CFG, tmp_path)
    rec = vs.parse_europepmc(dict(EPMC_RESULT, isOpenAccess="N", license=""))
    assert rec["oa"] is False
    vs.enrich_oa(f.http, rec)
    assert rec["oa"] is True and rec["license"] == "CC BY"
    fig = f.fetch(rec, "oa1")
    assert fig["kind"] == "figure" and "CC BY" in fig["credit"] and (tmp_path / "figs/oa1.jpg").exists()


def test_mode_all_uses_figure_even_for_paywalled(tmp_path):
    cfg = vs.load_config(HERE.parent / "config.yaml")
    cfg["figures"]["mode"] = "all"
    f = vs.FigureFetcher(PolicyHttp(cfg), cfg, tmp_path)
    assert f.fetch(paywalled_acs(), "acs3")["kind"] == "figure"


def test_open_access_page_without_og_image_uses_first_figure(tmp_path):
    f = vs.FigureFetcher(PolicyHttp(CFG), CFG, tmp_path)
    rec = {"source": "crossref", "title": "Diamond SERS", "doi": "10.37188/lam.2026.999", "url": "https://doi.org/10.37188/lam.2026.999", "journal": "Light: Advanced Manufacturing", "oa": True, "license": "CC BY 4.0"}
    fig = f.fetch(rec, "lam")
    assert fig["kind"] == "figure" and (tmp_path / "figs/lam.jpg").exists()


def test_first_figure_ignores_related_article_thumbnails():
    page = ('<figure><img src="https://media.springernature.com/w72/springer-static/cover-hires/journal/12911"></figure>'
            '<figure><img src="https://media.springernature.com/w215h120/springer-static/image/art%3A10.1186%2Fs40644-025-00921-w/MediaObjects/Fig1.png"></figure>')
    assert vs.extract_first_figure(page, "https://link.springer.com/x", "10.1186/s12911-026-03922-2") is None
    own = page + '<figure><img src="https://media.springernature.com/lw685/springer-static/image/art%3A10.1186%2Fs12911-026-03922-2/MediaObjects/Fig1.png"></figure>'
    assert "s12911-026-03922-2" in vs.extract_first_figure(own, "https://link.springer.com/x", "10.1186/s12911-026-03922-2")


def test_springer_paywalled_gets_upgraded_homepage_cover_not_figure(tmp_path):
    f = vs.FigureFetcher(PolicyHttp(CFG), CFG, tmp_path)
    rec = vs.enrich_oa(f.http, {"source": "crossref", "title": "Bone SRS", "doi": "10.1007/s10439-026-99999-x", "url": "https://doi.org/10.1007/s10439-026-99999-x", "journal": "Annals of Biomedical Engineering", "oa": False})
    fig = f.fetch(rec, "abme")
    assert fig["kind"] == "cover" and not (tmp_path / "figs/abme.jpg").exists()
    assert vs.upgrade_image_url("https://media.springernature.com/w92/springer-static/cover/journal/10439.jpg").endswith("/w316/springer-static/cover/journal/10439.jpg")


def test_refresh_finds_missing_doi_by_title(repo, monkeypatch):
    monkeypatch.setattr(vs, "Http", PolicyHttp)
    issue = {"id": "2026-11-02", "number": 1, "date": "2026-11-02", "window": ["a", "b"], "removed": [], "articles": [
        {"id": "jlmn", "title": "Femtosecond laser dicing of sapphire wafers with Bessel beams", "doi": None, "url": "https://www.jlps.gr.jp/jlmn/", "journal": "Journal of Laser Micro/Nanoengineering", "oa": False, "license": "", "fig": None}]}
    p = repo / "data/issues/2026-11-02.json"
    p.write_text(json.dumps(issue))
    vs.main(["--root", str(repo), "--issue-date", "2026-11-02", "--refresh-figures"])
    art = json.loads(p.read_text())["articles"][0]
    assert art["doi"] == "10.2961/jlmn.2026.03.2001" and art["url"] == "https://doi.org/10.2961/jlmn.2026.03.2001"
    assert art["fig"]["kind"] == "cover"     # the article page exposes a cover image


def test_refresh_figures_for_existing_issue(repo, monkeypatch):
    monkeypatch.setattr(vs, "Http", PolicyHttp)
    issue = {"id": "2026-11-02", "number": 1, "date": "2026-11-02", "window": ["2026-10-26", "2026-11-01"], "removed": [], "articles": [
        {"id": "oa-paper", "title": "OA paper", "doi": "10.1038/s41467-026-00001-x", "url": "https://doi.org/10.1038/s41467-026-00001-x", "journal": "Nature Communications", "oa": False, "license": "", "fig": None},
        {"id": "pw-paper", "title": "Paywalled paper", "doi": "10.1021/acs.analchem.6c99999", "url": "https://doi.org/10.1021/acs.analchem.6c99999", "journal": "Analytical Chemistry", "oa": False, "license": "", "fig": None},
    ]}
    p = repo / "data/issues/2026-11-02.json"
    p.write_text(json.dumps(issue))
    assert vs.main(["--root", str(repo), "--issue-date", "2026-11-02", "--refresh-figures"]) == 0
    out = {a["id"]: a for a in json.loads(p.read_text())["articles"]}
    assert out["oa-paper"]["oa"] is True and out["oa-paper"]["fig"]["kind"] == "figure"
    assert out["pw-paper"]["fig"]["kind"] == "cover"


# ----------------------------------------------------------------- fs-laser directions

@pytest.mark.parametrize("title,abstract,keep,cat,glyph", [
    ("Femtosecond laser direct writing of waveguides in lithium niobate", "", True, "Waveguides & Photonic Chips", "waveguide"),
    ("Two-photon polymerization of micro-optics on fiber tips", "", True, "Two-Photon Polymerization", "tpp"),
    ("Laser-induced periodic surface structures on titanium for antibacterial implants", "", True, "Surface Structuring & LIPSS", "lipss"),
    ("Stealth dicing of 4H-SiC wafers with picosecond pulses", "", True, "Hard & Brittle Materials", "dicing"),
    ("Bessel beam cutting of chemically strengthened glass", "", True, "Hard & Brittle Materials", "dicing"),
    ("5D optical data storage in silica glass by ultrafast laser writing", "", True, "Optical Data Storage", "storage"),
    ("Ultrafast laser welding of glass to copper", "", True, "Ultrafast Welding & Joining", "weld"),
    ("Selective laser-induced etching of fused silica for microfluidic chips", "", True, "Selective Etching & Microfluidics", "etch"),
    ("GHz-burst femtosecond ablation of silicon", "", True, "Spatiotemporal & Burst Control", None),
    ("Femtosecond laser written diffractive neural network for optical computing", "", True, "Optical Computing", "computing"),
    ("Ultrafast demagnetization in iron thin films", "Femtosecond laser pulses excite spins.", False, None, None),
    ("Attosecond pulse generation with femtosecond lasers in gases", "", False, None, None),
    ("Two-photon fluorescence microscopy of cortical neurons", "", False, None, None),
    ("LA-ICP-MS U-Pb dating of zircon by femtosecond laser ablation", "", False, None, None),
    ("Femtosecond laser-assisted cataract surgery versus phacoemulsification: 12-month outcomes", "", False, None, None),
])
def test_fs_laser_directions(title, abstract, keep, cat, glyph):
    rec = {"title": title, "abstract": abstract}
    assert vs.is_relevant(rec, CFG) is keep, title
    if keep:
        cats = vs.categorize(rec, CFG)
        assert cat in cats, cats
        if glyph:
            assert vs.glyph_for(cats, CFG) == glyph


# ----------------------------------------------------------------- daily mode

def test_daily_mode_adds_to_this_weeks_issue_and_never_repeats_across_issues(repo):
    assert vs.main(["--root", str(repo), "--daily", "--today", "2026-11-11", "--no-figures"]) == 0   # Wednesday
    wk1 = json.loads((repo / "data/issues/2026-11-09.json").read_text())
    assert wk1["window"][0] == "2026-11-09" and wk1["updated"] == "2026-11-11"
    n1 = len(wk1["articles"])
    assert n1 >= 3
    # next day: same papers come back from the APIs -> nothing new, window extends
    vs.main(["--root", str(repo), "--daily", "--today", "2026-11-12", "--no-figures"])
    wk1b = json.loads((repo / "data/issues/2026-11-09.json").read_text())
    assert len(wk1b["articles"]) == n1 and wk1b["window"][1] == "2026-11-12"
    # following Monday: a new issue starts, but papers already published last week are not repeated
    vs.main(["--root", str(repo), "--daily", "--today", "2026-11-16", "--no-figures"])
    assert not (repo / "data/issues/2026-11-16.json").exists()      # no empty issue published
    idx = json.loads((repo / "data/issues/index.json").read_text())
    assert [i["id"] for i in idx["issues"]] == ["2026-11-09"]


# ----------------------------------------------------------------- recall safeguards

def test_recall_safeguards_end_to_end(repo):
    assert vs.main(["--root", str(repo), "--daily", "--today", "2026-11-11", "--no-figures"]) == 0
    arts = json.loads((repo / "data/issues/2026-11-09.json").read_text())["articles"]
    titles = {a["title"]: a for a in arts}
    tpp = titles.get("Bend-insensitive image relay through a hollow-core fibre")
    assert tpp is not None and "Two-Photon Polymerization" in tpp["categories"]
    assert tpp["institutions"] == ["Zhejiang University"]                     # institutions straight from OpenAlex
    assert "Thermal lensing in high-power galvanometer scanners" in titles    # core journal
    assert "High-entropy oxide cathodes for sodium batteries" not in titles   # femtosecond laser only in passing
    assert "Femtosecond laser writing of waveguides in glass" not in titles   # older than max_age_days
    dic = titles["Femtosecond laser dicing of sapphire wafers with Bessel beams"]
    assert "Bessel-beam dicing" in dic["summary"]
    # Europe PMC was searched by entry date in daily mode
    q = next(c[1]["query"] for c in FakeHttp.calls if "europepmc" in c[0] and c[1] and "query" in c[1] and not c[1]["query"].startswith("DOI"))
    assert "CREATION_DATE:[2026-11-08 TO 2026-11-11]" in q and "KW:" in q
    # OpenAlex looked back 30 days
    oa = next(c[1]["filter"] for c in FakeHttp.calls if c[0] == "https://api.openalex.org/works")
    assert "from_publication_date:2026-10-12" in oa
    stats = json.loads((repo / "data/stats.json").read_text())[-1]
    assert stats["sources"]["openalex"] == 4 * len(CFG["openalex_terms"]) and stats["added"] == len(arts)


def test_process_name_once_is_enough_but_generic_mention_is_not():
    assert vs.is_relevant({"title": "Metabolic sensors", "abstract": "Printed by two-photon polymerization."}, CFG)
    assert not vs.is_relevant({"title": "Battery cathodes", "abstract": "Cleaned with a femtosecond laser before XRD and XPS."}, CFG)
    assert vs.is_relevant({"title": "Glass cutting at speed", "abstract": "GHz-burst pulses were used."}, CFG)


def test_blocked_publisher_is_skipped_after_two_403s(tmp_path):
    class BlockHttp(FakeHttp):
        def get(self, url, check_robots=False, params=None, **kw):
            FakeHttp.calls.append((url, params))
            self.last_url = url.replace("https://doi.org/", "https://www.sciencedirect.com/")
            self.last_status = 403
            return None
    FakeHttp.calls = []
    f = vs.FigureFetcher(BlockHttp(CFG), CFG, tmp_path)
    for i in range(6):
        rec = {"source": "crossref", "title": f"p{i}", "doi": f"10.1016/j.x.{i}", "url": f"https://doi.org/10.1016/j.x.{i}", "journal": "Talanta", "oa": True}
        assert f.fetch(rec, f"e{i}") is None
    landing = [c for c in FakeHttp.calls if c[0].startswith("https://doi.org/10.1016/")]
    assert len(landing) == 2          # after two 403s the prefix is skipped


def test_extra_topics_laser_written_photonics_and_light_fields():
    cfg = vs.load_config(Path(__file__).resolve().parent.parent / "config.yaml")
    yes = [
        ("Waveguide arrays for quantum walks", "Femtosecond-laser-written waveguides form the lattice."),
        ("Distributed temperature sensing to 1000 C", "Gratings were made by point-by-point inscription."),
        ("Holographic parallel printing of microstructures", ""),
    ]
    no = [
        ("Holographic microscopy of living cells", ""),
        ("Optical tweezers with multifocal holograms for cell processing", ""),
        ("Waveguide arrays for quantum walks", "Lithographically etched silicon nitride waveguides."),
    ]
    for t, a in yes:
        assert vs.is_relevant({"title": t, "abstract": a}, cfg), t
    for t, a in no:
        assert not vs.is_relevant({"title": t, "abstract": a}, cfg), t


def test_clutter_filters_and_venues(tmp_path):
    cfg = vs.load_config(Path(__file__).resolve().parent.parent / "config.yaml")
    drop = ["Endovenous laser ablation of varicose veins: two-year results",
            "LIBS analysis of soils with femtosecond laser ablation",
            "Laser cladding of Inconel 718 coatings with a fibre laser micromachining head",
            "Wakefield acceleration driven by femtosecond laser pulses",
            "Two-photon excitation microscopy of mouse cortex"]
    keep = ["Femtosecond laser texturing of titanium implants",
            "Picosecond laser drilling of turbine blades",
            "Ultrafast laser micromachining of stents"]
    for t in drop:
        assert not vs.is_relevant({"title": t, "abstract": ""}, cfg), t
    for t in keep:
        assert vs.is_relevant({"title": t, "abstract": ""}, cfg), t

    class H:
        calls = 0
        def get(self, url):
            H.calls += 1
            class R:
                def json(self_inner):
                    return {"summary_stats": {"h_index": 55 if "1234-5678" in url else 3}}
            return R()
    v = vs.VenueChecker(H(), cfg, tmp_path, online=True)
    (tmp_path / "data").mkdir()
    assert v.ok({"doi": "10.1021/acs.analchem.1", "journal": "Analytical Chemistry"})
    assert v.ok({"doi": "", "journal": "arXiv (preprint)"})
    assert not v.ok({"doi": "10.21203/rs.3", "journal": "Research Square"})
    assert not v.ok({"doi": "10.1051/e3sconf/1", "journal": "E3S Web of Conferences"})
    assert v.ok({"doi": "10.9999/x", "journal": "Good Society Journal", "issns": ["1234-5678"]})
    assert not v.ok({"doi": "10.9998/y", "journal": "Unknown Journal", "issns": ["0000-0001"]})
    n = H.calls
    assert v.ok({"doi": "10.9999/z", "journal": "Good Society Journal", "issns": ["1234-5678"]}) and H.calls == n  # cached
    v.save()
    assert json.loads((tmp_path / "data" / "venues.json").read_text())["issn:1234-5678"] == 55


def test_routine_clinical_outcomes_dropped_process_papers_kept():
    cfg = vs.load_config(Path(__file__).resolve().parent.parent / "config.yaml")
    for t in ["Femtosecond laser-assisted keratoplasty in 40 patients: a retrospective study",
              "Femtosecond laser-assisted cataract surgery: outcomes in 500 eyes"]:
        assert not vs.is_relevant({"title": t, "abstract": ""}, cfg), t
    for t in ["Femtosecond laser cutting of corneal lenticules: plasma dynamics",
              "Ultrafast laser processing of perovskite nanocrystals in glass"]:
        assert vs.is_relevant({"title": t, "abstract": ""}, cfg), t


def test_technique_papers_always_included_and_promoted():
    cfg = vs.load_config(Path(__file__).resolve().parent.parent / "config.yaml")
    # a method paper that also looks like a routine clinical application is still kept
    rec = {"title": "Femtosecond laser-assisted keratoplasty outcomes with a novel incision design",
           "abstract": "Here we develop a new femtosecond laser cutting strategy and report outcomes in 30 patients."}
    assert vs.is_technique(rec, cfg, strong=True) and vs.is_relevant(rec, cfg)
    # one mention is enough for a method paper
    rec2 = {"title": "A broadband process", "abstract": "We demonstrate a new strategy that uses an ultrafast laser to weld sapphire."}
    assert vs.is_relevant(rec2, cfg)
    art = vs.to_article({**rec, "date": "2026-11-03", "authors": [], "doi": "10.1/x"}, cfg)
    assert art.get("tier") == "notable"
    # routine application without technique cues is still dropped, and is not promoted
    rec3 = {"title": "Femtosecond laser-assisted cataract surgery: outcomes in dense cataracts", "abstract": "Retrospective review of 200 eyes."}
    assert not vs.is_technique(rec3, cfg) and not vs.is_relevant(rec3, cfg)
    # exclusions are checked before technique cues: LA-ICP-MS method papers stay out
    assert not vs.is_relevant({"title": "Femtosecond laser ablation ICP-MS of zircon", "abstract": "We develop a femtosecond LA-ICP-MS method."}, cfg)


def test_standalone_page_embeds_all_issues(tmp_path):
    import build_standalone
    root = HERE.parent.parent
    for f in ["index.html", "data/issues/index.json", "data/meetings.json"]:
        (tmp_path / f).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / f).write_bytes((root / f).read_bytes())
    for meta in json.loads((root / "data/issues/index.json").read_text(encoding="utf-8"))["issues"]:
        (tmp_path / f"data/issues/{meta['id']}.json").write_bytes((root / f"data/issues/{meta['id']}.json").read_bytes())
    out = build_standalone.build(tmp_path)
    html = out.read_text(encoding="utf-8")
    assert "window.FEMTO_DATA = {" in html and "<!--FEMTO_DATA-->" not in html
    assert html.count("</script>") == (root / "index.html").read_text(encoding="utf-8").count("</script>") + 1
