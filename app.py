import os
import shutil
import uuid
from typing import Optional
from fastapi import FastAPI, File, UploadFile, HTTPException, Body
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from parser.docx_parser import DocxParser
from parser.pdf_parser import PdfParser
from shuffler.exam_shuffler import ExamShuffler
from exporter.docx_exporter import DocxExporter
from exporter.excel_exporter import ExcelExporter
from exporter.zip_exporter import ZipExporter
from sample_generator import create_sample_docx, create_sample_pdf_from_docx

app = FastAPI(title="Website Trộn Đề Thi Chuẩn Bộ GD&ĐT", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
EXPORT_DIR = os.path.join(BASE_DIR, "exports")
SAMPLE_DIR = os.path.join(BASE_DIR, "samples")
STATIC_DIR = os.path.join(BASE_DIR, "static")

for d in [UPLOAD_DIR, EXPORT_DIR, SAMPLE_DIR, STATIC_DIR]:
    os.makedirs(d, exist_ok=True)

# Ensure sample files exist
SAMPLE_DOCX = os.path.join(SAMPLE_DIR, "de_thi_mau_chuan.docx")
SAMPLE_PDF = os.path.join(SAMPLE_DIR, "de_thi_mau_chuan.pdf")
if not os.path.exists(SAMPLE_DOCX):
    create_sample_docx(SAMPLE_DOCX)
if not os.path.exists(SAMPLE_PDF):
    create_sample_pdf_from_docx(SAMPLE_DOCX, SAMPLE_PDF)

# In-memory store for sessions
sessions = {}

@app.get("/api/health")
def health():
    return {"status": "ok", "message": "Server đang hoạt động bình thường"}

@app.get("/api/download-sample-docx")
def download_sample_docx():
    if not os.path.exists(SAMPLE_DOCX):
        create_sample_docx(SAMPLE_DOCX)
    return FileResponse(
        SAMPLE_DOCX,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename="de_thi_mau_chuan_toan_ly_hoa.docx"
    )

@app.get("/api/download-sample-pdf")
def download_sample_pdf():
    if not os.path.exists(SAMPLE_PDF):
        create_sample_pdf_from_docx(SAMPLE_DOCX, SAMPLE_PDF)
    return FileResponse(
        SAMPLE_PDF,
        media_type="application/pdf",
        filename="de_thi_mau_chuan_toan_ly_hoa.pdf"
    )

@app.get("/api/load-sample")
def load_sample():
    """Loads sample exam directly into session for instant testing without uploading."""
    if not os.path.exists(SAMPLE_DOCX):
        create_sample_docx(SAMPLE_DOCX)
    
    session_id = str(uuid.uuid4())
    parser = DocxParser(SAMPLE_DOCX)
    data = parser.parse()
    
    sessions[session_id] = {
        "exam_data": data,
        "filename": "de_thi_mau_chuan.docx"
    }
    return {
        "session_id": session_id,
        "filename": "de_thi_mau_chuan.docx",
        "exam_data": data
    }

@app.post("/api/upload")
async def upload_exam(file: UploadFile = File(...)):
    filename = file.filename or "exam"
    ext = os.path.splitext(filename)[1].lower()
    
    if ext not in [".docx", ".pdf"]:
        raise HTTPException(status_code=400, detail="Chỉ hỗ trợ file Word (.docx) hoặc PDF (.pdf)")
    
    session_id = str(uuid.uuid4())
    saved_filename = f"{session_id}_{filename}"
    saved_path = os.path.join(UPLOAD_DIR, saved_filename)
    
    with open(saved_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        if ext == ".docx":
            parser = DocxParser(saved_path)
            data = parser.parse()
        else:
            parser = PdfParser(saved_path)
            data = parser.parse()
            
        sessions[session_id] = {
            "exam_data": data,
            "filename": filename,
            "file_path": saved_path
        }
        
        return {
            "session_id": session_id,
            "filename": filename,
            "exam_data": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi đọc file: {str(e)}")

@app.post("/api/save-exam")
async def save_exam(payload: dict = Body(...)):
    """Saves user modifications to the exam questions and answers."""
    session_id = payload.get("session_id")
    exam_data = payload.get("exam_data")
    
    if not session_id or session_id not in sessions:
        # If new session, initialize it
        if not session_id:
            session_id = str(uuid.uuid4())
        sessions[session_id] = {}
        
    sessions[session_id]["exam_data"] = exam_data
    return {"status": "success", "session_id": session_id, "message": "Đã lưu thay đổi đề thi thành công!"}

@app.post("/api/shuffle")
async def shuffle_exam(payload: dict = Body(...)):
    """
    Shuffles exam according to config and generates export files.
    """
    session_id = payload.get("session_id")
    config = payload.get("config", {})
    custom_exam_data = payload.get("exam_data")
    
    if custom_exam_data:
        exam_data = custom_exam_data
    elif session_id in sessions and "exam_data" in sessions[session_id]:
        exam_data = sessions[session_id]["exam_data"]
    else:
        raise HTTPException(status_code=400, detail="Không tìm thấy dữ liệu đề thi. Vui lòng tải đề lên trước.")

    try:
        shuffler = ExamShuffler(exam_data, config)
        shuffled_result = shuffler.shuffle()
        
        # Unique export directory for this shuffle run
        run_id = str(uuid.uuid4())
        run_dir = os.path.join(EXPORT_DIR, run_id)
        os.makedirs(run_dir, exist_ok=True)
        
        # 1. Export DOCX files
        docx_exp = DocxExporter(shuffled_result, output_dir=run_dir)
        docx_files = docx_exp.export_all()
        
        # 2. Export Excel matrix
        excel_path = os.path.join(run_dir, "Bang_dap_an_tong_hop.xlsx")
        excel_exp = ExcelExporter(shuffled_result, output_path=excel_path)
        excel_file = excel_exp.export()
        
        # 3. Zip package
        all_files = docx_files["test_files"] + docx_files["key_files"] + [docx_files["summary_file"], excel_file]
        zip_path = os.path.join(run_dir, "Bo_de_thi_tron.zip")
        zip_exp = ZipExporter(all_files, output_zip_path=zip_path)
        zip_file = zip_exp.create_zip()
        
        # Build download links
        download_links = {
            "zip": f"/api/download/{run_id}/Bo_de_thi_tron.zip",
            "excel": f"/api/download/{run_id}/Bang_dap_an_tong_hop.xlsx",
            "summary_docx": f"/api/download/{run_id}/Bang_dap_an_tong_hop.docx",
            "tests": [
                {
                    "code": v["code"],
                    "filename": f"De_thi_{v['code']}.docx",
                    "url": f"/api/download/{run_id}/De_thi_{v['code']}.docx"
                }
                for v in shuffled_result["variants"]
            ],
            "keys": [
                {
                    "code": v["code"],
                    "filename": f"Dap_an_chi_tiet_{v['code']}.docx",
                    "url": f"/api/download/{run_id}/Dap_an_chi_tiet_{v['code']}.docx"
                }
                for v in shuffled_result["variants"]
            ]
        }
        
        return {
            "run_id": run_id,
            "summary": shuffled_result["summary"],
            "variants_count": len(shuffled_result["variants"]),
            "downloads": download_links
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Lỗi trong quá trình trộn đề: {str(e)}")

@app.get("/api/download/{run_id}/{filename}")
def download_file(run_id: str, filename: str):
    file_path = os.path.join(EXPORT_DIR, run_id, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File không tồn tại hoặc đã hết hạn")
        
    return FileResponse(file_path, filename=filename)

# Mount static files
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    is_dev = "PORT" not in os.environ
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=is_dev)
