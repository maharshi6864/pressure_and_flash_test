from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from core.database import get_db
from models.db_models import Proof
from core.security import get_current_user
import json
import os

router = APIRouter()
templates = Jinja2Templates(directory="views/templates")

@router.api_route("/favicon.ico", methods=["GET", "HEAD"], include_in_schema=False)
async def favicon():
    fav_path = "views/static/images/favicon-32x32_ver-1.1.png"
    if os.path.exists(fav_path):
        return FileResponse(fav_path, media_type="image/png")
    raise HTTPException(status_code=404, detail="Favicon not found")

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(request=request, name="login.html")

@router.get("/", response_class=HTMLResponse)
async def dashboard_page(request: Request, db: Session = Depends(get_db)):
    # Assuming user is authenticated via JS token logic
    total_proofs = db.query(Proof).count()
    return templates.TemplateResponse(request=request, name="manage_proofs.html", context={"total_proofs": total_proofs})

@router.get("/manage-proofs", response_class=HTMLResponse)
async def manage_proofs_page(request: Request):
    return templates.TemplateResponse(request=request, name="manage_proofs.html")

@router.get("/proof/{proof_id}", response_class=HTMLResponse)
async def proof_detail_page(request: Request, proof_id: int):
    return templates.TemplateResponse(request=request, name="proof_detail.html", context={"proof_id": proof_id})

@router.get("/proof/{proof_id}/print", response_class=HTMLResponse)
async def print_proof_page(request: Request, proof_id: int):
    return templates.TemplateResponse(request=request, name="proof_slip_print.html", context={"proof_id": proof_id})

@router.get("/manage-users", response_class=HTMLResponse)
async def manage_users_page(request: Request):
    return templates.TemplateResponse(request=request, name="manage_users.html")
