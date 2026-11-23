# Västtrafik M34

Home Assistant-integration för avgångar via Västtrafik API v4 (Planera Resa). Namnet kommer från spårvagnslinjen M34.

## Installation

### Via HACS (rekommenderat)

1. Lägg till detta repository som en **Custom Repository** av typen *Integration* i HACS.
2. Sök efter **Västtrafik M34** och installera.
3. Starta om Home Assistant.
4. **Inställningar → Enheter & tjänster → Lägg till → Västtrafik M34**.

### Manuellt

1. Kopiera mappen `custom_components/vasttrafik_m34` till din HA `config/custom_components/`.
2. Starta om Home Assistant.
3. Lägg till integrationen från **Enheter & tjänster**.

### API-nyckel

Du behöver en Authentication Key från [developer.vasttrafik.se](https://developer.vasttrafik.se):

1. Skapa ett konto och en app.
2. Prenumerera på API:t **API Planera Resa**.
3. Kopiera nyckeln/secret och använd den Base64-kodade formen `key:secret` som integrationen ber om.

Sök sedan efter en hållplats (t.ex. `Näverstigen`) och välj rätt träff. En hållplats per config entry.

## Entiteter

Per hållplats skapas tre sensorer:

| Sensor | Typ | Beskrivning |
|--------|-----|-------------|
| `<hållplats>` | Text | `kl. 07:18 (3 min) → Resecentrum` |
| `<hållplats> Nästa avgång` | Timestamp | Tidpunkt för nästa avgång (användbar i automatiseringar) |
| `<hållplats> Minuter till nästa avgång` | Nummer | Nedräkning i minuter |

Attribut på textsensorn: `next_line`, `next_destination`, `next_departure_time`, `next_minutes_until`, `next_track`, `next_delay_minutes`, `next_is_realtime`, `departures`, `departures_json`, `from_cache` och `cache_reason`.

## Alternativ (efter installation)

Öppna integrationen → **Konfigurera**:

| Alternativ | Standard | Exempel |
|------------|----------|---------|
| Riktning | – | `Resecentrum` |
| Linje | – | `Buss 6` |
| Dölj inställda avgångar | på | av/på |
| Visa försening | av | av/på |
| Tidsfönster | 90 min | 15–180 min |
| Max avgångar per linje | 4 | 1–10 |
| Uppdateringsintervall | 60 s | 30–300 s |

Om API-nyckeln blir ogiltig får du en reauth-prompt där du kan klistra in en ny nyckel utan att ta bort hållplatsen.

## Cache och driftstopp

Integrationen sparar den senaste lyckade avgångslistan. Vid tillfälliga API-fel används cachen i högst 15 minuter och sensorn får attributen `from_cache=true` och `cache_reason`. Äldre cache kastas bort. Cachen skrivs bara om avgångarna faktiskt ändras (eller vart 15:e minuter).

## Exempel

```yaml
{{ state_attr('sensor.naverstigen_skovde', 'next_minutes_until') }}
{{ state_attr('sensor.naverstigen_skovde', 'next_track') }}
{{ states('sensor.naverstigen_skovde_nasta_avgang') }}
```

Fler dashboard-exempel finns i [LOVELACE_EXAMPLES.md](LOVELACE_EXAMPLES.md).

## Avinstallation

1. **Inställningar → Enheter & tjänster → Västtrafik M34 → ... → Ta bort** för varje konfigurerad hållplats.
2. Ta bort integrationen från HACS (eller radera `config/custom_components/vasttrafik_m34` vid manuell installation).
3. Starta om Home Assistant.

Cachefiler ligger under `config/.storage/vasttrafik_m34.<entry_id>` och kan raderas manuellt om du vill rensa helt.

Ändringar mellan versioner finns i [CHANGELOG.md](CHANGELOG.md).
