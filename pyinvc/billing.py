import asyncio
from datetime import timedelta, datetime
from enum import Enum
from typing import List, Dict

import httpx
from decouple import config
from httpx import Response


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

    @staticmethod
    def _validate_datetime(due_date: str, date_format: str) -> bool:
        try:
            datetime.strptime(due_date, date_format)
            return True
        except ValueError:
            return False

    async def get(self, url: str, data: dict = None):
        async with httpx.AsyncClient() as client:
            return await client.get(
                url=url,
                headers=self.HEADER,
                params=data
            )

    async def post(self, url: str, data: dict = None) -> Response:
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

    async def invoice_list_async(self) -> Response:
        return await self.request(
            method=Billing.RequestMethod.GET.value,
            url=f"{self.BASE_URL}/invoice?filters[business_user_id][$eq]={self.user_id}{self.filters}",
        )

    def invoice_list_sync(self) -> Response:
        return asyncio.run(self.invoice_list_async())

    async def invoice_detail_async(self, *, invoice_id: int) -> Response:
        return await self.request(
            method=Billing.RequestMethod.GET.value,
            url=f"{self.BASE_URL}/invoice/{invoice_id}?filters[business_user_id][$eq]={self.user_id}{self.filters}",
        )

    def invoice_detail_sync(self, *, invoice_id: int) -> Response:
        return asyncio.run(self.invoice_detail_async(invoice_id=invoice_id))

    async def invoice_create_async(self, *, items: List[Dict], due_date: str = None) -> Response:

        formatted_due_date = (
            datetime.now() + timedelta(days=3) if due_date is None else datetime.strptime(due_date, "%Y-%m-%dT%H:%M:%S")
        ).strftime("%Y-%m-%dT%H:%M:%S")

        return await self.request(
            method=Billing.RequestMethod.POST.value,
            url=f"{self.BASE_URL}/invoice",
            data={
                "user_id": self.user_id,
                "duedate": formatted_due_date,  # noqa
                "items": items
            }
        )

    def invoice_create_sync(self, *, items: List[Dict], due_date: str = None) -> Response:
        date_format = "%Y-%m-%dT%H:%M:%S"
        if due_date and not self._validate_datetime(due_date, date_format):
            raise ValueError(f"Invalid due_date format: {due_date}. Expected format is '{date_format}'.")
        return asyncio.run(self.invoice_create_async(items=items, due_date=due_date))

    async def add_promotion_async(self, *, invoice_id: int, promotion_data: dict) -> Response:
        return await self.request(
            method=Billing.RequestMethod.POST.value,
            url=f"{self.BASE_URL}/item/{invoice_id}",
            data={
                "items": [promotion_data]
            }
        )

    def add_promotion_sync(self, *, invoice_id: int, promotion_data: dict) -> Response:
        return asyncio.run(self.add_promotion_async(invoice_id=invoice_id, promotion_data=promotion_data))

    async def payment_async(self, *, invoice_id: int, payment_type: str = None) -> Response:
        return await self.request(
            method=Billing.RequestMethod.POST.value,
            url=f"{self.BASE_URL}/payment/{invoice_id}",
            data={
                "callback_url": f"{config("BILLING_CALLBACK_URL")}/{invoice_id}",
                **({"payment_type": payment_type} if payment_type is not None else {})
            }
        )

    def payment_sync(self, *, invoice_id: int, payment_type: str = None) -> Response:
        return asyncio.run(self.payment_async(invoice_id=invoice_id, payment_type=payment_type))

    async def invoice_delete_item_async(self, *, invoice_id: int, item_id: int) -> Response:
        return await self.request(
            method=Billing.RequestMethod.POST.value,
            url=f"{self.BASE_URL}/item/{invoice_id}/{item_id}"
        )

    def invoice_delete_item_sync(self, *, invoice_id: int, item_id: int) -> Response:
        return asyncio.run(self.invoice_delete_item_async(invoice_id=invoice_id, item_id=item_id))

    async def settle_async(self, *, invoice_id: int) -> Response:
        return await self.request(
            method=Billing.RequestMethod.POST.value,
            url=f"{self.BASE_URL}/invoice/settel",  # noqa
            data={"invoice_id": invoice_id}
        )

    def settle_sync(self, *, invoice_id: int) -> Response:
        return asyncio.run(self.settle_async(invoice_id=invoice_id))

    async def transactions_async(self, *, invoice_id: int) -> Response:
        return await self.request(
            method=Billing.RequestMethod.GET.value,
            url=f"{self.BASE_URL}/transaction?filters[invoice_id][$eq]={invoice_id}"
        )

    def transactions_sync(self, *, invoice_id: int) -> Response:
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

    async def billable_create_async(
            self,
            invoice_item_id: int,
            quantity: int,
            description: str,
            started_at: str,
            ended_at: str
    ):
        """
            URL : https://sample-domain/api/v1/billable
            Method : POST    

            # Parameters:
                - invoice_item_id = the id of invoice item  
                - quantity = the quantity of billable
                - description = the description of billable
                - started_at = the start date of billable in string format
                - ended_at = the end date of billable in string format
        """

        return await self.request(
            url=f"{self.BASE_URL}/billable",
            method=Billing.RequestMethod.POST.value,
            data={
                "invoice_item_id": invoice_item_id,
                "quantity": quantity,
                "description": description,
                "started_at": started_at,
                "ended_at": ended_at,
                "user_id": self.user_id,
            }
        )

    def billable_create_sync(
            self,
            invoice_item_id: int,
            quantity: int,
            description: str,
            started_at: str,
            ended_at: str
    ):
        return asyncio.run(
            self.billable_create_async(
                invoice_item_id,
                quantity,
                description,
                started_at,
                ended_at
            )
        )

    async def billable_pay_async(self, invoice_item_id: int):
        """ 
            URL : https://sample-domain/api/v1/billable/collect/pay

            # Parameters:
                - invoice_item_id = the id of invoice item
        """
        return await self.request(
            url=f"{self.BASE_URL}/billable/collect/pay",
            method=Billing.RequestMethod.POST.value,
            data={
                "invoice_item_id": invoice_item_id
            }
        )

    def billable_pay_sync(self, invoice_item_id: int):
        return asyncio.run(self.billable_pay_async(invoice_item_id))

    async def billable_collect_async(self, invoice_item_id: int):
        """ 
            URL : https://sample-domain/api/v1/billable/collect

            # Parameters:
                - invoice_item_id = the id of invoice item
        """
        return await self.request(
            url=f"{self.BASE_URL}/billable/collect",
            method=Billing.RequestMethod.POST.value,
            data={
                "invoice_item_id": invoice_item_id
            }
        )

    def billable_collect_sync(self, invoice_item_id: int):
        return asyncio.run(self.billable_collect_async(invoice_item_id))

    def invoice_update_item_plan_sync(self, item: dict) -> Response:
        """
        URL : https://sample-domain/api/v1/item/update/plan
        :param item: dict
        :return httpx.Response
        """
        if not isinstance(item, dict):
            raise ValueError("Invalid Item Type")
        return asyncio.run(self.invoice_update_item_plan_async(item))

    async def invoice_update_item_plan_async(self, item: dict) -> Response:
        return await self.request(
            url=f"{self.BASE_URL}/item/update/plan",
            method=Billing.RequestMethod.POST.value,
            data=item,
        )
