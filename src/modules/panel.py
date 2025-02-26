import datetime
import random
import string
from pyrogram import Client, filters
from src.database.products_db import menu_db
from src.database.credits_db import credit_db
from src.database.sudo_db import sudo_user_db
from src.database.stock_db import stocks_db
from src.modules.keyboard import button_builder, build_keyboard
from src.decorators import admins_only
from pyrogram.errors.pyromod.listener_timeout import ListenerTimeout
from pyrogram.errors.exceptions.bad_request_400 import MessageEmpty

add_menu_data = {}


@Client.on_message(filters.command("topup"))
@admins_only
async def add_saldo(client, message):
    replied = message.reply_to_message
    admin_id = message.from_user.id
    if replied.photo:
        file_id = replied.photo.file_id
        user_id = replied.from_user.id
        mention = replied.from_user.mention
        if len(message.command) == 2:
            nominal = int(message.command[1])
            get_balance = await credit_db.get_balance(user_id)
            remaining = get_balance.get("credits")
            remaining_balance = 0 if remaining is None else remaining
            yes_btn = button_builder("✅ Ya", f"topup|{admin_id}|{nominal}|{user_id}")
            close_btn = button_builder("❎ Tidak", f"cls")
            button = build_keyboard([yes_btn, close_btn], row_width=2)
            try:
                balance = nominal + remaining_balance
                msg = (
                    f"💰 **INFORMASI TOPUP** 💰\n\n• **ID Pengguna:** {mention} (`{user_id}`)\n"
                    f"• **Saldo Terakhir:** Rp{remaining}\n• **Nominal Topup:** Rp{nominal}\n\n"
                    "❓ **Apakah informasi tersebut benar?**"
                )
                await message.reply(msg, reply_markup=button)
            except ValueError:
                print("error")

@Client.on_message(filters.command("addstock"))
@admins_only
async def add_stock(client, message):
    chat = message.chat
    try:
        product_code = await chat.ask(
            text=(
                "📥 Masukkan **[KODE]** produk:\n⚠️ __Pastikan kode sama "
                "dengan yang terdaftar di menu etalase__"
            ),
            timeout=60
        )
        product_item = await chat.ask(
            text='📥 Masukkan **[1 STOCK]** produk:\n⚠️ __Masukkan produk satu per satu.',
            timeout=60
        )
        await stocks_db.add_stock(product_code.text, product_item.text)
        await message.reply("Selesai.")
    except ListenerTimeout:
        await message.reply(
            "😢 Oops! Waktu untuk mengisi menu berakhir, silahkan ulangi."
        )

@Client.on_message(filters.command("add"))
@admins_only
async def add_menu(client, message):
    chat = message.chat
    random_string = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(5))
    try:
        close_btn = button_builder("❎ Tidak", f"cls")
        yes_btn = button_builder("✅ Ya", f"addmenu|{random_string}")
        button = build_keyboard([yes_btn, close_btn], row_width=2)
        product_code = await chat.ask(text='ℹ️ Masukkan **[KODE]** produk:', timeout=60)
        product_name = await chat.ask(text='ℹ️ Masukkan **[NAMA]** produk:', timeout=60)
        product_price = await chat.ask(text='ℹ️ Masukkan **[HARGA]** produk:', timeout=60)
        int(product_price.text) + 1
        product_desc = await chat.ask(text='ℹ️ Masukkan **[DESKRIPSI]** produk:', timeout=60)
        add_menu_data.update(
            {
                random_string: {
                    "code": product_code.text,
                    "name": product_name.text,
                    "price": product_price.text,
                    "desc": product_desc.text
                }
            }
        )
        await message.reply(
            f"❓ Anda yakin ingin menambahkan produk **{product_name.text}** ke menu?",
            reply_markup=button
        )
    except ValueError:
        await message.reply(
            "Error: Harga harus berupa angka, contoh: 5000",
        )
    except IndexError:
        await message.reply(
            "**Example:** /add code|name|price"
        )
    except ListenerTimeout:
        await message.reply(
            "😢 Oops! Waktu untuk mengisi menu berakhir, silahkan ulangi."
        )

@Client.on_message(filters.command("delete"))
@admins_only
async def delete_menu(client, message):
    try:
        product_code = " ".join(message.command[1:])
        await menu_db.delete_menu(product_code)
        await message.reply(
            f"✅ [{product_code}] Produk dihapus dari menu!"
        )
    except IndexError:
        await message.reply(
            "**Example:** /delete code"
        )


@Client.on_message(filters.command("menu"))
@admins_only
async def menu(client, message):
    list_menu = []
    bot_info = await client.get_me()
    username = bot_info.username
    try:
        all_menu = await menu_db.get_all_menus()
        for item in all_menu:
            stock = await stocks_db.get_stock(item['key'])
            list_stock = stock.get("stock", [])
            url_product = f"http://t.me/{username}?start={item['key']}"
            list_menu.append(
                f"**🏷 {item['name']}**\n• **💵 Harga:** Rp{int(item['price']):,}\n• **📦 Stok Tersedia:** {len(list_stock)}\n"
                f"• **🆔 Kode:** [{item['key']}]({url_product})\n• **📄 Desk:** __{item['desc']}__"
            )
        await message.reply("\n\n".join(list_menu), disable_web_page_preview=True)
    except MessageEmpty:
        await message.reply("Menu etalase kosong!")

@Client.on_message(filters.command("promote"))
async def promote_user(client, message):
    if len(message.command) == 2:
        if message.command[1].startswith("@"):
            username = message.command[1].split("@")[1]
            userdata = await client.get_users(username)
            await sudo_user_db.add_sudo(userdata.id)
            await message.reply(f"{userdata.mention} Ditambahkan sebagai admin.")
