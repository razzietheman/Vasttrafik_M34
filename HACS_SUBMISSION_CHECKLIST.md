# HACS Submission Checklist – v2.0.5

## Repository

- [x] `hacs.json` med `name`, `country: SE`, `render_readme: true` och `homeassistant: 2024.11.0`.
- [x] `custom_components/vasttrafik_m34/` med `manifest.json`, `config_flow.py`, `coordinator.py`, `sensor.py`, `strings.json`, `translations/sv.json`.
- [x] `README.md` med installation, API-nyckel, alternativ och avinstallation.
- [x] `LICENSE` (MIT).
- [x] Ikon/logo i repositoryts rot.

## manifest.json

- [x] `domain`: `vasttrafik_m34`
- [x] `name`: `Västtrafik M34`
- [x] `version`: `2.0.5`
- [x] `config_flow: true`
- [x] `integration_type: service`
- [x] `iot_class: cloud_polling`
- [x] `quality_scale: bronze`
- [x] `requirements: []` (aiohttp ingår i Home Assistant)

## CI (måste vara gröna)

- [x] `.github/workflows/test.yml` – pytest på Python 3.12 med `pytest-homeassistant-custom-component`.
- [x] `.github/workflows/validate.yaml` – HACS Action + hassfest.

Kör lokalt före push:

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements_test.txt
pytest -q
```

## Release

- [ ] Skapa GitHub Release **v2.0.5** med release notes som nämner:
  - korrekt `maxDeparturesPerLineAndDirection` + `limit` mot Västtrafik v4
  - reauth-flöde för API-nyckel
  - cache med 15 minuters TTL och automatisk re-filtrering
  - nya sensorer för timestamp och minuter
  - uppdaterat minimikrav till HA 2024.11
- [ ] Ladda upp zip:en `Vasttrafik_M34-2.0.5.zip` som release-tillgång (valfritt men praktiskt för manuell installation).
- [ ] Kontrollera repository description/topics: `home-assistant`, `hacs`, `vasttrafik`, `sweden`.

## HACS default repository

- [ ] Öppna PR mot `hacs/default` enligt HACS dokumentation när releasen är publicerad.
- [ ] Bifoga länk till repository och release.
- [ ] Vänta på review; svara på eventuella hassfest-/HACS-annoteringar.
