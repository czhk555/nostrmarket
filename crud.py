import json
from typing import List, Optional

from lnbits.helpers import urlsafe_short_hash

from . import db
from .models import (
    Customer,
    CustomerProfile,
    DirectMessage,
    Merchant,
    MerchantConfig,
    Order,
    PartialDirectMessage,
    PartialMerchant,
    PartialProduct,
    PartialStall,
    PartialZone,
    Product,
    Stall,
    Zone,
)

######################################## MERCHANT ########################################


async def create_merchant(user_id: str, m: PartialMerchant) -> Merchant:
    merchant_id = urlsafe_short_hash()
    await db.execute(
        """
        INSERT INTO nostrmarket.merchants (user_id, id, private_key, public_key, meta)
        VALUES (?, ?, ?, ?, ?)
        """,
        (user_id, merchant_id, m.private_key, m.public_key, json.dumps(dict(m.config))),
    )
    merchant = await get_merchant(user_id, merchant_id)
    assert merchant, "Created merchant cannot be retrieved"
    return merchant


async def update_merchant(
    user_id: str, merchant_id: str, config: MerchantConfig
) -> Optional[Merchant]:
    await db.execute(
        f"""
            UPDATE nostrmarket.merchants SET meta = ?
            WHERE id = ? AND user_id = ?
        """,
        (json.dumps(config.dict()), merchant_id, user_id),
    )
    return await get_merchant(user_id, merchant_id)


async def get_merchant(user_id: str, merchant_id: str) -> Optional[Merchant]:
    row = await db.fetchone(
        """SELECT * FROM nostrmarket.merchants WHERE user_id = ? AND id = ?""",
        (
            user_id,
            merchant_id,
        ),
    )

    return Merchant.from_row(row) if row else None


async def get_merchant_by_pubkey(public_key: str) -> Optional[Merchant]:
    row = await db.fetchone(
        """SELECT * FROM nostrmarket.merchants WHERE public_key = ? """,
        (public_key,),
    )

    return Merchant.from_row(row) if row else None


async def get_public_keys_for_merchants() -> List[str]:
    rows = await db.fetchall(
        """SELECT public_key FROM nostrmarket.merchants""",
    )

    return [row[0] for row in rows]


async def get_merchant_for_user(user_id: str) -> Optional[Merchant]:
    row = await db.fetchone(
        """SELECT * FROM nostrmarket.merchants WHERE user_id = ? """,
        (user_id,),
    )

    return Merchant.from_row(row) if row else None


async def delete_merchant(merchant_id: str) -> None:
    await db.execute(
        "DELETE FROM nostrmarket.merchants WHERE id = ?",
        (merchant_id,),
    )


######################################## ZONES ########################################


async def create_zone(merchant_id: str, data: PartialZone) -> Zone:
    zone_id = urlsafe_short_hash()
    await db.execute(
        f"""
        INSERT INTO nostrmarket.zones (id, merchant_id, name, currency, cost, regions)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            zone_id,
            merchant_id,
            data.name,
            data.currency,
            data.cost,
            json.dumps(data.countries),
        ),
    )

    zone = await get_zone(merchant_id, zone_id)
    assert zone, "Newly created zone couldn't be retrieved"
    return zone


async def update_zone(merchant_id: str, z: Zone) -> Optional[Zone]:
    await db.execute(
        f"UPDATE nostrmarket.zones SET name = ?, cost = ?, regions = ?  WHERE id = ? AND merchant_id = ?",
        (z.name, z.cost, json.dumps(z.countries), z.id, merchant_id),
    )
    return await get_zone(merchant_id, z.id)


async def get_zone(merchant_id: str, zone_id: str) -> Optional[Zone]:
    row = await db.fetchone(
        "SELECT * FROM nostrmarket.zones WHERE merchant_id = ? AND id = ?",
        (
            merchant_id,
            zone_id,
        ),
    )
    return Zone.from_row(row) if row else None


async def get_zones(merchant_id: str) -> List[Zone]:
    rows = await db.fetchall(
        "SELECT * FROM nostrmarket.zones WHERE merchant_id = ?", (merchant_id,)
    )
    return [Zone.from_row(row) for row in rows]


async def delete_zone(merchant_id: str, zone_id: str) -> None:

    await db.execute(
        "DELETE FROM nostrmarket.zones WHERE merchant_id = ? AND id = ?",
        (
            merchant_id,
            zone_id,
        ),
    )


async def delete_merchant_zones(merchant_id: str) -> None:
    await db.execute(
        "DELETE FROM nostrmarket.zones WHERE merchant_id = ?", (merchant_id,)
    )


######################################## STALL ########################################


async def create_stall(merchant_id: str, data: PartialStall) -> Stall:
    stall_id = urlsafe_short_hash()

    await db.execute(
        f"""
        INSERT INTO nostrmarket.stalls (merchant_id, id, wallet, name, currency, zones, meta)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            merchant_id,
            stall_id,
            data.wallet,
            data.name,
            data.currency,
            json.dumps(
                [z.dict() for z in data.shipping_zones]
            ),  # todo: cost is float. should be int for sats
            json.dumps(data.config.dict()),
        ),
    )

    stall = await get_stall(merchant_id, stall_id)
    assert stall, "Newly created stall couldn't be retrieved"
    return stall


async def get_stall(merchant_id: str, stall_id: str) -> Optional[Stall]:
    row = await db.fetchone(
        "SELECT * FROM nostrmarket.stalls WHERE merchant_id = ? AND id = ?",
        (
            merchant_id,
            stall_id,
        ),
    )
    return Stall.from_row(row) if row else None


async def get_stalls(merchant_id: str) -> List[Stall]:
    rows = await db.fetchall(
        "SELECT * FROM nostrmarket.stalls WHERE merchant_id = ?",
        (merchant_id,),
    )
    return [Stall.from_row(row) for row in rows]


async def update_stall(merchant_id: str, stall: Stall) -> Optional[Stall]:
    await db.execute(
        f"""
            UPDATE nostrmarket.stalls SET wallet = ?, name = ?, currency = ?, zones = ?, meta = ?
            WHERE merchant_id = ? AND id = ?
        """,
        (
            stall.wallet,
            stall.name,
            stall.currency,
            json.dumps(
                [z.dict() for z in stall.shipping_zones]
            ),  # todo: cost is float. should be int for sats
            json.dumps(stall.config.dict()),
            merchant_id,
            stall.id,
        ),
    )
    return await get_stall(merchant_id, stall.id)


async def delete_stall(merchant_id: str, stall_id: str) -> None:
    await db.execute(
        "DELETE FROM nostrmarket.stalls WHERE merchant_id =? AND id = ?",
        (
            merchant_id,
            stall_id,
        ),
    )


async def delete_merchant_stalls(merchant_id: str) -> None:
    await db.execute(
        "DELETE FROM nostrmarket.stalls WHERE merchant_id = ?",
        (merchant_id,),
    )


######################################## PRODUCTS ########################################


async def create_product(merchant_id: str, data: PartialProduct) -> Product:
    product_id = urlsafe_short_hash()

    await db.execute(
        f"""
        INSERT INTO nostrmarket.products (merchant_id, id, stall_id, name, price, quantity, image_urls, category_list, meta)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            merchant_id,
            product_id,
            data.stall_id,
            data.name,
            data.price,
            data.quantity,
            json.dumps(data.images),
            json.dumps(data.categories),
            json.dumps(data.config.dict()),
        ),
    )
    product = await get_product(merchant_id, product_id)
    assert product, "Newly created product couldn't be retrieved"

    return product


async def update_product(merchant_id: str, product: Product) -> Product:

    await db.execute(
        f"""
        UPDATE nostrmarket.products set name = ?, price = ?, quantity = ?, image_urls = ?, category_list = ?, meta = ?
        WHERE merchant_id = ? AND id = ?
        """,
        (
            product.name,
            product.price,
            product.quantity,
            json.dumps(product.images),
            json.dumps(product.categories),
            json.dumps(product.config.dict()),
            merchant_id,
            product.id,
        ),
    )
    updated_product = await get_product(merchant_id, product.id)
    assert updated_product, "Updated product couldn't be retrieved"

    return updated_product


async def update_product_quantity(
    product_id: str, new_quantity: int
) -> Optional[Product]:
    await db.execute(
        f"UPDATE nostrmarket.products SET quantity = ?  WHERE id = ?",
        (new_quantity, product_id),
    )
    row = await db.fetchone(
        "SELECT * FROM nostrmarket.products WHERE id = ?",
        (product_id,),
    )
    return Product.from_row(row) if row else None


async def get_product(merchant_id: str, product_id: str) -> Optional[Product]:
    row = await db.fetchone(
        "SELECT * FROM nostrmarket.products WHERE merchant_id =? AND id = ?",
        (
            merchant_id,
            product_id,
        ),
    )
    return Product.from_row(row) if row else None


async def get_products(merchant_id: str, stall_id: str) -> List[Product]:
    rows = await db.fetchall(
        "SELECT * FROM nostrmarket.products WHERE merchant_id = ? AND stall_id = ?",
        (merchant_id, stall_id),
    )
    return [Product.from_row(row) for row in rows]


async def get_products_by_ids(
    merchant_id: str, product_ids: List[str]
) -> List[Product]:
    q = ",".join(["?"] * len(product_ids))
    rows = await db.fetchall(
        f"SELECT id, stall_id, name, price, quantity, category_list, meta  FROM nostrmarket.products WHERE merchant_id = ? AND id IN ({q})",
        (merchant_id, *product_ids),
    )
    return [Product.from_row(row) for row in rows]


async def get_wallet_for_product(product_id: str) -> Optional[str]:
    row = await db.fetchone(
        """
        SELECT s.wallet FROM nostrmarket.products p
        INNER JOIN nostrmarket.stalls s
        ON p.stall_id = s.id
        WHERE p.id=?
       """,
        (product_id,),
    )
    return row[0] if row else None


async def delete_product(merchant_id: str, product_id: str) -> None:
    await db.execute(
        "DELETE FROM nostrmarket.products WHERE merchant_id =? AND id = ?",
        (
            merchant_id,
            product_id,
        ),
    )


async def delete_merchant_products(merchant_id: str) -> None:
    await db.execute(
        "DELETE FROM nostrmarket.products WHERE merchant_id = ?",
        (merchant_id,),
    )


######################################## ORDERS ########################################


async def create_order(merchant_id: str, o: Order) -> Order:
    await db.execute(
        f"""
        INSERT INTO nostrmarket.orders (
            merchant_id, 
            id, 
            event_id, 
            event_created_at,
            merchant_public_key,
            public_key, 
            address, 
            contact_data, 
            extra_data, 
            order_items,
            shipping_id,
            stall_id, 
            invoice_id, 
            total
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(event_id) DO NOTHING
        """,
        (
            merchant_id,
            o.id,
            o.event_id,
            o.event_created_at,
            o.merchant_public_key,
            o.public_key,
            o.address,
            json.dumps(o.contact.dict() if o.contact else {}),
            json.dumps(o.extra.dict()),
            json.dumps([i.dict() for i in o.items]),
            o.shipping_id,
            o.stall_id,
            o.invoice_id,
            o.total,
        ),
    )
    order = await get_order(merchant_id, o.id)
    assert order, "Newly created order couldn't be retrieved"

    return order


async def get_order(merchant_id: str, order_id: str) -> Optional[Order]:
    row = await db.fetchone(
        "SELECT * FROM nostrmarket.orders WHERE merchant_id =? AND id = ?",
        (
            merchant_id,
            order_id,
        ),
    )
    return Order.from_row(row) if row else None


async def get_order_by_event_id(merchant_id: str, event_id: str) -> Optional[Order]:
    row = await db.fetchone(
        "SELECT * FROM nostrmarket.orders WHERE merchant_id =? AND  event_id =?",
        (
            merchant_id,
            event_id,
        ),
    )
    return Order.from_row(row) if row else None


async def get_orders(merchant_id: str, **kwargs) -> List[Order]:
    q = " AND ".join(
        [f"{field[0]} = ?" for field in kwargs.items() if field[1] != None]
    )
    values = ()
    if q:
        q = f"AND {q}"
        values = (v for v in kwargs.values() if v != None)
    rows = await db.fetchall(
        f"SELECT * FROM nostrmarket.orders WHERE merchant_id = ? {q} ORDER BY time DESC",
        (merchant_id, *values),
    )
    return [Order.from_row(row) for row in rows]


async def get_orders_for_stall(
    merchant_id: str, stall_id: str, **kwargs
) -> List[Order]:
    q = " AND ".join(
        [f"{field[0]} = ?" for field in kwargs.items() if field[1] != None]
    )
    values = ()
    if q:
        q = f"AND {q}"
        values = (v for v in kwargs.values() if v != None)
    rows = await db.fetchall(
        f"SELECT * FROM nostrmarket.orders WHERE merchant_id = ? AND stall_id = ? {q} ORDER BY time DESC",
        (merchant_id, stall_id, *values),
    )
    return [Order.from_row(row) for row in rows]


async def get_last_order_time(public_key: str) -> int:
    row = await db.fetchone(
        """
            SELECT event_created_at FROM nostrmarket.orders 
            WHERE merchant_public_key = ? ORDER BY event_created_at DESC LIMIT 1
        """,
        (public_key,),
    )
    return row[0] if row else 0


async def update_order_paid_status(order_id: str, paid: bool) -> Optional[Order]:
    await db.execute(
        f"UPDATE nostrmarket.orders SET paid = ?  WHERE id = ?",
        (paid, order_id),
    )
    row = await db.fetchone(
        "SELECT * FROM nostrmarket.orders WHERE id = ?",
        (order_id,),
    )
    return Order.from_row(row) if row else None


async def update_order_shipped_status(
    merchant_id: str, order_id: str, shipped: bool
) -> Optional[Order]:
    await db.execute(
        f"UPDATE nostrmarket.orders SET shipped = ?  WHERE merchant_id = ? AND id = ?",
        (shipped, merchant_id, order_id),
    )

    row = await db.fetchone(
        "SELECT * FROM nostrmarket.orders WHERE id = ?",
        (order_id,),
    )
    return Order.from_row(row) if row else None


async def delete_merchant_orders(merchant_id: str) -> None:
    await db.execute(
        "DELETE FROM nostrmarket.orders WHERE merchant_id = ?",
        (merchant_id,),
    )


######################################## MESSAGES ########################################L


async def create_direct_message(
    merchant_id: str, dm: PartialDirectMessage
) -> DirectMessage:
    dm_id = urlsafe_short_hash()
    await db.execute(
        f"""
        INSERT INTO nostrmarket.direct_messages (merchant_id, id, event_id, event_created_at, message, public_key, incoming)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(event_id) DO NOTHING
        """,
        (
            merchant_id,
            dm_id,
            dm.event_id,
            dm.event_created_at,
            dm.message,
            dm.public_key,
            dm.incoming,
        ),
    )
    if dm.event_id:
        msg = await get_direct_message_by_event_id(merchant_id, dm.event_id)
    else:
        msg = await get_direct_message(merchant_id, dm_id)
    assert msg, "Newly created dm couldn't be retrieved"
    return msg


async def get_direct_message(merchant_id: str, dm_id: str) -> Optional[DirectMessage]:
    row = await db.fetchone(
        "SELECT * FROM nostrmarket.direct_messages WHERE merchant_id = ? AND id = ?",
        (
            merchant_id,
            dm_id,
        ),
    )
    return DirectMessage.from_row(row) if row else None


async def get_direct_message_by_event_id(
    merchant_id: str, event_id: str
) -> Optional[DirectMessage]:
    row = await db.fetchone(
        "SELECT * FROM nostrmarket.direct_messages WHERE merchant_id = ? AND event_id = ?",
        (
            merchant_id,
            event_id,
        ),
    )
    return DirectMessage.from_row(row) if row else None


async def get_direct_messages(merchant_id: str, public_key: str) -> List[DirectMessage]:
    rows = await db.fetchall(
        "SELECT * FROM nostrmarket.direct_messages WHERE merchant_id = ? AND public_key = ? ORDER BY event_created_at",
        (merchant_id, public_key),
    )
    return [DirectMessage.from_row(row) for row in rows]


async def get_last_direct_messages_time(public_key: str) -> int:
    row = await db.fetchone(
        """
            SELECT event_created_at FROM nostrmarket.direct_messages 
            WHERE public_key = ? ORDER BY event_created_at DESC LIMIT 1
        """,
        (public_key,),
    )
    return row[0] if row else 0


async def delete_merchant_direct_messages(merchant_id: str) -> None:
    await db.execute(
        "DELETE FROM nostrmarket.direct_messages WHERE merchant_id = ?",
        (merchant_id,),
    )


######################################## CUSTOMERS ########################################


async def create_customer(merchant_id: str, data: Customer) -> Customer:
    await db.execute(
        f"""
        INSERT INTO nostrmarket.customers (merchant_id, public_key, meta)
        VALUES (?, ?, ?)
        """,
        (
            merchant_id,
            data.public_key,
            json.dumps(data.profile) if data.profile else "{}",
        ),
    )

    customer = await get_customer(merchant_id, data.public_key)
    assert customer, "Newly created customer couldn't be retrieved"
    return customer


async def get_customer(merchant_id: str, public_key: str) -> Optional[Customer]:
    row = await db.fetchone(
        "SELECT * FROM nostrmarket.customers WHERE merchant_id = ? AND public_key = ?",
        (
            merchant_id,
            public_key,
        ),
    )
    return Customer.from_row(row) if row else None


async def get_customers(merchant_id: str) -> List[Customer]:
    rows = await db.fetchall(
        "SELECT * FROM nostrmarket.customers WHERE merchant_id = ?", (merchant_id,)
    )
    return [Customer.from_row(row) for row in rows]


async def get_all_customers() -> List[Customer]:
    rows = await db.fetchall("SELECT * FROM nostrmarket.customers")
    return [Customer.from_row(row) for row in rows]


async def update_customer_profile(
    public_key: str, event_created_at: int, profile: CustomerProfile
):
    await db.execute(
        f"UPDATE nostrmarket.customers SET event_created_at = ?, meta = ? WHERE public_key = ?",
        (event_created_at, json.dumps(profile.dict()), public_key),
    )


async def increment_customer_unread_messages(public_key: str):
    await db.execute(
        f"UPDATE nostrmarket.customers SET unread_messages = unread_messages + 1 WHERE public_key = ?",
        (public_key,),
    )


async def update_customer_no_unread_messages(public_key: str):
    await db.execute(
        f"UPDATE nostrmarket.customers SET unread_messages = 0 WHERE public_key = ?",
        (public_key,),
    )
