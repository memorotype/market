from services.supabase_client import get_client
from services.images import fetch_google_image

# Basit Almanca market eşleşme sözlüğü
GERMAN_FOOD_MAP = {
    "domates": "Tomaten",
    "çeri domates": "Cherrytomaten",
    "Cherry domates": "Cherrytomaten",
    "kiraz domates": "Cherrytomaten",
    "salatalık": "Gurke",
    "hıyar": "Gurke",
    "biber": "Paprika",
    "patates": "Kartoffeln",
    "soğan": "Zwiebeln",
    "elma": "Apfel",
    "armut": "Birne",
    "süt": "Milch",
    "yoğurt": "Joghurt",
    "peynir": "Käse",
    "ekmek": "Brot",
    "yumurta": "Eier",
    "kıyma": "Hackfleisch",
}


def _ensure_label(sb, concept_id: str, lang: str, label: str | None):
    """product_labels içinde (concept_id, lang) yoksa ekler."""
    if not label:
        return
    exists = sb.table("product_labels").select("*") \
                .eq("concept_id", concept_id) \
                .eq("lang", lang).execute().data
    if not exists:
        sb.table("product_labels").insert({
            "concept_id": concept_id,
            "lang": lang,
            "label": label,
            "synonyms": []
        }).execute()


def upsert_concept_with_labels(tr_label=None, ru_label=None, de_label=None):
    """
    1) Eğer label var ve zaten concept varsa → etiketi güncelle & eksikleri ekle
    2) Yoksa yeni concept yarat → TR/RU etiketlerini kaydet
    3) DE etiketi otomatik Almanca sözlükten çevrilir
    4) Görsel boşsa bir defa Google CSE'den çekilir
    """

    sb = get_client()

    # 1) Eski kavram var mı?
    for lang, lbl in (("tr", tr_label), ("ru", ru_label), ("de", de_label)):
        if not lbl:
            continue

        match = sb.table("product_labels").select("*") \
                  .eq("lang", lang).eq("label", lbl).execute().data

        if match:
            concept_id = match[0]["concept_id"]
            concept = sb.table("product_concepts").select("*") \
                        .eq("id", concept_id).execute().data[0]

            # Eksik etiketleri tamamla
            _ensure_label(sb, concept_id, "tr", tr_label)
            _ensure_label(sb, concept_id, "ru", ru_label)

            # DE otomatik çeviri
            base = (de_label or tr_label or ru_label or "").lower()
            de_auto = GERMAN_FOOD_MAP.get(base, (tr_label or ru_label or de_label))

            _ensure_label(sb, concept_id, "de", de_auto)

            # Görsel boşsa bir defa al
            if not concept.get("image_url"):
                query = de_auto or tr_label or ru_label
                img = fetch_google_image(f"{query} Lebensmittel Deutschland")
                if img:
                    sb.table("product_concepts").update({
                        "image_url": img,
                        "image_source": "google"
                    }).eq("id", concept_id).execute()

            return sb.table("product_concepts").select("*") \
                     .eq("id", concept_id).execute().data[0]

    # 2) Hiç kavram bulunamadıysa → YENİ yarat
    concept = sb.table("product_concepts").insert({
        "category": None
    }).execute().data[0]

    cid = concept["id"]

    # TR / RU etiketlerini ekle
    if tr_label:
        sb.table("product_labels").insert({
            "concept_id": cid,
            "lang": "tr",
            "label": tr_label
        }).execute()

    if ru_label:
        sb.table("product_labels").insert({
            "concept_id": cid,
            "lang": "ru",
            "label": ru_label
        }).execute()

    # 3) DE etiketi otomatik belirle
    base = (de_label or tr_label or ru_label or "").lower()
    de_auto = GERMAN_FOOD_MAP.get(base, (tr_label or ru_label or de_label))

    if de_auto:
        sb.table("product_labels").insert({
            "concept_id": cid,
            "lang": "de",
            "label": de_auto
        }).execute()

    # 4) Görsel çek
    query = de_auto or tr_label or ru_label
    if query:
        img = fetch_google_image(f"{query} Lebensmittel Deutschland")
        if img:
            sb.table("product_concepts").update({
                "image_url": img,
                "image_source": "google"
            }).eq("id", cid).execute()
            concept["image_url"] = img

    return concept


def get_labels(concept_id: str):
    sb = get_client()
    rows = sb.table("product_labels").select("*") \
                .eq("concept_id", concept_id).execute().data
    labels = {"tr": None, "ru": None, "de": None}
    for r in rows:
        labels[r["lang"]] = r["label"]
    return labels


def add_item(household_code: str, concept_id: str, qty=None, unit=None, note=None):
    sb = get_client()
    return sb.table("list_items").insert({
        "household_code": household_code,
        "concept_id": concept_id,
        "qty": qty,
        "unit": unit,
        "note": note
    }).execute()


def mark_done(item_id: str):
    sb = get_client()
    return sb.table("list_items").update({
        "is_done": True,
        "moved_to_history": True,
        "moved_at": "now()"
    }).eq("id", item_id).execute()


def undo_item(item_id: str):
    sb = get_client()
    return sb.table("list_items").update({
        "is_done": False,
        "moved_to_history": False,
        "moved_at": None
    }).eq("id", item_id).execute()


def fetch_active_and_history(household_code: str):
    sb = get_client()

    active = sb.table("list_items").select("*") \
                .eq("household_code", household_code) \
                .eq("moved_to_history", False) \
                .order("created_at").execute().data

    history = sb.table("list_items").select("*") \
                 .eq("household_code", household_code) \
                 .eq("moved_to_history", True) \
                 .order("moved_at", desc=True).execute().data

    return active, history


def concept_by_id(concept_id: str):
    sb = get_client()
    data = sb.table("product_concepts").select("*") \
              .eq("id", concept_id).execute().data
    return data[0] if data else None
