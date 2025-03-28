# DMS-Butler für d.velop
Mit dieser Anwendung können Dokumente im d.velop-DMS gesucht und anhand bestimmter Kriterien automatisch angepasst werden.

### Beispiel
Suche alle Dokumente der Kategorie "Mietvertrag", die die Begriffe "Mietvertrag" und "Unterschrift", 
jedoch nicht den Begriff "Test" enthalten. Die Dateien dürfen minimal 10 und maximal 20 Seiten haben. Setze bei
zutreffenden Dokumenten die Eigenschaft "Teilen mit Mieterportal" auf "Ja".

### Disclaimer
**Bitte benutzen Sie diese Anwendung nur, wenn Sie sicher sind, was Sie erreichen möchten. Testen Sie auf keinen Fall in einer produktiven Umgebung. Ich übernehme keine Haftung für ungewollte Massenänderungen am DMS, die durch Fehler in der Anwendung oder Konfigurationsfehler entstanden sind.
  Sollten Sie Unterstützung benötigen, schreiben Sie mir bitte eine Nachricht oder erstellen Sie einen Eintrag in den Issues.**

### Installation
* Repository klonen
``` git clone https://github.com/seb-bau/dms_butler.git ```
* Voraussetzungen installieren
```
cd dms_butler
pip install -r requirements.txt
```
* config_example.ini in config.ini umbenennen und Werte anpassen
* profiles.ini anlegen oder Beispiel umbenennen (Details siehe unten)

Hinweis: In einer produktiven Umgebung wird der Einsatz einer virtuellen Umgebung (venv) empfohlen
### Konfiguration
#### config.ini
Es wird ein API-KEy für das d.velop DMS benötigt. Der entsprechende User benötigt Schreibzugriff auf die gewünschten
Kategorien. Hinweis: Sollte eine Berechtigung im DMS verändert werden, muss der API-Key anschließend neu
erstellt werden.

host: Domain der d.velop-Instanz ohne https://. Beispiel: meinefirma.d-velop.cloud
api-key: Der o.g. API-Key des zugreifenden Benutzers
repo: Die ID des gewünschten Repositories. Sollte es nur eins geben, kann das Feld frei bleiben

Das Logging kann entweder über Graylog oder in eine Datei erfolgen. Sollte die Log-Methode "file" gewählt werden,
werden die Log-Dateien im Unterordner "log" angelegt. Bei Auswahl der Methode "Graylog" werden der Graylog Host
und Port verwendet.

#### profiles.ini
Beispiel:
```
[Mietverträge]
allowed_filetypes = pdf|docx
categories = Meine Kategorie
fulltext = Wort1 Wort2 -(Ausschlusswort1|Ausschlusswort2)
min_pages = 10
max_pages = 25
search_props = ZuSuchendeEigenschaft:ZuSuchenderWert|NochEineEigenschaft:NochEinWert
set_props = ZuSetzendeEigenschaft:ZuSetzenderWert|NochEineEigenschaft:NochEinWert
```

Alle Felder sind Pflichtfelder!
Grundsätzliche Funktion: Bis auf die Eigenschaft set_props dienen alle anderen Felder dazu, die betroffenen Dokumente eindeutig zuzuordnen.
Die Auswahlmöglichkeiten orientieren sich dabei an der GUI-Suchmaske in d.velop. Die letzte Option stellt die eigentliche Änderung der Dokumente dar.
* Der Wert in eckigen Klammern ist der Profilname. Dieser hat (außer für das Logging) keine relevanz, muss jedoch eindeutig sein.
* Die Datei profiles.ini kann mehrere Profile enthalten
* allowed_filetypes: Dateiendungen, die beachtet werden. Groß- und Kleinschreibung wird nicht beachtet. Mehrere Dateiendungen werden per Pipe getrennt
* categories: Kategorien, die durchsucht werden sollen. Mehrere Kategorien werden durch Pipe getrennt.
* fulltext: Volltext-Suche innerhalb der Datei(!). Hier kann jede Syntax verwendet werden, die auch in der d.velop Suchmaske vorhanden ist (siehe auch https://help.d-velop.de/docs/de/pub/documents/cloud/erste-schritte-beim-suchen-und-finden)
```

    + oder Leerzeichen: Einzelne Suchbegriffe werden für die Und-Suche durch diese Zeichen getrennt
    | Einzelne Suchbegriffe werden für die Oder-Suche durch dieses Zeichen getrennt
    - Dieses Zeichen wird ohne Leerzeichen vor dem Suchbegriff gesetzt, der nicht enthalten sein soll
    " " Mehrere Suchbegriffe, die zu einer Phrase verbunden werden sollen, werden von diesen Zeichen umschlossen
    * Platzhalter für eine unbekannte Zeichenanzahl am Wortende
    ( ) Mehrere Suchbegriffe, die zu einer Gruppe zusammengefasst werden sollen, werden von diesen Zeichen umschlossen
    \ Um nach einem Sonderzeichen zu suchen, muss dieses Zeichen dem Sonderzeichen vorangestellt werden
    Groß- und Kleinschreibung wird bei der Suche nicht berücksichtigt

```
* min_pages und max_pages: Die Datei wird nur verändert, wenn die Seitenzahl innerhalb dieser Begrenzungen liegt. Funktioniert aktuell nur mit PDF-Dateien. Soll die Datei genau eine Seitenzahl enthalten, können beide Werte auch gleich sein.
* search_props: Diese Eigenschaften müssen gesetzt sein, damit das Dokument beachtet wird. Eigenschaftsnamen und -werte werden per Doppelpunkt getrennt. Mehrere Eigenschaftswerte werden per Pipe getrennt. Werden mehrere Eigenschaftspaare verwendet, müssen beide für einen Match zutreffen (UND-Verknüpfung)
* set_props: Diese Eigenschaften werden gesetzt/verändert. Auch hier gilt die Abgrenzung der Paare per Pipe und die Abgrenzung von Name zu Wert per Doppelpunkt

### Benutzung
Wurde die Konfiguration und Profileinrichtung durchgeführt, kann die Anwendung einmalig oder per Cronjob ausgeführt werden:  
```python3 main.py```

#### Kommandozeilenargumente
* whatif: Um zu prüfen, ob die Profileinrichtung erfolgreich war, kann der Parameter "whatif" genutzt werden. Es werden dann keine Änderungen am DMS durchgeführt, sondern nur angezeigt, wie viele Dokumente pro Profil betroffen wären.
```
python3 main.py --whatif
```
* verbose (nur in Verbindung mit whatif): Wird der Verbose-Parameter mit angegeben, wird der Titel jedes betroffenen Dokumentes mit ausgegeben. Es werden ebenfalls keine Änderungen durchgeführt
```
python3 main.py --whatif --verbose
```