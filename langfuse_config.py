from langfuse import Langfuse
from langfuse.callback import CallbackHandler

SECRET_KEY = "sk-lf-a65b23f9-0ffb-4063-8c09-5e1c265e9c4a"
PUBLIC_KEY = "pk-lf-c5d11bfe-392e-4ae1-ad90-aa4a8639965c"
host = "https://cloud.langfuse.com"

langfuse = Langfuse(
    secret_key=SECRET_KEY,
    public_key=PUBLIC_KEY,
    host=host
)

langfuse_handler = CallbackHandler(
    secret_key=SECRET_KEY,
    public_key=PUBLIC_KEY,
    host=host
)