import asyncio
from datetime import timedelta, datetime
from typing import List, Dict

import httpx
from decouple import config


class Billing:

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

    async def invoice_list_async(self) -> Dict:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url=f"{self.BASE_URL}/invoice?filters[business_user_id][$eq]={self.user_id}{self.filters}",
                headers=self.HEADER,
            )
            response.raise_for_status()
            return response.json()

    def invoice_list_sync(self) -> Dict:
        return asyncio.run(self.invoice_list_async())

    async def invoice_detail_async(self, *, invoice_id: int) -> Dict:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url=f"{self.BASE_URL}/invoice/{invoice_id}?filters[business_user_id][$eq]={self.user_id}{self.filters}",
                headers=self.HEADER,
            )
            response.raise_for_status()
            return response.json()

    def invoice_detail_sync(self, *, invoice_id: int) -> Dict:
        return asyncio.run(self.invoice_detail_async(invoice_id=invoice_id))

    async def invoice_create_async(self, *, items: List[Dict]) -> Dict:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url=f"{self.BASE_URL}/invoice",
                headers=self.HEADER,
                json={
                    "user_id": self.user_id,
                    "duedate": (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%dT%H:%M:%S"),
                    "items": items
                }
            )
            response.raise_for_status()
            return response.json()

    def invoice_create_sync(self, *, items: List[Dict]) -> Dict:
        return asyncio.run(self.invoice_create_async(items=items))

    async def add_promotion_async(self, *, invoice_id: int, promotion_data: dict) -> Dict:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url=f"{self.BASE_URL}/item/{invoice_id}",
                headers=self.HEADER,
                json={
                    "items": [promotion_data]
                }
            )
            response.raise_for_status()
            return response.json()

    def add_promotion_sync(self, *, invoice_id: int, promotion_data: dict) -> Dict:
        return asyncio.run(self.add_promotion_async(invoice_id=invoice_id, promotion_data=promotion_data))

    async def payment_async(self, *, invoice_id: int) -> str:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url=f"{self.BASE_URL}/payment/{invoice_id}",
                headers=self.HEADER,
                json={
                    "callback_url": f"{config("BILLING_CALLBACK_URL")}/{invoice_id}",
                }
            )
            response.raise_for_status()
            return response.text

    def payment_sync(self, *, invoice_id: int) -> str:
        return asyncio.run(self.payment_async(invoice_id=invoice_id))

    async def invoice_delete_item_async(self, *, invoice_id: int, item_id: int) -> Dict:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url=f"{self.BASE_URL}/item/{invoice_id}/{item_id}",
                headers=self.HEADER,
            )
            response.raise_for_status()
            return response.json()

    def invoice_delete_item_sync(self, *, invoice_id: int, item_id: int) -> Dict:
        return asyncio.run(self.invoice_delete_item_async(invoice_id=invoice_id, item_id=item_id))

    async def settle_async(self, *, invoice_id: int) -> Dict:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url=f"{self.BASE_URL}/invoice/settel",
                headers=self.HEADER,
                json={"invoice_id": invoice_id}
            )
            response.raise_for_status()
            return response.json()

    def settle_sync(self, *, invoice_id: int) -> Dict:
        return asyncio.run(self.settle_async(invoice_id=invoice_id))

    async def transactions_async(self, *, invoice_id: int) -> Dict:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url=f"{self.BASE_URL}/transaction?filters[invoice_id][$eq]={invoice_id}",
                headers=self.HEADER,
            )
            response.raise_for_status()
            return response.json()

    def transactions_sync(self, *, invoice_id: int) -> Dict:
        return asyncio.run(self.transactions_async(invoice_id=invoice_id))
