from pyrogram import Client, filters
from src.database.products_db import menu_db
from src.database.stock_db import stocks_db
from src.modules.keyboard import button_builder, build_keyboard


@Client.on_message(filters.command("start"))
async def start(client, message):
    if len(message.command) == 2:
        if message.command[1] == "confirm_payment":
            confirm_btn = button_builder("⁉️ Konfirmasi", f"confirm_topup|input_data")
            button = build_keyboard([confirm_btn], row_width=1)
            return await message.reply(
                "**Klik konfirmasi untuk melanjutkan.**",
                reply_markup=button
            )
        item = await menu_db.get_menu(message.command[1])
        stock = await stocks_db.get_stock(message.command[1])
        stock_avail = len(stock.get("stock", []))
        min_btn = button_builder("-1 ««", f"order|item_min|-1|{item['key']}")
        total_item = button_builder("1x", f"p")
        plus_btn = button_builder("»» +1", f"order|item_plus|1|{item['key']}")
        checkout_btn = button_builder(f"Checkout Rp{int(item['price']):,}", f"order|checkout|1|{item['key']}")
        button = build_keyboard([min_btn, total_item, plus_btn, checkout_btn], row_width=3)
        msg = (
            f"**»»» CHECKOUT MENU «««**\n\n**🏷 {item['name']}**\n• **💵 Harga:** Rp{int(item['price']):,}\n• **📦 Stok Tersedia:** {stock_avail}\n"
            f"• **🆔 Kode:** `{item['key']}`\n• **📄 Desk:** __{item['desc']}__"
            "\n\n**Jumlah item:**"
        )
        await message.reply(msg, reply_markup=button)
