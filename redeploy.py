"""Re-deploy updated files to HF Space."""
import os, sys
token = os.environ.get("HF_TOKEN")
if not token:
    print("ERROR: Set HF_TOKEN first")
    sys.exit(1)

from huggingface_hub import HfApi, login
login(token=token)
api = HfApi()
print(f"Logged in as: {api.whoami()['name']}")

api.upload_folder(
    folder_path=".",
    repo_id="UtkarshSatav/sql-env",
    repo_type="space",
    ignore_patterns=[
        "__pycache__", "*.pyc", ".git", ".git/*",
        "test_results/*", "tests/*", "PHASE*.md",
        "*.egg-info", "deploy.py", "redeploy.py",
        "PROJECT_ARCHITECTURE.md",
    ],
)
print("Re-deployed! Space will rebuild.")
print("URL: https://huggingface.co/spaces/UtkarshSatav/sql-env")
