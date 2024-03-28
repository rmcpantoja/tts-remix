import json
import os

def read_config():
	if os.path.exists("config.json"):
		with open("config.json", "r", encoding="utf-8") as config:
			base = config.read()
		settings = json.loads(base)
	else:
		# first time:
		settings = {
			"autoplay": True,
			"models_path": os.path.join(os.getcwd(), "models"),
			"extra_silence": True
		}
		write_config(settings)
	return settings

def write_config(cfg):
	with open("config.json", "w", encoding="utf-8") as config:
		json.dump(cfg, config, indent=4)