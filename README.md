# Grafika Differ - Image Analysis Framework

Cross-platform automation framework with support for both Windows and Linux/X11:

- Replays recorded mouse event scripts with your graphics application (script mode)
- Compares images from two screenshot runs using pixel-wise absolute differences (comparison mode)  
- Opens interactive viewer for viewing two runs (and optional diff) with side-by-side, overlay, and "split" views (interactive mode)

Platform support:
- **Windows**: pywinauto and Windows UI automation
- **Linux**: X11 automation with python-xlib, psutil, and xdotool

Main entry point: `python src/main.py`


## Installation and Setup

### Prerequisites

#### Python Dependencies
Install required Python packages:
```bash
pip install -r requirements.txt
```

#### Windows
For Windows automation support:
```bash
pip install pywinauto
```

#### Linux
Linux dependencies:
- **X11 server**: Ensure X11 server is running (default on most Linux desktop environments)
- **Screenshot tools**: `scrot`, `imagemagick`, or `xwd` (at least one required)
- **Input tools**: `xdotool` (recommended for better reliability)
- **System packages**:

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3-venv python3-dev scrot imagemagick xdotool

# Fedora/RHEL
sudo dnf install python3-venv python3-devel scrot ImageMagick xdotool

# Arch Linux
sudo pacman -S python-venv python-devtools scrot imagemagick xdotool
```

### Setting up the environment

Create and activate a virtual environment:
```bash
# Using the setup script
./create_venv_and_install.sh

# Or manually
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

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

## Usage Examples

### Windows
1) **Run script mode to replay events and capture screenshots:**

```powershell
python src/main.py --mode script --script events.txt --exe .\glProgram\x64\Debug\GreenTriangle.exe --window-title "Green triangle" --output .\screenshots\run01 --capture-delay 0.05
```

2) **Repeat for second run:**

```powershell
python src/main.py --mode script --script events.txt --exe .\glProgram\x64\Debug\GreenTriangle.exe --window-title "Green triangle" --output .\screenshots\run02 --capture-delay 0.05
```

3) **Generate pixel-wise absolute differences:**

```powershell
python src/main.py --mode comparison --inputs .\screenshots\run01 .\screenshots\run02 --output .\screenshots\comparison01
```

4) **View interactively:**

```powershell
python src/main.py --mode interactive --inputs .\screenshots\run01 .\screenshots\run02 .\screenshots\comparison01
```

### Linux
1) **Run script mode to replay events and capture screenshots:**

```bash
python src/main.py --mode script --script events.txt --exe ./GreenTriangle --window-title "Green triangle" --output ./screenshots/run01 --capture-delay 0.05
```

2) **Repeat for second run:**

```bash
python src/main.py --mode script --script events.txt --exe ./GreenTriangle --window-title "Green triangle" --output ./screenshots/run02 --capture-delay 0.05
```

3) **Generate pixel-wise absolute differences:**

```bash
python src/main.py --mode comparison --inputs ./screenshots/run01 ./screenshots/run02 --output ./screenshots/comparison01
```

4) **View interactively:**

```bash
python src/main.py --mode interactive --inputs ./screenshots/run01 ./screenshots/run02 ./screenshots/comparison01
```

### ⚡ Enhanced Workflow (OpenRouter AI Analysis)

#### 1. Stealth Mode Usage (Recommended - No Code Injection Required)

```bash
# First run (no code injection needed)
python src/main.py --mode stealth --exe ./GreenTriangle --output ./screenshots/run01 --delta 100 --length 3000 --capture-delay 0.05

# Second run (same parameters)
python src/main.py --mode stealth --exe ./GreenTriangle --output ./screenshots/run02 --delta 100 --length 3000 --capture-delay 0.05
```

#### 2. Generate Difference Images

```bash
python src/main.py --mode comparison --inputs ./screenshots/run01 ./screenshots/run02 --output ./screenshots/comparison01
```

#### 3. AI-Powered Analysis with OpenRouter

```bash
# Set API key
export OPENROUTER_API_KEY='your_key_here'

# Run AI analysis (GPT-4o-mini model recommended)
python src/analyze_images.py \
    --inputs ./screenshots/run01 ./screenshots/run02 \
    --diff-dir ./screenshots/comparison01 \
    --output ./analysis_results \
    --model openai/gpt-4o-mini \
    --rate-limit 1.0

# View results
cat ./analysis_results/_summary.txt
cat ./analysis_results/*_analysis.txt
```

#### 4. Automated Complete Workflow

```bash
# Using the analysis script (.env file automatically loaded)
./analyze_differences.sh \
    -a ./screenshots/run01 \
    -b ./screenshots/run02 \
    --diff-dir ./screenshots/comparison01 \
    -o ./analysis_results

# With environment variable
export OPENROUTER_API_KEY='your_key_here'
./analyze_differences.sh \
    -a ./screenshots/run01 \
    -b ./screenshots/run02 \
    --diff-dir ./screenshots/comparison01 \
    -o ./analysis_results
```

### Stealth Mode (No Code Injection Required)

If you don't want to inject time stamping/logging into your own program, you can use stealth mode, which simply captures screenshots at fixed intervals for a given duration.

Example (5 seconds, 50ms period, 0.05s extra delay before each screenshot):

#### Windows
```powershell
# Short form: EXE path can be provided as positional argument
python src/main.py --mode stealth .\glProgram\x64\Debug\GreenTriangle.exe --window-title "Green triangle" --output .\screenshots\run02 --capture-delay 0.05 --delta 50 --length 5000

# Official form: with --exe flag
python src/main.py --mode stealth --exe .\glProgram\x64\Debug\GreenTriangle.exe --window-title "Green triangle" --output .\screenshots\run02 --capture-delay 0.05 --delta 50 --length 5000
```

#### Linux
```bash
# Short form: EXE path can be provided as positional argument
python src/main.py --mode stealth ./GreenTriangle --window-title "Green triangle" --output ./screenshots/run02 --capture-delay 0.05 --delta 50 --length 5000

# Official form: with --exe flag
python src/main.py --mode stealth --exe ./GreenTriangle --window-title "Green triangle" --output ./screenshots/run02 --capture-delay 0.05 --delta 50 --length 5000
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

## 🧪 Tesztelés és validáció

### Built-in Testing
```bash
# Environment and dependencies check
cd test
python test_setup.py

# OpenGL/GLFW application testing
export DISPLAY=:0
source .venv/bin/activate
python src/main.py --mode stealth --exe ./test/example_executables/example1 --output ./test_run --delta 100 --length 1000
```

### Valós tesztelési eredmények
✅ **Sikeresen tesztelve** Linux/Fedora környezetben
✅ **Ablakkeresés javítása**: Többstratégiás detektálás (PID, cím, fallback)
✅ **Valós alkalmazások**: GLFW/OpenGL alapú programok
✅ **AI elemzés**: OpenRouter GPT-4o-mini sikeres integráció
✅ **Teljes munkafolyamat**: Stealth → Comparison → AI Analysis
✅ **Új projekt szerkezet**: Teszt fájlok a `test/` mappában
✅ **`.env` fájl támogatás**: API kulcsok automatikus betöltése

### Teljesítmény optimalizálás
```bash
# Ajánlott paraméterek stabil képrögzítéshez
--delta 100          # 100ms间隔 (good balance)
--length 3000        # 3 másodperc rögzítés
--capture-delay 0.05 # Extra várakozás minden képhoz

# Rate limiting beállítása API-hoz
--rate-limit 1.0     # 1 másodperc a képek között
```

## Tippek stabil, megismételhető képkivágáshoz

- Használd a **stealth módot** kódinjektálás nélküli teszteléshez (ajánlott)
- Használd a kliens-területi kivágást (alapértelmezett); az OS felület és értesítések zajt vihetnek a képekbe.
- Adj `--capture-delay 0.03`–`0.10` másodpercet, hogy a frame teljesen kirajzolódjon.
- Kerüld az átfedő ablakokat, tooltipeket, illetve a kézi egérmozgatást felvétel közben.
- Tartsd állandóan az ablak méretét és a DPI skálázást a futások között.
- Használd ugyanazt a `--window-title` értéket, és lehetőleg ne válts ablakot indítás közben.
- **Linux/X11**: A javított ablakkeresés automatikusan alkalmazkodik - nincs szükség pontos cím megadására

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
- **Failed to locate window**: 
  - **Linux/X11 javított ablakkeresés**: A framework most már többféle stratégiát használ:
    1. **Cím alapú keresés** (meglévő viselkedés)
    2. **Folyamat alapú keresés** (új, megbízhatóbb): `xdotool search --pid`
    3. **Bármilyen látható ablak** (fallback)
  - Ha a régi módszer nem működik, használd a `--window-title` paramétert vagy hagyd üresen a folyamat alapú kereséshez
  - Az ablak információk lekéréséhez használd: `xprop WM_NAME` vagy `xdotool search --class <class_name>`
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

Make these modifications in the `src/` module files as appropriate.

## 🆕 Új funkciók és fejlesztések

### Javított Linux/X11 ablakkeresés
- **Többstratégiás ablakfelismerés**: A framework automatikusan próbálja:
  1. Cím alapú keresés (legacy viselkedés)
  2. **Folyamat ID alapú keresés** (új, megbízhatóbb)
  3. Fallback: bármilyen látható ablak keresése
- **Eredmény**: Sokkal megbízhatóbb ablakdetektálás különböző GUI alkalmazásoknál

### Automatizált munkafolyamat
- **`analyze_differences.sh`**: Teljes munkafolyamat egy parancsban
- **Dry-run mód**: API költségek nélküli teszteléshez
- **Javított hibakezelés**: Részletesebb hibajelentések és recovery opciók

## AI-alapú képelemzés (OpenRouter integráció)

A `image_analysis_openrouter.py` szkript OpenRouter API-n keresztül használja a GPT-4o-mini modellt (ajánlott) vagy más multimodális modelleket a képek közötti különbségek részletes szöveges leírásához. Ez lehetővé teszi, hogy nem-multimodális LLM-ek is elemezzék a vizuális változásokat.

### Telepítés és beállítás

1. **API kulcs beszerzése:**
   - Regisztrálj az [OpenRouter](https://openrouter.ai/) oldalon
   - Generálj egy API kulcsot
   - **Opció 1**: Szerkeszd a `.env` fájlt a projekt root-jában:
     ```bash
     OPENROUTER_API_KEY=your_key_here
     ```
   - **Opció 2**: Állítsd be környezeti változóként:
     ```bash
     export OPENROUTER_API_KEY=your_key_here
     ```

2. **Függőségek:**
   A `requests` csomag szükséges, ami már szerepel a `requirements.txt`-ben.

### Használat

#### Alapvető használat (.env fájl használata)
```bash
# API kulcs beállítása a .env fájlban (automatikusan betöltve)
python image_analysis_openrouter.py \
    --inputs screenshots/run01 screenshots/run02 \
    --output analysis_results
```

#### Környezeti változó használata
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
    --model openai/gpt-4o-mini \
    --prompt "Csak a színbeli különbségeket írd le részletesen"
```

#### Tesztelés API költségek nélkül (Dry Run mód)
```bash
python image_analysis_openrouter.py \
    --api-key your_key_here \
    --inputs screenshots/run01 screenshots/run02 \
    --diff-dir screenshots/comparison01 \
    --output analysis_results \
    --dry-run

# A dry-run request format megtekinthető:
cat analysis_results/dry_runs/dry_run_request_*.txt
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
- `--model NAME`: OpenRouter modell neve (ajánlott: `openai/gpt-4o-mini` vision elemzéshez)
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

### Példa elemzési kimenet

A rendszer sikeresen elemezte a valós grafikus alkalmazásokat:

**Bemenet**: 2 futás képei geometriai alakzatokkal (henger, kúp, téglatest)
**Kimenet**: Részletes elemzés, amely tartalmazza:
- Vizuális különbségek (pozíció, szín, méret változások)
- Szemantikus értelmezés (animáció, állapotváltozások)
- Kvantitatív megfigyelések (pixel elmozdulások, koordináták)

### Telepített AI modellek és árak

| Modell | Típus | Ár (prompt/completion) | Ajánlás |
|--------|-------|----------------------|---------|
| `openai/gpt-4o-mini` | Multimodális | $0.15/$0.60 per 1M token | ⭐ **Ajánlott** |
| `google/gemini-2.0-flash-thinking-exp:free` | Ingyenes | Ingyenes | Limitált capacity |
| `anthropic/claude-3-opus` | Multimodális | $15/$75 per 1M token | Prémium minőség |

### Megjegyzések

- A szkript PNG formátumú képeket dolgo fel
- Az API kérések között 1 másodperc késleltetés van a rate limiting miatt (módosítható a `--rate-limit` paraméterrel)
- A modell részletes, formázatlan szöveget generál, amely könnyen feldolgozható nem-multimodális LLM-ek által
- A különbségi képek opcionálisak, de segítik a pontosabb elemzést
- Az elemzések UTF-8 kódolású szöveges fájlokban kerülnek mentésre
- **Dry-run mód** elérhető a költségmentes teszteléshez
- **Javított ablakkeresés** Linux/X11 rendszereken automatikusan alkalmazkodik a különböző GUI alkalmazásokhoz

## Project Structure

The project has been refactored into a modular structure:

```
grafika_differ/
├── src/                          # Main source code
│   ├── main.py                   # Modern entry point (replaces automation_framework.py)
│   ├── analyze_images.py         # AI-powered image analysis
│   ├── analysis/                 # Image analysis modules
│   ├── core/                     # Automation framework core
│   ├── platform/                 # Platform-specific implementations
│   ├── ui/                       # User interface components
│   └── utils/                    # Utility functions
├── test/                         # Test files and examples
├── tests/                        # Unit tests
├── run_automation.sh            # Linux launcher (updated)
├── analyze_differences.sh       # Complete workflow script (updated)
└── DOCUMENTATION.md             # Detailed project documentation
```

## Migration from Legacy Code

If you were using `automation_framework.py` previously, the main changes are:

- **Old**: `python automation_framework.py --mode script ...`
- **New**: `python src/main.py --mode script ...`

All functionality remains the same, but the code is now better organized and maintainable.

## License
MIT