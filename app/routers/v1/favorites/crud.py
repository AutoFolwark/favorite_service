import grpc
from AuthTools import HeaderUser
from fastapi import APIRouter, Depends, Body
from rfc9457 import BadRequestProblem, ServerProblem
from sqlalchemy.ext.asyncio import AsyncSession
from AuthTools.Permissions.dependencies import require_one_of_permissions
from fastapi_pagination.ext.sqlalchemy import apaginate
from app.config import Permissions
from app.core.logger import logger
from app.database.crud.favorite import FavoriteService
from app.database.db.session import get_async_db
from app.database.schemas.favorite import FavoriteRead, FavoriteCreate
from app.routers.v1.favorites.admin import admin_favorite_router
from app.rpc_client.auction_api import ApiRpcClient
from app.schemas.favorite import FavoriteIn, FavoriteSort
from app.schemas.pagination import FavoritesPage

favorites_router = APIRouter(prefix='/favorites')

favorites_router.include_router(admin_favorite_router, tags=['admin'])


@favorites_router.get(
    '/', 
    response_model=FavoritesPage,
    description=f'Get all favorites, required permissions: {Permissions.FAVORITES_READ.value}'
)
async def get_all_favorites_for_user(
        db: AsyncSession = Depends(get_async_db),
        sort: FavoriteSort = Depends(),
        user: HeaderUser = Depends(require_one_of_permissions(Permissions.FAVORITES_READ.value, Permissions.FAVORITES_OWN_FULL))
):
    user_uuid = user.uuid
    favorite_service = FavoriteService(db)
    stmt = await favorite_service.get_all_by_user_uuid(
        user_uuid,
        get_stmt=True,
        sort_by=sort.sort_by,
        sort_order=sort.sort_order,
    )
    return await apaginate(db, stmt)

@favorites_router.get('/for-lot', response_model=FavoriteRead, description='Get favorite for lot, required permissions:'
                                                                           f'{Permissions.FAVORITES_READ.value}')
async def get_favorite_for_lot(
        db: AsyncSession = Depends(get_async_db),
        data: FavoriteIn = Depends(),
        user: HeaderUser = Depends(require_one_of_permissions(Permissions.FAVORITES_READ, Permissions.FAVORITES_OWN_FULL))
):
    favorite_service = FavoriteService(db)
    favorite = await favorite_service.get_by_user_uuid_and_auction_lot_id(user.uuid, data.auction, data.lot_id)
    if favorite:
        return favorite
    else:
        raise BadRequestProblem(detail='Favorite not found')

@favorites_router.post('/', response_model=FavoriteRead,
                       description=f'Add lot to favorites, required permissions: {Permissions.FAVORITES_WRITE.value}')
async def add_lot_to_favorites(
        data: FavoriteIn = Body(...),
        db: AsyncSession = Depends(get_async_db),
        user: HeaderUser = Depends(require_one_of_permissions(Permissions.FAVORITES_WRITE, Permissions.FAVORITES_OWN_FULL))

):
    favorite_service = FavoriteService(db)

    exists = await favorite_service.get_by_auction_lot_id(data.auction, data.lot_id, user.uuid)
    if exists:
        return exists
    else:
        exists_other_user = await favorite_service.get_by_auction_lot_id(data.auction, data.lot_id)
        if exists_other_user:
            payload = FavoriteRead.model_validate(exists_other_user).model_dump(exclude={"id", "user_uuid", 'images'})
            payload["user_uuid"] = user.uuid
            payload["images"] = exists_other_user.images
            created = await favorite_service.create(FavoriteCreate(**payload))
            return created

    async with ApiRpcClient() as client:
      try:
        response = await client.get_lot_by_vin_or_lot_id(str(data.lot_id), data.auction)
      except grpc.aio.AioRpcError as e:
          logger.exception('Error while user liked lot', extra = {'error': e.details()})
          raise ServerProblem(detail=e.details()) from e

    if response:
      lot = response.lot[0]

      favorite = await favorite_service.create(FavoriteCreate(
          lot_id=data.lot_id,
          user_uuid=user.uuid,
          auction=data.auction,
          title=lot.title,
          auction_date=lot.auction_date if lot.auction_date else lot.sale_date,
          vin=lot.vin,
          images=','.join(lot.link_img_hd),
          odometer=lot.odometer,
          location=lot.location,
          damage_pr=lot.damage_pr,
          damage_sec=lot.damage_sec,
          fuel=lot.fuel,
          transmission=lot.transmission,
          engine_size=str(lot.engine_size),
          cylinders=str(lot.cylinders),
          seller=lot.seller,
          document=lot.document,
          status=lot.status

      )
      )
      return favorite
    else:
      raise BadRequestProblem(detail='Lot not found')


@favorites_router.delete('/{favorite_id}', response_model=FavoriteRead,
                         description=f'Remove lot from favorites, required permissions: {Permissions.FAVORITES_WRITE.value}')
async def remove_lot_from_favorites(
        favorite_id: int,
        db: AsyncSession = Depends(get_async_db),
        user: HeaderUser = Depends(require_one_of_permissions(Permissions.FAVORITES_DELETE, Permissions.FAVORITES_OWN_FULL))
):
    favorite_service = FavoriteService(db)
    favorite = await favorite_service.get_by_user_uuid_and_id(user.uuid, favorite_id)
    if favorite:
        await favorite_service.delete(favorite_id)
        return favorite
    else:
        raise BadRequestProblem(detail='Favorite not found')













