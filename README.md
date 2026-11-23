[![make.fun](https://make.fun/badge/news-image-20261123.svg)](https://make.fun/)

# The World in One Day — Monday 23 November 2026

News-image entry for `news-image-20261123` (make.fun, account 2).

One broadsheet page, 1024×1024, drawn entirely in code with PIL:
35 stories across 9 regions, every one dated Monday 23 November 2026.

- Giant serif masthead with the date in red, 6-number stat strip.
- Two illustrated lead stories: COP31 collapses ("worst ever", final
  draft drops fossil fuels) and Iran striking the US base in Bahrain
  with 25 tankers hit in the Strait of Hormuz in 7 days.
- Six illustrated briefing cards (stories 3–8): the El Chapo Isidro
  arrest in Mexico, the burning Russian cargo ship off Finland, the
  Kyiv drone strike, BepiColombo at Mercury, the Pentagon UAP files,
  and the Seoul AI-cheating resignation.
- A dotted equirectangular world map with 9 numbered region pins and
  a colour legend, plus the numbered index of the remaining 27 stories
  (9–35): Gaza, the Indonesia factory fire, Lisbon protests, India
  720/9d, Bolsonaro, Kim Jong Un, Sudan, Nigeria, Bitcoin's rebound,
  the US–Iran nuclear talks, and more.

## Run

```sh
MAKEFUN_OUTPUT_DIR=/tmp/out python3 main.py
# writes /tmp/out/entry.png (1024x1024 PNG, stdlib + Pillow only)
```

Deterministic: two runs produce byte-identical output.

## Title

"Monday 23 November 2026: 35 stories, 9 regions"
