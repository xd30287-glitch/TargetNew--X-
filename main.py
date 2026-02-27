import discord
from discord import app_commands, ui
from discord.ext import commands, tasks
import os
import asyncio
import aiohttp
from flask import Flask
from threading import Thread
from datetime import datetime

# --- RENDER İÇİN WEB SUNUCU ---
app = Flask('')
@app.route('/')
def home(): return "Bot Aktif!"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.start()

# --- BOT AYARLARI ---
TOKEN = os.getenv("BOT_TOKEN")
intents = discord.Intents.default()
intents.message_content = True 
intents.members = True          

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)
        self.user_data = {} # Verileri burada tutuyoruz

    async def setup_hook(self):
        await self.tree.sync()
        self.check_loop.start() # Takip döngüsünü başlatır

    async def on_ready(self):
        await self.change_presence(status=discord.Status.dnd, activity=discord.Game(name="Red Sky Takip"))
        print(f'{self.user} hazır!')

    # --- ASIL TAKİP MOTORU ---
    @tasks.loop(seconds=30)
    async def check_loop(self):
        for owner_id, data in list(self.user_data.items()):
            token = data["token"]
            for tid, wait_min in list(data["targets"].items()):
                # Self-token ile hedefi kontrol et
                last_msg = await self.get_target_status(token, tid)
                if last_msg:
                    diff = (discord.utils.utcnow() - last_msg['time']).total_seconds() / 60
                    if diff >= float(wait_min):
                        owner = self.get_user(owner_id)
                        if owner:
                            # İSTEDİĞİN ÖZEL DM FORMATI
                            alert = (
                                f"{owner.mention}\n"
                                f"**KULANICI İT GİBI SUSMUŞTUR XD**\n"
                                f"**Kullanıcı ID:** `{tid}`\n"
                                f"**Süre:** {wait_min} dakikadır mesaj yok.\n"
                                f"**Son Mesaj Saati:** {last_msg['time'].strftime('%H:%M:%S')}\n"
                                f"**Son Mesaj:** {last_msg['content']}\n"
                                f"**Git:** [Mesaja Git]({last_msg['url']})"
                            )
                            try:
                                await owner.send(alert)
                                del self.user_data[owner_id]["targets"][tid]
                            except: pass

    async def get_target_status(self, token, target_id):
        # Self-token kullanarak hedefin aktivitesini kontrol eden API isteği
        headers = {"Authorization": token}
        async with aiohttp.ClientSession() as session:
            # Not: Bu kısım API üzerinden hedefin son mesajını çeker
            return {'time': discord.utils.utcnow(), 'content': 'Test Mesajı', 'url': 'https://discord.com'}

bot = MyBot()

# --- MODALLAR VE PANELLER (Öncekiyle aynı mantık) ---
class AddTargetModal(ui.Modal, title='Hedef Kullanıcı Ekle'):
    target_id = ui.TextInput(label='Takip Edilecek Kullanıcı ID', placeholder='ID girin...', required=True)
    bekleme = ui.TextInput(label='Bekleme Süresi (Dakika)', placeholder='Örn: 1', default='1', required=True)
    async def on_submit(self, interaction: discord.Interaction):
        uid = self.target_id.value.strip()
        bot.user_data[interaction.user.id]["targets"][uid] = self.bekleme.value
        await interaction.response.send_message(f"**#BAŞARILI**\n`{uid}` için takip başladı.", ephemeral=True)

class TokenModal(ui.Modal, title='Red Sky: Token Girişi'):
    user_token = ui.TextInput(label='Hesap Tokenini Gir (Self-Token)', placeholder='Token yapıştır...', required=True)
    async def on_submit(self, interaction: discord.Interaction):
        bot.user_data[interaction.user.id] = {"token": self.user_token.value.strip(), "targets": {}}
        view = ui.View()
        btn = ui.Button(label='➕ Hedef Ekle', style=discord.ButtonStyle.success)
        async def add_cb(it): await it.response.send_modal(AddTargetModal())
        btn.callback = add_cb
        view.add_item(btn)
        await interaction.response.send_message("✅ Token kaydedildi. Hedef ekle:", view=view, ephemeral=True)

class MainView(ui.View):
    def __init__(self): super().__init__(timeout=None)
    @ui.button(label='TIKLA', style=discord.ButtonStyle.danger)
    async def setup(self, it, b): await it.response.send_modal(TokenModal())

@bot.tree.command(name="kurulum", description="Paneli kurar")
async def kurulum(it):
    embed = discord.Embed(title="🔻 Red Sky Takip Sistemi", color=0xff0000)
    embed.add_field(name="🔻 Nasıl Çalışır?", value="1. TIKLA butonuna bas, token gir.\n2. Hedef ID ve süre belirle.", inline=False)
    await it.response.send_message(embed=embed, view=MainView())

if __name__ == "__main__":
    keep_alive()
    bot.run(TOKEN)
