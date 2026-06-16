"""Supabase client. Reads SUPABASE_URL / SUPABASE_KEY from .env (or the environment)."""

import os

from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv()

supabase: Client = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])
