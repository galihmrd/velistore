import datetime
import random
import string
from pyrogram import Client, filters
from pyrogram.enums import ChatType
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from src.database.products_db import menu_db
from src.database.credits_db import credit_db
from src.database.sudo_db import sudo_user_db
from src.database.stock_db import stocks_db
from src.modules.keyboard import button_builder, build_keyboard
from src.decorators import admins_only
from pyrogram.errors.pyromod.listener_timeout import ListenerTimeout
from pyrogram.errors.exceptions.bad_request_400 import MessageEmpty

add_menu_data = {}
add_stock_data = {}


@Client.on_message(filters.command("saldo"))
async def cek_saldo(client, message):
    user = message.from_user
    get_balance = await credit_db.get_balance(user.id)
    remaining = get_balance.get("credits")
    check_time = datetime.datetime.now()
    remaining_balance = 0 if remaining is None else remaining
    try:
        caption = (
            f"💰 **INFORMASI SALDO PerlaPAY** 💰\n\n• **ID:** {user.mention} (`{user.id}`)\n"
            f"• **Saldo Terkini:** Rp{remaining_balance}\n• **Stampel Waktu:** `{check_time}`"
        )
        await message.reply(caption)
    except Exception as e:
        await message.reply(f"Error: {e}")

@Client.on_message(filters.command("topup"))
async def add_saldo(client, message):
    file_id = "./qris.jpg"
    if message.chat.type == ChatType.PRIVATE:
        confirm_btn = button_builder("⁉️ Konfirmasi", f"confirm_topup|input_data")
        button = build_keyboard([confirm_btn], row_width=1)
    else:
        bot = await client.get_me()
        button = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("⁉️ Konfirmasi", url=f"https://t.me/{bot.username}?start=confirm_payment"),
                ],
            ],
        )
    await message.reply_photo(
        file_id,
        caption=(
            "**1. Scan QRIS diatas\n2. Masukkan nominal TOPUP\n"
            "3. Screenshot bukti transfer\n4. Lalu klik konfirmasi untuk melanjutkan.**"
        ),
        reply_markup=button
    )

@Client.on_message(filters.command("addstock"))
@admins_only
async def add_stock(client, message):
    chat = message.chat
    try:
        random_string = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(5))
        close_btn = button_builder("❎ Tidak", f"cls")
        yes_btn = button_builder("✅ Ya", f"restock|{random_string}")
        button = build_keyboard([yes_btn, close_btn], row_width=2)
        product_code = await chat.ask(
            text=(
                "📥 Masukkan **[KODE]** produk:\n⚠️ __Pastikan kode sama "
                "dengan yang terdaftar di menu etalase__"
            ),
            timeout=240
        )
        product_item = await chat.ask(
            text='📥 Masukkan **[1 STOCK]** produk:\n⚠️ __Masukkan produk satu per satu.',
            timeout=240
        )
        add_stock_data.update(
            {
                random_string: {
                    "code": product_code.text.lower(),
                    "item": product_item.text,
                }
            }
        )
        await message.reply(
            f"❓ Apakah anda yakin data tersebut benar?",
            reply_markup=button
        )
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
        product_code = await chat.ask(text='ℹ️ Masukkan **[KODE]** produk:', timeout=240)
        product_name = await chat.ask(text='ℹ️ Masukkan **[NAMA]** produk:', timeout=240)
        product_price = await chat.ask(text='ℹ️ Masukkan **[HARGA]** produk:', timeout=240)
        int(product_price.text) + 1
        product_desc = await chat.ask(text='ℹ️ Masukkan **[DESKRIPSI]** produk:', timeout=240)
        add_menu_data.update(
            {
                random_string: {
                    "code": product_code.text.lower(),
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
        await menu_db.delete_menu(product_code.lower())
        await stocks_db.delete_stock(product_code.lower())
        await message.reply(
            f"✅ [{product_code}] Produk dihapus dari menu!"
        )
    except IndexError:
        await message.reply(
            "**Example:** /delete code"
        )


@Client.on_message(filters.command("menu"))
async def menu(client, message):
    list_menu = []
    bot_info = await client.get_me()
    username = bot_info.username
    user_id = message.from_user.id
    try:
        next_btn = button_builder("Berikutnya ➡️", f"showmenu|next|5|{user_id}")
        button = build_keyboard([next_btn], row_width=1)
        caption = "**»»» PERLA BOT STORE «««**\n\n"
        all_menu = await menu_db.get_all_menus()
        i = 0
        for item in all_menu:
            i = i + 1
            stock = await stocks_db.get_stock(item['key'])
            list_stock = stock.get("stock", [])
            url_product = f"http://t.me/{username}?start={item['key']}"
            list_menu.append(
                f"**🏷 {item['name']}**\n• **💵 Harga:** Rp{int(item['price']):,}\n• **📦 Stok Tersedia:** {len(list_stock)}\n"
                f"• **🆔 Kode:** `{item['key']}` | [Beli]({url_product})\n• **📄 Desk:** __{item['desc']}__"
            )
            if i == 5:
                break
        await message.reply(caption + "\n\n".join(list_menu), reply_markup=button, disable_web_page_preview=True)
    except MessageEmpty:
        await message.reply("Menu etalase kosong!")

@Client.on_message(filters.command("promote"))
@admins_only
async def promote_user(client, message):
    if len(message.command) == 2:
        if message.command[1].startswith("@"):
            username = message.command[1].split("@")[1]
            userdata = await client.get_users(username)
            await sudo_user_db.add_sudo(userdata.id)
            await message.reply(f"{userdata.mention} Ditambahkan sebagai admin.")
