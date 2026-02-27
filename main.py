import discord
from discord import app_commands, ui
from discord.ext import commands
import datetime
import asyncio
import os
from flask import Flask
from threading import Thread

# --- RENDER İÇİN WEB SUNUCU ---
app = Flask('')

@app.route('/')
def home():
    return "Bot Aktif!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- BOT AYARLARI ---
TOKEN = os.getenv("BOT_TOKEN")
intents = discord.Intents.default()
intents.message_content = True  #
intents.members = True          #

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()
        print(f"Slash komutları senkronize edildi: {self.user}")

    async def on_ready(self):
        # RAHATSIZ ETMEYİN MODU
        await self.change_presence(
            status=discord.Status.dnd, 
            activity=discord.Game(name="Red Sky Takip")
        )
        print(f'{self.user} hazır!')

bot = MyBot()
active_tasks = {}

# --- MODAL (FORM) ---
class TargetModal(ui.Modal, title='Red Sky Takip Sistemi'):
    target_id = ui.TextInput(label='Takip Edilecek Kullanıcı ID', placeholder='ID girin...', required=True)
    user_token = ui.TextInput(label='Hesap Tokenini Gir (Self-Token)', placeholder='Token yapıştır...', required=True)
    bekleme = ui.TextInput(label='Bekleme Süresi (Dakika)', placeholder='Örn: 5', default='5', required=True)

    async def on_submit(self, interaction: discord.Interaction):
        uid = self.target_id.value.strip()
        # Mesajı istediğin formata göre güncelledik
        success_msg = (
            f"**#TAKİP İŞLEMİ BAŞARI**\n"
            f"**HEDEF KULLANICI İD:** `{uid}`\n"
            f"**DURUM:** Kullanıcı sustuğunda sana DM üzerinden mesaj gönderilecek!"
        )
        await interaction.response.send_message(success_msg, ephemeral=True)

# --- PANEL GÖRÜNÜMÜ ---
class PersistentView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label='TIKLA', style=discord.ButtonStyle.danger, custom_id='setup_btn')
    async def setup_btn(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(TargetModal())

# --- KOMUTLAR ---
@bot.tree.command(name="kurulum", description="Giriş panelini kurar")
async def kurulum(interaction: discord.Interaction):
    # Çift mesaj sorununu çözmek için sadece tek bir embed gönderiyoruz
    embed = discord.Embed(title="🔻 Red Sky Takip Sistemi", color=0xff0000)
    embed.add_field(
        name="🔻 Nasıl Çalışır?", 
        value="Butona bas, ID gir, sustuğunda bot sana DM atsın!", 
        inline=False
    )
    # response.send_message kullanarak tek ve temiz bir panel oluşturuyoruz
    await interaction.response.send_message(embed=embed, view=PersistentView())

if __name__ == "__main__":
    keep_alive() #
    bot.run(TOKEN)
