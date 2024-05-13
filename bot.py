import discord
from discord.ext import commands
import asyncio
import colorama
import logging
import json
import requests
from bs4 import BeautifulSoup
import threading

# Configuración del logger
logging.basicConfig(filename='bot_errors.log', level=logging.ERROR, format='%(asctime)s - %(message)s')

# Cargar la configuración desde el archivo JSON
def load_config():
    try:
        with open("config.json", "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

# Guardar la configuración en el archivo JSON
def save_config(config):
    with open("config.json", "w") as file:
        json.dump(config, file, indent=4)

# Configuración inicial del bot
config = load_config()
TOKEN = config.get("token")  # Obtener el token del archivo de configuración

colorama.init()  # Inicializar colorama para habilitar los colores en la consola de Windows

intents = discord.Intents.all()

bot = commands.Bot(command_prefix='/', intents=intents)

def load_links():
    try:
        with open("links.txt", "r") as file:
            return [line.strip() for line in file.readlines()]
    except FileNotFoundError:
        return []

def save_links(links):
    with open("links.txt", "w") as file:
        for link in links:
            file.write(link + "\n")

def load_channel():
    try:
        with open("channel.txt", "r") as file:
            channel_id_str = file.readline().strip()
            if channel_id_str:
                return int(channel_id_str)
            else:
                return None
    except FileNotFoundError:
        return None

def save_channel(channel_id):
    with open("channel.txt", "w") as file:
        file.write(str(channel_id))

links = load_links()
channel_id = load_channel()

@bot.event
async def on_ready():
    print(f'Bot is ready. Logged in as {bot.user}')
    print_links()
    print_guilds_and_channels()  # Muestra los servidores y canales en los que está el bot
    await send_online_message()  # Envía el mensaje "Estoy Online"
    print_channel_info()  # Imprime información sobre el canal de publicación en cada servidor

async def send_online_message():
    online_message = "Estoy Online"
    for guild in bot.guilds:
        # Obtener el objeto del canal por su ID
        channel = guild.get_channel(531224707211722753)
        if channel:
            await channel.send(online_message)
            return

@bot.event
async def on_connect():
    print("Bot connected to the Discord gateway.")

@bot.event
async def on_disconnect():
    print("Bot disconnected from the Discord gateway.")

@bot.event
async def on_guild_join(guild):
    print(f"Joined guild: {guild.name}")

@bot.event
async def on_guild_remove(guild):
    print(f"Left guild: {guild.name}")

@bot.event
async def on_command_error(ctx, error):
    # Registrar el error en el archivo de registro
    logging.error(f'Error en el comando "{ctx.message.content}" - {error}')

# URL de la página de noticias de World of Warcraft
WOW_NEWS_URL = "https://worldofwarcraft.blizzard.com/es-es/news"

@bot.command()
async def wow_news(ctx):
    try:
        # URL de la página de noticias de World of Warcraft
        WOW_NEWS_URL = "https://worldofwarcraft.blizzard.com/es-es/news"

        # Realizar la solicitud GET a la página de noticias
        response = requests.get(WOW_NEWS_URL)
        response.raise_for_status()  # Lanzar una excepción si la solicitud no fue exitosa
        soup = BeautifulSoup(response.content, 'html.parser')

        # Buscar los elementos HTML que contienen las noticias
        news_items = soup.find_all('div', class_='NewsListing-newsListingRow-2-xyw')

        # Extraer el título y el enlace de cada noticia
        news_list = []
        for item in news_items:
            title_element = item.find('a', class_='NewsListing-newsTitle-3cGQA')
            link_element = item.find('a', class_='NewsListing-newsTitle-3cGQA')
            if title_element and link_element:
                title = title_element.text.strip()
                link = link_element['href']
                news_list.append(f"**{title}**: {WOW_NEWS_URL}{link}")

        # Enviar las noticias al canal de Discord
        await ctx.send("\n".join(news_list))

    except Exception as e:
        await ctx.send(f"Ocurrió un error al obtener las noticias: {e}")

@bot.command()
async def add_link(ctx, link: str):
    links.append(link)
    save_links(links)
    await ctx.send(f'Enlace añadido: {link}')
    print_links()

@bot.command()
async def set_channel(ctx, channel: discord.TextChannel):
    global channel_id
    channel_id = channel.id
    save_channel(channel_id)
    await ctx.send(f'Canal de publicación establecido en {channel.mention}')

@bot.command()
async def list_links(ctx):
    print_links()
    formatted_links = "\n".join([f"{i+1}. {link}" for i, link in enumerate(links)])
    await ctx.send(f'WEBS AÑADIDAS:\n{formatted_links}')

@bot.command(description="Comprueba si el bot está en línea.")
async def check_online(ctx):
    print("Comando check_online recibido.")
    if bot.is_ready():
        await ctx.send("El bot está en línea.")
    else:
        await ctx.send("El bot no está en línea.")

@bot.command(description="Obtiene una respuesta de Pong!")
async def bot_ping(ctx):
    await ctx.send("Pong!")

@bot.command()
async def prueba(ctx):
    try:
        # URL de la página de noticias de World of Warcraft
        WOW_NEWS_URL = "https://worldofwarcraft.blizzard.com/es-es/news"

        # Realizar la solicitud GET a la página de noticias
        response = requests.get(WOW_NEWS_URL)
        response.raise_for_status()  # Lanzar una excepción si la solicitud no fue exitosa
        soup = BeautifulSoup(response.content, 'html.parser')

        # Buscar los elementos HTML que contienen las noticias
        news_items = soup.find_all('div', class_='NewsListing-newsListingRow-2-xyw')

        # Lista para almacenar las últimas noticias
        latest_news = []

        # Iterar sobre las noticias y agregarlas a la lista
        for item in news_items:
            title_element = item.find('a', class_='NewsListing-newsTitle-3cGQA')
            link_element = item.find('a', class_='NewsListing-newsTitle-3cGQA')
            if title_element and link_element:
                title = title_element.text.strip()
                link = link_element['href']
                latest_news.append(f"**{title}**: {WOW_NEWS_URL}{link}")

        # Comprobar si hay noticias disponibles
        if latest_news:
            # Enviar las últimas noticias al canal de Discord
            await ctx.send("\n".join(latest_news))
        else:
            await ctx.send("No se encontraron noticias disponibles en este momento.")

    except Exception as e:
        await ctx.send(f"Ocurrió un error al obtener las últimas noticias: {e}")

async def start_bot():
    print("Iniciando el bot...")
    print(colorama.Fore.YELLOW + "WARNING  discord.ext.commands.bot Privileged message content intent is missing, commands may not work as expected.")
    print("INFO     discord.client logging in using static token")
    print("INFO     discord.gateway Shard ID None has connected to Gateway (Session ID: 0b33659ab8e15485ae9d996a31f93013)." + colorama.Style.RESET_ALL)
    # await bot.start('TOKEN')
    print("Bot iniciado correctamente.")

def print_links():
    if links:
        print(colorama.Fore.YELLOW + "WEBS AÑADIDAS:" + colorama.Style.RESET_ALL)
        for i, link in enumerate(links, start=1):
            print(colorama.Fore.LIGHTRED_EX + f"{i}. {link}" + colorama.Style.RESET_ALL)
    else:
        print(colorama.Fore.RED + "NO HAY ENLACES TRABAJANDO" + colorama.Style.RESET_ALL)

def print_guilds_and_channels():
    print("Servidores y canales:")
    for guild in bot.guilds:
        print(f"- Servidor: {guild.name}")
        print("  Información sobre los canales de publicación establecidos:")
        channel = guild.get_channel(channel_id)
        if channel:
            print(f"    Canal de publicación establecido en {channel.name}")



def print_channel_info():
    print("Información sobre los canales de publicación establecidos:")
    for guild in bot.guilds:
        channel = guild.get_channel(channel_id)
        if channel:
            print(f'Canal de publicación establecido en {channel.name} en el servidor {guild.name}')
        else:
            print(f'No se ha establecido un canal de publicación en el servidor {guild.name}')

async def accept_console_commands():
    print("Esperando comandos desde la consola...")
    while True:
        command = await asyncio.to_thread(input, "Ingrese un enlace para agregar al bot (o 'exit' para salir): ")
        print("Comando ingresado desde la consola:", command)  # Debug
        if command.lower() == 'exit':
            break
        else:
            links.append(command)
            save_links(links)
            print("Enlace añadido:", command)
            print_links()

async def main():
    print("Iniciando el bot...")
    tasks = [accept_console_commands(), start_bot()]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    # Comando para establecer el token del bot (solo para propósitos de configuración)
    @bot.command()
    async def set_token(ctx, token: str):
        config["token"] = token
        save_config(config)
        await ctx.send("Token configurado correctamente.")

    asyncio.run(main())

    # Ejecutar el bot con el token configurado
    bot.run(TOKEN)
