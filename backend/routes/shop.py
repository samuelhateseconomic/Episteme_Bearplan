from fastapi import APIRouter, Request
from pydantic import BaseModel, ConfigDict, StrictInt, StrictStr

from backend.domain.rewards import PurchaseResult, ShopView

router = APIRouter(prefix="/api/shop")


class PurchaseRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    species: StrictStr
    expected_price: StrictInt
    operation_id: StrictStr


@router.get("")
def get_shop(request: Request) -> ShopView:
    request.app.state.timer.get()
    return request.app.state.shop.get()


@router.post("/purchases", status_code=201)
def purchase_species(body: PurchaseRequest, request: Request) -> PurchaseResult:
    return request.app.state.shop.purchase(**body.model_dump())
