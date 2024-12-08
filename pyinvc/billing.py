import asyncio
from datetime import timedelta, datetime
from enum import Enum
from typing import List, Dict

import httpx
from decouple import config


class Billing:
    class RequestMethod(Enum):
        GET = 1
        POST = 2
        DELETE = 3
        PATCH = 4
        PUT = 5

    def __init__(self, *, base_url: str = None, secret_token: str = None, user_id: int, filters: str = None):
        self.BASE_URL = base_url or config("BILLING_BASE_URL")
        self.HEADER = {
            "Authorization": secret_token or f"Bearer {config("BILLING_SECRET_TOKEN")}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        self.user_id = user_id

        if filters and not isinstance(filters, str):
            raise ValueError("The filters must be string type.")

        self.filters = f"&{filters}" if filters else ""

    async def get(self, url: str, data: dict = None):
        async with httpx.AsyncClient() as client:
            return await client.get(
                url=url,
                headers=self.HEADER,
                params=data
            )
            

    async def post(self, url: str, data: dict = None) -> httpx.Response:
        async with httpx.AsyncClient() as client:
            return await client.post(
                url=url,
                headers=self.HEADER,
                json=data
            )


    async def request(self, url: str, method: int, data: dict = None):
        match method:
            case Billing.RequestMethod.GET.value:
                return await self.get(url, data)

            case Billing.RequestMethod.POST.value:
                return await self.post(url, data)

    async def invoice_list_async(self) -> Dict:
        return await self.request(
            method=Billing.RequestMethod.GET.value,
            url=f"{self.BASE_URL}/invoice?filters[business_user_id][$eq]={self.user_id}{self.filters}",
        )

    def invoice_list_sync(self) -> Dict:
        return asyncio.run(self.invoice_list_async())

    async def invoice_detail_async(self, *, invoice_id: int) -> Dict:
        return await self.request(
            method=Billing.RequestMethod.GET.value,
            url=f"{self.BASE_URL}/invoice/{invoice_id}?filters[business_user_id][$eq]={self.user_id}{self.filters}",
        )

    def invoice_detail_sync(self, *, invoice_id: int) -> Dict:
        return asyncio.run(self.invoice_detail_async(invoice_id=invoice_id))

    async def invoice_create_async(self, *, items: List[Dict]) -> Dict:
        return await self.request(
            method=Billing.RequestMethod.POST.value,
            url=f"{self.BASE_URL}/invoice",
            data={
                "user_id": self.user_id,
                "duedate": (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%dT%H:%M:%S"),
                "items": items
            }
        )

    def invoice_create_sync(self, *, items: List[Dict]) -> Dict:
        return asyncio.run(self.invoice_create_async(items=items))

    async def add_promotion_async(self, *, invoice_id: int, promotion_data: dict) -> Dict:
        return await self.request(
            method=Billing.RequestMethod.POST.value,
            url=f"{self.BASE_URL}/item/{invoice_id}",
            data={
                "items": [promotion_data]
            }
        )

    def add_promotion_sync(self, *, invoice_id: int, promotion_data: dict) -> Dict:
        return asyncio.run(self.add_promotion_async(invoice_id=invoice_id, promotion_data=promotion_data))

    async def payment_async(self, *, invoice_id: int, payment_type: str = None) -> str:
        return await self.request(
            method=Billing.RequestMethod.POST.value,
            url=f"{self.BASE_URL}/payment/{invoice_id}",
            data={
                "callback_url": f"{config("BILLING_CALLBACK_URL")}/{invoice_id}",
                **({"payment_type": payment_type} if payment_type is not None else {})
            }
        )

    def payment_sync(self, *, invoice_id: int, payment_type: str = None) -> str:
        return asyncio.run(self.payment_async(invoice_id=invoice_id, payment_type=payment_type))

    async def invoice_delete_item_async(self, *, invoice_id: int, item_id: int) -> Dict:
        return await self.request(
            method=Billing.RequestMethod.POST.value,
            url=f"{self.BASE_URL}/item/{invoice_id}/{item_id}"
        )

    def invoice_delete_item_sync(self, *, invoice_id: int, item_id: int) -> Dict:
        return asyncio.run(self.invoice_delete_item_async(invoice_id=invoice_id, item_id=item_id))

    async def settle_async(self, *, invoice_id: int) -> Dict:
        return await self.request(
            method=Billing.RequestMethod.POST.value,
            url=f"{self.BASE_URL}/invoice/settel",
            data={"invoice_id": invoice_id}
        )

    def settle_sync(self, *, invoice_id: int) -> Dict:
        return asyncio.run(self.settle_async(invoice_id=invoice_id))

    async def transactions_async(self, *, invoice_id: int) -> Dict:
        return await self.request(
            method=Billing.RequestMethod.GET.value,
            url=f"{self.BASE_URL}/transaction?filters[invoice_id][$eq]={invoice_id}"
        )

    def transactions_sync(self, *, invoice_id: int) -> Dict:
        return asyncio.run(self.transactions_async(invoice_id=invoice_id))

    async def wallet_create_async(self):
        return await self.request(
            method=Billing.RequestMethod.POST.value,
            url=f"{self.BASE_URL}/credit/wallet",
            data={
                "user_id": self.user_id,
            }
        )

    def wallet_create_sync(self):
        return asyncio.run(self.wallet_create_async())

    async def wallet_detail_async(self):
        return await self.request(
            method=Billing.RequestMethod.GET.value,
            url=f"{self.BASE_URL}/credit/{self.user_id}"
        )

    def wallet_detail_sync(self):
        return asyncio.run(self.wallet_detail_async())

    async def credit_transaction_create_async(self, amount: int, type_: str, description: str = ""):
        if type_ in {"credit", "debit"}:
            return await self.request(
                method=Billing.RequestMethod.POST.value,
                url=f"{self.BASE_URL}/credit",
                data={
                    "user_id": self.user_id,
                    "amount": str(amount),
                    "description": description,
                    "type": type_
                }
            )

        raise ValueError("invalid type")

    def credit_transaction_create_sync(self, amount: int, type_: str, description: str = ""):
        return asyncio.run(self.credit_transaction_create_async(amount, type_, description))
