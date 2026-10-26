# Service Endpoints

JSON/REST-style endpoints, taken from `fluidsynthui/urls.py` and the view code. They all live in one Django app and are called by the Stream Deck and browser JavaScript.

## JSON services

| Method | Path | Purpose | Notes |
|---|---|---|---|
| GET | `/sets/active/song/current/` | Current song in the active set | |
| POST/GET | `/sets/active/song/next/activate/` | Go to the next song and apply its patch | |
| POST/GET | `/sets/active/song/prev/activate/` | Go to the previous song and apply its patch | |
| POST/GET | `/sets/active/song/first/activate/` | Go to the first song and apply its patch | |
| POST/GET | `/sets/active/song/last/activate/` | Go to the last song and apply its patch | |
| POST/GET | `/sets/active/song/pad/start/` | Start the active song's pad | |
| POST/GET | `/sets/active/song/pad/stop/` | Stop the pad | |
| POST/GET | `/sets/active/song/pad/toggle/` | Toggle the pad | |
| any | `/sets/active/song/metronome/start/` | Start the metronome at the song's tempo | no method check |
| any | `/sets/active/song/metronome/stop/` | Stop the metronome | no method check |
| any | `/sets/active/song/metronome/faster/` | BPM +1 | no method check |
| any | `/sets/active/song/metronome/slower/` | BPM -1 | no method check |
| any | `/sets/active/song/metronome/softer/` | Gain -0.1 | no method check |
| any | `/sets/active/song/metronome/louder/` | Gain +0.1 | no method check |
| POST/GET | `/pad/test/start/` | Test-play a pad | |
| any | `/pad/test/stop/` | Stop the test pad | no method check |
| GET | `/pad/usage/<pk>/` | Which songs use this pad | |
| GET | `/patch/usage/<pk>/` | Which songs use this patch | |
| GET | `/get-presets-json/<sf_name>/` | Presets in a soundfont | 400 if no synth |
| POST | `/apply_patch_preview` | Apply unsaved patch form data to the synth | returns `{'status': ...}`, not `{'success': ...}` |
| POST | `/mp3/play/<slot>/` | Play MP3 slot 1-8 for the active song | `csrf_exempt` |
| POST | `/mp3/stop/` | Stop all MP3 playback | `csrf_exempt` |

## HTML or form endpoints

These are page views rather than services:

- `/`, `/patches/`, `/songs`, `/sets`, `/pads/`, `/stream-deck/`, `/mp3/`
- Add or edit forms: `/patch/add/`, `/patch/edit/<pk>/`, `/songs/add/`, `/songs/edit/<pk>/`, `/sets/add/`, `/sets/edit/<pk>/`, `/pad/add/`, `/pad/edit/<pk>/`. These accept `_method` overrides.
- Redirect actions: `/patch/apply/<pk>/`, `/sets/activate/<pk>/` (POST only), `/mp3/upload/` (POST), `/mp3/delete/` (POST)
- `/admin/` (Django admin)

## Things to review

- **No authentication.** No endpoint has a login or permission check, including the state-changing ones. Access control is limited to `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` in `fluidsynthui/settings.py`.
- **State changes via GET.** The `active/song/*` and pad endpoints accept GET, so a link, prefetch, or crawler can trigger them. This was probably intended for Stream Deck URL buttons.
- **Missing method restrictions.** The metronome endpoints and `/pad/test/stop/` accept any HTTP method.
- **CSRF exemption.** Only the two MP3 endpoints use `csrf_exempt`. The other POST endpoints rely on Django's CSRF check, so a plain POST to `/sets/active/song/next/activate/` needs a CSRF token.
- **Inconsistent responses.** Some endpoints return `{'success': ...}` and others return `{'error': ...}`, `{'status': ...}`, or bare data. Names are also mixed: `sets/active/song/...` covers pads and the metronome, while `pad/test/...` and `mp3/...` use different patterns.

Method and response details come from reading the code; they have not been tested against a running server.
