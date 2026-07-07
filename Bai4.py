from fastapi import FastAPI, HTTPException, status, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

app = FastAPI(title="Logistics Shipment Tracking API")


shipments_db = [
    {"id": 1001, "code": "VN-DHL-8821", "status": "in_transit", "created_at": "2026-07-08T10:00:00Z"},
    {"id": 1002, "code": "VN-VTP-3941", "status": "delivered", "created_at": "2026-07-08T11:15:00Z"},
    {"id": 1003, "code": "VN-EMS-0023", "status": "pending", "created_at": "2026-07-08T12:30:00Z"}
]

# =================================================================
# LÁ CHẮN BẢO MẬT: GLOBAL EXCEPTION HANDLER (OWASP A05)
# =================================================================
# Ngăn chặn hoàn toàn việc lộ Stack Trace thô chứa tên file, số dòng ra ngoài
@app.exception_handler(Exception)
def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "statusCode": 500,
            "message": "Hệ thống gặp sự cố nội bộ, vui lòng thử lại sau!",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "path": request.url.path
        }
    )

# Handler bẫy lỗi nghiệp vụ 404 sạch sẽ cho Client
@app.exception_handler(HTTPException)
def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "statusCode": exc.status_code,
            "message": exc.detail,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "path": request.url.path
        }
    )


# =================================================================
# API CHỨC NĂNG: GET /shipments/{shipment_id}
# =================================================================
@app.get("/shipments/{shipment_id}")
def get_shipment_by_id(shipment_id: int):
    
    # -------------------------------------------------------------
    # GIẢI PHÁP 2 (MÔ PHỎNG .filter().first() TRÊN DATABASE):
    # Chặn sớm, chỉ lấy đúng 1 bản ghi duy nhất, không nạp toàn bộ mảng vào RAM.
    # -------------------------------------------------------------
    target_shipment = None
    
    # Duyệt mảng tìm kiếm tuyến tính ngắt sớm (Mô phỏng Index Lookup + LIMIT 1)
    for shipment in shipments_db:
        if shipment["id"] == shipment_id:
            target_shipment = shipment
            break # Thỏa mãn LIMIT 1: Dừng ngay lập tức khi tìm thấy bản ghi đầu tiên
            
    # Quy tắc nghiệp vụ: Nếu không tìm thấy, trả về mã trạng thái lỗi RESTful chuẩn 404
    if target_shipment is None and target_shipment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy thông tin vận đơn với ID {shipment_id}"
        )
        
    # Quy tắc nghiệp vụ: Nếu tìm thấy dữ liệu, trả về mã chuẩn 200 OK kèm thông tin trạng thái
    return {
        "status_code": 200,
        "message": "Tra cứu thông tin vận đơn thành công",
        "data": target_shipment
    }