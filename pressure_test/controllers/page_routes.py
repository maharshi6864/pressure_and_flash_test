from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from services.camera_service import camera_service
from services.measurement_service import measurement_service

router = APIRouter()
templates = Jinja2Templates(directory="views/templates")

# @router.get("/", response_class=HTMLResponse)
# async def dashboard(request: Request):
#     return templates.TemplateResponse(request=request, name="dashboard.html", context={"request": request, "source": camera_service.source})

@router.get("/", response_class=HTMLResponse)
async def test_page(request: Request):
    return templates.TemplateResponse(request=request, name="test.html", context={"request": request, "marker_size": measurement_service.marker_size})


@router.get("/capture", response_class=HTMLResponse)
async def capture_page(request: Request):
    return templates.TemplateResponse(request=request, name="capture.html", context={"request": request})

@router.get("/calibrate", response_class=HTMLResponse)
async def calibrate_page(request: Request):
    return templates.TemplateResponse(request=request, name="calibrate.html", context={"request": request})

@router.get("/test", response_class=HTMLResponse)
async def test_page(request: Request):
    return templates.TemplateResponse(request=request, name="test.html", context={"request": request, "marker_size": measurement_service.marker_size})

@router.get("/manage-proofs", response_class=HTMLResponse)
async def manage_proofs_page(request: Request):
    return templates.TemplateResponse(request=request, name="manage_proofs.html", context={"request": request})

@router.get("/proofs/{proof_id}/results", response_class=HTMLResponse)
async def proof_results_page(request: Request, proof_id: int):
    return templates.TemplateResponse(request=request, name="proof_results.html", context={"request": request, "proof_id": proof_id})
