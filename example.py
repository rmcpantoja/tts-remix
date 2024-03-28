from include import ft_tts
import sounddevice as sd

model_name = "models/forward/thorsten_fastpitch_50k.pt"
ft = ft_tts.forward(model_name)

audio, sr = ft.speak(
	"Du sagst, Hunde fressen keine Schnecken?"
)
sd.play(audio, sr, blocking=True)