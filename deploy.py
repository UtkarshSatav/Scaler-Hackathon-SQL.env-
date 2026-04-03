"""Deploy SQL Env to Hugging Face Spaces."""
import os
import sys

token = os.environ.get("HF_TOKEN")
if not token:
    print("ERROR: Set HF_TOKEN first: export HF_TOKEN='hf_...'")
    sys.exit(1)

from huggingface_hub import HfApi, login

login(token=token)
api = HfApi()
user = api.whoami()
print(f"Logged in as: {user['name']}")

repo_id = f"{user['name']}/sql-env"

api.create_repo(repo_id, repo_type="space", space_sdk="docker", exist_ok=True)
print(f"Space created: {repo_id}")

api.upload_folder(
    folder_path=".",
    repo_id=repo_id,
    repo_type="space",
    ignore_patterns=[
        "__pycache__", "*.pyc", ".git", ".git/*",
        "test_results/*", "tests/*", "PHASE*.md",
        "*.egg-info", "deploy.py", "PROJECT_ARCHITECTURE.md",
    ],
)
print(f"Uploaded!")
print(f"URL: https://huggingface.co/spaces/{repo_id}")
