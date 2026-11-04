"""
Tests for hostel scoping, gender-based hostel allocations, and primary caretaker scoping.
"""

import pytest
from src.db.models import Profile, Complaint, UserRole, Category, Priority, ComplaintStatus
from src.utils.auth import hash_password, register
from src.utils.hostel_rules import (
    validate_allocation,
    can_user_access_complaint,
    get_caretaker_email_for_complaint,
    PRIMARY_CARETAKERS,
)
from src.utils.complaints import create_complaint, list_complaints


def test_gender_hostel_allocation_validation():
    # Boys validations
    assert validate_allocation("Male", "Kalam", "Block A")[0] is True
    assert validate_allocation("Male", "Kalam", "Block D")[0] is True
    assert validate_allocation("Male", "CV Raman", "")[0] is True
    assert validate_allocation("Male", "CVR", "")[0] is True
    assert validate_allocation("Male", "Aryabhatta", "Block A")[0] is True
    assert validate_allocation("Male", "Aryabhatta", "Block B")[0] is True
    assert validate_allocation("Male", "Aryabhatta", "Block D")[0] is True

    # Boys cannot be in Aryabhatta Block C or Asima
    ok, err = validate_allocation("Male", "Aryabhatta", "Block C")
    assert ok is False
    assert "reserved for female students" in err

    ok, err = validate_allocation("Male", "Asima", "")
    assert ok is False

    # Girls validations
    assert validate_allocation("Female", "Asima", "")[0] is True
    assert validate_allocation("Female", "Aryabhatta", "Block C")[0] is True

    # Girls cannot be in Kalam, CVR, or Aryabhatta Blocks A, B, D
    assert validate_allocation("Female", "Kalam", "Block A")[0] is False
    assert validate_allocation("Female", "CV Raman", "")[0] is False
    assert validate_allocation("Female", "Aryabhatta", "Block A")[0] is False


def test_caretaker_routing():
    assert get_caretaker_email_for_complaint("Kalam", "Block A") == "kalam_caretaker@iitp.ac.in"
    assert get_caretaker_email_for_complaint("Kalam", "Block C") == "kalam_caretaker@iitp.ac.in"
    assert get_caretaker_email_for_complaint("Asima", "") == "asima_caretaker@iitp.ac.in"
    assert get_caretaker_email_for_complaint("CV Raman", "") == "cvr_caretaker@iitp.ac.in"
    assert get_caretaker_email_for_complaint("CVR", "") == "cvr_caretaker@iitp.ac.in"
    assert get_caretaker_email_for_complaint("Aryabhatta", "Block C") == "aryabhatta_girls_caretaker@iitp.ac.in"
    assert get_caretaker_email_for_complaint("Aryabhatta", "Block A") == "aryabhatta_caretaker@iitp.ac.in"
    assert get_caretaker_email_for_complaint("Aryabhatta", "Block D") == "aryabhatta_caretaker@iitp.ac.in"


def test_caretaker_scoping(db):
    admin = Profile(id="admin-1", email="admin@iitp.ac.in", display_name="Admin", password_hash="x", role=UserRole.admin)
    ct_kalam = Profile(id="ct-kalam", email="kalam_caretaker@iitp.ac.in", display_name="Kalam CT", password_hash="x", role=UserRole.caretaker, hostel="Kalam")
    ct_asima = Profile(id="ct-asima", email="asima_caretaker@iitp.ac.in", display_name="Asima CT", password_hash="x", role=UserRole.caretaker, hostel="Asima")
    ct_ary_girls = Profile(id="ct-ary-g", email="aryabhatta_girls_caretaker@iitp.ac.in", display_name="Ary Girls CT", password_hash="x", role=UserRole.caretaker, hostel="Aryabhatta")
    ct_ary_boys = Profile(id="ct-ary-b", email="aryabhatta_caretaker@iitp.ac.in", display_name="Ary Boys CT", password_hash="x", role=UserRole.caretaker, hostel="Aryabhatta")
    ct_cvr = Profile(id="ct-cvr", email="cvr_caretaker@iitp.ac.in", display_name="CVR CT", password_hash="x", role=UserRole.caretaker, hostel="CV Raman")

    for u in [admin, ct_kalam, ct_asima, ct_ary_girls, ct_ary_boys, ct_cvr]:
        db.add(u)
    db.commit()

    # Kalam caretaker
    assert can_user_access_complaint(ct_kalam, "Kalam", "Block A") is True
    assert can_user_access_complaint(ct_kalam, "Asima", "") is False
    assert can_user_access_complaint(ct_kalam, "Aryabhatta", "Block A") is False

    # Asima caretaker
    assert can_user_access_complaint(ct_asima, "Asima", "") is True
    assert can_user_access_complaint(ct_asima, "Kalam", "Block A") is False

    # Aryabhatta Girls caretaker (Block C only)
    assert can_user_access_complaint(ct_ary_girls, "Aryabhatta", "Block C") is True
    assert can_user_access_complaint(ct_ary_girls, "Aryabhatta", "Block A") is False
    assert can_user_access_complaint(ct_ary_girls, "Kalam", "Block A") is False

    # Aryabhatta Boys caretaker (Blocks A, B, D only)
    assert can_user_access_complaint(ct_ary_boys, "Aryabhatta", "Block A") is True
    assert can_user_access_complaint(ct_ary_boys, "Aryabhatta", "Block B") is True
    assert can_user_access_complaint(ct_ary_boys, "Aryabhatta", "Block D") is True
    assert can_user_access_complaint(ct_ary_boys, "Aryabhatta", "Block C") is False

    # CV Raman caretaker
    assert can_user_access_complaint(ct_cvr, "CV Raman", "") is True
    assert can_user_access_complaint(ct_cvr, "CVR", "") is True
    assert can_user_access_complaint(ct_cvr, "Kalam", "") is False

    # Admin accesses everything
    assert can_user_access_complaint(admin, "Kalam", "Block A") is True
    assert can_user_access_complaint(admin, "Asima", "") is True
    assert can_user_access_complaint(admin, "Aryabhatta", "Block C") is True
    assert can_user_access_complaint(admin, "Aryabhatta", "Block A") is True
    assert can_user_access_complaint(admin, "CV Raman", "") is True


def test_student_scoping_and_list_complaints(db):
    admin = Profile(id="admin-1", email="admin@iitp.ac.in", display_name="Admin", password_hash="x", role=UserRole.admin)
    student_kalam = Profile(id="stu-kalam", email="boy_kalam@iitp.ac.in", display_name="Kalam Boy", password_hash="x", role=UserRole.student, gender="Male", hostel="Kalam", block="Block B")
    student_asima = Profile(id="stu-asima", email="girl_asima@iitp.ac.in", display_name="Asima Girl", password_hash="x", role=UserRole.student, gender="Female", hostel="Asima", block="")
    student_ary_c = Profile(id="stu-ary-c", email="girl_ary@iitp.ac.in", display_name="Ary Girl", password_hash="x", role=UserRole.student, gender="Female", hostel="Aryabhatta", block="Block C")
    student_ary_a = Profile(id="stu-ary-a", email="boy_ary@iitp.ac.in", display_name="Ary Boy", password_hash="x", role=UserRole.student, gender="Male", hostel="Aryabhatta", block="Block A")

    for u in [admin, student_kalam, student_asima, student_ary_c, student_ary_a]:
        db.add(u)
    db.commit()

    # Create complaints in different hostels
    create_complaint(db, title="Kalam Issue", description="Desc", category="Plumbing", hostel="Kalam", block="Block B", floor="1", location_detail="", submitter_id=student_kalam.id)
    create_complaint(db, title="Asima Issue", description="Desc", category="Water Supply", hostel="Asima", block="", floor="2", location_detail="", submitter_id=student_asima.id)
    create_complaint(db, title="Aryabhatta C Issue", description="Desc", category="Electrical", hostel="Aryabhatta", block="Block C", floor="3", location_detail="", submitter_id=student_ary_c.id)
    create_complaint(db, title="Aryabhatta A Issue", description="Desc", category="Cleaning & Waste", hostel="Aryabhatta", block="Block A", floor="1", location_detail="", submitter_id=student_ary_a.id)

    # Student Kalam should only see Kalam complaints
    kalam_list, kalam_total = list_complaints(db, current_user=student_kalam)
    assert kalam_total == 1
    assert kalam_list[0].title == "Kalam Issue"

    # Student Asima should only see Asima complaints
    asima_list, asima_total = list_complaints(db, current_user=student_asima)
    assert asima_total == 1
    assert asima_list[0].title == "Asima Issue"

    # Student Aryabhatta C should only see Aryabhatta Block C complaints
    ary_c_list, ary_c_total = list_complaints(db, current_user=student_ary_c)
    assert ary_c_total == 1
    assert ary_c_list[0].title == "Aryabhatta C Issue"

    # Student Aryabhatta A should only see Aryabhatta Boys complaints (not Block C)
    ary_a_list, ary_a_total = list_complaints(db, current_user=student_ary_a)
    assert ary_a_total == 1
    assert ary_a_list[0].title == "Aryabhatta A Issue"

    # Admin sees all 4 complaints
    admin_list, admin_total = list_complaints(db, current_user=admin)
    assert admin_total == 4
