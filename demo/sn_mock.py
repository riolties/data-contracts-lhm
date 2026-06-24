#!/usr/bin/env python3
"""demo/sn_mock.py — ServiceNow-Mock für Hackathon-Demo LHM Data Contracts

Simuliert den Governance-First-Workflow:
  Formular → Freigabe (Dateneigner*in [+ DSB]) → Pipeline (lokal + GitHub Actions) → Ergebnis

Starten:
    cd <projektroot>
    streamlit run demo/sn_mock.py
"""
from __future__ import annotations
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).parent.parent
REPO = "riolties/data-contracts-lhm"

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="LHM ServiceNow · Neues Datenprodukt",
    page_icon="🏛️",
    layout="wide",
)

st.markdown("""
<style>
  [data-testid="stHeader"] { background: #003D8F; }
  .lhm-header {
    background: #003D8F; color: white; padding: 1rem 1.5rem;
    border-radius: 6px; margin-bottom: 1.5rem;
    display: flex; align-items: center; gap: 1rem;
  }
  .approval-box {
    border: 1px solid #ddd; border-radius: 6px;
    padding: .9rem 1rem; margin: .4rem 0; background: #fafafa;
  }
  .approval-ok  { border-color: #28a745 !important; background: #f0fff4 !important; }
  .gh-step      { font-family: monospace; font-size: .88rem; padding: .15rem 0; }
  .ok   { color: #28a745; font-weight: bold; }
  .run  { color: #e07800; font-weight: bold; }
  .err  { color: #dc3545; font-weight: bold; }
  .skip { color: #999; }
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
_D = dict(
    step=0, intake={},
    owner_ok=False, dsb_ok=False,
    local_done=False, local_ok=False,
    gh_triggered=False, gh_run_id=None, gh_run_url=None,
    gh_done=False, gh_ok=False, gh_pr_url=None,
)
for k, v in _D.items():
    st.session_state.setdefault(k, v)

# ── Lookup tables ─────────────────────────────────────────────────────────────
DOMAINS = [
    "mobilitaetsreferat", "sozialreferat", "referat-fuer-gesundheit",
    "kommunalreferat", "umweltreferat",
]
LICENSES = {
    "Datenlizenz Deutschland – Namensnennung (dl-de/by-2-0)":
        "https://www.govdata.de/dl-de/by-2-0",
    "Datenlizenz Deutschland – Zero (dl-de/zero-2-0)":
        "https://www.govdata.de/dl-de/zero-2-0",
    "Creative Commons BY 4.0":
        "https://creativecommons.org/licenses/by/4.0/",
    "Creative Commons Zero (CC0)":
        "https://creativecommons.org/publicdomain/zero/1.0/",
}
GOVDATA_THEMES = {
    "Transport":                       "http://publications.europa.eu/resource/authority/data-theme/TRAN",
    "Bevölkerung & Gesellschaft":      "http://publications.europa.eu/resource/authority/data-theme/SOCI",
    "Umwelt":                          "http://publications.europa.eu/resource/authority/data-theme/ENVI",
    "Regierung & öffentlicher Sektor": "http://publications.europa.eu/resource/authority/data-theme/GOVE",
    "Wirtschaft":                      "http://publications.europa.eu/resource/authority/data-theme/ECON",
    "Gesundheit":                      "http://publications.europa.eu/resource/authority/data-theme/HEAL",
}

# ── Helpers ───────────────────────────────────────────────────────────────────
def _stepper(active: int) -> None:
    names = ["1 · Formular", "2 · Freigabe", "3 · Pipeline", "4 · Ergebnis"]
    cols = st.columns(len(names))
    for i, (col, name) in enumerate(zip(cols, names)):
        if i < active:
            col.markdown(f"✅ ~~{name}~~")
        elif i == active:
            col.markdown(f"**▶ {name}**")
        else:
            col.markdown(f"○ {name}")
    st.markdown("---")


def _run_local(label: str, cmd: list[str]) -> bool:
    ph = st.empty()
    ph.markdown(f"<span class='run'>⟳ {label} …</span>", unsafe_allow_html=True)
    res = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
    ok = res.returncode == 0
    ph.markdown(
        f"<span class='{'ok' if ok else 'err'}'>{'✅' if ok else '❌'} {label}</span>",
        unsafe_allow_html=True,
    )
    out = (res.stdout + res.stderr).strip()
    if out:
        with st.expander("Output", expanded=not ok):
            st.code(out)
    return ok


def _step_icon(status: str, conclusion: str | None) -> str:
    if status == "completed":
        return {"success": "✅", "failure": "❌", "skipped": "⊘"}.get(conclusion or "", "✅")
    if status == "in_progress":
        return "⟳"
    if status == "queued":
        return "⏳"
    return "○"


def _gh_run_status(run_id: int) -> dict:
    r = subprocess.run(
        ["gh", "run", "view", str(run_id), "--json",
         "status,conclusion,jobs,url"],
        cwd=str(ROOT), capture_output=True, text=True,
    )
    if r.returncode != 0:
        return {}
    return json.loads(r.stdout)


def _find_latest_run() -> dict | None:
    """Neuesten Run von intake-to-contract.yml holen (bis zu 10s warten)."""
    for _ in range(5):
        r = subprocess.run(
            ["gh", "run", "list", "--workflow", "intake-to-contract.yml",
             "--limit", "1", "--json", "databaseId,status,url,createdAt"],
            cwd=str(ROOT), capture_output=True, text=True,
        )
        if r.returncode == 0:
            runs = json.loads(r.stdout)
            if runs:
                return runs[0]
        time.sleep(2)
    return None


def _find_pr(domain: str, product: str) -> str | None:
    branch = f"contract/{domain}/{product}"
    r = subprocess.run(
        ["gh", "pr", "list", "--head", branch,
         "--json", "url,title,state", "--limit", "1"],
        cwd=str(ROOT), capture_output=True, text=True,
    )
    if r.returncode == 0:
        prs = json.loads(r.stdout)
        if prs:
            return prs[0]["url"]
    return None


# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="lhm-header">
  <span style="font-size:2rem">🏛️</span>
  <div>
    <strong style="font-size:1.1rem">Landeshauptstadt München &nbsp;·&nbsp; ServiceNow</strong><br>
    <span style="opacity:.85">Katalog-Item: Neues Datenprodukt anmelden</span>
  </div>
</div>
""", unsafe_allow_html=True)

step = st.session_state.step

# ══════════════════════════════════════════════════════════════════════════════
# STEP 0 — Formular
# ══════════════════════════════════════════════════════════════════════════════
if step == 0:
    _stepper(0)

    with st.form("intake_form"):
        st.markdown("#### 📁 Allgemeine Angaben")
        c1, c2 = st.columns(2)
        domain = c1.selectbox("Referat (Domäne) *", DOMAINS)
        product = c2.text_input("Produkt-ID *", value="radverkehr")
        title = st.text_input("Titel *", value="Radverkehr Tageswerte München")

        st.markdown("#### 📝 Beschreibung")
        purpose = st.text_area("Zweck *",
            value="Tägliche Radverkehrszahlen je Dauerzählstelle inkl. Wetterdaten.", height=70)
        c1, c2 = st.columns(2)
        usage = c1.text_area("Nutzung",
            value="Mobilitätsplanung, Monitoring, Open-Data-Veröffentlichung.", height=70)
        limitations = c2.text_area("Einschränkungen",
            value="Nur Dauerzählstellen; Wetter aggregiert je Tag.", height=70)

        st.markdown("#### 👤 Verantwortung")
        c1, c2, c3 = st.columns(3)
        data_owner = c1.text_input(
            "Dateneigner*in (Datenverantwortliche*r) *",
            value="dateneigner.mobilitaet@muenchen.de",
        )
        data_steward = c2.text_input(
            "Data Steward",
            value="steward.mobilitaet@muenchen.de",
            help="Operativ verantwortliche Person für Qualität und Pflege des Datenprodukts",
        )
        contact = c3.text_input("Kontakt", value="open.data@muenchen.de")

        st.markdown("#### 🔒 Klassifizierung & Datenschutz")
        c1, c2, c3, c4 = st.columns(4)
        classification = c1.selectbox("Klassifizierung *",
                                      ["public", "internal", "confidential"])
        update_frequency = c2.text_input("Aktualisierungsfrequenz",
                                         value="P1D", help="ISO-8601: P1D=täglich, P1M=monatlich")
        personal_data = c3.toggle("Personenbezogene Daten?", value=False)
        open_data_candidate = c4.toggle("Open-Data-Kandidat?", value=True)

        legal_basis = retention_period = ""
        if personal_data:
            c1, c2 = st.columns(2)
            legal_basis = c1.text_input("Rechtsgrundlage *", value="Art. 6(1)(e) DSGVO")
            retention_period = c2.text_input("Aufbewahrungsfrist *", value="P3Y")

        license_uri = spatial = ""
        govdata_cats: list[str] = []
        if open_data_candidate:
            st.markdown("#### 🌐 Open-Data-Details")
            c1, c2 = st.columns(2)
            lic_label = c1.selectbox("Lizenz *", list(LICENSES.keys()))
            license_uri = LICENSES[lic_label]
            spatial = c2.text_input("Räumliche Abdeckung (GeoNames-URI)",
                                    value="https://sws.geonames.org/2867714/")
            theme_labels = st.multiselect("GovData-Kategorie(n) *",
                                          list(GOVDATA_THEMES.keys()), default=["Transport"])
            govdata_cats = [GOVDATA_THEMES[t] for t in theme_labels]

        st.markdown("#### 🗄️ Datenquelle")
        st.caption("Spalten & Typen werden **nicht** eingetragen — der Profiler zieht sie automatisch aus der CSV nach Freigabe.")
        c1, c2 = st.columns(2)
        source_type = c1.selectbox("Quelltyp *",
                                   ["file_export", "reporting_db", "eai", "api"])
        source_location = c2.text_input("Quellpfad / CSV-Datei *",
                                        value="data/sample_radverkehr_tageswerte_2025_01.csv")

        submitted = st.form_submit_button(
            "📋 Antrag einreichen", type="primary", use_container_width=True)

    if submitted:
        intake: dict = {
            "domain": domain, "product": product, "title": title,
            "description": {"purpose": purpose, "usage": usage, "limitations": limitations},
            "owner": {"data_owner": data_owner, "data_steward": data_steward, "contact": contact},
            "classification": classification, "update_frequency": update_frequency,
            "personal_data": personal_data, "open_data_candidate": open_data_candidate,
            "source": {"type": source_type, "location": source_location},
        }
        if personal_data:
            intake["legal_basis"] = legal_basis
            intake["retention_period"] = retention_period
        if open_data_candidate:
            if license_uri:
                intake["license"] = license_uri
            if spatial:
                intake["spatial"] = spatial
            if govdata_cats:
                intake["govdata_category"] = govdata_cats

        for k, v in _D.items():
            st.session_state[k] = v
        st.session_state.intake = intake
        st.session_state.step = 1
        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# STEP 1 — Freigabe
# ══════════════════════════════════════════════════════════════════════════════
elif step == 1:
    _stepper(1)
    intake = st.session_state.intake

    st.subheader("Freigabe-Workflow")
    st.info(
        f"**{intake['title']}** · Domäne: `{intake['domain']}` "
        f"· Produkt: `{intake['product']}` · Klassifizierung: `{intake['classification']}`"
    )

    # Stufe 1: Dateneigner*in
    ok1 = st.session_state.owner_ok
    st.markdown(f"""
    <div class="approval-box {'approval-ok' if ok1 else ''}">
      <strong>Stufe 1 — Dateneigner*in (Datenverantwortliche*r)</strong>
      &nbsp; {'✅ Freigegeben' if ok1 else '⏳ Ausstehend'}<br>
      <small>📧 {intake['owner']['data_owner']}</small><br>
      <small>Data Steward: {intake['owner'].get('data_steward', '–')}</small>
    </div>""", unsafe_allow_html=True)
    if not ok1:
        if st.button("✅ Als Dateneigner*in freigeben", type="primary"):
            st.session_state.owner_ok = True
            st.rerun()

    # Stufe 2: DSB (nur bei personal_data)
    if intake.get("personal_data"):
        ok2 = st.session_state.dsb_ok
        st.markdown(f"""
        <div class="approval-box {'approval-ok' if ok2 else ''}">
          <strong>Stufe 2 — Datenschutzbeauftragte*r (DSB)</strong>
          &nbsp; {'✅ Freigegeben' if ok2 else '⏳ Ausstehend'}<br>
          <small>Erforderlich weil <code>personal_data = true</code></small>
        </div>""", unsafe_allow_html=True)
        if not ok2:
            if st.button("✅ Als Datenschutzbeauftragte*r freigeben"):
                st.session_state.dsb_ok = True
                st.rerun()
    else:
        st.markdown("""
        <div class="approval-box">
          <strong>Stufe 2 — Datenschutzbeauftragte*r (DSB)</strong>
          &nbsp; <em>nicht erforderlich</em><br>
          <small><code>personal_data = false</code></small>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")
    needs_dsb = intake.get("personal_data", False)
    can_go = st.session_state.owner_ok and (not needs_dsb or st.session_state.dsb_ok)

    if can_go:
        st.success("Governance-Freigabe vollständig — ServiceNow triggert jetzt die Pipeline.")
        if st.button("🚀 Pipeline triggern", type="primary", use_container_width=True):
            st.session_state.step = 2
            st.rerun()
    else:
        st.button("🚀 Pipeline triggern", disabled=True, use_container_width=True)

    if st.button("← Zurück zum Formular"):
        st.session_state.step = 0
        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# STEP 2 — Pipeline (lokal + GitHub Actions)
# ══════════════════════════════════════════════════════════════════════════════
elif step == 2:
    _stepper(2)
    intake = st.session_state.intake
    product_dir = ROOT / "domains" / intake["domain"] / "data-products" / intake["product"]

    # ── A: Lokale Pipeline ────────────────────────────────────────────────────
    st.markdown("### 🖥️ Lokale Pipeline")
    st.caption("Schritt 1–4 laufen lokal zur Voransicht der generierten Dateien.")

    if not st.session_state.local_done:
        intake_file = Path(tempfile.gettempdir()) / "lhm_demo_intake.json"
        profiling_file = Path(tempfile.gettempdir()) / "lhm_demo_profiling.json"
        intake_file.write_text(json.dumps(intake, ensure_ascii=False, indent=2), encoding="utf-8")

        all_ok = True
        ok1 = _run_local(
            "Schritt 1 · Profiler — Spalten & Typen aus CSV extrahieren",
            [sys.executable, "scripts/profile_source.py",
             "--source", intake["source"]["location"],
             "--out", str(profiling_file)],
        )
        all_ok = all_ok and ok1

        if ok1:
            ok2 = _run_local(
                "Schritt 2 · intake_to_odcs — Input/Output-Contracts + data-product.yaml",
                [sys.executable, "scripts/intake_to_odcs.py",
                 "--intake", str(intake_file),
                 "--profiling", str(profiling_file),
                 "--write"],
            )
            all_ok = all_ok and ok2
        else:
            ok2 = False

        if ok2:
            glob_pat = (f"domains/{intake['domain']}/data-products/"
                        f"{intake['product']}/contracts/**/*.odcs.yaml")
            ok3 = _run_local(
                "Schritt 3 · validate_odcs — ODCS-Schema + LHM-Regeln R1–R10",
                [sys.executable, "scripts/validate_odcs.py", glob_pat],
            )
            all_ok = all_ok and ok3

            if ok3:
                _run_local(
                    "Schritt 4 · render_catalog — Markdown-Katalogseite generieren",
                    [sys.executable, "scripts/render_catalog.py",
                     "--product", str(product_dir), "--write"],
                )

        out_dir = product_dir / "contracts" / "output"
        out_contracts = list(out_dir.glob("*.odcs.yaml")) if out_dir.exists() else []
        if out_contracts:
            _run_local(
                "CKAN · Payload-Vorschau (dry-run)",
                [sys.executable, "scripts/ckan_publish.py",
                 "--contract", str(out_contracts[0])],
            )

        st.session_state.local_done = True
        st.session_state.local_ok = all_ok
    else:
        icon = "✅" if st.session_state.local_ok else "❌"
        st.markdown(f"{icon} Lokale Pipeline abgeschlossen.")

    if not st.session_state.local_ok:
        st.error("Lokale Pipeline fehlgeschlagen — Fehlerdetails oben.")
        if st.button("← Zurück"):
            for k, v in _D.items():
                st.session_state[k] = v
            st.session_state.intake = intake
            st.session_state.step = 1
            st.rerun()
        st.stop()

    # ── B: GitHub Actions ─────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### ☁️ GitHub Actions — echter Pipeline-Trigger")
    st.caption("Simuliert den ServiceNow → GitLab-Trigger in der echten Umgebung.")

    # Trigger (einmalig)
    if not st.session_state.gh_triggered:
        with st.spinner("Workflow wird ausgelöst …"):
            intake_json_str = json.dumps(intake, ensure_ascii=False)
            tr = subprocess.run(
                ["gh", "workflow", "run", "intake-to-contract.yml",
                 "--ref", "main",
                 "-f", f"intake_json={intake_json_str}"],
                cwd=str(ROOT), capture_output=True, text=True,
            )
            if tr.returncode != 0:
                st.error(f"Trigger fehlgeschlagen:\n```\n{tr.stderr}\n```")
                st.stop()

            with st.spinner("Warte auf Run-ID …"):
                run_info = _find_latest_run()

        if run_info:
            st.session_state.gh_run_id = run_info["databaseId"]
            st.session_state.gh_run_url = run_info["url"]
        st.session_state.gh_triggered = True
        st.rerun()

    # Run-URL anzeigen
    if st.session_state.gh_run_url:
        st.markdown(f"🔗 **GitHub Actions Run:** [{st.session_state.gh_run_url}]({st.session_state.gh_run_url})")

    # Poll & Fortschritt anzeigen
    if st.session_state.gh_run_id and not st.session_state.gh_done:
        run_data = _gh_run_status(st.session_state.gh_run_id)
        overall_status = run_data.get("status", "queued")
        overall_conclusion = run_data.get("conclusion")

        with st.container():
            jobs = run_data.get("jobs", [])
            if jobs:
                for job in jobs:
                    j_icon = _step_icon(job.get("status", ""), job.get("conclusion"))
                    st.markdown(f"**{j_icon} Job: {job['name']}**")
                    for s in job.get("steps", []):
                        icon = _step_icon(s.get("status", ""), s.get("conclusion"))
                        css = "skip" if s.get("conclusion") == "skipped" else ""
                        st.markdown(
                            f"<div class='gh-step'><span class='{css}'>"
                            f"&nbsp;&nbsp;&nbsp;{icon}&nbsp; {s['name']}</span></div>",
                            unsafe_allow_html=True,
                        )
            else:
                status_label = {
                    "queued": "⏳ Run steht in der Warteschlange …",
                    "in_progress": "⟳ Run läuft …",
                    "completed": "Abgeschlossen.",
                }.get(overall_status, f"Status: {overall_status}")
                st.markdown(status_label)

        if overall_status == "completed":
            st.session_state.gh_ok = overall_conclusion == "success"
            st.session_state.gh_done = True
            # PR suchen
            pr_url = _find_pr(intake["domain"], intake["product"])
            if pr_url:
                st.session_state.gh_pr_url = pr_url
            st.rerun()
        else:
            time.sleep(5)
            st.rerun()

    # Abgeschlossen
    if st.session_state.gh_done:
        if st.session_state.gh_ok:
            st.success("✅ GitHub Actions Run erfolgreich!")
        else:
            st.warning("⚠️ GitHub Actions Run abgeschlossen (siehe Run-Link für Details).")

        if st.session_state.gh_pr_url:
            st.success(f"🎉 Pull Request geöffnet: [{st.session_state.gh_pr_url}]({st.session_state.gh_pr_url})")

        if st.button("📄 Ergebnis anzeigen →", type="primary", use_container_width=True):
            st.session_state.step = 3
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# STEP 3 — Ergebnis
# ══════════════════════════════════════════════════════════════════════════════
elif step == 3:
    _stepper(3)
    intake = st.session_state.intake
    product_dir = ROOT / "domains" / intake["domain"] / "data-products" / intake["product"]

    st.success(f"🎉 Data Contract für **{intake['title']}** erfolgreich erstellt!")

    if st.session_state.gh_pr_url:
        st.info(f"**GitHub PR:** [{st.session_state.gh_pr_url}]({st.session_state.gh_pr_url})")

    tab_readme, tab_out, tab_in, tab_ckan = st.tabs([
        "📖 Katalog / README",
        "📋 Output Contract (ODCS)",
        "📥 Input Contract (ODCS)",
        "🌐 CKAN-Payload",
    ])

    with tab_readme:
        readme = product_dir / "README.md"
        if readme.exists():
            st.markdown(readme.read_text(encoding="utf-8"))
        else:
            st.warning("README.md nicht gefunden.")

    with tab_out:
        out_files = list((product_dir / "contracts" / "output").glob("*.odcs.yaml"))
        if out_files:
            st.code(out_files[0].read_text(encoding="utf-8"), language="yaml")
        else:
            st.warning("Kein Output-Contract gefunden.")

    with tab_in:
        in_files = list((product_dir / "contracts" / "input").glob("*.odcs.yaml"))
        if in_files:
            st.code(in_files[0].read_text(encoding="utf-8"), language="yaml")
        else:
            st.warning("Kein Input-Contract gefunden.")

    with tab_ckan:
        out_files = list((product_dir / "contracts" / "output").glob("*.odcs.yaml"))
        if out_files:
            res = subprocess.run(
                [sys.executable, "scripts/ckan_publish.py",
                 "--contract", str(out_files[0])],
                cwd=str(ROOT), capture_output=True, text=True,
            )
            st.code(res.stdout or res.stderr, language="json")

    st.markdown("---")
    if st.button("🔄 Neue Demo starten", use_container_width=True):
        for k, v in _D.items():
            st.session_state[k] = v
        st.rerun()
