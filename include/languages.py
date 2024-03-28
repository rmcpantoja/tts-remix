# Languages

languages = {
	"ar": "ألعَرَبِي",
	"ca": "Català",
	"cs": "čeština",
	"da": "Dansk",
	"de": "Deutsch",
	"el": "Ελληνικά",
	"en": "English",
	"en-gb": "English (British)",
	"en-us": "English (U.S.)",
	"eo": "Esperanto",
	"es": "Español",
	"es-es": "Español (españa)",
	"es-419": "Español (Latinoamericano)",
	"fi": "Suomi",
	"fr": "Français",
	"hu": "Magyar",
	"is": "Icelandic",
	"it": "Italiano",
	"ka": "ქართული",
	"kk": "қазақша",
	"lb": "Lëtzebuergesch",
	"ne": "नेपाली",
	"nl": "Nederlands",
	"nb": "Norsk",
	"pl": "Polski",
	"pt-br": "Português (Brasil)",
	"pt-pt": "Português (Portugal)",
	"ro": "Română",
	"ru": "Русский",
	"sr": "Српски",
	"sv": "Svenska",
	"sw": "Kiswahili",
	"tr": "Türkçe",
	"uk": "украї́нська",
	"vi": "Tiếng Việt",
	"zh": "简体中文"
}

def _get_language(code):
	global languages
	return languages[code]