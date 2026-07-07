from fastapi import FastAPI, HTTPException, status, Request, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# Giả lập các thành phần SQLAlchemy để code chạy được trên FastAPI độc lập
# Trong dự án thực tế, bạn sẽ import chúng từ sqlalchemy.orm
class FakeSession:
    def add(self, instance): pass
    def commit(self): pass
    def refresh(self, instance): pass
    def close(self): pass

# Giả lập hàm get_db cung cấp session cho mỗi Request
def get_db():
    db = FakeSession()
    try:
        yield db
    finally:
        # Thiết lập giải phóng session trong khối lệnh finally an toàn
        db.close()

app = FastAPI(title="CRM Membership Management API")

# Dữ liệu Mock mô phỏng 2 bảng lưu trong MySQL
customers_db = [
    {"id": 1, "name": "Nguyen Van A"},
    {"id": 2, "name": "Tran Thi B"}
]

memberships_db = [
    {"id": 1, "card_number": "VIP-8888", "customer_id": 1}
]

# Schema tiếp nhận dữ liệu Request Body
class MembershipCreate(BaseModel):
    card_number: str
    customer_id: int

# =================================================================
# CẤU TRÚC ĐÓNG GÓI ĐỒNG NHẤT 6 TRƯỜNG QUY CHUẨN (UNIFIED ENVELOPE)
# =================================================================
def create_unified_envelope(status_code: int, message: str, data: Optional[dict] = None, error: Optional[str] = None, path: str = ""):
    return {
        "statusCode": status_code,
        "message": message,
        "data": data,
        "error": error,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "path": path
    }

# Bẫy lỗi tập trung HTTPException để trả về cấu trúc 6 trường sạch sẽ
@app.exception_handler(HTTPException)
def http_exception_handler(request: Request, exc: HTTPException):
    # Trích xuất thông điệp kỹ thuật nếu được truyền qua dict detail
    if isinstance(exc.detail, dict):
        msg = exc.detail.get("message", "Error occurred")
        err_log = exc.detail.get("error", "Technical details hidden")
    else:
        msg = exc.detail
        err_log = "Application logic constraint violation."

    envelope = create_unified_envelope(
        status_code=exc.status_code,
        message=msg,
        error=err_log,
        path=request.url.path
    )
    return JSONResponse(status_code=exc.status_code, content=envelope)


# =================================================================
# 2. API ĐĂNG KÝ THẺ THÀNH VIÊN: POST /memberships
# =================================================================
@app.post("/memberships", status_code=status.HTTP_201_CREATED)
def create_membership(payload: MembershipCreate, request: Request, db=Depends(get_db)):
    
    # Giới hạn nghiêm ngặt: Chỉ sử dụng lệnh SELECT (qua kiểm tra mảng) để xác thực
    
    # 1. KIỂM TRA BẪY 2: Gửi trùng card_number đã thuộc về thành viên khác
    existing_card = None
    for m in memberships_db:
        if m["card_number"] == payload.card_number:
            existing_card = m
            break # Mô phỏng tương đương lệnh .first()
            
    if existing_card is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Mã số thẻ thành viên này đã được sử dụng",
                "error": "Unique constraint violation: card_number field value already exists in table memberships."
            }
        )

    # 2. KIỂM TRA BẪY 1: Gửi customer_id không tồn tại trong bảng customers
    target_customer = None
    for c in customers_db:
        if c["id"] == payload.customer_id:
            target_customer = c
            break # Mô phỏng tương đương lệnh .first()
            
    if target_customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "message": "Khách hàng không tồn tại trên hệ thống",
                "error": "Foreign key constraint violation: customer_id can not be found in parent table customers."
            }
        )

    # 3. THỰC HIỆN HÀNH VI INSERT (Khi tất cả dữ liệu đã hợp lệ và an toàn)
    new_id = len(memberships_db) + 1
    new_membership = {
        "id": new_id,
        "card_number": payload.card_number,
        "customer_id": payload.customer_id
    }
    
    # Mô phỏng các thao tác lưu trữ SQLAlchemy ORM hoàn chỉnh
    db.add(new_membership)
    db.commit()
    db.refresh(new_membership)
    
    # Thêm trực tiếp vào DB mock để lưu lại trạng thái
    memberships_db.append(new_membership)
    
    # Đảm bảo trả về cấu trúc dữ liệu phản hồi dạng 6 trường quy chuẩn
    return create_unified_envelope(
        status_code=201,
        message="Hệ thống thực hiện lệnh INSERT thành công",
        data=new_membership,
        path=request.url.path
    )