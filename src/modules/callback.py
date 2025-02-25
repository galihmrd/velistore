import random
import string
from datetime import datetime
from pyrogram import Client, filters
from src.database.products_db import menu_db
from src.modules.panel import add_menu_data
from src.database.credits_db import credit_db
from src.modules.keyboard import button_builder, build_keyboard

@Client.on_callback_query(filters.regex(pattern=r"addmenu"))
async def cb_add_menu(b, cb):
    key_data = cb.data.strip().split("|")[1]
    data = add_menu_data.get(key_data)
    await menu_db.add_menu(
        data["code"],
        data["name"],
        data["price"],
        data["desc"]
    )
    await cb.message.edit(
        f"✅ Produk {data['name']} ditambahkan ke menu etalase."
    )

@Client.on_callback_query(filters.regex(pattern=r"order"))
async def cb_order_menu(b, cb):
    user_id = cb.from_user.id
    type = cb.data.strip().split("|")[1]
    random_string = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(10))
    if type in ["item_plus", "item_min"]:
        if type == "item_plus":
            current_item = int(cb.data.strip().split("|")[2]) + 1
        else:
            current_item = int(cb.data.strip().split("|")[2]) - 1
        key_item = cb.data.strip().split("|")[3]
        menu = await menu_db.get_menu(key_item)
        price = int(menu["price"]) * current_item
        min_btn = button_builder("-1 ««", f"order|item_min|{current_item}|{key_item}")
        total_item = button_builder(f"{current_item}x", f"p")
        plus_btn = button_builder("»» +1", f"order|item_plus|{current_item}|{key_item}")
        checkout_btn = button_builder(f"Checkout Rp{price:,}", f"order|checkout|{current_item}|{key_item}")
        button = build_keyboard([min_btn, total_item, plus_btn, checkout_btn], row_width=3)
        await cb.message.edit(
            cb.message.text.markdown,
            reply_markup=button,
        )
    elif type == "checkout":
        total_item = int(cb.data.strip().split("|")[2])
        key_item = cb.data.strip().split("|")[3]
        menu = await menu_db.get_menu(key_item)
        price = int(menu["price"]) * int(total_item)
        get_balance = await credit_db.get_balance(user_id)
        remaining = get_balance.get("credits")
        remaining_balance = 0 if remaining is None else remaining
        if price > remaining_balance:
            return await cb.answer(f"Saldo anda tidak mencukupi.", show_alert=True)
        elif price <= remaining_balance:
            balance = remaining_balance - price
            await credit_db.add_balance(
                user_id,
                balance,
                random_string
            )
            await cb.message.edit("Order berhasil.")

@Client.on_callback_query(filters.regex(pattern=r"topup"))
async def cb_topup_menu(b, cb):
    task_id = cb.data.strip().split("|")[1]
    nominal = int(cb.data.strip().split("|")[2])
    user_id = cb.data.strip().split("|")[3]
    if int(task_id) == cb.from_user.id:
        random_string = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(10))
        try:
            userdata = await b.get_users(int(user_id))
            get_balance = await credit_db.get_balance(int(user_id))
            remaining = get_balance.get("credits")
            remaining_balance = 0 if remaining is None else remaining 
            balance = int(nominal) + remaining_balance
            await credit_db.add_balance(
                int(user_id),
                balance,
                random_string
            )
            msg = (
                f"💰 **INFORMASI TOPUP** 💰\n\n• **ID Pengguna:** {userdata.mention} (`{user_id}`)\n"
                f"• **Saldo Terakhir:** Rp{remaining:,}\n• **Nominal Topup:** Rp{nominal:,}\n\n"
                f"• **Saldo Terkini:** Rp{balance:,}\n• **ID Pembayaran:** `{random_string}`\n"
                f"• **Stampel Waktu:** `{datetime.now()}`"
            )
            await cb.message.edit(msg)
        except Exception as e:
            await cb.message.edit(e)
    else:
        await cb.answer("Hanya admin yang dapat melakukan tindakan ini.", show_alert=True)
