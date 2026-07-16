import requests
import streamlit as st

API_URL = "http://localhost:8000"

st.set_page_config(
    page_title="AML Compliance Agent",
    page_icon="⚖️",
    layout="centered",
)

st.title("⚖️ AML Compliance Agent")
st.caption("Wsparcie decyzji analitycznej — dane przetwarzane lokalnie (RODO-compliant)")

st.info(
    "**Opisz sytuację bez danych osobowych.**  \n"
    "Nie podawaj nazwisk, PESEL-u ani numerów rachunków — tylko opis zachowania/transakcji.",
    icon="ℹ️",
)

with st.form("case_form"):
    description = st.text_area(
        "Opis sytuacji transakcyjnej / behawioralnej",
        height=200,
        placeholder=(
            "Przykład: Klient dokonał 3 wpłat gotówkowych w ciągu 5 dni: "
            "6 000 EUR, 5 500 EUR i 4 200 EUR — w różnych oddziałach. "
            "Brak spójnego wyjaśnienia źródła środków. "
            "Działalność gospodarcza zarejestrowana 2 miesiące temu..."
        ),
    )
    analyst_id = st.text_input("ID analityka (audit log)", value="analityk_01")
    submitted = st.form_submit_button("Analizuj", type="primary", use_container_width=True)

if submitted:
    if len(description.strip()) < 20:
        st.error("Opis jest za krótki — dodaj więcej szczegółów sytuacji.")
        st.stop()

    with st.spinner("Przeszukuję przepisy i analizuję sprawę..."):
        try:
            resp = requests.post(
                f"{API_URL}/analyze",
                json={"description": description, "analyst_id": analyst_id},
                timeout=120,
            )
            resp.raise_for_status()
            result = resp.json()
        except requests.exceptions.ConnectionError:
            st.error(
                "Nie można połączyć z API. "
                "Uruchom backend: `uvicorn api.main:app --port 8000`"
            )
            st.stop()
        except Exception as e:
            st.error(f"Błąd: {e}")
            st.stop()

    flag = result["flag_recommended"]
    confidence = result["confidence"]

    # ── Verdict ──────────────────────────────────────────────────────────
    if flag:
        st.error(f"⚠️ **ZALECANA FLAGA: TAK** — pewność modelu: {confidence:.0%}")
    else:
        st.success(f"✅ **BRAK PODSTAW DO FLAGOWANIA** — pewność modelu: {confidence:.0%}")

    st.progress(confidence)

    # ── Reasoning ────────────────────────────────────────────────────────
    with st.expander("Uzasadnienie", expanded=True):
        st.write(result["reasoning"])

    # ── Citations ────────────────────────────────────────────────────────
    citations = result.get("citations", [])
    if citations:
        with st.expander(f"Podstawy prawne — {len(citations)} przepis(ów)", expanded=True):
            for c in citations:
                st.markdown(f"**{c['article_ref']} — {c['law_name']}**")
                excerpt = c["text"]
                if len(excerpt) > 350:
                    excerpt = excerpt[:350] + "…"
                st.markdown(f"> {excerpt}")
                st.divider()

    # ── Recommendation ───────────────────────────────────────────────────
    st.info(f"**Rekomendacja:** {result['recommendation']}")

    # ── Metadata ─────────────────────────────────────────────────────────
    with st.expander("Szczegóły techniczne"):
        st.json({
            "model": result["model_used"],
            "retrieved_chunks": result["retrieved_chunks"],
            "processing_time_ms": result["processing_time_ms"],
        })
