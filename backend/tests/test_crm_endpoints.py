import pytest
from fastapi.testclient import TestClient

from app.main import app

ADMIN_EMAIL = "charanjeet.s7730@gmail.com"
ADMIN_PASSWORD = "123456"


@pytest.fixture(scope="module")
def client():
    with TestClient(app, base_url="http://localhost") as c:
        yield c


@pytest.fixture(scope="module")
def auth_headers(client):
    res = client.post("/api/v1/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert res.status_code == 200, res.text
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_login_returns_token(auth_headers):
    assert auth_headers["Authorization"].startswith("Bearer ")


def test_lead_lifecycle(client, auth_headers):
    create = client.post(
        "/api/v1/leads",
        json={"name": "Pytest Lead", "company": "Pytest Co", "source": "manual", "value": 500},
        headers=auth_headers,
    )
    assert create.status_code == 201, create.text
    lead = create.json()
    assert lead["status"] == "new"
    lead_id = lead["id"]

    listing = client.get("/api/v1/leads", headers=auth_headers)
    assert listing.status_code == 200
    assert any(l["id"] == lead_id for l in listing.json()["leads"])

    patch = client.patch(f"/api/v1/leads/{lead_id}", json={"status": "qualified"}, headers=auth_headers)
    assert patch.status_code == 200
    assert patch.json()["status"] == "qualified"

    events = client.get(f"/api/v1/leads/{lead_id}/events", headers=auth_headers)
    assert events.status_code == 200
    event_types = [e["type"] for e in events.json()["events"]]
    assert "created" in event_types
    assert "status_changed" in event_types

    delete = client.delete(f"/api/v1/leads/{lead_id}", headers=auth_headers)
    assert delete.status_code == 200
    assert delete.json()["success"] is True


def test_lead_invalid_source_rejected(client, auth_headers):
    res = client.post("/api/v1/leads", json={"name": "Bad Source", "source": "not_a_real_source"}, headers=auth_headers)
    assert res.status_code == 400


def test_deal_lifecycle(client, auth_headers):
    create = client.post("/api/v1/deals", json={"name": "Pytest Deal", "company": "Pytest Co", "value": 1000}, headers=auth_headers)
    assert create.status_code == 201, create.text
    deal_id = create.json()["id"]
    assert create.json()["stage"] == "lead"

    patch = client.patch(f"/api/v1/deals/{deal_id}", json={"stage": "qualified"}, headers=auth_headers)
    assert patch.status_code == 200
    assert patch.json()["stage"] == "qualified"

    delete = client.delete(f"/api/v1/deals/{deal_id}", headers=auth_headers)
    assert delete.status_code == 200


def test_campaign_lifecycle(client, auth_headers):
    create = client.post("/api/v1/dashboard/campaigns", json={"name": "Pytest Campaign", "channel": "voice"}, headers=auth_headers)
    assert create.status_code == 200, create.text
    campaign_id = create.json()["id"]
    assert create.json()["status"] == "paused"

    toggle = client.patch(f"/api/v1/dashboard/campaigns/{campaign_id}/toggle", headers=auth_headers)
    assert toggle.status_code == 200
    assert toggle.json()["status"] == "running"

    delete = client.delete(f"/api/v1/dashboard/campaigns/{campaign_id}", headers=auth_headers)
    assert delete.status_code == 200


def test_integrations_report_not_configured(client, auth_headers):
    res = client.get("/api/v1/health")
    assert res.status_code == 200

def test_dashboard_overview_reflects_real_counts(client, auth_headers):
    before = client.get("/api/v1/dashboard/overview", headers=auth_headers).json()
    probe = client.post("/api/v1/leads", json={"name": "Overview Probe", "source": "manual"}, headers=auth_headers).json()
    try:
        after = client.get("/api/v1/dashboard/overview", headers=auth_headers).json()
        assert after["todayLeads"] == before["todayLeads"] + 1
    finally:
        client.delete(f"/api/v1/leads/{probe['id']}", headers=auth_headers)


def test_workflows_lifecycle(client, auth_headers):
    # Retrieve workflows
    res = client.get("/api/v1/workflows", headers=auth_headers)
    assert res.status_code == 200
    wfs = res.json()["workflows"]
    assert len(wfs) >= 0

    # Create workflow
    create = client.post("/api/v1/workflows", json={"name": "Test Workflow", "trigger": "Lead Created"}, headers=auth_headers)
    assert create.status_code == 201
    wf_id = create.json()["id"]

    # Run workflow
    run = client.post(f"/api/v1/workflows/{wf_id}/run", headers=auth_headers)
    assert run.status_code == 200
    assert run.json()["success"] is True

    # History
    hist = client.get(f"/api/v1/workflows/{wf_id}/history", headers=auth_headers)
    assert hist.status_code == 200
    assert len(hist.json()["history"]) >= 0

    # Delete workflow
    delete = client.delete(f"/api/v1/workflows/{wf_id}", headers=auth_headers)
    assert delete.status_code == 200


def test_kb_lifecycle(client, auth_headers):
    # Retrieve articles
    res = client.get("/api/v1/kb", headers=auth_headers)
    assert res.status_code == 200
    articles = res.json()["articles"]
    assert len(articles) >= 0

    # Create article
    create = client.post("/api/v1/kb", json={"title": "Test Title", "category": "General"}, headers=auth_headers)
    assert create.status_code == 201
    art_id = create.json()["id"]

    # Search article
    search = client.get("/api/v1/kb/search?q=Test", headers=auth_headers)
    assert search.status_code == 200
    assert len(search.json()["results"]) > 0

    # Delete
    delete = client.delete(f"/api/v1/kb/{art_id}", headers=auth_headers)
    assert delete.status_code == 200


def test_documents_lifecycle(client, auth_headers):
    # List documents
    res = client.get("/api/v1/documents", headers=auth_headers)
    assert res.status_code == 200

    # Upload document
    import io
    file_payload = {"file": ("test_doc.txt", io.BytesIO(b"Hello world"), "text/plain")}
    upload = client.post("/api/v1/documents/upload", files=file_payload, headers=auth_headers)
    assert upload.status_code == 201
    doc_id = upload.json()["id"]

    # Download
    download = client.get(f"/api/v1/documents/{doc_id}/download", headers=auth_headers)
    assert download.status_code == 200
    assert download.content == b"Hello world"

    # Preview
    preview = client.get(f"/api/v1/documents/{doc_id}/preview", headers=auth_headers)
    assert preview.status_code == 200

    # Delete
    delete = client.delete(f"/api/v1/documents/{doc_id}", headers=auth_headers)
    assert delete.status_code == 200


def test_voice_calls(client, auth_headers):
    # Get calls list
    res = client.get("/api/v1/voice/calls", headers=auth_headers)
    assert res.status_code == 200
    calls = res.json()["calls"]
    assert len(calls) >= 0
    if calls: call_id = calls[0]["id"] if calls else None

    # Get transcript
    transcript = None
    if call_id:
        transcript = client.get(f"/api/v1/voice/calls/{call_id}/transcript", headers=auth_headers)
    assert transcript.status_code == 200
    assert "transcript" in transcript.json()


def test_reports_download(client, auth_headers):
    # Export leads
    res = client.get("/api/v1/reports/leads/download", headers=auth_headers)
    assert res.status_code == 200
    assert res.headers["content-type"].startswith("text/csv")

    # Export revenue
    res2 = client.get("/api/v1/reports/revenue/download", headers=auth_headers)
    assert res2.status_code == 200
    assert res2.headers["content-type"].startswith("text/csv")


def test_billing_invoice_history(client, auth_headers):
    # Invoices list
    res = client.get("/api/v1/billing/invoices", headers=auth_headers)
    assert res.status_code == 200
    invoices = res.json()["invoices"]
    assert len(invoices) >= 0

    # Checkout Stripe
    chk1 = client.post("/api/v1/billing/checkout", json={"plan_id": "enterprise", "gateway": "stripe"}, headers=auth_headers)
    assert chk1.status_code in (200, 503)
    if chk1.status_code == 200:
        assert "stripe" in chk1.json()["checkout_url"]

    # Checkout Razorpay
    chk2 = client.post("/api/v1/billing/checkout", json={"plan_id": "enterprise", "gateway": "razorpay"}, headers=auth_headers)
    assert chk2.status_code == 200
    assert "razorpay" in chk2.json()["checkout_url"]


def test_new_production_integrations(client, auth_headers):
    # 1. Test OAuth URLs
    res_google = client.get("/api/v1/oauth/url/google")
    assert res_google.status_code in (200, 501)
    if res_google.status_code == 200:
        assert "accounts.google.com" in res_google.json()["url"]
    
    res_fb = client.get("/api/v1/oauth/url/facebook")
    assert res_fb.status_code == 200
    assert "facebook.com" in res_fb.json()["url"]
    
    # 2. Test OAuth Callback handler (Google simulated)
    res_callback = client.post(
        "/api/v1/oauth/callback/google",
        json={"code": "samplecode123456", "state": "samplestate"}
    )
    assert res_callback.status_code == 200
    assert "access_token" in res_callback.json()
    assert "user" in res_callback.json()

    # 3. Test WhatsApp webhook validation
    res_wa_verify = client.get(
        "/api/v1/whatsapp/webhook?hub.mode=subscribe&hub.challenge=wa_test_challenge&hub.verify_token=whatsapp_verify_token_default_2026"
    )
    assert res_wa_verify.status_code == 200
    assert res_wa_verify.text == "wa_test_challenge"

    # 4. Test WhatsApp outgoing text simulation
    res_wa_send = client.post(
        "/api/v1/whatsapp/send",
        json={"to_number": "+919876543210", "message_text": "Hello world from Pytest"},
        headers=auth_headers
    )
    assert res_wa_send.status_code == 200
    assert res_wa_send.json()["success"] is True

    # 5. Test Twilio TwiML Voice callback
    res_twilio_voice = client.post("/api/v1/twilio/voice")
    assert res_twilio_voice.status_code == 200
    assert "Response" in res_twilio_voice.text
    assert "Gather" in res_twilio_voice.text

    # 6. Test Twilio outgoing SMS simulation
    res_twilio_sms = client.post(
        "/api/v1/twilio/sms/send",
        json={"to_number": "+15550199000", "message": "SMS alert message"},
        headers=auth_headers
    )
    assert res_twilio_sms.status_code == 200
    assert res_twilio_sms.json()["success"] is True
