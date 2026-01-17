from datetime import datetime, UTC, timezone
from typing import Optional, Literal
from pydantic import BaseModel, ConfigDict, field_validator, computed_field

from app.schemas.favorite import Auctions


class FavoriteBase(BaseModel):
    lot_id: int
    auction: Auctions


    title: str | None = None
    auction_date: datetime | None = None
    vin: str | None = None
    images: str | None = None
    odometer: int | None = None
    location: str | None = None
    damage_pr: str | None = None
    damage_sec: str | None = None
    fuel: str | None = None
    transmission: str | None = None
    engine_size: str | None = None
    cylinders: str | None = None

    seller: str | None = None
    document: str | None = None
    status: str | None = None

    @field_validator("auction_date", mode="before")
    @classmethod
    def validate_auction_date(cls, v):
        if isinstance(v, str) and not v.strip():
            return None
        return v


class FavoriteCreate(FavoriteBase):
    user_uuid: str



class FavoriteUpdate(FavoriteBase):
    lot_id: int | None = None
    auction: Auctions | None = None
    user_uuid: str | None = None


class FavoriteRead(FavoriteBase):
    id: int
    images: list[str]

    @field_validator("images", mode="before")
    @classmethod
    def validate_images(cls, v):
        if v:
            return v.split(",")
        return None

    @computed_field
    @property
    def form_get_type(self) -> Literal["active", "history"]:
        now = datetime.now(timezone.utc)
        if self.auction_date and self.auction_date < now:
            return "history"
        return "active"

    model_config = ConfigDict(from_attributes=True)
