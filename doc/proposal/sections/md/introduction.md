# Introduction

In todays university life, practical courses or laboratories are often attendance-based.
Attendance sheets are used to record students attendance.
These need manual analysis to determine wether a student has successfully participated.
To automate the attendance monitoring and ease the analysis of instructors, a indoor localisatiuon service is proosed.

While GPS and cell-tower based localisaiton is often used in outdoor environments, these are not suitable in an indoor environment, such as an university.
To facilitate accurate indoor localisation services a different approach is needed:
Wireless probe-requests are used by wifi-enabled devices like smartphones to find and auto connect to known access-points.
With 

# Ausgangssituation

An der Technischen Hochschule Nürnberg werden viele Fächer von einem Labor bzw. einem Praktikum begleitet um praktische Anwendungen besser kennen zu lernen.
Diese Praktika und Labore sind in der Regel Anwesenheitspflichtig und es muss eine bestimmte Anzahl von Terminen besucht werden um den Kurs erfolgreich zu absolvieren.
Über die Anwesenheit der Teilnehmer wird also Protokoll geführt, üblicherweise in Form von Anwesenheitsblättern auf denen jeder Teilnehmer unterschreibt.
Diese Anwesenheitsblätter müssen im Nachhinein manuell analysiert werden um eine erfolgreiche Teilnahme zu Bescheinigen.
Um die Anwesenheitskontrolle zu erleichtern und zu digitalisieren würde sich ein Lokalisierungssystem anbieten, welches die Anwesenheit automatisch protokolliert.

Durch die Allgegenwart von Smartphones heutzutage liegt es nahe dessen Funktionen zu benutzen um die Anwesenheit von Studenten festzustellen.
Somit soll auf ein WLAN basiertes Lokalisierungssystem zurückgegriffen werden, welches auf sogenannten Wifi Probe Requests basiert.
Probe-Requests sind Kontrollframes von WLAN fähigen Geräten, die periodisch gesendet werden, um bekannte WLAN-Netzwerke zu finden und sich automatisch mit diesen zu verbinden. [1]
Im Rahmen eines Probe Requests werden die MAC-Adresse des Senders, die Signalstärke und dem Gerät bekannte Accesspoints öffentlich gesendet.
Dies machen sich bereits einige Forschungsarbeiten zur Nutze um Anwesenheit von Personen zu erkennen bzw. Personen zu tracken. [2,3]

[1]: wifiproberequests2019.bib
[2]: sail2014.bib
[3]: sherlock2018.bib
