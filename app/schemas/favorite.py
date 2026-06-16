from enum import Enum

from pydantic import BaseModel, Field

class Auctions(str, Enum):
    COPART = "copart"
    IAAI = "iaai"


class FavoriteIn(BaseModel):
    lot_id: int = Field(..., description="Lot ID")
    auction: Auctions = Field(..., description="Auction type")

class FavoriteSort(BaseModel):
    sort_by: str = Field(
        default="created_at",
        pattern="^(created_at|auction_date)$",
    )
    sort_order: str = Field(
        default="desc",
        pattern="^(asc|desc)$",
    )
