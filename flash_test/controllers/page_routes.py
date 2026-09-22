from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from services.camera_service import camera_service

router = APIRouter()
templates = Jinja2Templates(directory="views/templates")

@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse(request=request, name="test.html", context={"request": request})

@router.get("/test", response_class=HTMLResponse)
async def test_page(request: Request):
    return templates.TemplateResponse(request=request, name="test.html", context={"request": request})

@router.get("/manage-proofs", response_class=HTMLResponse)
async def manage_proofs_page(request: Request):
    return templates.TemplateResponse(request=request, name="manage_proofs.html", context={"request": request})
