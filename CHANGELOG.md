### Version 0.1.24 - 2024/12/08

- Changed the return type of `get` and `post` functions.
- Added `payment_type` to payment request.
- Removed `credit` from `wallet_create` request.
- Fixed issue with `wallet_detail` URL.
- Fixed issue with `credit_transaction_create` function.

### Version 0.1.25 - 2024/12/11

- Bump httpx version to 0.28.1

### Version 0.1.30 - 2024/02/05

- Added new instance method `invoice_update_item_plan_sync` for update one invoice item.
- Changed input argument in `billable_create_sync` method - Alter `amount` to `quantity`.
-

### Version 0.1.31 - 2024/02/09

- use `due_date` argument in `invoice_create_async` instance method.

### Version 0.1.32 - 2024/02/11

- add `callback_url` argument in `payment_sync` instance method.

### Version 0.1.33 - 2024/02/23

- remove `/invoice_id` from `callback_url` in payment.

