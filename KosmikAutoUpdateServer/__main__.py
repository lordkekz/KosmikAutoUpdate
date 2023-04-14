import os

from version_manager import VersionManager
import waitress
import rest_api

# Parse env
rest_api.KEYS_PATH = os.path.abspath(os.environ["KOSMIK_KEYS_PATH"] if "KOSMIK_KEYS_PATH" in os.environ else "/keys.json")
rest_api.INDEX_PATH = os.path.abspath(os.environ["KOSMIK_INDEX_PATH"] if "KOSMIK_INDEX_PATH" in os.environ else "/index.db")
rest_api.DL_PATH = os.path.abspath(os.environ["KOSMIK_DL_PATH"] if "KOSMIK_DL_PATH" in os.environ else  "/dl/")
rest_api.DL_HOST = os.path.abspath(os.environ["KOSMIK_DL_HOST"] if "KOSMIK_DL_HOST" in os.environ else "http://0.0.0.0/")

print("Running waitress.serve...")
waitress.serve(rest_api.app)
print("Exiting...")
