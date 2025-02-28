import random
import string
import traceback
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.errors.exceptions.flood_420 import FloodWait
from src.database.products_db import menu_db
from src.modules.panel import add_menu_data, add_stock_data
from src.database.credits_db import credit_db
from src.database.sudo_db import sudo_user_db
from src.database.stock_db import stocks_db
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

@Client.on_callback_query(filters.regex(pattern=r"showmenu"))
async def cb_show_menu(b, cb):
    action = cb.data.strip().split("|")[1]
    position = cb.data.strip().split("|")[2]
    task_id = cb.data.strip().split("|")[3]
    if cb.from_user.id == int(task_id):
        list_menu = []
        bot_info = await b.get_me()
        username = bot_info.username
        try:
            caption = "**»»» PERLA BOT STORE «««**\n\n"
            all_menu = await menu_db.get_all_menus()
            for i in range(int(position), len(all_menu)):
                item = all_menu[i]
                stock = await stocks_db.get_stock(item['key'])
                list_stock = stock.get("stock", [])
                url_product = f"http://t.me/{username}?start={item['key']}"
                list_menu.append(
                    f"**🏷 {item['name']}**\n• **💵 Harga:** Rp{int(item['price']):,}\n• **📦 Stok Tersedia:** {len(list_stock)}\n"
                    f"• **🆔 Kode:** `{item['key']}` | [Beli]({url_product})\n• **📄 Desk:** __{item['desc']}__"
                )
                current_position = int(position) + 4
                if current_position == i:
                    break
            back_position = int(position) - 4
            next_btn = button_builder("⬇️ Berikutnya", f"showmenu|next|{current_position}|{task_id}")
            back_btn = button_builder("⬆️ Kembali", f"showmenu|back|{back_position}|{task_id}")
            button = build_keyboard([back_btn, next_btn], row_width=1)
            await cb.message.edit(caption + "\n\n".join(list_menu), reply_markup=button, disable_web_page_preview=True)
        except Exception:
            if action == "next":
                await cb.answer("Anda telah mencapai batas akhir menu etalase.", show_alert=True)
            elif action == "back":
                await cb.answer("Anda telah mencapai batas awal menu etalase.", show_alert=True)
        except FloodWait as e:
            await cb.answer(f"Terlalu cepat! Tunggu {e.value} detik.")
    else:
        await cb.answer("Ketik /menu untuk melihat menu anda sendiri.", show_alert=True)

@Client.on_callback_query(filters.regex(pattern=r"restock"))
async def cb_add_stock(b, cb):
    key_data = cb.data.strip().split("|")[1]
    data = add_stock_data.get(key_data)
    menu = await menu_db.is_menu_exist(data['code'])
    if menu:
        try:
            await stocks_db.add_stock(data['code'], data['item'])
            await cb.message.edit(
                f"✅ 1 Stock {data['code']} ditambahkan."
            )
        except Exception as e:
            await cb.answer(str(e), show_alert=True)
    else:
        await cb.answer(
            "Kode produk tidak terdaftar di menu etalase.",
            show_alert=True
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
            if current_item == 0:
                return await cb.answer("Checkout setidaknya 1 item.", show_alert=True)
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
        stock = await stocks_db.get_stock(key_item)
        remain_stock = len(stock.get("stock", []))
        if total_item > remain_stock:
            if remain_stock == 0:
                return await cb.answer(f"Stock item kosong.", show_alert=True)
            return await cb.answer(f"Stock tidak mencukupi.", show_alert=True)
        if price > remaining_balance:
            return await cb.answer(f"Saldo anda tidak mencukupi.", show_alert=True)
        elif price <= remaining_balance:
            balance = remaining_balance - price
            await credit_db.add_balance(
                user_id,
                balance,
                random_string
            )
            for i in range(int(total_item)):
                item = stock.get("stock")[i]
                await b.send_message(
                    user_id,
                    f"**»»» DATA PESANAN {i+1} «««**\n\n{item}")
                await stocks_db.remove_item(key_item, item)
            list_admin = await sudo_user_db.get_all_sudo()
            await cb.message.edit(
                f"**»»» DETAIL PESANAN «««**\n\n• **Layanan:** {menu['name']}\n"
                f"• **ID Pembeli:** {user_id}\n• **Harga**: Rp{int(menu['price']):,}\n"
                f"• **Jumlah Item:** {total_item}x\n• **Total Bayar:** Rp{price:,}\n"
                f"• **Saldo Awal:** Rp{remaining_balance:,}\n• **Sisa Saldo:** Rp{balance:,}\n"
                f"• **Desc:** {menu['desc']}\n• **Stampel Waktu:** {datetime.now()}"
            )

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
                f"💰 **INFORMASI TOPUP PerlaPAY** 💰\n\n• **ID Pengguna:** {userdata.mention} (`{user_id}`)\n"
                f"• **Saldo Terakhir:** Rp{remaining}\n• **Nominal Topup:** Rp{nominal}\n\n"
                f"• **Saldo Terkini:** Rp{balance}\n• **ID Pembayaran:** `{random_string}`\n"
                f"• **Stampel Waktu:** `{datetime.now()}`"
            )
            await cb.message.edit(msg)
            await b.send_message(
                int(user_id),
                f"✅ **Permintaan TOPUP Saldo PerlaPAY anda telah disetujui.**\n\n"
                f"• **Nominal TOPUP:** Rp{nominal:,}\n• **Saldo Terkini:** Rp{balance:,}"
            )
        except Exception as e:
            await cb.answer(f"Error: {e}")
    else:
        await cb.answer("Hanya admin yang dapat melakukan tindakan ini.", show_alert=True)

@Client.on_callback_query(filters.regex(pattern=r"cls"))
async def close_btn(b, cb):
    await cb.message.delete()
    await cb.answer("Tugas dibatalkan.")
