from dataclasses import dataclass

@dataclass
class ListItem:
    id: str
    concept_id: str
    qty: str | None
    unit: str | None
    note: str | None
    is_done: bool
    moved_to_history: bool
