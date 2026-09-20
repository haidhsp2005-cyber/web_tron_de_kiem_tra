import sys
sys.stdout.reconfigure(encoding='utf-8')
from starlette.testclient import TestClient
from app import app

client = TestClient(app)

print("1. Testing /api/health...")
res = client.get("/api/health")
assert res.status_code == 200, f"Health failed: {res.text}"
print("   Health:", res.json())

print("2. Testing /api/download-sample-docx...")
res = client.get("/api/download-sample-docx")
assert res.status_code == 200, f"Sample docx failed: {res.status_code}"
assert len(res.content) > 1000
print(f"   Sample docx downloaded, size: {len(res.content)} bytes")

print("3. Testing /api/download-sample-pdf...")
res = client.get("/api/download-sample-pdf")
assert res.status_code == 200, f"Sample pdf failed: {res.status_code}"
assert len(res.content) > 1000
print(f"   Sample pdf downloaded, size: {len(res.content)} bytes")

print("4. Testing /api/load-sample...")
res = client.get("/api/load-sample")
assert res.status_code == 200, f"Load sample failed: {res.text}"
sample_data = res.json()
session_id = sample_data["session_id"]
exam_data = sample_data["exam_data"]
print(f"   Sample loaded, session_id: {session_id}")
print(f"   Total questions: {exam_data['stats']['total_questions']}")
print(f"   Part 1: {len(exam_data['part1'])} questions")
print(f"   Part 2: {len(exam_data['part2'])} questions")
print(f"   Part 3: {len(exam_data['part3'])} questions")
print(f"   Part 4: {len(exam_data['part4'])} questions")

print("5. Testing /api/save-exam...")
# Modify an answer in part 1
exam_data["part1"][0]["question"] += " (Đã chỉnh sửa bởi giáo viên)"
res = client.post("/api/save-exam", json={
    "session_id": session_id,
    "exam_data": exam_data
})
assert res.status_code == 200
print("   Save exam status:", res.json())

print("6. Testing /api/shuffle...")
res = client.post("/api/shuffle", json={
    "session_id": session_id,
    "exam_data": exam_data,
    "config": {
        "num_variants": 4,
        "start_code": 101,
        "shuffle_p1_questions": True,
        "shuffle_p1_choices": True,
        "shuffle_p2_questions": True,
        "shuffle_p2_items": True,
        "shuffle_p3_questions": True,
        "shuffle_p4_questions": False
    }
})
assert res.status_code == 200, f"Shuffle failed: {res.text}"
shuffle_res = res.json()
print("   Variants generated:", shuffle_res["variants_count"])
print("   Summary codes:", shuffle_res["summary"]["codes"])
print("   Downloads:", shuffle_res["downloads"])

print("7. Testing downloading generated zip...")
zip_url = shuffle_res["downloads"]["zip"]
res = client.get(zip_url)
assert res.status_code == 200, f"Download zip failed: {res.status_code}"
assert len(res.content) > 5000
print(f"   ZIP downloaded successfully, size: {len(res.content)} bytes")

print("8. Testing downloading generated excel matrix...")
excel_url = shuffle_res["downloads"]["excel"]
res = client.get(excel_url)
assert res.status_code == 200, f"Download excel failed: {res.status_code}"
assert len(res.content) > 2000
print(f"   Excel downloaded successfully, size: {len(res.content)} bytes")

print("9. Testing uploading Word file...")
with open("samples/de_thi_mau_chuan.docx", "rb") as f:
    res = client.post("/api/upload", files={"file": ("test_upload.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")})
assert res.status_code == 200, f"Upload docx failed: {res.text}"
upload_data = res.json()
print("   Upload docx success, session:", upload_data["session_id"])

print("10. Testing uploading PDF file...")
with open("samples/de_thi_mau_chuan.pdf", "rb") as f:
    res = client.post("/api/upload", files={"file": ("test_upload.pdf", f, "application/pdf")})
assert res.status_code == 200, f"Upload pdf failed: {res.text}"
upload_pdf_data = res.json()
print("   Upload pdf success, session:", upload_pdf_data["session_id"])

print("ALL 10 API TEST SUITES PASSED FLAWLESSLY!")
