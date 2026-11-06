"""
Hostel, gender, and caretaker scope rules for IIT Patna Hostel Platform.

Rules:
- Boys Hostels: Kalam (Blocks A, B, C, D), CV Raman (CVR), Aryabhatta (Blocks A, B, D)
- Girls Hostels: Aryabhatta (Block C), Asima
- Primary Caretakers:
  * kalam_caretaker@iitp.ac.in -> Kalam (Blocks A, B, C, D)
  * asima_caretaker@iitp.ac.in -> Asima
  * aryabhatta_girls_caretaker@iitp.ac.in -> Aryabhatta (Block C)
  * aryabhatta_caretaker@iitp.ac.in -> Aryabhatta (Blocks A, B, D)
  * cvr_caretaker@iitp.ac.in -> CV Raman (CVR)
"""

from __future__ import annotations
from typing import Optional, Dict, Any, List
from sqlalchemy import or_, and_, not_

PRIMARY_CARETAKERS = {
    # ── Primary Caretakers ──
    "kalam_caretaker@iitp.ac.in": {
        "display_name": "Kalam Hostel Caretaker",
        "hostel": "Kalam",
        "gender": "Boys",
        "blocks": ["Block A", "Block B", "Block C", "Block D"],
        "description": "Caretaker for APJ Abdul Kalam Hostel (Blocks A, B, C, D)",
        "password": "caretaker123",
    },
    "asima_caretaker@iitp.ac.in": {
        "display_name": "Asima Hostel Caretaker",
        "hostel": "Asima",
        "gender": "Girls",
        "blocks": ["All Blocks"],
        "description": "Caretaker for Asima Girls Hostel",
        "password": "caretaker123",
    },
    "aryabhatta_girls_caretaker@iitp.ac.in": {
        "display_name": "Aryabhatta Girls Caretaker",
        "hostel": "Aryabhatta",
        "gender": "Girls",
        "blocks": ["Block C"],
        "description": "Caretaker for Aryabhatta Girls Hostel (Block C)",
        "password": "caretaker123",
    },
    "aryabhatta_caretaker@iitp.ac.in": {
        "display_name": "Aryabhatta Boys Caretaker",
        "hostel": "Aryabhatta",
        "gender": "Boys",
        "blocks": ["Block A", "Block B", "Block D"],
        "description": "Caretaker for Aryabhatta Boys Hostel (Blocks A, B, D)",
        "password": "caretaker123",
    },
    "cvr_caretaker@iitp.ac.in": {
        "display_name": "CV Raman (CVR) Caretaker",
        "hostel": "CV Raman",
        "gender": "Boys",
        "blocks": ["All Blocks"],
        "description": "Caretaker for CV Raman (CVR) Boys Hostel",
        "password": "caretaker123",
    },

    # ── Primary Wardens (Same Caretaker Role & Scoped Access) ──
    "kalam_warden@iitp.ac.in": {
        "display_name": "Kalam Hostel Warden",
        "hostel": "Kalam",
        "gender": "Boys",
        "blocks": ["Block A", "Block B", "Block C", "Block D"],
        "description": "Warden for APJ Abdul Kalam Hostel (Blocks A, B, C, D)",
        "password": "warden123",
    },
    "asima_warden@iitp.ac.in": {
        "display_name": "Asima Hostel Warden",
        "hostel": "Asima",
        "gender": "Girls",
        "blocks": ["All Blocks"],
        "description": "Warden for Asima Girls Hostel",
        "password": "warden123",
    },
    "aryabhatta_girls_warden@iitp.ac.in": {
        "display_name": "Aryabhatta Girls Warden",
        "hostel": "Aryabhatta",
        "gender": "Girls",
        "blocks": ["Block C"],
        "description": "Warden for Aryabhatta Girls Hostel (Block C)",
        "password": "warden123",
    },
    "aryabhatta_warden@iitp.ac.in": {
        "display_name": "Aryabhatta Boys Warden",
        "hostel": "Aryabhatta",
        "gender": "Boys",
        "blocks": ["Block A", "Block B", "Block D"],
        "description": "Warden for Aryabhatta Boys Hostel (Blocks A, B, D)",
        "password": "warden123",
    },
    "cvr_warden@iitp.ac.in": {
        "display_name": "CV Raman (CVR) Warden",
        "hostel": "CV Raman",
        "gender": "Boys",
        "blocks": ["All Blocks"],
        "description": "Warden for CV Raman (CVR) Boys Hostel",
        "password": "warden123",
    },
}

DEFAULT_CARETAKER_PASSWORD = "caretaker123"
DEFAULT_WARDEN_PASSWORD = "warden123"
DEFAULT_ADMIN_PASSWORD = "admin1234"

BOYS_HOSTEL_OPTIONS = [
    {"hostel": "Kalam", "block": "Block A", "label": "Kalam - Block A"},
    {"hostel": "Kalam", "block": "Block B", "label": "Kalam - Block B"},
    {"hostel": "Kalam", "block": "Block C", "label": "Kalam - Block C"},
    {"hostel": "Kalam", "block": "Block D", "label": "Kalam - Block D"},
    {"hostel": "CV Raman", "block": "", "label": "CV Raman (CVR)"},
    {"hostel": "Aryabhatta", "block": "Block A", "label": "Aryabhatta - Block A"},
    {"hostel": "Aryabhatta", "block": "Block B", "label": "Aryabhatta - Block B"},
    {"hostel": "Aryabhatta", "block": "Block D", "label": "Aryabhatta - Block D"},
]

GIRLS_HOSTEL_OPTIONS = [
    {"hostel": "Aryabhatta", "block": "Block C", "label": "Aryabhatta - Block C"},
    {"hostel": "Asima", "block": "", "label": "Asima"},
]


def normalize_hostel(hostel: Optional[str]) -> str:
    if not hostel:
        return ""
    h = hostel.strip().lower()
    if h in ("cvr", "cv raman", "c.v. raman", "cv-raman"):
        return "CV Raman"
    if "kalam" in h:
        return "Kalam"
    if "asima" in h:
        return "Asima"
    if "aryabhatta" in h:
        return "Aryabhatta"
    return hostel.strip()


def normalize_block(block: Optional[str]) -> str:
    if not block:
        return ""
    b = block.strip()
    # Check single letters
    b_upper = b.upper()
    if b_upper in ("A", "BLOCK A", "BLOCK-A", "WING A"):
        return "Block A"
    if b_upper in ("B", "BLOCK B", "BLOCK-B", "WING B"):
        return "Block B"
    if b_upper in ("C", "BLOCK C", "BLOCK-C", "WING C"):
        return "Block C"
    if b_upper in ("D", "BLOCK D", "BLOCK-D", "WING D"):
        return "Block D"
    return b


def is_block_c(block: Optional[str]) -> bool:
    if not block:
        return False
    b = block.strip().upper()
    return b in ("C", "BLOCK C", "BLOCK-C", "WING C") or "BLOCK C" in b or " C " in f" {b} "


def get_options_for_gender(gender: str) -> List[Dict[str, str]]:
    g = (gender or "").strip().lower()
    if g in ("female", "girl", "girls", "f"):
        return GIRLS_HOSTEL_OPTIONS
    return BOYS_HOSTEL_OPTIONS


def validate_allocation(gender: str, hostel: str, block: Optional[str] = "") -> tuple[bool, str]:
    g = (gender or "").strip().lower()
    norm_h = normalize_hostel(hostel)
    norm_b = normalize_block(block)

    if g in ("female", "girl", "girls", "f"):
        if norm_h == "Asima":
            return True, ""
        if norm_h == "Aryabhatta" and is_block_c(norm_b):
            return True, ""
        return False, "Female students can only be allocated to Aryabhatta (Block C) or Asima."

    # Default to male / boys
    if norm_h == "Kalam":
        return True, ""
    if norm_h == "CV Raman":
        return True, ""
    if norm_h == "Aryabhatta":
        if is_block_c(norm_b):
            return False, "Aryabhatta Block C is reserved for female students. Male students are in Blocks A, B, or D."
        return True, ""

    return False, f"Invalid hostel allocation '{hostel}' for male students. Allowed: Kalam (A-D), CV Raman, Aryabhatta (A, B, D)."


def get_caretaker_email_for_complaint(hostel: str, block: Optional[str] = "") -> str:
    norm_h = normalize_hostel(hostel)
    norm_b = normalize_block(block)

    if norm_h == "Kalam":
        return "kalam_caretaker@iitp.ac.in"
    if norm_h == "Asima":
        return "asima_caretaker@iitp.ac.in"
    if norm_h == "CV Raman":
        return "cvr_caretaker@iitp.ac.in"
    if norm_h == "Aryabhatta":
        if is_block_c(norm_b):
            return "aryabhatta_girls_caretaker@iitp.ac.in"
        return "aryabhatta_caretaker@iitp.ac.in"
    return "kalam_caretaker@iitp.ac.in"


def is_boys_complaint(hostel: str, block: Optional[str] = "") -> bool:
    norm_h = normalize_hostel(hostel)
    norm_b = normalize_block(block)
    if norm_h in ("Kalam", "CV Raman"):
        return True
    if norm_h == "Aryabhatta":
        return not is_block_c(norm_b)
    return False


def can_user_access_complaint(user, complaint_hostel: str, complaint_block: Optional[str] = "") -> bool:
    if not user:
        # Public board: boys hostels only
        return is_boys_complaint(complaint_hostel, complaint_block)
    role = getattr(user, "role", None)
    role_val = getattr(role, "value", str(role)).lower()
    if role_val == "admin":
        return True

    norm_ch = normalize_hostel(complaint_hostel)
    norm_cb = normalize_block(complaint_block)

    email = (getattr(user, "email", "") or "").lower()

    if role_val == "caretaker":
        if email in ("kalam_caretaker@iitp.ac.in", "kalam_warden@iitp.ac.in"):
            return norm_ch == "Kalam"
        if email in ("asima_caretaker@iitp.ac.in", "asima_warden@iitp.ac.in"):
            return norm_ch == "Asima"
        if email in ("cvr_caretaker@iitp.ac.in", "cvr_warden@iitp.ac.in"):
            return norm_ch == "CV Raman"
        if email in ("aryabhatta_girls_caretaker@iitp.ac.in", "aryabhatta_girls_warden@iitp.ac.in"):
            return norm_ch == "Aryabhatta" and is_block_c(norm_cb)
        if email in ("aryabhatta_caretaker@iitp.ac.in", "aryabhatta_warden@iitp.ac.in"):
            return norm_ch == "Aryabhatta" and not is_block_c(norm_cb)
        # Fallback to user's assigned hostel if custom caretaker
        user_h = normalize_hostel(getattr(user, "hostel", ""))
        return norm_ch == user_h if user_h else True

    if role_val == "student":
        user_h = normalize_hostel(getattr(user, "hostel", ""))
        user_b = normalize_block(getattr(user, "block", ""))
        user_g = (getattr(user, "gender", "") or "").lower()

        if not user_h:
            return True  # unassigned student

        if norm_ch != user_h:
            return False

        # In Aryabhatta, enforce gender/block boundary
        if norm_ch == "Aryabhatta":
            is_student_girls = (user_g in ("female", "girl", "girls", "f") or is_block_c(user_b))
            is_issue_girls = is_block_c(norm_cb)
            return is_student_girls == is_issue_girls

        return True

    return True


def sql_is_block_c(complaint_cls):
    return or_(
        complaint_cls.block.ilike("Block C"),
        complaint_cls.block.ilike("Block C%"),
        complaint_cls.block.ilike("Block-C%"),
        complaint_cls.block.ilike("% Block C%"),
        complaint_cls.block.ilike("% C"),
        complaint_cls.block == "C",
        complaint_cls.block == "c",
    )


def apply_hostel_filter_to_query(query, user, complaint_cls):
    """
    Apply SQLAlchemy filtering on Complaint model query according to user's scope.
    """
    if not user:
        # Public complaint board shows boys hostels only: Kalam, CV Raman, and Aryabhatta (Blocks A, B, D)
        return query.filter(
            or_(
                complaint_cls.hostel.ilike("Kalam"),
                complaint_cls.hostel.ilike("CV Raman"),
                complaint_cls.hostel.ilike("CVR"),
                complaint_cls.hostel.ilike("%Raman%"),
                and_(
                    complaint_cls.hostel.ilike("Aryabhatta"),
                    or_(
                        complaint_cls.block == None,
                        complaint_cls.block == "",
                        not_(sql_is_block_c(complaint_cls)),
                    ),
                ),
            )
        )

    role = getattr(user, "role", None)
    role_val = getattr(role, "value", str(role)).lower()
    if role_val == "admin":
        return query

    email = (getattr(user, "email", "") or "").lower()

    if role_val == "caretaker":
        if email in ("kalam_caretaker@iitp.ac.in", "kalam_warden@iitp.ac.in"):
            return query.filter(complaint_cls.hostel.ilike("Kalam"))
        if email in ("asima_caretaker@iitp.ac.in", "asima_warden@iitp.ac.in"):
            return query.filter(complaint_cls.hostel.ilike("Asima"))
        if email in ("cvr_caretaker@iitp.ac.in", "cvr_warden@iitp.ac.in"):
            return query.filter(
                or_(
                    complaint_cls.hostel.ilike("CV Raman"),
                    complaint_cls.hostel.ilike("CVR"),
                    complaint_cls.hostel.ilike("%Raman%"),
                )
            )
        if email in ("aryabhatta_girls_caretaker@iitp.ac.in", "aryabhatta_girls_warden@iitp.ac.in"):
            return query.filter(
                and_(
                    complaint_cls.hostel.ilike("Aryabhatta"),
                    sql_is_block_c(complaint_cls),
                )
            )
        if email in ("aryabhatta_caretaker@iitp.ac.in", "aryabhatta_warden@iitp.ac.in"):
            return query.filter(
                and_(
                    complaint_cls.hostel.ilike("Aryabhatta"),
                    or_(
                        complaint_cls.block == None,
                        complaint_cls.block == "",
                        not_(sql_is_block_c(complaint_cls)),
                    ),
                )
            )
        # Custom caretaker
        user_h = getattr(user, "hostel", None)
        if user_h:
            return query.filter(complaint_cls.hostel.ilike(user_h))
        return query

    if role_val == "student":
        user_h = normalize_hostel(getattr(user, "hostel", ""))
        user_b = normalize_block(getattr(user, "block", ""))
        user_g = (getattr(user, "gender", "") or "").lower()

        if not user_h:
            return query

        if user_h == "CV Raman":
            return query.filter(
                or_(
                    complaint_cls.hostel.ilike("CV Raman"),
                    complaint_cls.hostel.ilike("CVR"),
                    complaint_cls.hostel.ilike("%Raman%"),
                )
            )
        elif user_h == "Aryabhatta":
            is_student_girls = (user_g in ("female", "girl", "girls", "f") or is_block_c(user_b))
            if is_student_girls:
                return query.filter(
                    and_(
                        complaint_cls.hostel.ilike("Aryabhatta"),
                        sql_is_block_c(complaint_cls),
                    )
                )
            else:
                return query.filter(
                    and_(
                        complaint_cls.hostel.ilike("Aryabhatta"),
                        or_(
                            complaint_cls.block == None,
                            complaint_cls.block == "",
                            not_(sql_is_block_c(complaint_cls)),
                        ),
                    )
                )
        else:
            return query.filter(complaint_cls.hostel.ilike(user_h))

    return query
