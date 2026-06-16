from typing import Sequence

from sqlalchemy import nulls_last, select, Select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.crud.base import BaseService
from app.database.models import Favorite
from app.database.schemas.favorite import FavoriteCreate, FavoriteUpdate


class FavoriteService(BaseService[Favorite, FavoriteCreate, FavoriteUpdate]):
    def __init__(self, session: AsyncSession):
        super().__init__(Favorite, session)

    async def get_all_by_user_uuid(
        self,
        user_uuid: str,
        get_stmt: bool = False,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> Select[tuple[Favorite]] | Sequence[Favorite]:

        sort_order = sort_order.lower()
        if sort_order not in ("asc", "desc"):
            raise ValueError("sort_order must be either 'asc' or 'desc'")

        sort_field = Favorite.created_at
        if sort_by == "created_at":
            sort_field = Favorite.created_at
        elif sort_by == "auction_date":
            sort_field = Favorite.auction_date

        order_expr = sort_field.desc() if sort_order == "desc" else sort_field.asc()
        if sort_by == "auction_date":
            order_expr = nulls_last(order_expr)

        order_by = [order_expr]
        if sort_by != "created_at":
            order_by.append(Favorite.created_at.desc())
        order_by.append(Favorite.id.desc())

        stmt = select(self.model).where(self.model.user_uuid == user_uuid).order_by(*order_by)
        if get_stmt:
            return stmt
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_user_uuid_and_id(self, user_uuid: str, favorite_id: int) -> Favorite | None:
        stmt = select(Favorite).where(Favorite.user_uuid == user_uuid, Favorite.id == favorite_id).limit(1)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_user_uuid_and_auction_lot_id(self, user_uuid: str, auction: str, lot_id: int) -> Favorite | None:
        stmt = select(Favorite).where(Favorite.user_uuid == user_uuid, Favorite.auction == auction, Favorite.lot_id == lot_id).limit(1)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_auction_lot_id(self, auction: str, lot_id: int, for_user_uuid: str = None)-> Favorite | None:
        stmt = select(Favorite).where(Favorite.auction == auction, Favorite.lot_id == lot_id).limit(1)
        if for_user_uuid:
            stmt = stmt.where(Favorite.user_uuid == for_user_uuid)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

