from huggingface_hub import HfApi
api = HfApi()

# Upload all the content from the local folder to your remote Space.
# By default, files are uploaded at the root of the repo
api.upload_folder(
folder_path="/path/to/local/space",
repo_id="Oscar-ConvFinQ",
repo_type="model",
)
