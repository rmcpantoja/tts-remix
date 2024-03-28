# Model manager
# By rmcpantoja
import os
import json

class manager:
	def __init__(self, hnd: str = "models.json") -> None:
		self.hnd = hnd
		self.info = None
		self.available_models = None
		if not os.path.exists(self.hnd):
			raise FileNotFoundError(f"File '{self.hnd}' is not found.")
		else:
			with open(self.hnd, "r") as f:
				data = f.read()
			self.info = json.loads(data)

	def list_models(self) -> list[str]:
		return list(self.info.keys())

	def get_model_properties(self, model: str) -> dict:
		return self.info[model]

	def get_available_controls(self, model: str) -> list[str]:
		controls = self.info[model]["controls"]
		available_controls = []
		for control, available in controls.items():
			if available:
				available_controls.append(control)
		return available_controls

	def detect_models(self, path: str) -> dict[str, list[str]]:
		model_dict = {}
		for model_name, properties in self.info.items():
			model_folder = os.path.join(path, properties["id"])
			if os.path.exists(model_folder):
				model_paths = []
				for root, dirs, files in os.walk(model_folder):
					pt_files = [f for f in files if f.endswith(".pt") and not f.startswith("vocoder")]
					model_paths.extend([os.path.join(root, f) for f in pt_files])
				if len(model_paths) == 0:
					model_dict[model_name] = ["Empty folder, please add models"]
				else:
					model_dict[model_name] = model_paths
		return model_dict

#m = manager("../models.json")
#list = m.list_models()
#print(list)
#voices = m.detect_models(os.getcwd()+"/../models")
#print(voices)