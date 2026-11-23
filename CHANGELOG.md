# Changelog

## 2.0.5

- **Fix:** korrekt API-parameternamn `maxDeparturesPerLineAndDirection` och `limit=50` mot Västtrafik v4. Alternativet "Max avgångar per linje" fungerar nu.
- **Fix:** 401/403 från token-endpointen visas som `invalid_auth` i config- och reauth-flödet.
- **Fix:** hållplatssökning klarar list-svar från API:t utan krasch.
- **Nytt:** reauth-flöde för att byta API-nyckel utan att ta bort hållplatsen.
- **Nytt:** två extra sensorer – timestamp för nästa avgång och numerisk nedräkning i minuter.
- **Förbättrat:** cache har 15 minuters TTL, re-filtreras före användning och skrivs bara när avgångarna ändras.
- **Förbättrat:** säker tidsbehandling för naiva tider och avrundad försening.
- **Förbättrat:** generaliserad destinationsvisning (ingen hårdkodad "Resecentrum").
- **Fix:** minimikrav i `hacs.json` höjt till HA 2024.11 (options flow kräver det).
- **Fix:** testsviten skrevs om med riktiga HA-fixtures; CI kör Python 3.12 och hela sviten.
- **Docs:** README, quality scale, HACS-checklista och Lovelace-exempel uppdaterade.

## 2.0.4

- Ursprunglig version i arkivet `Vasttrafik_M34-2.0.4.zip`.
