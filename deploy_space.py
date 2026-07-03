#!/usr/bin/env python
"""
Deploy the Valence psych host to a Hugging Face Space. One command, run from
the repo root:

    python deploy_space.py

Needs a WRITE-scope HF token (the read token in backend/.env cannot create
repos). Provide it any of these ways, first hit wins:
    1. HF_WRITE_TOKEN env var (or add HF_WRITE_TOKEN=... to backend/.env)
    2. `hf auth login` (cached token)

The script:
    - creates the Space <username>/valence-psych-host (docker sdk) if missing
    - uploads hf-space/ (Dockerfile, app.py, README.md)
    - sets the SPECIALTY_REGISTRY_SECRET Space secret from backend/.env
    - prints the static URL to put in SPECIALTY_SPACE_URL (already the default)

Re-run any time you change hf-space/ — uploads trigger a rebuild.
"""

import os
import sys

from dotenv import dotenv_values
from huggingface_hub import HfApi, get_token

ROOT = os.path.dirname(os.path.abspath(__file__))
SPACE_NAME = "valence-psych-host"


def main() -> int:
    env = dotenv_values(os.path.join(ROOT, "backend", ".env"))

    token = os.getenv("HF_WRITE_TOKEN") or env.get("HF_WRITE_TOKEN") or get_token()
    if not token:
        print("No HF token found. Create a WRITE token at "
              "https://huggingface.co/settings/tokens and either:\n"
              "  - add HF_WRITE_TOKEN=hf_... to backend/.env, or\n"
              "  - run `hf auth login`")
        return 1

    api = HfApi(token=token)
    who = api.whoami()
    role = (who.get("auth", {}).get("accessToken", {}) or {}).get("role")
    if role == "read":
        print(f"Token for '{who['name']}' is READ-scope; a WRITE token is "
              "required to create/upload the Space.")
        return 1

    repo_id = f"{who['name']}/{SPACE_NAME}"
    print(f"Deploying to Space {repo_id} ...")

    api.create_repo(repo_id=repo_id, repo_type="space", space_sdk="docker",
                    private=False, exist_ok=True)
    api.upload_folder(folder_path=os.path.join(ROOT, "hf-space"),
                      repo_id=repo_id, repo_type="space")

    secret = env.get("SPECIALTY_REGISTRY_SECRET") or os.getenv("SPECIALTY_REGISTRY_SECRET")
    if secret:
        api.add_space_secret(repo_id=repo_id, key="SPECIALTY_REGISTRY_SECRET",
                             value=secret)
        print("Space secret SPECIALTY_REGISTRY_SECRET set.")
    else:
        print("WARNING: SPECIALTY_REGISTRY_SECRET not found in backend/.env — "
              "the Space will accept unauthenticated /infer calls.")

    url = f"https://{who['name']}-{SPACE_NAME}.hf.space"
    print(f"\nDone. First build takes a few minutes (watch: "
          f"https://huggingface.co/spaces/{repo_id})")
    print(f"Worker URL: {url}")
    print("Make sure backend/.env has:")
    print(f"  SPECIALTY_SPACE_URL={url}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
