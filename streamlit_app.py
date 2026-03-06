import streamlit as st
from services.db import (
    upsert_concept_with_labels, get_labels, add_item,
    mark_done, undo_item, fetch_active_and_history,
    concept_by_id
)
from core.i18n import UI_TEXT

st.set_page_config(page_title="Alışveriş Listesi", page_icon="🛒", layout="wide")

st.title("🛒 Ortak Alışveriş Listesi — TR / DE / RU")

# Sidebar ayarları
with st.sidebar:
    st.header("Ayarlar")
    user_lang = st.selectbox("Dil", ["tr","ru"], index=0)
    household_code = st.text_input("Hane Kodu", value="bizim-ev")
    st.caption("Aynı hane kodunu eşin de girerse aynı listeyi görür.")

ui = UI_TEXT[user_lang]

st.subheader(ui["add_item"])

with st.form("add_form"):
    text = st.text_input("Ürün adı (TR veya RU)")
    qty  = st.text_input(ui["qty"])
    unit = st.selectbox(ui["unit"], ["adet","paket","kg","g","L","ml","—"])
    note = st.text_input(ui["note"])
    submit = st.form_submit_button("Ekle")

if submit and text.strip() and household_code.strip():
    tr_label = text if user_lang=="tr" else None
    ru_label = text if user_lang=="ru" else None
    concept = upsert_concept_with_labels(tr_label=tr_label, ru_label=ru_label, de_label=None)
    add_item(household_code, concept["id"], qty or None, unit or None, note or None)
    st.success("Eklendi ✔")
    st.rerun()

# Listeyi yükle
active, history = fetch_active_and_history(household_code)

def render_row(item):
    c = concept_by_id(item["concept_id"])
    labels = get_labels(item["concept_id"])
    img = c.get("image_url")

    col = st.columns([0.15, 0.45, 0.4])

    with col[0]:
        if img:
            st.image(img, width=60)
        else:
            st.write("—")

    with col[1]:
        st.write(f"**TR:** {labels.get('tr') or '—'}")
        st.write(f"**DE:** {labels.get('de') or '—'}")

    with col[2]:
        st.write(f"**RU:** {labels.get('ru') or '—'}")
        st.write(f"{item.get('qty') or ''} {item.get('unit') or ''}")
        st.write(f"_{item.get('note') or ''}_")

        if not item["moved_to_history"]:
            if st.button("✓ Sepete", key=f"done_{item['id']}"):
                mark_done(item["id"])
                st.rerun()
        else:
            if st.button("↩ Geri Al", key=f"undo_{item['id']}"):
                undo_item(item["id"])
                st.rerun()

# Alınacaklar
st.subheader("🧾 " + ui["todo"])
for it in active:
    render_row(it)

st.markdown("---")

# Son alınanlar — listenin ALTINDA
st.subheader("🕘 " + ui["history"])
for it in history:
    render_row(it)
