### ENG BELOW!

(<small>Pozwole sobię zrezygnować z oficjalnego tonu na rzecz czytelności i łatwości zrozumienia</small>)

# Moduł samouczący do systemu automatyki domowej
Celem tej pracy jest opracowanie modułu samouczącego do zastosowań automatyki domowej. Dokładnie praca o czym jest, jak i na co się składa jest opisane w pracy, znajdującej się w folderze `thesis/thesis.pdf`. Odsyłam tam w celu dokładnego poznania zagadnienia i celów. W wypadku gdybym tę pracę w późniejszym czasie kontynuuował, wersja która znajduje się w archwium Politechniki Wrocławskiej będzie oznaczona tagiem `thesis`, w przeciwnym wypadku ostatnia, aktualna wersja jest tą oficjalną.

## Opowiastka o wymaganiach
Do pracy jako supervisor'a automatyki domowej wybrałem [HomeAssistant](https://www.home-assistant.io/), zatem jest ono w 100% wymagane. HA połączone jest z obrazem [AppDaemon](https://github.com/AppDaemon/appdaemon/). Chciałem żeby taki system mógł działać wszędzie tam gdzie może działać HA, zatem postawiłem na Dockera. Co widać [tutaj](https://analytics.home-assistant.io/) duża część instalacji jest w kontenerach. W przypadku instalacji HA jako system, z tego co kojarze to jest opcja doinstalowania sobie dockera i tam wtedy można dodać ten moduł. Samo budowanie modułu jest zautomatyzowane z Makefile bo buduje tam samą aplikację a potem wrzucam ją do customowego obrazu AppDaemon.