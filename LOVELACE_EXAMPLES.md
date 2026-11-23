# Skapa Avgångstavla i Home Assistant - Exempel

## 📋 Exempel: Sommarhemsvägen i Härryda

Här är flera sätt att visa dina Västtrafik-avgångar som en snygg avgångstavla i Home Assistant!

> **🆕 Rekommenderat:** Använd `departures_json` för strukturerad data som är lättare att arbeta med!

---

## 🏆 Alternativ 0: Markdown Card med JSON (Rekommenderat!)

### Modern Avgångstavla med departures_json
Detta format är mycket enklare att arbeta med och ger dig full kontroll!stavla i Home Assistant - Exempel

## 📋 Exempel: Sommarhemsvägen i Härryda

Här är flera sätt att visa dina Västtrafik-avgångar som en snygg avgångstavla i Home Assistant!

> **🆕 Nytt i v2.0.5:** Använd `departures_json` för strukturerad data som är lättare att arbeta med!

---

## � Alternativ 0: Markdown Card med JSON (Nytt i v2.0.5!)

### Modern Avgångstavla med departures_json
Detta format är mycket enklare att arbeta med och ger dig full kontroll!

```yaml
type: markdown
content: |
  ## 🚌 {{ state_attr('sensor.sommarhemsvägen', 'station_name') }}
  
  {% set deps = state_attr('sensor.sommarhemsvägen', 'departures_json') %}
  {% if deps %}
  {% for dep in deps[:8] %}
  **Linje {{ dep.line }}** → {{ dep.destination }}
  🕒 {{ dep.departure_time }} ({{ dep.relative_time }}){% if dep.track %} • 📍 Läge {{ dep.track }}{% endif %}
  {% if dep.is_cancelled %}⚠️ **INSTÄLLD**{% elif dep.delay_minutes > 0 %}⏱️ +{{ dep.delay_minutes }} min{% endif %}
  
  {% endfor %}
  {% else %}
  *Inga avgångar tillgängliga*
  {% endif %}
  
  📊 {{ state_attr('sensor.sommarhemsvägen', 'departure_count') }} avgångar • 🕒 {{ relative_time(states.sensor.sommarhemsvägen.last_updated) }} sedan
```

**Fördelar med departures_json:**
- ✅ Enklare att filtrera och sortera
- ✅ Direkt åtkomst till alla fält
- ✅ Perfekt för automationer
- ✅ Kan visa exakt vad du vill

### Filtrera Specifika Linjer
Visa bara vissa linjer (t.ex. bara linje 16 och 310):

```yaml
type: markdown
content: |
  ## 🚌 Mina Linjer
  
  {% set deps = state_attr('sensor.sommarhemsvägen', 'departures_json') %}
  {% set my_lines = ['16', '310'] %}
  {% for dep in deps if dep.line in my_lines %}
  **Linje {{ dep.line }}** → {{ dep.destination }}
  🕒 {{ dep.departure_time }} ({{ dep.relative_time }})
  
  {% endfor %}
```

### Visa Bara Avgångar inom 10 Minuter
```yaml
type: markdown
content: |
  ## 🚌 Avgår inom 10 min
  
  {% set deps = state_attr('sensor.sommarhemsvägen', 'departures_json') %}
  {% for dep in deps if dep.minutes_until <= 10 %}
  **Linje {{ dep.line }}** → {{ dep.destination }}
  🕒 {{ dep.departure_time }} (**{{ dep.relative_time }}**)
  
  {% endfor %}
```

---

## 🎨 Alternativ 1: Markdown Card (Traditionell Format)

### Enkel Avgångstavla
```yaml
type: markdown
content: |
  ## 🚌 {{ state_attr('sensor.sommarhemsvägen', 'station_name') }}
  
  {% set deps = state_attr('sensor.sommarhemsvägen', 'departures') %}
  {% if deps %}
  {% for dep in deps[:8] %}
  {{ dep }}
  {% endfor %}
  {% else %}
  *Inga avgångar tillgängliga*
  {% endif %}
  
  *Uppdaterad: {{ relative_time(states.sensor.sommarhemsvägen.last_updated) }} sedan*
```

### Avancerad Avgångstavla med Styling
```yaml
type: markdown
card_mod:
  style: |
    ha-card {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      font-family: 'Roboto Mono', monospace;
    }
content: |
  # 🚌 AVGÅNGSTAVLA
  ## {{ state_attr('sensor.sommarhemsvägen', 'station_name') }}
  
  ---
  
  {% set deps = state_attr('sensor.sommarhemsvägen', 'departures') %}
  {% if deps %}
  {% for dep in deps[:10] %}
  `{{ dep }}`
  {% endfor %}
  {% else %}
  **⚠️ Inga avgångar**
  {% endif %}
  
  ---
  
  📊 **{{ state_attr('sensor.sommarhemsvägen', 'departure_count') }}** avgångar | ⏱️ Uppdaterad: **{{ relative_time(states.sensor.sommarhemsvägen.last_updated) }}** sedan
```

---

## 🎯 Alternativ 2: Entities Card med Attributes

### Visa alla avgångar som lista
```yaml
type: entities
title: 🚌 Sommarhemsvägen
entities:
  - entity: sensor.sommarhemsvägen
    name: Status
  - type: attribute
    entity: sensor.sommarhemsvägen
    attribute: departures
    name: Kommande avgångar
```

---

## 📊 Alternativ 3: Custom Button Card (Kräver custom:button-card)

```yaml
type: custom:button-card
entity: sensor.sommarhemsvägen
name: |
  [[[ return states['sensor.sommarhemsvägen'].attributes.station_name; ]]]
show_state: true
show_label: true
label: |
  [[[
    const deps = states['sensor.sommarhemsvägen'].attributes.departures;
    if (!deps) return 'Inga avgångar';
    return deps.slice(0, 5).join('\n');
  ]]]
styles:
  card:
    - background: linear-gradient(to right, #0f2027, #203a43, #2c5364)
    - color: white
    - padding: 20px
    - border-radius: 15px
  name:
    - font-size: 24px
    - font-weight: bold
  label:
    - font-family: monospace
    - font-size: 14px
    - white-space: pre-line
    - text-align: left
```

---

## 📺 Alternativ 4: Grid Layout - "Flygplatstavla-stil"

```yaml
type: vertical-stack
cards:
  # Header
  - type: markdown
    content: |
      # 🚌 AVGÅNGSTAVLA
      ## {{ state_attr('sensor.sommarhemsvägen', 'station_name') }}
    card_mod:
      style: |
        ha-card {
          background: #1a1a1a;
          color: #00ff00;
          font-family: 'Courier New', monospace;
          text-align: center;
          padding: 10px;
        }
  
  # Avgångar
  - type: markdown
    content: |
      ```
      LINJE  DESTINATION                TID    STATUS
      ─────────────────────────────────────────────────
      {% set deps = state_attr('sensor.sommarhemsvägen', 'next_departures') %}
      {% if deps %}
      {% for dep in deps[:10] %}
      {{ "%-6s %-25s %-7s %s" | format(
          dep.line[:6],
          dep.destination[:25],
          dep.departure_time.split('T')[1][:5] if 'T' in dep.departure_time else dep.departure_time[:5],
          '🔴 REALTID' if dep.is_realtime else ''
      ) }}
      {% endfor %}
      {% endif %}
      ```
      
      Uppdaterad: {{ now().strftime('%H:%M:%S') }}
    card_mod:
      style: |
        ha-card {
          background: #000000;
          color: #ffff00;
          font-family: 'Courier New', monospace;
          font-size: 12px;
        }
```

---

## 🎨 Alternativ 5: Auto-Entities (Dynamisk lista)

```yaml
type: custom:auto-entities
card:
  type: entities
  title: 🚌 Sommarhemsvägen - Nästa Avgångar
filter:
  include:
    - entity_id: sensor.sommarhemsvägen
      options:
        type: custom:template-entity-row
        name: |
          {% set deps = state_attr('sensor.sommarhemsvägen', 'departures') %}
          {{ deps[0] if deps else 'Inga avgångar' }}
```

---

## 🚀 Alternativ 6: Picture Elements (Mest avancerad)

```yaml
type: picture-elements
image: /local/vasttrafik_background.jpg  # Lägg till din egen bakgrundsbild
elements:
  - type: state-label
    entity: sensor.sommarhemsvägen
    attribute: station_name
    style:
      top: 10%
      left: 50%
      font-size: 32px
      font-weight: bold
      color: white
      text-shadow: 2px 2px 4px black
  
  - type: state-label
    entity: sensor.sommarhemsvägen
    attribute: departures
    prefix: 'Nästa: '
    style:
      top: 30%
      left: 50%
      font-size: 24px
      color: yellow
      font-family: monospace
```

---

## 🎯 Alternativ 7: Minimal & Clean (Rekommenderat för Dashboard)

```yaml
type: vertical-stack
cards:
  - type: markdown
    content: |
      ## 🚌 {{ state_attr('sensor.sommarhemsvägen', 'station_name') }}
      {{ states('sensor.sommarhemsvägen') }}
  
  - type: markdown
    content: |
      {% set deps = state_attr('sensor.sommarhemsvägen', 'departures') %}
      {% if deps %}
      {% for dep in deps[:5] %}
      **{{ dep.split(' - ')[0] }}** - {{ dep.split(' - ')[1] if ' - ' in dep else dep }}
      {% endfor %}
      {% else %}
      *Inga avgångar*
      {% endif %}
```

---

## 📱 Alternativ 8: Mobile-Friendly Compact

```yaml
type: custom:mushroom-template-card
primary: 🚌 {{ state_attr('sensor.sommarhemsvägen', 'station_name') }}
secondary: |
  {% set deps = state_attr('sensor.sommarhemsvägen', 'departures') %}
  {{ deps[0] if deps else 'Inga avgångar' }}
icon: mdi:bus
icon_color: blue
tap_action:
  action: more-info
```

---

## 🎨 Alternativ 9: Tabell-Layout (Kräver custom:flex-table-card)

```yaml
type: custom:flex-table-card
title: 🚌 Avgångstavla - Sommarhemsvägen
entities:
  include: sensor.sommarhemsvägen
columns:
  - name: Linje
    data: next_departures
    modify: x.line
  - name: Destination
    data: next_departures
    modify: x.destination
  - name: Avgång
    data: next_departures
    modify: x.departure_time.split('T')[1].slice(0,5)
  - name: Läge
    data: next_departures
    modify: x.track
  - name: Status
    data: next_departures
    modify: x.is_realtime ? '🔴 Live' : ''
```

---

## 🚌 Alternativ 10: Split-Screen Dashboard

```yaml
type: horizontal-stack
cards:
  # Vänster - Status
  - type: vertical-stack
    cards:
      - type: entity
        entity: sensor.sommarhemsvägen
        name: Status
        icon: mdi:bus-stop
      
      - type: markdown
        content: |
          **Station:**
          {{ state_attr('sensor.sommarhemsvägen', 'station_name') }}
          
          **Antal avgångar:**
          {{ state_attr('sensor.sommarhemsvägen', 'departure_count') }}
          
          **Uppdaterad:**
          {{ relative_time(states.sensor.sommarhemsvägen.last_updated) }} sedan
  
  # Höger - Avgångar
  - type: markdown
    content: |
      ### 📋 Kommande Avgångar
      
      {% set deps = state_attr('sensor.sommarhemsvägen', 'departures') %}
      {% if deps %}
      {% for dep in deps[:8] %}
      {{ loop.index }}. {{ dep }}
      {% endfor %}
      {% else %}
      *Inga avgångar*
      {% endif %}
```

---

## 💡 Rekommendation för Sommarhemsvägen

Här är min **bästa rekommendation** för en snygg och funktionell avgångstavla:

```yaml
type: vertical-stack
cards:
  # Header med station
  - type: markdown
    content: |
      # 🚌 Sommarhemsvägen, Härryda
      {{ states('sensor.sommarhemsvägen') }}
    card_mod:
      style: |
        ha-card {
          background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
          color: white;
          padding: 15px;
          text-align: center;
        }
  
  # Avgångslista
  - type: markdown
    content: |
      {% set deps = state_attr('sensor.sommarhemsvägen', 'departures') %}
      {% if deps %}
      {% for dep in deps[:10] %}
      `{{ dep }}`
      
      {% endfor %}
      {% else %}
      **⚠️ Inga avgångar tillgängliga**
      {% endif %}
      
      ---
      
      📊 **{{ state_attr('sensor.sommarhemsvägen', 'departure_count') }}** avgångar totalt | 🕒 Uppdaterad **{{ relative_time(states.sensor.sommarhemsvägen.last_updated) }}** sedan
    card_mod:
      style: |
        ha-card {
          background: #f5f5f5;
          padding: 15px;
          font-family: 'Roboto Mono', monospace;
        }
```

---

## 🔧 Installation

1. Gå till **Settings → Dashboards**
2. Välj din dashboard eller skapa ny
3. Klicka **Edit Dashboard**
4. Klicka **+ ADD CARD**
5. Välj **Manual** längst ner
6. Kopiera och klistra in valfri YAML-kod ovan
7. Byt `sensor.sommarhemsvägen` till ditt sensor-namn
8. Klicka **Save**

## 🎯 Tips

### Hitta ditt sensor-namn:
1. Gå till **Developer Tools → States**
2. Sök efter "sommarhem" eller "vasttrafik"
3. Kopiera entity_id (t.ex. `sensor.sommarhemsvagen`)

### Anpassa färger:
- Ändra `background` för bakgrundsfärg
- Ändra `color` för textfärg
- Ändra `font-family` för typsnitt

### Antal avgångar:
- Ändra `[:10]` till `[:5]` för färre avgångar
- Ändra `[:10]` till `[:15]` för fler avgångar

---

## 📸 Resultat

Med dessa kort får du en professionell avgångstavla som visar:
- ✅ Hållplatsnamn (Sommarhemsvägen, Härryda)
- ✅ Antal avgångar (5 avgångar från...)
- ✅ Linje nummer (Linje 16, Linje 310, etc.)
- ✅ Destination (→ Mölndals Centrum)
- ✅ Exakt avgångstid (14:25)
- ✅ Relativ tid ((2 min))
- ✅ Läge/spår (Läge A)
- ✅ Realtidsstatus (🔴)
- ✅ Uppdateringstid

Perfekt för en vägg-monterad tablet eller din dashboard! 🎉
