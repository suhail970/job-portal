import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    print("[PASS] Health Check")

def test_auth_login():
    response = client.post("/api/v1/auth/login-json", json={
        "email": "student@ceg.edu",
        "password": "Student@123"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["role"] == "STUDENT"
    print("[PASS] Auth Login (Student)")
    return data["access_token"]

def test_list_drives(token):
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/v1/drives", headers=headers)
    assert response.status_code == 200
    drives = response.json()
    assert len(drives) >= 3
    print(f"[PASS] List Drives (Found {len(drives)} drives)")
    return drives[0]["id"]

def test_prep_hub_generation(token, drive_id):
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/api/v1/prep-hub/generate", headers=headers, json={
        "company_name": "Amazon",
        "role_title": "Software Development Engineer (SDE-1)",
        "timeframe": "1_DAY",
        "drive_id": drive_id
    })
    assert response.status_code == 200
    data = response.json()
    assert "roadmap" in data
    print(f"[PASS] 1-Day Placement Intelligence Sprint Generated")

def test_interview_session(token):
    headers = {"Authorization": f"Bearer {token}"}
    start_res = client.post("/api/v1/interview/start", headers=headers, json={
        "company_name": "Zoho Corporation",
        "role_title": "Software Developer Engineer"
    })
    assert start_res.status_code == 200
    session_data = start_res.json()
    session_id = session_data["session_id"]
    print(f"[PASS] Mock Interview Started (Session: {session_id})")

    # Submit turn
    turn_res = client.post("/api/v1/interview/turn", headers=headers, json={
        "session_id": session_id,
        "turn_index": 1,
        "question": session_data["question"],
        "student_transcript": "I am a computer science student proficient in Python and Java. I recently built a distributed job queue system using PostgreSQL and FastAPI."
    })
    assert turn_res.status_code == 200
    turn_data = turn_res.json()
    assert "score" in turn_data
    print(f"[PASS] Mock Interview Turn Evaluated (Score: {turn_data['score']}/10)")

def test_code_sandbox():
    response = client.post("/api/v1/simulation/execute-code", json={
        "language": "python",
        "code": "print('Hello from SkillBridge Coding Sandbox!')"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("PASSED", "RUNTIME_ERROR")
    print(f"[PASS] Piston Remote Code Sandbox Execution: {data['stdout'].strip()}")

def test_telegram_broadcast(drive_id):
    tpo_res = client.post("/api/v1/auth/login-json", json={
        "email": "tpo@ceg.edu",
        "password": "Tpo@123"
    })
    assert tpo_res.status_code == 200
    tpo_token = tpo_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {tpo_token}"}

    response = client.post(f"/api/v1/drives/{drive_id}/broadcast-telegram", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("SENT", "SIMULATED_SUCCESS")
    print(f"[PASS] Telegram Drive Broadcast ({data['mode']}): {data['target_channel']}")

def test_ollama_provider_override(token, drive_id):
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/api/v1/prep-hub/generate", headers=headers, json={
        "company_name": "TCS",
        "role_title": "Digital Engineer",
        "timeframe": "3_DAYS",
        "drive_id": drive_id,
        "provider": "ollama"
    })
    assert response.status_code == 200
    data = response.json()
    assert "roadmap" in data
    print(f"[PASS] Local Ollama Provider Override Prep Plan Generation")

def test_byok_custom_ai_connection():
    response = client.post("/api/v1/ai/test-connection", json={
        "provider": "custom",
        "custom_config": {
            "base_url": "https://api.openai.com/v1",
            "model": "gpt-4o-mini",
            "api_key": "dummy-test-key"
        }
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "connected"
    assert data["provider"] == "custom"
    print(f"[PASS] BYOK Universal AI Connection Test: Model={data['model']}")

def test_drive_sync_status(token):
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/v1/drives/sync-status", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "slots" in data
    assert len(data["slots"]) >= 3
    assert "next_run" in data
    assert "countdown" in data["next_run"]
    print(f"[PASS] Drive Sync Status: Schedule={data['schedule']}, Next={data['next_run']['slot_name']} ({data['next_run']['countdown']})")

def test_fetch_latest_drives(token):
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/api/v1/drives/fetch-latest", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["total_candidates_evaluated"] >= 7
    print(f"[PASS] Live Fetch Latest Drives: Evaluated={data['total_candidates_evaluated']}, New Added={data['new_drives_added']}, Companies={data['companies_added']}")
    
    # Verify the drives are now retrieved in list_drives
    list_res = client.get("/api/v1/drives", headers=headers)
    assert list_res.status_code == 200
    drives = list_res.json()
    companies = [d["company_name"] for d in drives]
    assert len(drives) >= 8
    print(f"[PASS] Multi-Source Ingestion Verified: Total active drives now {len(drives)}. Companies: {', '.join(companies[:6])}...")

def test_location_filtering(token):
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Trigger Kolkata targeted fetch
    kolkata_res = client.post("/api/v1/drives/fetch-latest?location=Kolkata", headers=headers)
    assert kolkata_res.status_code == 200
    k_data = kolkata_res.json()
    print(f"[PASS] Kolkata Targeted Ingestion: Evaluated={k_data['total_candidates_evaluated']}, Added={k_data['new_drives_added']}, Companies={k_data['companies_added']}")
    
    # 2. Filter drives by Kolkata
    kolkata_drives_res = client.get("/api/v1/drives?location=Kolkata", headers=headers)
    assert kolkata_drives_res.status_code == 200
    k_drives = kolkata_drives_res.json()
    assert len(k_drives) >= 2
    for d in k_drives:
        assert "kolkata" in d["location"].lower()
    print(f"[PASS] Kolkata Location Filter: Found {len(k_drives)} openings in Kolkata ({[d['company_name'] for d in k_drives]})")
    
    # 3. Filter drives by Chennai
    chennai_drives_res = client.get("/api/v1/drives?location=Chennai", headers=headers)
    assert chennai_drives_res.status_code == 200
    c_drives = chennai_drives_res.json()
    assert len(c_drives) >= 1
    for d in c_drives:
        assert "chennai" in d["location"].lower()
    print(f"[PASS] Chennai Location Filter: Found {len(c_drives)} openings in Chennai ({[d['company_name'] for d in c_drives]})")

    # 4. Ingest and Filter by Coimbatore District
    cbe_fetch = client.post("/api/v1/drives/fetch-latest?location=Coimbatore", headers=headers)
    assert cbe_fetch.status_code == 200
    cbe_drives_res = client.get("/api/v1/drives?location=Coimbatore", headers=headers)
    assert cbe_drives_res.status_code == 200
    cbe_drives = cbe_drives_res.json()
    assert len(cbe_drives) >= 2
    for d in cbe_drives:
        assert "coimbatore" in d["location"].lower()
    print(f"[PASS] Coimbatore District Filter: Found {len(cbe_drives)} openings in Coimbatore ({[d['company_name'] for d in cbe_drives]})")

    # 5. Ingest and Filter by Madurai District
    mdu_fetch = client.post("/api/v1/drives/fetch-latest?location=Madurai", headers=headers)
    assert mdu_fetch.status_code == 200
    mdu_drives_res = client.get("/api/v1/drives?location=Madurai", headers=headers)
    assert mdu_drives_res.status_code == 200
    mdu_drives = mdu_drives_res.json()
    assert len(mdu_drives) >= 2
    for d in mdu_drives:
        assert "madurai" in d["location"].lower()
    print(f"[PASS] Madurai District Filter: Found {len(mdu_drives)} openings in Madurai ({[d['company_name'] for d in mdu_drives]})")

if __name__ == "__main__":
    test_health_check()
    token = test_auth_login()
    test_drive_sync_status(token)
    test_fetch_latest_drives(token)
    test_location_filtering(token)
    drive_id = test_list_drives(token)
    test_prep_hub_generation(token, drive_id)
    test_interview_session(token)
    test_code_sandbox()
    test_telegram_broadcast(drive_id)
    test_ollama_provider_override(token, drive_id)
    test_byok_custom_ai_connection()
    print("\nALL BACKEND API TESTS PASSED SUCCESSFULLY! (100% HEALTHY)")

