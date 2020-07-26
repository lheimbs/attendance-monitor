# vorgehen
Untersuchung der Eignung von PRs zur anwesenheitserkennung bei praktika

- Lokalisierungskonzepte (SHERLOC etc) existieren bereits
- Prototyp entwickelt und experimentell eignung konzepte testen

rssi baseline erstellen nach path-loss-model:
- rssi für versch. distanzen messen
- kurvenangleichung

# erwähnen
- wifi vs ble vs gps vs rfid vs andere (zigbee/...)
    (S. Sadowski, P. Spachos: RSSI-Based Indoor Localization With the IoT)

    wifi weil jeder hat handy + in uni überall aps

- wifi channels betrachten
- mac-randomization:
    - 

# ideen
- 3x esp probemon + synced clocks für Time-of-Arrival/trilateration lokalisierung
- nur einzelner pi/... als simpelste option, simuliert existierende aps -> rssi
- time-present als wert für anwesenheit errechnen
    - verschiedene pr intervalle müssen beachtet werden

- webservice:
    - frozen für mind. anwesenheitszeit
    - stdu rufen seite im handy auf:
        - wenn anwesenheit erkannt: gut
        - wenn nicht: warten oder selber loggen
    - wenn kein handy: im browser + id verfahren

# rssi
- most common in indoor localization
- power present in signal
- cheap
- errors due to interference makes it error prone

# L. Oliveiraet al.: Mobile Device Detection Through WiFi Probe Request Analysis





