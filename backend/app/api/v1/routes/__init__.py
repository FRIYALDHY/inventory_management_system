from fastapi import APIRouter

from app.api.v1.routes import (
    auth,
    backup,
    dashboard,
    health,
    inventory,
    master,
    purchases,
    reports,
    users,
    waste,
)

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(master.router, tags=["master-data"])
api_router.include_router(purchases.router, prefix="/purchases", tags=["purchases"])
api_router.include_router(inventory.router, prefix="/inventory", tags=["inventory"])
api_router.include_router(waste.router, prefix="/waste", tags=["waste"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(backup.router, prefix="/backups", tags=["backups"])

