(Pozwole sobie zrezygnować z oficjalnego tonu na rzecz czytelności i łatwości zrozumienia. Również niestety nie podam jak stworzyć sobie KOMPLETNE środowisko od zera HA + urządzenia, bo nie jest to moim celem. Zakładam, że osoba przynajmniej trochę zna sie na systemie HA)

# Moduł samouczący do systemu automatyki domowej
Celem tej pracy jest opracowanie modułu samouczącego do zastosowań automatyki domowej. Dokładnie praca o czym jest, jak i na co się składa jest opisane w pracy, znajdującej się w folderze `thesis/thesis.pdf`. Odsyłam tam w celu dokładnego poznania zagadnienia i celów. W wypadku gdybym tę pracę w późniejszym czasie kontynuował, wersja która znajduje się w archwium Politechniki Wrocławskiej będzie oznaczona tagiem `thesis`, w przeciwnym wypadku ostatnia, aktualna wersja jest tą oficjalną.

## Opowiastka o wymaganiach
Do pracy jako supervisor'a automatyki domowej wybrałem [HomeAssistant](https://www.home-assistant.io/), zatem jest ono w 100% wymagane. HA połączone jest z obrazem [AppDaemon](https://github.com/AppDaemon/appdaemon/). Chciałem żeby taki system mógł działać wszędzie tam gdzie może działać HA, zatem postawiłem na Dockera. Co widać [tutaj](https://analytics.home-assistant.io/) duża część instalacji jest w kontenerach. W przypadku instalacji HA jako system, z tego co kojarze to jest opcja doinstalowania sobie dockera i tam wtedy można dodać ten moduł. Samo budowanie modułu jest zautomatyzowane z Makefile bo buduje tam samą aplikację a potem wrzucam ją do customowego obrazu AppDaemon. Make nie jest wymagany, bo można przekleić sobie ze środka komendy do terminala, więc nie powiem, że jest to wymaganie, ale warto i polecam. Ze względu na to, że to nie jest praca o HA, nie chce opisywać procesu stawiania sobie całego stacku. Powiem tylko że istniejące HA jest wymagane do pracy. Konfigurację AD również zostawiam użytkownikowi. Po pierwszym uruchomieniu aplikacji pojawi się kilka folderów. Jedno należące do plików AppDaemon, drugie (jeśli używamy tego HA co stawiamy od zera w Makefile) z plikami od niego. [TOKEN](https://community.home-assistant.io/t/how-to-get-long-lived-access-token/162159) wymagany przez HA do komunikacji wystarczy zapisać w plikach które pojawią sie po pierwszym uruchomieniu aplikacji. 

Aplikacja była pisana pod dowolny system pracujący pod Linuxem, również pod VM'ki.

## Środowisko developerskie
Podczas pisania aplikacji korzystałem z Pipenva jako środowisko pythona, zatem odsyłam do instalacji, w razie chęci odtworzenia całego modułu. Jedna uwaga to w paczkach właściwych do pisania kodu `tensorflow` ma wersję przypiętą do 2.11, ze względu na to, że mój biedny i przestarzały GTX960 nie radzi sobie z akceleracją z nowszymi wersjami niż ta. Reszta bez zastrzeżeń. Dodatkowym bonusem jest pre-commit, o którym wspominałem w pracy. On sie sam zainstaluje podczas instalowania środowiska developerskiego. Jedyne co, to po zakończeniu trzeba zainstalować hooki, czyli `pre-commit install`.

### Wymagania
    linux
    pipenv
    docker
    Makefile (teoretycznie nie)
    najlepiej jakaś karta graficzna od nvidii
    **ISTNIEJĄCY** SYSTEM AUTOMATYKI DOMOWEJ HOMEASSISTANT

## Konfiguracja
Po włączeniu tej aplikacji przynajmniej **raz**, stworzą nam się dodatkowe foldery. Jednym z nich jest `appdeamon_config`. Wewnątrz niego trzeba edytować plik `apps/apps.yaml`, który mówi AD z jakich "modułów" ma korzystać. Tam trzeba dopisać kilka linijek w celu przekazania przekazania systemowi informacji o naszym środowisku.

```yaml
deep_network:
  module: app
  class: DeepNetwork

  revert_switch: <entity_name>
  devices:
    <entity_name>: <entity_type>
```

Pierwsze trzy linijki to rzeczy które wymaga AD. Dalej jest właściwa konfiguracja tego sprzężenia naszego modułu z rzeczywistym systemem HA. `revert_switch` wskazuje na dowolne urządzenie, które ma działać jako przycisk cofania niewłaściwych predykcji. Pole `devices` to słownik składający się z nazw urządzeń w środowisku domowym jako klucze, oraz typem urządzeń jako wartość. **Jedynymi** działającymi urządzeniami są urządzenia typu `bool` oraz `button`. Tak zdefiniowany plik konfiguracyjny AppDaemon powinien użyć naszego modułu i stworzyć modele. Korzystając z `docker logs` mozna podejrzeć co nam ta aplikacja robi w danym momencie. Dane `<entity_name>` to **istniejące** urządzenia dostepne w HA. Ich nazwa będzie przypominać coś na zasadzie `integracja.nazwa_urządzenia`.

## Dodawanie nowych urządzeń
Dodawanie nowych urządzeń nie polega na żadnych pluginach. Rozszerzanie możliwości systemu opiera sie na dopisaniu dwóch klas z klikoma funkcjami.

W pliku `collector/device_history.py` należy dopisać typ, który będzie przekształcał dane zawarte w historii HA do takiej, która potem będzie przekazywana do konwertera. Należy tam zdefiniować cztery funkcje zgodnie z abstrakcyjną klasą `DeviceHistoryGeneric`. `DEVICE_TYPE` wskazuje na wewnętrzny typ urządzenia i jest potrzebny do serializowania i deserializowania systemu.

- `get_past_state` - funkcja na podstawie typu do reprezentacji historii `TimeEntry`, bierze stan w danym momencie czasowym T, opcjonalnie w momencie czasowym T-n i opcjonalnie moment zakończenia przeglądanego epizodu, do wygenerowania dwóch zmiennych będących aktualnym stanem urządzenia i aktualną zmianą stanu urządzenia.
- `get_current_state` - na podstawie aktualnego `TimeEntry` oraz aktualnego czasu, zwraca wartość aktualnego stanu urządzenia.
- `get_current_change` - to co wyżej, ale aktualne przejście stanu.
- `generate_change_state_func` - funkcja, która na podstawie nazwy urządzenia, aktualnego stanu i docelowego przejścia zwraca funkcję, która jako parametr przyjmuje `self` od `hassapi` w celu użycia tego obiektu do zmiany aktualnego stanu systemu.

W pliku `models/converters.py` o ile nasz nowy typ urządzeń tego wymaga, musimy dopisać adapter przekształcający wartości pochodzące z `DeviceHistoryGeneric` do takiej rozumianej przez sieci neuronowe. Możemy tam skorzystać z typów `Convertable` lub `CompoundConvertable`. Pierwszy z nich przekształca `1 -> 1`. Za pomocą `convert_to` i `convert_from` zamieniamy do reprezentacji sieci neuronowych i z powrotem do takiej rozumianej przez resztę systemu. Zarówno `Convertable` jak i `CompoundConvertable` wymaga pola `TYPE` do serializowania i deserializowania. Dodatkowo w tej drugiej znajduje się informacja o typach wewnętrznych i ich nazwach, tak aby rozbita jedna zmienna do kilku mogła potem trafić odpowiednio do funkcji, żeby mogła zostać przetworzona w drugą stronę.

## Komendy
```bash
git clone [...]
cd self-learning-homeautomation/
python -m pip install pipenv
pipenv install --three --dev
make build_appdaemon run
make stop

# Korzystając z interfejsu HA generujemy TOKEN do komunikacji AD
# dopisujemy go do: `appdeamon_config/appdaemon.yaml`
# vim appdeamon_config/appdaemon.yaml

# dalej konfigurujemy swoje środowisko wg informacji wyżej:
# vim appdeamon_config/apps

make start
```