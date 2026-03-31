from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api import admin, documents, product, research
from app.config import PLAN_MAP, PLANS, get_settings
from app.services.scheduler_service import (
    get_open_access_scheduler_status,
    maybe_start_open_access_scheduler,
    stop_open_access_scheduler,
)
from app.services.security_scan_service import (
    get_security_scanner_status,
    maybe_start_security_scanner,
    stop_security_scanner,
)
from app.services.scheduler_config_service import get_runtime_scheduler_settings
from app.services.admin_auth_service import require_admin


BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_runtime_scheduler_settings(get_settings())
    maybe_start_open_access_scheduler(settings)
    maybe_start_security_scanner(settings)
    try:
        yield
    finally:
        stop_open_access_scheduler()
        stop_security_scanner()


app = FastAPI(
    title="Frontier Research Intelligence Platform",
    version="0.2.0",
    description="Scientific discovery intelligence system with research discovery, document intelligence, workspace tooling, and business analytics.",
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

app.include_router(documents.router, prefix="/documents", tags=["Documents"])
app.include_router(research.router, prefix="/research", tags=["Research"])
app.include_router(product.router, prefix="/product", tags=["Product"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])


def render_page(request: Request, template_name: str, **context):
    settings = get_settings()
    plans = [
        {
            "code": plan.code,
            "name": plan.name,
            "price": plan.price,
            "tagline": plan.tagline,
            "description": plan.description,
        }
        for plan in PLANS
        if plan.code != "free"
    ]
    nav_items = [
        {"label": "Home", "href": "/"},
        {"label": "Explore", "href": "/explore"},
        {"label": "Workspace", "href": "/workspace"},
        {"label": "Pricing", "href": "/pricing"},
        {"label": "Docs", "href": "/docs"},
        {"label": "Use Cases", "href": "/use-cases"},
        {"label": "Careers", "href": "/careers"},
        {"label": "Admin", "href": "/admin-controls"},
    ]
    return templates.TemplateResponse(
        request,
        template_name,
        {
            "request": request,
            "app_name": settings.app_name,
            "settings": settings,
            "plans": plans,
            "nav_items": nav_items,
            **context,
        },
    )


@app.get("/")
def home(request: Request):
    featured_workflows = [
        "Search platform papers",
        "Pull in arXiv work",
        "Compare serious sources",
        "Ask grounded questions",
        "Save to workspace",
        "Build a draft without losing the thread",
    ]
    return render_page(
        request,
        "home.html",
        page_title="Frontier Research Intelligence",
        page_name="home",
        featured_workflows=featured_workflows,
    )


@app.get("/explore")
def explore(request: Request):
    return render_page(
        request,
        "explore.html",
        page_title="Explore Research",
        page_name="explore",
    )


@app.get("/workspace")
def workspace(request: Request):
    return render_page(
        request,
        "workspace.html",
        page_title="Workspace",
        page_name="workspace",
    )


@app.get("/pricing")
def pricing(request: Request):
    return render_page(
        request,
        "pricing.html",
        page_title="Pricing",
        page_name="pricing",
    )


@app.get("/auth")
def auth_page(request: Request, plan: str = "student", mode: str = "sign-up"):
    raw_plan = PLAN_MAP.get(plan, PLAN_MAP["student"])
    selected_plan = {
        "code": raw_plan.code,
        "name": raw_plan.name,
        "price": raw_plan.price,
        "tagline": raw_plan.tagline,
        "description": raw_plan.description,
    }
    return render_page(
        request,
        "auth.html",
        page_title=f"{selected_plan['name']} Access",
        page_name="auth",
        selected_plan=selected_plan,
        auth_mode="sign-in" if mode == "sign-in" else "sign-up",
    )


@app.get("/plans/{plan_code}")
def plan_checkout(plan_code: str):
    plan = plan_code if plan_code in PLAN_MAP else "student"
    return RedirectResponse(url=f"/auth?plan={plan}&mode=sign-up", status_code=302)


@app.get("/docs")
def docs_page(request: Request):
    return render_page(
        request,
        "docs.html",
        page_title="Documentation",
        page_name="docs",
    )


@app.get("/careers")
def careers_page(request: Request):
    return render_page(
        request,
        "careers.html",
        page_title="Careers",
        page_name="careers",
    )


@app.get("/use-cases")
def use_cases_page(request: Request):
    return render_page(
        request,
        "use_cases.html",
        page_title="Use Cases",
        page_name="use-cases",
    )


@app.get("/admin-controls")
def admin_controls_page(request: Request, _: dict = Depends(require_admin)):
    return render_page(
        request,
        "admin_controls.html",
        page_title="Admin Controls",
        page_name="admin-controls",
    )


@app.get("/health")
def health():
    settings = get_settings()
    return {
        "message": "Frontier Research Intelligence backend is online.",
        "ui": {
            "home": "/",
            "explore": "/explore",
            "workspace": "/workspace",
            "pricing": "/pricing",
            "auth": "/auth",
            "docs": "/docs",
            "careers": "/careers",
            "use_cases": "/use-cases",
        },
        "services": {
            "documents": "/documents/health",
            "research": "/research/health",
            "product": "/product/health",
            "admin": "/admin/health",
        },
        "integrations": {
            "clerk": settings.has_clerk,
            "supabase": settings.has_supabase,
            "stripe": settings.has_stripe,
        },
        "jobs": {
            "open_access_auto_indexer": get_open_access_scheduler_status(),
            "security_auto_scanner": get_security_scanner_status(),
        },
    }
