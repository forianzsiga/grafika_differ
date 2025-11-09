# GreenTriangle automatizációs keretrendszer

Cross-platform automatizálási keretrendszer, amely támogatja mind a Windows-t, mind a Linux/X11-et:

- Rögzített egéresemény-szkripteket játszik vissza a grafika háziddal (script mód)
- Két képrögzítési futás képeit hasonlítja össze pixelenkénti abszolút különbséggel (comparison mód)
- Interaktív nézőt nyit a két futás (és opcionális diff) megtekintéséhez egymás melletti, átfedéses és „split" nézettel (interactive mód)

Platform támogatás:
- **Windows**: pywinauto és Windows UI automation
- **Linux**: X11 automation with python-xlib, psutil, és xdotool

Fájl: `automation_framework.py`


## Telepítés és előkészületek

### Windows
0. **helper kód implementálása a saját projektedben:**

A programnak szüksége van egy olyan jól formattált stdout kimenetre, amely tartalmazza az egéreseményeket (lásd a „transzkript formátum” részt lent). Ezt a kimenetet a saját programodban kell előállítanod. Példa:

Sajnos a hülye keretrendszer nem enged semmit importálni, így időmérést bele kell iktatni a programod loopjába:

 
>**FONTOS! ⚠️⚠️⚠️**

> Ha nem Stealth módban futtatod a programot, azaz tervezed a beillesztett kódot feltölteni, a kódodba ékelj be néhány használatlan változót! Az alap MOSS implementációt ez az egyszerű trükk megzavarhatja. Csak a változónév átírása nem elég, ténylegesen legyenek használatlan változók a kódban. Ha csak bemásolod a kódot, az másokkal együtt növeli a plágiumdetektálás esélyét, de önmagában nem kéne, hogy átbillentse a tresholdot. Figyelj erre!

>Emellett ha valaki már az adott házihoz futtatott nem stealth módban sikeres feladatot, akkor el is tudod csak kérni az stdout kimenetet tőle, így nem kell a kódodba beépíteni ezt a részt!

>Ha nincs ilyenre lehetőséged, és nem is akarsz kockázatot vállalni, írhatsz magadtól is egy event.txt fájlt a transzkript formátum alapján, és azt használhatod a script módhoz.

```cpp
namespace {
	static double g_elapsedSeconds = 0.0;
	static bool g_elapsedInitialized = false;

	void setAppStart() {
		g_elapsedSeconds = 0.0;
		g_elapsedInitialized = true;
	}

	void addElapsed(double dt) {
		if (!g_elapsedInitialized) setAppStart();
		g_elapsedSeconds += dt;
	}

	void formatElapsed(char* buf, size_t bufsz) {
		if (!g_elapsedInitialized) {
			snprintf(buf, bufsz, "+0.000s");
			return;
		}
		long long secs = (long long)g_elapsedSeconds;
		long long rem = (long long)((g_elapsedSeconds - (double)secs) * 1000.0 + 0.5);
		if (rem >= 1000) { secs += 1; rem -= 1000; }
		snprintf(buf, bufsz, "+%lld.%03llds", secs, rem);
	}

	void debugPrintf(const char* fmt, ...) {
		char timebuf[32];
		formatElapsed(timebuf, sizeof(timebuf));
		printf("[ %s ] ", timebuf);
		va_list args;
		va_start(args, fmt);
		vprintf(fmt, args);
		va_end(args);
		fflush(stdout);
	}
}
```

Elindításhoz hívd meg a `setAppStart()`-ot, a fő loop-ban pedig minden frame-ben hívd meg az `addElapsed(dt)`-t, ahol `dt` az előző frame óta eltelt idő másodpercben.

```cpp
...
GreenTriangleApp() : glApp("Green triangle") { setAppStart(); }
...
```

```cpp
...
void onTimeElapsed(float startTime, float endTime) override {
	float dt = endTime - startTime;
	if (dt <= 0.0f) return;

	addElapsed((double)dt);
		const float maxStep = 0.02f;
		float remaining = dt;
		while (remaining > 0.0f) {
			float step = std::min(remaining, maxStep);
			// A te frissítési logikád itt jön
			remaining -= step;
		}
		// Egyéb renderelési logika
	}
...
```
Emellett fontos, hogy az stdoutra íráshoz használd a `debugPrintf`-et!

1. **Függőségek telepítése:**

#### Windows
Futtasd a `create_venv_and_install.bat` fájlt a virtuális környezet létrehozásához és a függőségek telepítéséhez. Ez megnyit egy új PowerShell ablakot az aktivált környezettel, ahol futtathatod a parancsokat.

```powershell
.\create_venv_and_install.bat
```

#### Linux
Futtasd a `create_venv_and_install.sh` fájlt vagy használd a `run_automation.sh` launchert:

```bash
# Válassz egyet:
./create_venv_and_install.sh
# vagy
./run_automation.sh --help
```

Linux függőségek:
- **X11 szerver**: Győződj meg róla, hogy az X11 szerver fut (többnyire alapértelmezett Linux desktop környezetekben)
- **Screenshot eszközök**: `scrot`, `imagemagick` vagy `xwd` (legalább egy szükséges)
- **Input eszköz**: `xdotool` (ajánlott jobb megbízhatóságért)
- **System packages**: A Python csomagok telepítése előtt:

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3-venv python3-dev scrot imagemagick xdotool

# Fedora/RHEL
sudo dnf install python3-venv python3-devel scrot ImageMagick xdotool

# Arch Linux
sudo pacman -S python-venv python-devtools scrot imagemagick xdotool
```

2. **Eventek kinyerése:**

JPortán megtalálható stdout kimenetet mentsd le egy fájlba. Az itteni kimeneti mintát meg kell valósítanod a saját programodban hogy a program felismerje az eseményeket.
![stdout.png](./stdout.png)

## Használati példa

Először futtasd a megfelelő scriptet a környezet beállításához. Ez után minden parancsot a terminálban futtass, ahol a virtuális környezet aktiválva van.

### Windows
2) **Futtasd a script módot az események visszajátszásához és képernyőképek mentéséhez:**

```powershell
python automation_framework.py --mode script --script events.txt --exe .\glProgram\x64\Debug\GreenTriangle.exe --window-title "Green triangle" --output .\screenshots\run01 --capture-delay 0.05
```

3) **Ismételd meg a második futáshoz:**

```powershell
python automation_framework.py --mode script --script events.txt --exe .\glProgram\x64\Debug\GreenTriangle.exe --window-title "Green triangle" --output .\screenshots\run02 --capture-delay 0.05
```

4) **Készíts képenkénti abszolút különbségeket:**

```powershell
python automation_framework.py --mode comparison --inputs .\screenshots\run01 .\screenshots\run02 --output .\screenshots\comparison01
```

5) **Nézd meg interaktívan:**

```powershell
python automation_framework.py --mode interactive --inputs .\screenshots\run01 .\screenshots\run02 .\screenshots\comparison01
```

### Linux
2) **Futtasd a script módot az események visszajátszásához és képernyőképek mentéséhez:**

```bash
./run_automation.sh --mode script --script events.txt --exe ./GreenTriangle --window-title "Green triangle" --output ./screenshots/run01 --capture-delay 0.05
```

3) **Ismételd meg a második futáshoz:**

```bash
./run_automation.sh --mode script --script events.txt --exe ./GreenTriangle --window-title "Green triangle" --output ./screenshots/run02 --capture-delay 0.05
```

4) **Készíts képenkénti abszolút különbségeket:**

```bash
./run_automation.sh --mode comparison --inputs ./screenshots/run01 ./screenshots/run02 --output ./screenshots/comparison01
```

5) **Nézd meg interaktívan:**

```bash
./run_automation.sh --mode interactive --inputs ./screenshots/run01 ./screenshots/run02 ./screenshots/comparison01
```

### Stealth mód (kód injektálás nélkül)

Ha nem szeretnél a saját programodba időbélyeget/naplózást injektálni, használhatod a stealth módot, ami egyszerűen csak képkivágásokat készít megadott időközönként egy adott időtartamon keresztül.

Példa (5 másodpercig, 50 ms periódussal, 0.05 s extra késleltetéssel minden képkivágás előtt):

#### Windows
```powershell
# Rövid forma: az EXE útvonal megadható pozicionális argumentumként is
python automation_framework.py --mode stealth .\glProgram\x64\Debug\GreenTriangle.exe --window-title "Green triangle" --output .\screenshots\run02 --capture-delay 0.05 --delta 50 --length 5000

# Hivatalos forma: --exe kapcsolóval
python automation_framework.py --mode stealth --exe .\glProgram\x64\Debug\GreenTriangle.exe --window-title "Green triangle" --output .\screenshots\run02 --capture-delay 0.05 --delta 50 --length 5000
```

#### Linux
```bash
# Rövid forma: az EXE útvonal megadható pozicionális argumentumként is
./run_automation.sh --mode stealth ./GreenTriangle --window-title "Green triangle" --output ./screenshots/run02 --capture-delay 0.05 --delta 50 --length 5000

# Hivatalos forma: --exe kapcsolóval
./run_automation.sh --mode stealth --exe ./GreenTriangle --window-title "Green triangle" --output ./screenshots/run02 --capture-delay 0.05 --delta 50 --length 5000
```

## Módok

### script
Szöveges transzkriptből visszajátssza az egéreseményeket, fókuszálja a célt ablakot, a felvett kliens-területi koordinátákra kattint, és minden esemény után képernyőképet ment (indítás után és kilépés előtt is).

Kötelező paraméterek:
- `--script PATH` — transzkript fájl (pl. `events.txt`)
- `--exe PATH` — a `GreenTriangle.exe` elérési útja

Hasznos paraméterek:
- `--window-title TEXT` — a főablak pontos címe (ha üres, a legfelső ablakot keresi)
- `--output DIR` — a képernyőképek célkönyvtára (alapból a `--screenshots` értéke)
- `--screenshots DIR` — régi kimeneti kapcsoló (akkor használatos, ha nincs `--output`)
- `--capture-delay FLOAT` — extra várakozás minden képkivágás előtt a stabil frame-hez (pl. `0.05`)
- `--pointer-duration FLOAT` — egérmozgatás animációjának hossza (másodperc)
- `--launch-wait FLOAT` — plusz várakozás, miután az ablak kész
- `--window-timeout FLOAT` — a főablak megjelenéséig várakozás
- `--exit-timeout FLOAT` — a folyamat kilépéséig várakozás a lejátszás végén
- `--log-level {DEBUG,INFO,WARNING,ERROR}`

Kimenet elnevezése:
- A fájlnevek futó indexet és eseménycímkét tartalmaznak, pl. `000_0000_after_launch.png`, `001_000_..._mouse_press_left.png`.
- Elsődlegesen a kliens-területet vágja ki; hiba esetén teljes ablakra vagy teljes képernyőre esik vissza.

### comparison
Abszolút (pixelenkénti) különbséget készít két könyvtár azonos nevű képfájljai között. A különbség a `PIL.ImageChops.difference` műveletének felel meg, amely csatornánkénti abszolút különbséget számol.

Kötelező paraméterek:
- `--inputs DIR_A DIR_B` — két bemeneti könyvtár, egyező nevű `.png` fájlokkal
- `--output DIR` — az `_diff.png` képek célkönyvtára

Viselkedés:
- Csak a mindkét könyvtárban megtalálható fájlneveket dolgozza fel.
- Méreteltérés esetén a képet kihagyja és figyelmeztet.
- Az egyezés nélkülieket naplózza és kihagyja.

### interactive
Egyszerű képnézegetőt nyit két futás (és opcionálisan egy előre legenerált diff-könyvtár) képeihez.

Paraméterek:
- `--inputs DIR_A DIR_B [DIR_DIFF]` — két kötelező könyvtár; a harmadik (opcionális) a diff nézethez

Billentyűparancsok:
- `Left` / `Right` — előző / következő kép
- `1` — egymás mellett (A | B)
- `2` — átfedés (A a B-n), állítható alphával
- `3` — split nézet (A balra, B jobbra), húzható elválasztóval
- `4` — diff (ha van előre számolt diff, azt mutatja; különben menet közben számol)
- `[` / `]` — átfedés alpha csökkentése / növelése
- `,` / `.` — split pozíció balra / jobbra
- `F` — képernyőhöz igazítás ki/be
- `H` vagy `?` — súgósor ki/be

Vizuális segítség:
- Split módban egy sárga függőleges vonal jelöli a pontos elválasztási pozíciót.
- A kurzor split módban vízszintes átméretezésre vált a jobb érthetőségért.

### stealth
Kód injektálása nélkül képkockákat rögzít az alkalmazás kliens-területéről állandó időközönként.

Kötelező/hasznos paraméterek:
- `--exe PATH` — a cél `GreenTriangle.exe` elérési útja (stealth módban pozicionálisan is megadható az `--exe` helyett)
- `--window-title TEXT` — a főablak pontos címe (ha üres, a legfelső ablakot keresi)
- `--output DIR` — a képernyőképek célkönyvtára (alapból a `--screenshots` értéke)
- `--delta INT(ms)` — képkivágások közti időköz milliszekundumban (alapértelmezés: 50)
- `--length INT(ms)` — teljes rögzítési idő milliszekundában (alapértelmezés: 5000)
- `--capture-delay FLOAT` — extra várakozás másodpercben minden képkivágás előtt (pl. `0.05`)

Viselkedés:
- Indítás után készít egy kezdeti képet (`after_launch`), majd `--delta` szerint időzíti a rögzítést a megadott `--length` időtartamig, végül egy záró képet (`after_stealth`).
- Elsődlegesen a kliens-területet vágja ki; hiba esetén teljes ablakra vagy teljes képernyőre esik vissza.

## Tippek stabil, megismételhető képkivágáshoz

- Használd a kliens-területi kivágást (alapértelmezett); az OS felület és értesítések zajt vihetnek a képekbe.
- Adj `--capture-delay 0.03`–`0.10` másodpercet, hogy a frame teljesen kirajzolódjon.
- Kerüld az átfedő ablakokat, tooltipeket, illetve a kézi egérmozgatást felvétel közben.
- Tartsd állandóan az ablak méretét és a DPI skálázást a futások között.
- Használd ugyanazt a `--window-title` értéket, és lehetőleg ne válts ablakot indítás közben.

## Hibaelhárítás

- **Nincs összehasonlítási kimenet:** figyelj, hogy az útvonal ne egy magányos backslash-sel kezdődjön (használd a `.\screenshots\comparison01` formát vagy abszolút utat). A program a hiányzó könyvtárakat létrehozza.
- **Ablak nem található:** ellenőrizd a `--window-title` értékét, és hogy az EXE látható UI-t nyit-e a `--window-timeout` időn belül.
- **Jogosultsági gondok:** ha más folyamat blokkolja az UI automatizálást, futtasd a terminált Rendszergazdaként.
- **Hiányzó Tkinter:** az interaktív módhoz szükséges. A Windowsos Python telepítő tartalmazza; egyedi disztribúciónál engedélyezd/telepítsd.
- **Lag:** Ha a grafika program elfoglal egy teljes magot, a visszajátszás és képkivágás közben a rendszer túlterhelődhet, ami késleltetést okozhat az események feldolgozásában. Próbáld meg növelni a `--capture-delay` értékét, vagy futtasd a grafika programot egy kevésbé terhelt környezetben. így sem garantált a pontos időzítés! Erre egy másik megoldás lehet ha kérsz egy executablet, ahol a dt meg van szorozva egy kis értékkel, így a program „lassabban” fut, és több idő jut az események feldolgozására.

### Linux/X11 hibák
- **"DISPLAY environment variable not set":** Győződj meg róla, hogy X11 szerver fut. Ha SSH-n keresztül dolgozol, használd az `-X` vagy `-Y` kapcsolót (`ssh -X user@host`).
- **"No screenshot tool available":** Telepíts legalább egy screenshot eszközt: `sudo apt install scrot` vagy `sudo apt install imagemagick`.
- **"xdotool not found":** Telepítsd a `xdotool`-t: `sudo apt install xdotool` (ajánlott jobb input kezelésért).
- **"Failed to locate window":** Ellenőrizd a `--window-title` értékét. Linux-on a pontos ablakcím szükséges. Használd a `xprop` eszközt az ablak információk lekéréséhez: `xprop WM_NAME`.
- **Permission denied a képernyőképek mentésénél:** Győződj meg róla, hogy van írási jogod a célkönyvtárban.
- **X11 hiba: BadWindow:** Ez általában akkor történik, ha az ablak bezáródik az automatizálás közben. Növeld a `--window-timeout` értékét.

## Transzkript formátum
Példa eseménysorok (idők relatívak):

```
[ +0.370s ] onMousePressed L: window(100,100) -> world(-16.666666,16.666666)
[ +0.370s ] onMouseReleased L: window(100,100) -> world(-16.666666,16.666666)
[ +4.370s ] Exiting application
```

A parser a következőket olvassa ki:
- Eseményidőzítés (delta) és monoton per-esemény késleltetés
- Egér lenyomás/felengedés bal/jobb gombbal
- Opcionális ablakkoordináta és világkoordináta (a visszajátszáshoz az ablakkoordinátát használja)

Ezeket a módosításokat a `automation_framework.py` fájlban végezd el.

## AI-alapú képelemzés (OpenRouter integráció)

A `image_analysis_openrouter.py` szkript OpenRouter API-n keresztül használja a Gemini 2.5 Pro modellt a képek közötti különbségek részletes szöveges leírásához. Ez lehetővé teszi, hogy nem-multimodális LLM-ek is elemezzék a vizuális változásokat.

### Telepítés és beállítás

1. **API kulcs beszerzése:**
   - Regisztrálj az [OpenRouter](https://openrouter.ai/) oldalon
   - Generálj egy API kulcsot
   - Állítsd be környezeti változóként: `export OPENROUTER_API_KEY=your_key_here`

2. **Függőségek:**
   A `requests` csomag szükséges, ami már szerepel a `requirements.txt`-ben.

### Használat

#### Alapvető használat (környezeti változóból származó API kulccsal)
```bash
export OPENROUTER_API_KEY=your_key_here

python image_analysis_openrouter.py \
    --inputs screenshots/run01 screenshots/run02 \
    --output analysis_results
```

#### API kulcs parancssorból
```bash
python image_analysis_openrouter.py \
    --api-key your_key_here \
    --inputs screenshots/run01 screenshots/run02 \
    --output analysis_results
```

#### Különbségi képekkel együtt
```bash
python image_analysis_openrouter.py \
    --api-key your_key_here \
    --inputs screenshots/run01 screenshots/run02 \
    --diff-dir screenshots/comparison01 \
    --output analysis_results
```

#### Egyéni modell és prompt
```bash
python image_analysis_openrouter.py \
    --api-key your_key_here \
    --inputs screenshots/run01 screenshots/run02 \
    --output analysis_results \
    --model google/gemini-2.0-flash-thinking-exp:free \
    --prompt "Csak a színbeli különbségeket írd le részletesen"
```

### Kimenet

A szkript minden képpárhoz létrehoz egy `*_analysis.txt` fájlt a megadott kimeneti könyvtárban. Minden fájl tartalmazza:

1. **Metaadat fejléc:** A vizsgált képek elérési útjai
2. **Részletes elemzés:**
   - Vizuális különbségek (pozíció, szín, megjelenés)
   - Szemantikus jelentés (mit reprezentálnak a változások)
   - Kvantitatív megfigyelések (méretek, elmozdulások)
   - Különbségi kép elemzése (ha elérhető)

Emellett létrejön egy `_summary.txt` fájl, amely összefoglalja az összes elemzést.

### Paraméterek

- `--api-key`: OpenRouter API kulcs (opcionális, ha `OPENROUTER_API_KEY` környezeti változó be van állítva)
- `--inputs DIR_A DIR_B`: Két bemeneti könyvtár az összehasonlítandó képekkel (kötelező)
- `--diff-dir DIR`: Opcionális könyvtár a különbségi képekkel (amelyeket a `comparison` mód generált)
- `--output DIR`: Kimeneti könyvtár az elemzési szövegfájlok számára (kötelező)
- `--model NAME`: OpenRouter modell neve (alapértelmezett: `google/gemini-2.0-flash-thinking-exp:free`)
- `--prompt TEXT`: Egyéni prompt az elemzéshez (opcionális)
- `--rate-limit FLOAT`: Késleltetés az API kérések között másodpercben (alapértelmezett: 1.0)
- `--log-level LEVEL`: Naplózási szint (DEBUG, INFO, WARNING, ERROR)

### Tipikus munkafolyamat

1. **Képek generálása:**
   ```bash
   # Első futás
   ./run_automation.sh --mode script --script events.txt \
       --exe ./GreenTriangle --window-title "Green triangle" \
       --output ./screenshots/run01 --capture-delay 0.05

   # Második futás
   ./run_automation.sh --mode script --script events.txt \
       --exe ./GreenTriangle --window-title "Green triangle" \
       --output ./screenshots/run02 --capture-delay 0.05
   ```

2. **Különbségek generálása:**
   ```bash
   ./run_automation.sh --mode comparison \
       --inputs ./screenshots/run01 ./screenshots/run02 \
       --output ./screenshots/comparison01
   ```

3. **AI elemzés futtatása:**
   ```bash
   export OPENROUTER_API_KEY=your_key_here
   python image_analysis_openrouter.py \
       --inputs screenshots/run01 screenshots/run02 \
       --diff-dir screenshots/comparison01 \
       --output analysis_results
   ```

4. **Eredmények áttekintése:**
   ```bash
   # Összefoglaló megtekintése
   cat analysis_results/_summary.txt
   
   # Egyedi elemzések olvasása
   cat analysis_results/000_0000_after_launch_analysis.txt
   ```

### Megjegyzések

- A szkript PNG formátumú képeket dolgoz fel
- Az API kérések között 1 másodperc késleltetés van a rate limiting miatt (módosítható a `--rate-limit` paraméterrel)
- A modell részletes, formázatlan szöveget generál, amely könnyen feldolgozható nem-multimodális LLM-ek által
- A különbségi képek opcionálisak, de segítik a pontosabb elemzést
- Az elemzések UTF-8 kódolású szöveges fájlokban kerülnek mentésre

## Licenc
MITtudom én, nem vagyok jogász, csak egy vibecoder mérnöktanonc.