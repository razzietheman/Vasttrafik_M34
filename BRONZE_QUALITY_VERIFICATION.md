# Bronze Quality Scale – verifiering (v2.0.5)

Denna fil sammanfattar varför integrationen klassificeras som Bronze. Detaljerad status finns i `custom_components/vasttrafik_m34/quality_scale.yaml`.

## Verifierat i 2.0.5

| Regel | Status | Bevis |
|-------|--------|-------|
| `config-flow` | done | `config_flow.py`: nyckel → hållplatssökning → val, med `data_description` i `strings.json` och `translations/sv.json`. |
| `config-flow-test-coverage` | done | `tests/test_config_flow.py`, `tests/test_init.py`, `tests/test_sensor.py`, `tests/test_coordinator.py` körs i CI med HA-testfixtures. |
| `test-before-configure` | done | Nyckeln testas mot `/token` innan entry skapas; 401/403 ger `invalid_auth`. |
| `test-before-setup` | done | `async_setup_entry` kör första uppdateringen via `async_config_entry_first_refresh`. |
| `unique-config-entry` | done | `async_set_unique_id(f"vasttrafik_{gid}")` + `_abort_if_unique_id_configured`. |
| `entity-unique-id` | done | Tre stabila unika ID:n per hållplats i `sensor.py`. |
| `has-entity-name` | done | `_attr_has_entity_name = True` på samtliga entiteter. |
| `runtime-data` | done | `entry.runtime_data = coordinator`, typad som `VasttrafikConfigEntry`. |
| `appropriate-polling` | done | `DataUpdateCoordinator`, 60 s standard, delad aiohttp-session. |
| `dependency-transparency` | done | Inga externa requirements i `manifest.json`. |
| Dokumentation | done | `README.md` med beskrivning, installation, alternativ, exempel och avinstallation. |

## Undantagna regler

- `action-setup`, `docs-actions`: inga service actions.
- `entity-event-setup`: moln-polling via coordinator, inga händelseprenumerationer.
- `brands`: HACS-ikon finns i repo:t; riktiga brand-assets hanteras i `home-assistant/brands`.

## CI

- `.github/workflows/test.yml`: pytest på Python 3.12 med `pytest-homeassistant-custom-component`.
- `.github/workflows/validate.yaml`: HACS validation + hassfest.

Alla tester måste vara gröna före release. Se till skillnad från tidigare versioner inga påståenden om `SCAN_INTERVAL`, externa aiohttp-krav eller radnummer som inte finns i koden.
