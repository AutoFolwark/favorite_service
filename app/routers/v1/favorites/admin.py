from AuthTools.Permissions.dependencies import require_permissions
from fastapi import Depends, APIRouter, Query
from fastapi_pagination.ext.sqlalchemy import apaginate
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Permissions
from app.database.crud.favorite import FavoriteService
from app.database.db.session import get_async_db
from app.schemas.pagination import FavoritesPage

admin_favorite_router = APIRouter(prefix='/for-user')

@admin_favorite_router.get('', response_model=FavoritesPage, dependencies=[Depends(require_permissions(Permissions.FAVORITES_READ_ALL))],
                      description=f'Get all favorites for specific user, required permissions: {Permissions.FAVORITES_READ_ALL.value}')
@admin_favorite_router.get('/', include_in_schema=False)
async def get_all_favorites_for_user(
        db: AsyncSession = Depends(get_async_db),
        user_uuid: str = Query(...)
):
    favorite_service = FavoriteService(db)
    stmt = await favorite_service.get_all_by_user_uuid(user_uuid, True)
    return await apaginate(db, stmt)