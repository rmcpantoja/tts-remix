import os
import wx
from playsound import playsound
playsound("sounds/open.wav", block=False)
#from cytolk import tolk
#tolk.load()
#tolk.speak("Loading, please wait...")
from include import config, Model_manager
from include.tts_models.ft_tts import forward
import string
from include.tts_models.piper_tts import piper
ttsmix_models = Model_manager.manager()
import sounddevice as sd
import soundfile as sf
import threading 
import numpy as np
from typing import Optional
import webbrowser

version = "0.1a1"
config = config.read_config()

class MyApp(wx.App):
	def OnInit(self):
		self.frame = MyFrame(None, title=f"TTS remix {version}")
		#self.SetTopWindow(self.frame)
		self.frame.Maximize()
		self.frame.Show(True)
		return True

class MyFrame(wx.Frame):
	def __init__(self, *args, **kwargs):
		super(MyFrame, self).__init__(*args, **kwargs)
		self.tts = None
		self.tts_thread = None
		self.audio = None
		self.models = ttsmix_models.list_models()
		self.model_list = ttsmix_models.detect_models(config["models_path"])
		self.selected_model = None
		self.current_voices = None
		self.voice_names = []
		self.available_controls = None
		# UI:
		panel = wx.Panel(self)
		vbox = wx.BoxSizer(wx.VERTICAL)
		menubar = wx.MenuBar()
		voices_menu = wx.Menu()
		download_voice = voices_menu.Append(wx.ID_ANY, "Download voices")
		install_voice = voices_menu.Append(wx.ID_ANY, "Install a voice locally")
		menubar.Append(voices_menu, "Voices")
		help_menu = wx.Menu()
		user_manual = help_menu.Append(wx.ID_ANY, "User manual")
		error_reporting = help_menu.Append(wx.ID_ANY, "Errors and suggestions")
		self.Bind(wx.EVT_MENU, self.on_error_reporting, error_reporting)
		error_reporting_gh = help_menu.Append(wx.ID_ANY, "Errors and suggestions (gitHub)")
		self.Bind(wx.EVT_MENU, self.on_error_reporting_gh, error_reporting_gh)
		website = help_menu.Append(wx.ID_ANY, "&Visit website")
		self.Bind(wx.EVT_MENU, self.on_website, website)
		about = help_menu.Append(wx.ID_ANY, "About")
		self.Bind(wx.EVT_MENU, self.on_about, about)
		menubar.Append(help_menu, "Help")
		self.SetMenuBar(menubar)
		# Model selection group
		model_group = wx.StaticBox(panel, label="Model/voice Selection")
		model_sizer = wx.StaticBoxSizer(model_group, wx.VERTICAL)
		model_label = wx.StaticText(panel, label="model:")
		model_sizer.Add(model_label, 0, wx.ALL, 5)
		self.model_combobox = wx.Choice(panel, wx.ID_ANY, choices=self.models)
		self.model_combobox.SetSelection(0)
		self.model_combobox.Bind(wx.EVT_CHOICE, self.process_voice_models)
		model_sizer.Add(self.model_combobox, 0, wx.ALL | wx.EXPAND, 5)
		# Voice stuff:
		voice_label = wx.StaticText(panel, label="Select voice:")
		model_sizer.Add(voice_label, 0, wx.ALL, 5)
		self.voice_combobox = wx.Choice(panel, wx.ID_ANY, choices=self.voice_names)
		model_sizer.Add(self.voice_combobox, 0, wx.ALL | wx.EXPAND, 5)
		load_button = wx.Button(panel, label="Load")
		load_button.Bind(wx.EVT_BUTTON, self.on_load_model)
		model_sizer.Add(load_button, 0, wx.ALL | wx.EXPAND, 5)
		vbox.Add(model_sizer, 0, wx.ALL | wx.EXPAND, 10)
		# Generation group
		generation_group = wx.StaticBox(panel, label="Synthesis")
		generation_sizer = wx.StaticBoxSizer(generation_group, wx.VERTICAL)
		text_label = wx.StaticText(panel, label="Text:")
		generation_sizer.Add(text_label, 0, wx.ALL, 5)
		self.text_ctrl = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_PROCESS_ENTER)
		self.text_ctrl.Bind(wx.EVT_KEY_DOWN, self.on_text_key_down)
		generation_sizer.Add(self.text_ctrl, 1, wx.ALL | wx.EXPAND, 5)
		self.rate_label = wx.StaticText(panel, label="Rate:")
		generation_sizer.Add(self.rate_label, 0, wx.ALL, 5)
		self.rate_slider = wx.Slider(panel, wx.ID_ANY, 50, 0, 100, style=wx.SL_HORIZONTAL)
		self.rate_slider.Bind(wx.EVT_SLIDER, self.on_rate)
		generation_sizer.Add(self.rate_slider, 0, wx.ALL | wx.EXPAND, 5)
		self.noise_label = wx.StaticText(panel, label="Noise scale:")
		generation_sizer.Add(self.noise_label, 0, wx.ALL, 5)
		self.noise_slider = wx.Slider(panel, wx.ID_ANY, 50, 0, 100, style=wx.SL_HORIZONTAL)
		self.noise_slider.Bind(wx.EVT_SLIDER, self.on_scale1)
		generation_sizer.Add(self.noise_slider, 0, wx.ALL | wx.EXPAND, 5)
		self.noise_w_label = wx.StaticText(panel, label="Phoneme stressing scale:")
		generation_sizer.Add(self.noise_w_label, 0, wx.ALL, 5)
		self.noise_w_slider = wx.Slider(panel, wx.ID_ANY, 50, 0, 100, style=wx.SL_HORIZONTAL)
		self.noise_w_slider.Bind(wx.EVT_SLIDER, self.on_scale2)
		generation_sizer.Add(self.noise_w_slider, 0, wx.ALL | wx.EXPAND, 5)
		self.pitch_label = wx.StaticText(panel, label="Pitch:")
		generation_sizer.Add(self.pitch_label, 0, wx.ALL, 5)
		self.pitch_slider = wx.Slider(panel, wx.ID_ANY, 50, 0, 100, style=wx.SL_HORIZONTAL)
		self.pitch_slider.Bind(wx.EVT_SLIDER, self.on_pitch)
		generation_sizer.Add(self.pitch_slider, 0, wx.ALL | wx.EXPAND, 5)
		self.energy_label = wx.StaticText(panel, label="Energy:")
		generation_sizer.Add(self.energy_label, 0, wx.ALL, 5)
		self.energy_slider = wx.Slider(panel, wx.ID_ANY, 50, 0, 100, style=wx.SL_HORIZONTAL)
		self.energy_slider.Bind(wx.EVT_SLIDER, self.on_energy)
		generation_sizer.Add(self.energy_slider, 0, wx.ALL | wx.EXPAND, 5)
		generate_button = wx.Button(panel, label="&Synthesize")
		generate_button.Bind(wx.EVT_BUTTON, self.on_generate)
		generate_button.SetDefault()
		generation_sizer.Add(generate_button, 0, wx.ALL | wx.EXPAND, 5)
		vbox.Add(generation_sizer, 0, wx.ALL | wx.EXPAND, 10)
		audio_group = wx.StaticBox(panel, label="Audio Controls")
		audio_sizer = wx.StaticBoxSizer(audio_group, wx.HORIZONTAL)
		self.play_button = wx.Button(panel, label="&Replay")
		self.play_button.Bind(wx.EVT_BUTTON, self.on_play)
		audio_sizer.Add(self.play_button, 0, wx.ALL | wx.EXPAND, 5)
		self.pause_button = wx.Button(panel, label="&Pause")
		self.pause_button.Bind(wx.EVT_BUTTON, self.on_pause)
		audio_sizer.Add(self.pause_button, 0, wx.ALL | wx.EXPAND, 5)
		self.save_button = wx.Button(panel, label="Save to &audio")
		self.save_button.Bind(wx.EVT_BUTTON, self.on_save_audio)
		audio_sizer.Add(self.save_button, 0, wx.ALL | wx.EXPAND, 5)
		vbox.Add(audio_sizer, 0, wx.ALL | wx.EXPAND, 10)
		panel.SetSizer(vbox)
		# Process models at first:
		self.process_voice_models()
		# Apply prosody controls:
		self.apply_prosody_controls()
		# Disable play-pause by default:
		self.play_button.Disable()
		self.pause_button.Disable()
		# Load TTS model
		if self.current_voices:
			self.load_tts_model(self.model_propperties["id"], self.voice_names[0])
			self.voice_combobox.SetSelection(0)

	def process_voice_models(self, event: Optional[wx.Event] = None):
		self.voice_combobox.Clear()
		self.selected_model = self.model_combobox.GetStringSelection()
		self.model_propperties = ttsmix_models.get_model_properties(self.selected_model)
		try:
			self.current_voices = self.model_list[self.selected_model]
			self.voice_names = [os.path.splitext(os.path.basename(filename))[0] for filename in self.current_voices]
		except KeyError:
			self.current_voices = None
			self.voice_names = ["No voices available for this model."]
		self.voice_combobox.AppendItems(self.voice_names)
		self.voice_combobox.SetSelection(0)

	def apply_prosody_controls(self):
		self.available_controls = ttsmix_models.get_available_controls(self.selected_model)
		self.rate_label.Enable("rate" in self.available_controls)
		self.rate_slider.Enable("rate" in self.available_controls)
		self.noise_label.Enable("scale1" in self.available_controls)
		self.noise_slider.Enable("scale1" in self.available_controls)
		self.noise_w_label.Enable("scale2" in self.available_controls)
		self.noise_w_slider.Enable("scale2" in self.available_controls)
		self.pitch_label.Enable("pitch" in self.available_controls)
		self.pitch_slider.Enable("pitch" in self.available_controls)
		self.energy_label.Enable("energy" in self.available_controls)
		self.energy_slider.Enable("energy" in self.available_controls)

	def load_tts_model(self, tts_func_name, model_name):
		try:
			tts_module = globals().get(tts_func_name)
		except AttributeError:
			return -1
		# Try to load the voice model and initializae phonemizer correctly.
		try:
			#tolk.speak(f"loading voice {model_name}...")
			self.tts= tts_module(f'{config["models_path"]}/{self.model_propperties["id"]}/{model_name}/{model_name}.pt')
		except RuntimeError:
			print("Seems espeak is not installed. Trying to setup the variable...")
			os.environ["PHONEMIZER_ESPEAK_LIBRARY"] = "C:/Program Files/eSpeak NG/libespeak-ng.dll"
			# Try again:
			#tolk.speak(f"Couldn't find espeak-ng but we set it up. So, trying to load voice {model_name} again...")
			self.tts= tts_module(f'{config["models_path"]}/{self.model_propperties["id"]}/{model_name}/{model_name}.pt')
		#tolk.speak(f"Voice {model_name} loaded!")
		self.apply_prosody_controls()

	def on_error_reporting(self, event):
		webbrowser.open("https://docs.google.com/forms/d/e/1FAIpQLSdDW6LqMKGHjUdKmHkAZdAlgSDilHaWQG9VZjwLz0CJSXKqHA/viewform?usp=sf_link")

	def on_error_reporting_gh(self, event):
		webbrowser.open("https://github.com/rmcpantoja/tts-remix/issues/new")

	def on_website(self, event):
		webbrowser.open("http://mateocedillo.260mb.net")

	def on_about(self, event):
		wx.MessageBox(
			"An easy way to use various Text-To-Speech torch models in one, alternative to C++ TensorBox but more accessible for screen reader users.\nThis program has been developed by Mateo Cedillo.",
			"About",
			wx.ICON_INFORMATION
		)

	def on_load_model(self, event):
		selected_model = self.voice_combobox.GetStringSelection()
		if not selected_model == "No voices available for this model.":
			self.load_tts_model(self.model_propperties["id"], selected_model)

	# Prosody controls:
	def on_rate(self, event):
		self.tts.set_rate(self.rate_slider.GetValue()/50.0)

	def on_scale1(self, event):
		self.tts.set_noise_scale(self.noise_slider.GetValue()/50.0)

	def on_scale2(self, event):
		self.tts.set_noise_scale(self.noise_w_slider.GetValue()/50.0)

	def on_pitch(self, event):
		self.tts.set_pitch(self.pitch_slider.GetValue()/50.0)

	def on_energy(self, event):
		self.tts.set_energy(self.energy_slider.GetValue()/50.0)

	def generate_audio(self, text, autoplay=True, callback=None):
		if self.selected_model == "ForwardTacotron+FastPitch using HiFi-GAN (mix)" and not text.endswith(tuple(string.punctuation)):
			# In ForwardTacotron, if the text not ends with a punctuation mark, the speechs ends impropperly.
			text += "."
		if autoplay:
			self.pause_button.Enable()
			self.play_button.Disable()
		audio, sr = self.tts.speak(text)
		if autoplay :
			if config["extra_silence"]:
				# Extra silence can only be applied on autoplay because sounddevice wait bug.
				silence_duration = int(0.2 * sr)
				silence = np.zeros(silence_duration, dtype=np.int16)
				audio = np.concatenate((audio, silence))
			sd.play(audio, sr)
			sd.wait()
			self.pause_button.Disable()
			self.play_button.Enable()
		else:
			self.play_button.Enable()
		if callback:
			wx.CallAfter(callback, audio)
		return audio

	def on_generate(self, event):
		if self.tts:
			text = self.text_ctrl.GetValue()
			if not text:
				playsound("sounds/error.wav", block=False)
				wx.MessageBox("You must write something!", "Text empti", wx.ICON_ERROR)
				return
			alpha = self.rate_slider.GetValue() / 50.0
			pitch = self.pitch_slider.GetValue() / 50.0
			energy = self.energy_slider.GetValue() / 50.0
			self.tts_thread = threading.Thread(target=self.generate_audio, args=(text, config["autoplay"], self.on_audio_generated))
			self.tts_thread.start()
			#self.tts_thread.join()

	def on_audio_generated(self, result):
		self.audio = result

	def on_text_key_down(self, event):
		keycode = event.GetKeyCode()
		shift_down = event.ShiftDown()
		if keycode == wx.WXK_RETURN and shift_down:
			self.text_ctrl.WriteText('\n')
		elif keycode == wx.WXK_RETURN:
			self.on_generate(event)
		else:
			event.Skip()

	def on_pause(self, event):
		sd.stop()

	def on_play(self, event):
		if self.audio is not None:
			#sd.stop()
			sd.play(self.audio, 22050)
		else:
			playsound("sounds/error.wav", block=False)
			wx.MessageBox("Please generate an audio first.", "Error", wx.ICON_ERROR)
			return

	def on_save_audio(self, event):
		dlg = wx.FileDialog(self, "Export to audio", wildcard="wav files (*.wav)|*.wav", style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
		if dlg.ShowModal() == wx.ID_OK:
			if self.audio is not None:
				path = dlg.GetPath()
				sf.write(path, self.audio, 22050)
				dlg.Destroy()
				wx.MessageBox(f"audio has been saved: {path}.", "Success", wx.OK | wx.ICON_INFORMATION)
			else:
				playsound("sounds/error.wav", block=False)
				wx.MessageBox("You haven't generated any audio!", "No speech", wx.ICON_ERROR)
				return


if __name__ == '__main__':
	app = MyApp(False)
	app.MainLoop()
	playsound("sounds/close.wav")
	#tolk.unload()