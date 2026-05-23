from fastapi import APIRouter

from app.api.v1 import auth, nl2sql, im, admin, dashboard, agents, crawler

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(nl2sql.router, prefix="/nl2sql", tags=["智能问数"])
api_router.include_router(im.router, prefix="/im", tags=["即时通讯"])
api_router.include_router(dashboard.router, prefix="/dashboards", tags=["数字大屏"])
api_router.include_router(agents.router, prefix="/agents", tags=["数字员工"])
api_router.include_router(admin.router, prefix="/admin", tags=["管理端"])
api_router.include_router(crawler.router, prefix="/crawler", tags=["爬虫"])
