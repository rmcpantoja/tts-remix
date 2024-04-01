import os
import sys
from .misc import audio_float_to_int16
_DIR = os.path.abspath(os.path.dirname(__file__))
_BASE_ROOT = os.path.abspath(os.path.join(_DIR, os.pardir, os.pardir))
_TTS_MODULE_DIR = os.path.join(_BASE_ROOT, "engines", "piper", "src", "python")
sys.path.insert(0, _TTS_MODULE_DIR)
import json
import torch
from phonemizer import phonemize
from phonemizer.backend import EspeakBackend
#sys.path.remove(_TTS_MODULE_DIR)
#del _DIR, _BASE_ROOT, _TTS_MODULE_DIR

class piper:
	def __init__(self, model_path):
		self.model_path = model_path
		self.config_path = None
		self.speaker_id = None
		self.length_scale = 1
		self.noise_scale = 0.667
		self.noise_w = 0.8
		self._BOS = "^"
		self._EOS = "$"
		self._PAD = "_"
		self.load_tts_model(self.model_path)

	def load_tts_model(self, checkpoint_path):
		if not checkpoint_path.endswith("_jit.pt"):
			self.model = torch.load(checkpoint_path)
		else:
			self.model = torch.jit.load(checkpoint_path)
		self.model.eval()
		self.config_path = checkpoint_path+".json"
		if not os.path.exists(self.config_path):
			raise FileNotFoundError(f"Config file {self.config_path} doesn't exists!")
		with open(self.config_path, "r", encoding="utf-8") as config_file:
			self.config_dict = json.load(config_file)
		self.backend = EspeakBackend(self.config_dict["espeak"]["voice"], preserve_punctuation=True, with_stress=True)

	def get_language(self):
		return self.config_dict["espeak"]["voice"]

	def set_rate(self, new_scale):
		self.length_scale = new_scale

	def set_noise_scale(self, new_scale):
		self.noise_scale = new_scale

	def set_noise_scale_w(self, new_scale):
		self.noise_w = new_scale

	def set_speaker(self, sid):
		self.speaker_id = sid

	def is_multispeaker(self):
		return self.config_dict["num_speakers"] > 1

	def list_speakers(self):
		if self.is_multispeaker():
			return self.config_dict.speaker_id_map
		else:
			raise Exception("This is not a multispeaker model!")

	def speak(self, text):
		if self.speaker_id is None and self.is_multispeaker():
			self.set_speaker(0)
		# Phonemize:
		phonemes_str = self.backend.phonemize([text], strip=True)[0]
		phonemes = [self._BOS] + list(phonemes_str)
		phoneme_ids: List[int] = []
		for phoneme in phonemes:
			if phoneme in self.config_dict["phoneme_id_map"]:
				phoneme_ids.extend(self.config_dict["phoneme_id_map"][phoneme])
				phoneme_ids.extend(self.config_dict["phoneme_id_map"][self._PAD])
			else:
				print(f"Skipping phoneme {phoneme}.")
		phoneme_ids.extend(self.config_dict["phoneme_id_map"][self._EOS])
		phoneme_tensor = torch.LongTensor(phoneme_ids).unsqueeze(0)
		phoneme_lengths = torch.LongTensor([len(phoneme_ids)])
		sid = torch.LongTensor([self.speaker_id]) if self.speaker_id is not None else None
		audio = (
			self.model(
				phoneme_tensor,
				phoneme_lengths,
				sid,
				torch.FloatTensor([self.noise_scale]),
				torch.FloatTensor([self.length_scale]),
				torch.FloatTensor([self.noise_w]),
			)[0]
			.detach()
			.numpy()
		)
		audio = audio.squeeze()
		audio = audio_float_to_int16(audio)
		return audio, self.config_dict["audio"]["sample_rate"]

# Testing:
#p = piper("../../models/piper/es_ES-orioltonoalto-medium/es_ES-orioltonoalto-medium.pt")
#audio, sr = p.speak("Soy Oriol gómez, el rey del bítstar.")
#sd.play(audio, sr, blocking=True)