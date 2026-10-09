# concert-archive-data

Nieuws voor de Concert Archive-app (Archive, concert 8 september 2027).

- `news.json` wordt twee keer per dag bijgewerkt door `.github/workflows/update-news.yml`.
- `scripts/update_news.py` zoekt nieuws via Google News RSS en bewaart alleen kop, bron, datum en link.
- Optioneel pushbericht via [ntfy](https://ntfy.sh): zet een geheim `NTFY_TOPIC` in de repo.
- Handmatig nieuws toevoegen: voeg een item toe aan `news.json` met een unieke `id`.
