import sys
sys.path.append('engines/ForwardTacotron')
sys.path.append('engines/hifi-gan')
import os
from os.path import exists
import torch
import json
from typing import Tuple, Dict, Any, Union
from utils.checkpoints import init_tts_model
from utils.text.cleaners import Cleaner
from utils.text.tokenizer import Tokenizer
from models.fast_pitch import FastPitch
from models.forward_tacotron import ForwardTacotron
#from denoiser import Denoiser
from meldataset import MAX_WAV_VALUE
from hifimodels import Generator
from env import AttrDict
import numpy as np

class forward:
	def __init__(self, model_path):
		self.model_path = model_path
		self.model = None
		self.config = None
		self.cleaner = None
		self.tokenizer = Tokenizer()
		self.rate = 1
		self.pitch = 1.0
		self.energy = 1.0
		self.hifigan = None
		self.h = None
		#self.denoiser = None
		self.load_tts_model(self.model_path)
		self.get_hifigan(os.path.dirname(self.model_path), os.path.basename(self.model_path))

	def load_tts_model(self, checkpoint_path: str) -> Tuple[Union[ForwardTacotron, FastPitch], Dict[str, Any]]:
		if not checkpoint_path.endswith("_jit.pt"):
			checkpoint = torch.load(checkpoint_path, map_location=torch.device('cpu'))
			self.config = checkpoint['config']
			self.model = init_tts_model(self.config)
			self.model.load_state_dict(checkpoint['model'])
			self.model.eval()
			# Init also text processing tools:
			self.cleaner = Cleaner.from_config(self.config)
		else:
			self.model = torch.jit.load(checkpoint_path)
			_config_file = checkpoint_path+".json"
			with open(_config_file) as f:
				self.config = json.loads(f.read())
			self.cleaner = Cleaner('no_cleaners', True, self.config["language"])

	def get_hifigan(self, data_path, MODEL_NAME):
		hifigan_pretrained_model = os.path.join(data_path, 'vocoder_' + MODEL_NAME)
		if not exists(hifigan_pretrained_model):
			raise Exception(f"HiFI-GAN model {hifigan_pretrained_model} doesn't exists!")
		# Load HiFi-GAN
		if not MODEL_NAME.endswith("_jit.pt"):
			conf = hifigan_pretrained_model + ".json"
			with open(conf) as f:
				json_config = json.loads(f.read())
			self.h = AttrDict(json_config)
			torch.manual_seed(self.h.seed)
			self.hifigan = Generator(self.h).to(torch.device("cpu"))
			state_dict_g = torch.load(hifigan_pretrained_model, map_location=torch.device("cpu"))
			self.hifigan.load_state_dict(state_dict_g["generator"])
			self.hifigan.eval()
			self.hifigan.remove_weight_norm()
			#self.denoiser = Denoiser(self.hifigan, mode="normal")
		else:
			self.hifigan = torch.jit.load(hifigan_pretrained_model, map_location="cpu")

	def get_language(self):
		return self.config["preprocessing"]["language"]

	def set_rate(self, rate: float):
		self.rate = rate

	def set_pitch(self, pitch: float):
		self.pitch = pitch

	def set_energy(self, energy: float):
		self.energy = energy

	def speak(self, text):
		x = self.cleaner(text)
		x = self.tokenizer(x)
		x = torch.as_tensor(x, dtype=torch.long, device="cpu").unsqueeze(0)
		if hasattr(self.model, 'generate'):
			pitch_function = lambda x: x * self.pitch
			energy_function = lambda x: x*self.energy
			arguments = {
				'pitch_function': pitch_function,
				'energy_function': energy_function
			}
			gen_func = self.model.generate
		elif hasattr(self.model, 'generate_jit'):
			arguments = {
				'beta': self.pitch
			}
			gen_func = self.model.generate_jit
		else:
			return -1
		gen = gen_func(
			x=x,
			alpha=self.rate,
			**arguments
		)
		m = gen['mel_post'].cpu()
		#m = m.cpu()
		with torch.no_grad():
			y_g_hat = self.hifigan(m)
			audio = y_g_hat.squeeze()
			audio = audio * MAX_WAV_VALUE
			#audio_denoised = self.denoiser(audio.view(1, -1), strength=35)[:, 0]
			audio = audio.cpu().numpy().reshape(-1)
			normalize = (MAX_WAV_VALUE / np.max(np.abs(audio))) ** 0.9
			audio = audio * normalize
		return         audio.astype(np.int16), 22050