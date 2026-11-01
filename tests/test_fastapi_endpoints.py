"""
End-to-end integration tests for the FastAPI backend and endpoints.
"""

import sys
import os
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient
from backend.app import app

client = TestClient(app)

def test_full_migration_flow():
    print("Testing FastAPI endpoints...")

    # 1. SPA and Documentation serving
    res = client.get("/")
    assert res.status_code == 200
    assert "Hostel Grievance" in res.text
    print("[PASS] Root SPA index.html served successfully")

    res = client.get("/static/app.jsx")
    assert res.status_code == 200
    assert "ReactDOM.createRoot" in res.text
    print("[PASS] React application bundle served successfully")

    # 2. Demo accounts
    res = client.get("/api/auth/demo-accounts")
    assert res.status_code == 200
    accounts = res.json()
    assert len(accounts) >= 6
    print(f"[PASS] {len(accounts)} 1-click demo accounts available")

    # 3. Login as student
    res = client.post("/api/auth/login", json={"email": "student1@demo.teamr", "password": "demo1234"})
    assert res.status_code == 200
    student_data = res.json()
    student_token = student_data["token"]
    student_headers = {"Authorization": f"Bearer {student_token}"}
    print("[PASS] Student authenticated successfully")

    # 4. Login as caretaker
    res = client.post("/api/auth/login", json={"email": "caretaker@demo.teamr", "password": "demo1234"})
    assert res.status_code == 200
    caretaker_token = res.json()["token"]
    caretaker_headers = {"Authorization": f"Bearer {caretaker_token}"}
    print("[PASS] Caretaker authenticated successfully")

    # 5. Login as admin
    res = client.post("/api/auth/login", json={"email": "admin@demo.teamr", "password": "demo1234"})
    assert res.status_code == 200
    admin_token = res.json()["token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    print("[PASS] Admin authenticated successfully")

    # 6. List complaints
    res = client.get("/api/complaints?page=1&page_size=5")
    assert res.status_code == 200
    board_data = res.json()
    assert "complaints" in board_data
    assert "total" in board_data
    print(f"[PASS] Complaint board returned {len(board_data['complaints'])} items out of {board_data['total']} total")

    # 7. Create an anonymous complaint
    res = client.post(
        "/api/complaints",
        data={
            "title": "Migrated Test Complaint",
            "description": "Testing the new FastAPI + React stack with anonymous submission.",
            "category": "Plumbing",
            "hostel": "Aryabhatta",
            "block": "Block B",
            "floor": "3rd Floor",
            "location_detail": "Room 312 washroom",
            "is_anonymous": "true",
            "priority": "Medium",
            "is_public": "true",
        },
        headers=student_headers,
    )
    assert res.status_code == 200
    created = res.json()
    cid = created["complaint_id"]
    cnum = created["complaint_number"]
    print(f"[PASS] Created complaint {cnum} (ID: {cid})")

    # 8. Check complaint details
    res = client.get(f"/api/complaints/{cid}", headers=student_headers)
    assert res.status_code == 200
    detail = res.json()
    assert detail["title"] == "Migrated Test Complaint"
    assert detail["is_anonymous"] is True
    assert detail["submitter_name"] == "Anonymous"
    print("[PASS] Complaint details confirmed: anonymous submission respected")

    # 9. Support / Vote toggle
    res = client.post(f"/api/complaints/{cid}/vote", headers=student_headers)
    assert res.status_code == 200
    v_res = res.json()
    assert v_res["voted"] is True
    assert v_res["vote_count"] == 1
    print("[PASS] Vote added successfully")

    # 10. Caretaker marks complaint as seen
    res = client.post(f"/api/complaints/{cid}/seen", headers=caretaker_headers)
    assert res.status_code == 200
    print("[PASS] Caretaker marked complaint as seen")

    # 11. Caretaker acknowledges complaint
    res = client.post(
        f"/api/complaints/{cid}/acknowledge",
        json={"work_notes": "Plumber dispatched to Block B.", "estimated_completion": "2026-11-02T15:00:00"},
        headers=caretaker_headers,
    )
    assert res.status_code == 200
    print("[PASS] Caretaker acknowledged complaint")

    # 12. Add comment
    res = client.post(
        f"/api/complaints/{cid}/comments",
        json={"content": "Thank you for the quick inspection!", "is_official": False},
        headers=student_headers,
    )
    assert res.status_code == 200
    print("[PASS] Comment posted successfully")

    # 13. Caretaker dashboard
    res = client.get("/api/caretaker/dashboard", headers=caretaker_headers)
    assert res.status_code == 200
    ct_dash = res.json()
    assert "metrics" in ct_dash
    print(f"[PASS] Caretaker dashboard metrics: {ct_dash['metrics']}")

    # 14. Admin overview
    res = client.get("/api/admin/overview", headers=admin_headers)
    assert res.status_code == 200
    adm_ov = res.json()
    assert "total_complaints" in adm_ov
    print(f"[PASS] Admin overview: {adm_ov}")

    # 15. Analytics & CSV Export
    res = client.get("/api/analytics", headers=admin_headers)
    assert res.status_code == 200
    analytics_data = res.json()
    assert "by_category" in analytics_data
    print("[PASS] Analytics metrics retrieved successfully")

    res = client.get("/api/analytics/export", headers=admin_headers)
    assert res.status_code == 200
    assert "complaint_number" in res.text
    print("[PASS] CSV Export generated successfully")

    # 16. Delete complaint (clean up)
    # Since it was acknowledged, student cannot delete it, but admin can!
    res = client.delete(f"/api/complaints/{cid}", headers=admin_headers)
    assert res.status_code == 200
    print("[PASS] Admin deleted test complaint successfully")

    print("\nALL 16 FASTAPI + REACT INTEGRATION TESTS PASSED!")

if __name__ == "__main__":
    test_full_migration_flow()
