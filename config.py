import os

from dotenv import load_dotenv
env_path = "C:\\Users\\vppla\\OneDrive\\Documents\\HackUTD\\DiscordBotFinal\\DISCORD_TOKEN.env"
load_dotenv(dotenv_path=env_path)

TOKEN = os.getenv("DISCORD_TOKEN")


DATA_DIR = "data"  


MAX_FILE_SIZE = 8 * 1024 * 1024


VISION_MODEL = "gemma4:12b"
EMBED_MODEL = "nomic-embed-text"

TAG_PROMPT = (
    "Describe this image using as many accurate keywords/tags as possible. "
    "Keep tags in basic english, avoid large words. "
    "Transcribe any text in the image as a tag. "
    "Do NOT include any text whatsoever outside the tags. "
    "Split tags with a ,"
)

DEFAULT_RESULTS = 3
MAX_RESULTS = 10  
SIMILARITY_THRESHOLD = 0.6  
SIMILAR_TAGS_PER_WORD = 5  
