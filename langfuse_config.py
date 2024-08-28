import os
from langfuse import Langfuse
from langfuse.callback import CallbackHandler
import dotenv

dotenv.load_dotenv()

SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY")
PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY")
HOST = os.getenv("https://cloud.langfuse.com")

langfuse = Langfuse(secret_key=SECRET_KEY, public_key=PUBLIC_KEY, host=HOST)

langfuse_handler = CallbackHandler(
    secret_key=SECRET_KEY, public_key=PUBLIC_KEY, host=HOST
)
