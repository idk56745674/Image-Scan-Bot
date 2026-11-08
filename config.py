import os

from dotenv import load_dotenv

load_dotenv()

env_path = "C:\\Users\\vppla\\OneDrive\\Documents\\HackUTD\\DiscordBotFinal\\DISCORD_TOKEN.env"
load_dotenv(dotenv_path=env_path)
TOKEN = os.getenv("DISCORD_TOKEN")




DATA_DIR = "data"


MAX_FILE_SIZE = 8 * 1024 * 1024


MAX_IMAGE_SIZE = (1920, 1080)
JPEG_QUALITY = 90


VISION_MODEL = "gemma4:12b"
EMBED_MODEL = "nomic-embed-text"

TAG_PROMPT = (
    "Describe this image using as many accurate keywords/tags as possible. "
    "Focus on the main subject(s) in the image. "
    "Output tags as structured object-attribute pairs in the format [Attribute] [Object] (e.g., 'red car', 'wooden table'). For scene-wide attributes (e.g., 'sunny', 'vintage'), list them as individual tags"
    "Transcribe any text in the image as a tag. When transcribing text from the image, automatically delete any commas "
    "Do NOT include any text whatsoever outside the tags. "
    "Split tags with a ,"
)


DEFAULT_RESULTS = 3
MAX_RESULTS = 10
SIMILARITY_THRESHOLD = 0.6
SIMILAR_TAGS_PER_WORD = 5
