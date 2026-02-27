import discord
from discord import ui, app_commands
import os
import asyncio
import aiohttp
from flask import Flask
from threading import Thread

# Render'da 7/24 açık kalması için gereken ufak sunucu
app = Flask('')
@app.route('/')
def home(): return "Bot Aktif!"

def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.start()

# --- AYARLAR (Render Environment'dan çekilir) ---
TOKEN = os.getenv("BOT_TOKEN") 
ALLOWED_CHANNEL_ID = 1476943347594563656 # Mesajın atılacağı kanal

active_tasks = {}

# --- MODAL (FORM) ---
class TargetModal(ui.Modal, title='AuraNest Takip Sistemi'):
    target_id = ui.TextInput(label='Takip Edilecek Kullanıcı ID', placeholder='ID girin...')
    bekleme = ui.TextInput(label='Bekleme Süresi (Dakika)', placeholder='Örn: 5', default='5')
    webhook = ui.TextInput(label='Webhook URL', placeholder='https://discord.com/...')

    async def on_submit(self, interaction: discord.Interaction):
        uid = self.target_id.value.strip()
        active_tasks[uid] = {
            "vakit": discord.utils.utcnow(),
            "webhook": self.webhook.value,
            "süre": int(self.bekleme.value),
            "bildirildi": False
        }
        await interaction.response.send_message(f"✅ `{uid}` için takip başladı!", ephemeral=True)

# --- BUTON ---
class PersistentView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label='Tokenlerini Sokk .xd', style=discord.ButtonStyle.danger, custom_id='setup_btn')
    async def setup_btn(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(TargetModal())

class MyBot(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.all())
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        self.add_view(PersistentView())
        await self.tree.sync()

    async def on_ready(self):
        print(f"{self.user} hazır!")
        self.loop.create_task(self.takip_dongusu())

    async def on_message(self, message):
        uid = str(message.author.id)
        if uid in active_tasks:
            active_tasks[uid]["vakit"] = discord.utils.utcnow()
            active_tasks[uid]["bildirildi"] = False

    async def takip_dongusu(self):
        await self.wait_until_ready()
        while not self.is_closed():
            now = discord.utils.utcnow()
            for uid, data in list(active_tasks.items()):
                diff = (now - data["vakit"]).total_seconds()
                if diff >= (data["süre"] * 60) and not data["bildirildi"]:
                    msg = f"**KULLANICI SUSMUŞTUR XD**\n**ID:** `{uid}`\n**Süre:** {data['süre']} dk."
                    async with aiohttp.ClientSession() as session:
                        await session.post(data["webhook"], json={"content": msg})
                    data["bildirildi"] = True
            await asyncio.sleep(20)

bot = MyBot()

@bot.tree.command(name="kurulum", description="Giriş panelini kurar")
async def kurulum(interaction: discord.Interaction):
    embed = discord.Embed(title="⚡ Nasıl Çalışır?", color=0x2ecc71, description="* **Formu doldurun** ve tokenlerinizi girin\n* Sistem otomatik işlemleri başlatır")
    embed.add_field(name="💠 Neler Gerekiyor?", value="* Botu Sunucuya Ekle!\n* Sunucu ID ve **Tokenler** bilgisi", inline=False)
    embed.add_field(name="🛡️ Güvenlik", value=">> Veriler **güvenli işlenir**\n>> Paylaşılmaz", inline=False)
    embed.set_image(url="https://i.imgur.com/your_banner_link.png") # Kendi görsel linkini koyabilirsin
    await interaction.channel.send(embed=embed, view=PersistentView())
    await interaction.response.send_message("Panel kuruldu!", ephemeral=True)

if __name__ == "__main__":
    keep_alive()
    bot.run(TOKEN)
