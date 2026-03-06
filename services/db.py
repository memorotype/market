from .supabase_client import get_client
from services.images import fetch_google_image

def upsert_concept_with_labels(tr_label=None, ru_label=None, de_label=None):
    sb = get_client()

    # LABEL ile mevcut kavram var mı?
    for lang, lbl in (("tr",tr_label), ("ru",ru_label), ("de",de_label)):
        if not lbl: 
            continue
        found = sb.table("product_labels").select("*").eq("lang", lang).eq("label", lbl).execute().data
        if found:
            concept_id = found[0]["concept_id"]
            concept = sb.table("product_concepts").select("*").eq("id", concept_id).execute().data[0]
            return concept

    # Yeni kavram oluştur
    concept = sb.table("product_concepts").insert({"category": None}).execute().data[0]
    cid = concept["id"]

    # Dil etiketlerini ekle
    if tr_label:
        sb.table("product_labels").insert({"concept_id": cid, "lang":"tr", "label": tr_label}).execute()
    if ru_label:
        sb.table("product_labels").insert({"concept_id": cid, "lang":"ru", "label": ru_label}).execute()
    if de_label:
        sb.table("product_labels").insert({"concept_id": cid, "lang":"de", "label": de_label}).execute()

    # Google görseli — sadece 1 defa çek
    q = de_label or tr_label or ru_label
    if q:
        img = fetch_google_image(f"{q} Lebensmittel Deutschland")
        if img:
            sb.table("product_concepts").update({"image_url": img, "image_source": "google"}).eq("id", cid).execute()
            concept["image_url"] = img

    return concept

def get_labels(concept_id: str):
    sb = get_client()
    rows = sb.table("product_labels").select("*").eq("concept_id", concept_id).execute().data
    labels = {"tr":None,"ru":None,"de":None}
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
        .order("created_at") \
        .execute().data

    history = sb.table("list_items").select("*") \
        .eq("household_code", household_code) \
        .eq("moved_to_history", True) \
        .order("moved_at", desc=True) \
        .execute().data

    return active, history

def concept_by_id(concept_id: str):
    sb = get_client()
    data = sb.table("product_concepts").select("*").eq("id", concept_id).execute().data
    return data[0] if data else None
