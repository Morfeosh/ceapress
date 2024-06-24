import discord
from discord.ext import commands, tasks
import requests
from bs4 import BeautifulSoup
import os
import json
import time
from datetime import datetime, timedelta
import asyncio
import logging

# Configurar el registro
logging.basicConfig(level=logging.INFO, format='%(asctime)s:%(levelname)s:%(name)s: %(message)s', handlers=[logging.FileHandler('bot_errors.txt'), logging.StreamHandler()])

# Cargar configuración desde config.json
with open('config.json', 'r') as config_file:
    config = json.load(config_file)

BOT_TOKEN = config['BOT_TOKEN']
CHANNEL_ID = config['CHANNEL_ID']

intents = discord.Intents.default()
intents.messages = True
bot = commands.Bot(command_prefix=':', intents=discord.Intents.all())

# Función para reiniciar el bot
async def reinicio():
    logging.info('Reiniciando el bot...')
    await bot.close()
    await asyncio.sleep(5)
    os.execv(sys.executable, ['python'] + sys.argv)

# Tiempo de inicio del bot
start_time = time.time()

@bot.event
async def on_ready():
    logging.info(f'Bot conectado como {bot.user}')
    await wait_until_10am()
    send_images_task.start()
    uptime_task.start()

@bot.event
async def on_disconnect():
    logging.info('Bot desconectado')
    logging.info(f'Tiempo transcurrido: {get_uptime()}')

@bot.command(name="hello", description="Saluda al bot")
async def hello(ctx):
    await ctx.send('Hello World!')

@bot.command(name='reinicio', help='Reinicia el bot.')
async def reinicio_command(ctx):
    await ctx.send('Reiniciando el bot...')
    await reinicio()

@bot.command(name='send_images', help='Envía imágenes al canal de texto.')
async def send_images_command(ctx):
    await send_images()

async def send_images():
    try:
        # Leer los nombres de las imágenes desde copias.txt
        with open('copias.txt', 'r') as file:
            image_names = [line.strip() for line in file.readlines()]

        # URL de la página web de donde queremos copiar las imágenes
        base_url = 'https://www.lasportadas.es/'  # Cambia esto a la URL correcta
        response = requests.get(base_url)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Buscar todas las imágenes en la página web
        images = soup.find_all('img')

        # Crear el directorio 'images' si no existe
        if not os.path.exists('images'):
            os.makedirs('images')

        for image in images:
            src = image.get('src')
            if src:
                # Si la URL de la imagen es relativa, agregar el esquema y dominio base
                if not src.startswith(('http://', 'https://')):
                    src = os.path.join(base_url, src.lstrip('/'))

                # Obtener el nombre de la imagen desde la URL
                image_name = os.path.basename(src)

                if image_name in image_names:
                    # Descargar la imagen
                    image_response = requests.get(src)
                    if image_response.status_code == 200:
                        image_path = f'images/{image_name}'
                        with open(image_path, 'wb') as img_file:
                            img_file.write(image_response.content)

                        # Enviar la imagen al canal de texto de Discord
                        channel = bot.get_channel(CHANNEL_ID)
                        await channel.send(file=discord.File(image_path))

                        # Eliminar la imagen después de enviarla
                        os.remove(image_path)
        logging.info('Imágenes enviadas con éxito')
    except Exception as e:
        logging.error(f'Error al enviar imágenes: {e}')

# Función para obtener el tiempo transcurrido
def get_uptime():
    uptime_seconds = int(time.time() - start_time)
    uptime_string = time.strftime("%H:%M:%S", time.gmtime(uptime_seconds))
    return uptime_string

# Función para esperar hasta las 10 AM
async def wait_until_10am():
    now = datetime.now()
    target_time = now.replace(hour=10, minute=0, second=0, microsecond=0)
    if now > target_time:
        target_time += timedelta(days=1)
    await asyncio.sleep((target_time - now).total_seconds())

# Tarea programada para enviar imágenes cada 24 horas
@tasks.loop(hours=24)
async def send_images_task():
    await send_images()

# Tarea programada para imprimir el tiempo transcurrido cada minuto
@tasks.loop(minutes=1)
async def uptime_task():
    logging.info(f'Tiempo transcurrido: {get_uptime()}')

bot.run(BOT_TOKEN)
