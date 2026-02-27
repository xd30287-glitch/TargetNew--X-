import discord
from discord import app_commands, ui
from discord.ext import commands
import os
from flask import Flask
from threading import Thread

# --- WEB SUNUCU ---
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
    async def setup_hook(self):
        await self.tree.sync()
    async def on_ready(self):
        await self.change_presence(status=discord.Status.dnd, activity=discord.Game(name="Red Sky Takip"))
        print(f'{self.user} hazır!')

bot = MyBot()

# --- VERİ DEPOLAMA (Çoklu Takip İçin) ---
# Format: { user_id: { "token": "...", "targets": { "target_id": "dakika", ... } } }
user_data = {}

# --- 2. AŞAMA: HEDEF EKLEME FORMU ---
class AddTargetModal(ui.Modal, title='Hedef Kullanıcı Ekle'):
    target_id = ui.TextInput(label='Takip Edilecek Kullanıcı ID', placeholder='ID girin...', required=True)
    bekleme = ui.TextInput(label='Bekleme Süresi (Dakika)', placeholder='Örn: 5', default='5', required=True)

    async def on_submit(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        tid = self.target_id.value.strip()
        
        # Kullanıcın listesine hedefi ekle
        user_data[user_id]["targets"][tid] = self.bekleme.value
        
        msg = f"**#BAŞARILI**\n`{tid}` ID'li kullanıcı {self.bekleme.value} dakika sustuğunda bildirim alacaksın."
        await interaction.response.send_message(msg, ephemeral=True)

# --- 1. AŞAMA: TOKEN GİRİŞ FORMU ---
class TokenModal(ui.Modal, title='Red Sky: Token Girişi'):
    user_token = ui.TextInput(label='Hesap Tokenini Gir (Self-Token)', placeholder='Token yapıştır...', style=discord.TextStyle.short, required=True)

    async def on_submit(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        # Kullanıcı verisini oluştur veya güncelle
        if user_id not in user_data:
            user_data[user_id] = {"token": self.user_token.value.strip(), "targets": {}}
        else:
            user_data[user_id]["token"] = self.user_token.value.strip()
            
        # Token alındı, şimdi hedef ekleme butonlarının olduğu bir mesaj gönder
        view = ControlView()
        await interaction.response.send_message("✅ Token kaydedildi. Aşağıdaki butondan hedef ekleyebilir veya listenizi yönetebilirsiniz.", view=view, ephemeral=True)

# --- KONTROL PANELİ (DÜZENLEME VE EKLEME) ---
class ControlView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label='➕ Hedef Ekle', style=discord.ButtonStyle.success)
    async def add_btn(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(AddTargetModal())

    @ui.button(label='📋 Takip Listem', style=discord.ButtonStyle.secondary)
    async def list_btn(self, interaction: discord.Interaction, button: ui.Button):
        user_id = interaction.user.id
        targets = user_data.get(user_id, {}).get("targets", {})
        
        if not targets:
            return await interaction.response.send_message("Henüz kimseyi takip etmiyorsun.", ephemeral=True)
        
        list_msg = "**Takip Listen:**\n"
        for tid, min in targets.items():
            list_msg += f"• ID: `{tid}` | Süre: {min} dk\n"
        
        await interaction.response.send_message(list_msg, ephemeral=True)

# --- ANA PANEL ---
class MainView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label='TIKLA', style=discord.ButtonStyle.danger, custom_id='main_setup_btn')
    async def setup_btn(self, interaction: discord.Interaction, button: ui.Button):
        # Önce Token isteyen modalı aç
        await interaction.response.send_modal(TokenModal())

@bot.tree.command(name="kurulum", description="Giriş panelini kurar")
async def kurulum(interaction: discord.Interaction):
    embed = discord.Embed(title="🔻 Red Sky Takip Sistemi", color=0xff0000)
    embed.add_field(name="🔻 Nasıl Çalışır?", value="1. TIKLA butonuna basıp tokenini gir.\n2. Ardından hedef kullanıcılarını ekle.", inline=False)
    # Sadece tek bir ana panel mesajı
    await interaction.response.send_message(embed=embed, view=MainView())

if __name__ == "__main__":
    keep_alive() 
    bot.run(TOKEN)
