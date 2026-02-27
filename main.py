import discord
from discord import ui, app_commands
import os
import asyncio
from flask import Flask
from threading import Thread
from datetime import datetime

# --- RENDER WEB SUNUCU ---
app = Flask('')
@app.route('/')
def home(): return "Bot Aktif!"

def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.start()

# --- AYARLAR ---
TOKEN = os.getenv("BOT_TOKEN") 
ALLOWED_CHANNEL_ID = 1476943347594563656 

active_tasks = {}

class TargetModal(ui.Modal, title='AuraNest Takip Sistemi'):
    target_id = ui.TextInput(label='Takip Edilecek Kullanıcı ID', placeholder='ID girin...')
    bekleme = ui.TextInput(label='Bekleme Süresi (Dakika)', placeholder='Örn: 5', default='5')

    async def on_submit(self, interaction: discord.Interaction):
        uid = self.target_id.value.strip()
        try:
            minutes = int(self.bekleme.value)
        except:
            return await interaction.response.send_message("Lütfen sayı girin!", ephemeral=True)
        
        # Sistemi çalıştıran kişinin ID'sini (interaction.user.id) kaydediyoruz
        active_tasks[uid] = {
            "vakit": discord.utils.utcnow(),
            "owner_id": interaction.user.id, 
            "süre": minutes,
            "icerik": "Henüz mesaj yok",
            "link": "",
            "bildirildi": False
        }
        await interaction.response.send_message(f"✅ `{uid}` için takip başladı! Sustuğunda sana DM atacağım.", ephemeral=True)

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
        print(f"Giriş Başarılı: {self.user}")
        self.loop.create_task(self.takip_dongusu())

    async def on_message(self, message):
        uid = str(message.author.id)
        if uid in active_tasks:
            active_tasks[uid]["vakit"] = discord.utils.utcnow()
            active_tasks[uid]["icerik"] = message.content or "(Görsel/Dosya)"
            active_tasks[uid]["link"] = message.jump_url
            active_tasks[uid]["bildirildi"] = False

    async def takip_dongusu(self):
        await self.wait_until_ready()
        while not self.is_closed():
            now = discord.utils.utcnow()
            for uid, data in list(active_tasks.items()):
                diff = (now - data["vakit"]).total_seconds()
                if diff >= (data["süre"] * 60) and not data["bildirildi"]:
                    # DM Gönderme İşlemi
                    try:
                        user = await self.fetch_user(data["owner_id"])
                        msg = (
                            f"**KULLANICI SUSMUŞTUR XD**\n"
                            f"**Kullanıcı ID:** `{uid}`\n"
                            f"**Süre:** {data['süre']} dakikadır mesaj yok.\n"
                            f"**Son Mesaj:** {data['icerik']}\n"
                            f"**Git:** [Mesaja Git]({data['link']})"
                        )
                        await user.send(msg)
                        data["bildirildi"] = True
                    except Exception as e:
                        print(f"DM Gönderilemedi: {e}")
            await asyncio.sleep(20)

bot = MyBot()

@bot.tree.command(name="kurulum", description="Giriş panelini kurar")
async def kurulum(interaction: discord.Interaction):
    embed = discord.Embed(title="⚡ AuraNest Takip Sistemi", color=0x2ecc71)
    embed.add_field(name="🚀 Nasıl Çalışır?", value="Butona bas, ID gir, sustuğunda bot sana DM atsın!", inline=False)
    await interaction.channel.send(embed=embed, view=PersistentView())
    await interaction.response.send_message("Panel kuruldu!", ephemeral=True)

if __name__ == "__main__":
    keep_alive()
    bot.run(TOKEN)
