# Bachelorarbeit Pitch

## KI-gestützte Optimierung von Produktions- und Schichtplänen bei Ritter Sport

### 1. Situationsanalyse

| Wochentag | Ø Gesamtproduktionsstunden | Ø aktive Linien (max = 5) |  |
| --- | --- | --- | --- |
| **Mo** | ≈ 236 h | 4,3 |  |
| **Di** | ≈ 280 h | 4,6 |  |
| **Mi** | ≈ 230 h | 4,3 |  |
| **Do** | ≈ 149 h | 3,0 |  |
| **Fr** | ≈ 37 h | 1,4 |  |
- Vier der fünf Linien laufen von Montag bis Mittwoch nahezu voll aus, danach nimmt die Auslastung ab; freitags herrscht nahezu Stillstand.
- Die Linienauslastung ist unausgewogen: **massiv 3** (‑2.181 h) und **hohl 3** (‑2.117 h) tragen die Hauptlast, während **hohl 4** in acht Wochen weniger als 700 h beiträgt.
- Kalenderwochen 28–35 zeigen einen Anstieg der Wochenstunden (558 h → 1.370 h), ohne dass sich das „frontlastige“ Muster ändert.

Diese Befunde bestätigen das von Jörg Schweinberger beschriebene Problem: Zu viele Schichtleiter planen „so früh wie möglich“, was zu Spitzen zu Wochenbeginn, Überstunden für die Teams und Leerlaufzeiten am Ende der Woche führt.

### 2. Problemstellung

Die Schokoladenproduktion bei Ritter Sport ist derzeit gekennzeichnet durch:

- **Unausgeglichene Arbeitslast** – hohe Auslastung Mo–Mi, Unterauslastung Do–Fr.
- **Ressourcenungleichgewicht** – bestimmte Linien (z.B. hohl 3, massiv 3) sind Engpässe, andere bleiben ungenutzt.
- **Manuelle, dezentrale Planung** – jeder Schichtleiter optimiert lokal, nicht global.

Ergebnis: Höhere Personalkosten, längere Durchlaufzeiten, häufigere Überstunden, geringere Mitarbeiterzufriedenheit und suboptimale Energienutzung.

![image.png](attachment:075e7c4a-8978-47b3-966e-822c4e71e248:image.png)

### 3. Zielsetzung

Entwicklung und Validierung eines KI-gestützten Entscheidungsunterstützungssystems, das auf Basis von Prognosedaten und historischen Produktionsdaten:

1. **Prognostiziert** kurzfristige Produktionsstunden pro Linie und Qualifikationsbedarf (Zeitreihenmodelle / Transformer).
2. **Optimiert** Schicht- und Maschinenpläne zur Glättung von Spitzen, Einhaltung von Restriktionen (Arbeitsrecht, Wartungsfenster, Allergenwechsel) und Minimierung der Kosten (gemischt-ganzzahlige Programmierung oder Reinforcement Learning).
3. **Balanciert** Hilfsressourcen (Verpackung, Energie) durch optionale Integration des „Stromrechnungen“-Datensatzes von Denis Müller.
4. Bietet **Was-wäre-wenn-Simulation** und ein visuelles Dashboard für Planer.

### 4. Methodik

| Phase | Zentrale Aufgaben | Werkzeuge & Methoden |
| --- | --- | --- |
| **Datenaufbereitung** | Extraktion von MES-Logs, Schichtplänen, Auftragsbuch, Stromrechnungen; Bereinigung & Feature Engineering | Python, Pandas, SQL |
| **Prognose** | Vergleich Prophet, Temporal Fusion Transformer, LSTM; Modellauswahl via Backtesting (MAPE) | PyTorch, Optuna |
| **Optimierungsschicht** | Formulierung MILP / hybrides RL (multi-objektiv: Kosten, Auslastung, Zufriedenheit) | OR-Tools / Pyomo |
| **Prototyp & UI** | Interaktives Dashboard (Dash / Streamlit) mit Szenarienplanung | Plotly, Dash |
| **Evaluation** | KPI-Benchmarks: Überstunden, Auslastungsvarianz, Planstabilität, Zufriedenheit der Planer | A/B auf historische Wochen & Pilot |

![image.png](attachment:40d79da4-c6c9-4647-8f76-3c91996c10f8:image.png)

### 5. Erwartete Vorteile für Ritter Sport

- **± 20 % weniger Überstunden** und **± 15 % weniger Leerlauf** in der Pilotlinie.
- Glattere Energienachfragekurve → Möglichkeit für lastabhängige Stromtarife.
- Transparenter, datengetriebener Planungsprozess, der auf andere Werke übertragbar ist.

### 6. Ergebnisse / Deliverables

1. Bereinigter & dokumentierter Datensatz und Feature Store.
2. Trainiertes Prognosemodell mit reproduzierbarer Pipeline.
3. Optimierungs-Engine (Python-Paket) + REST- oder Excel-Schnittstelle.
4. Dashboard-Prototyp.
5. Abschlussbericht inkl. Business Case und Rollout-Roadmap.

### 7. Zeitplan (März–August 2026, 24 Wochen)

1. **Wochen 1–4:** Datenakquise & EDA
2. **Wochen 5–8:** Entwicklung Prognosemodell
3. **Wochen 9–14:** Optimierungs-Engine & Integration
4. **Wochen 15–18:** UI-Prototyp; Pilot mit Planungsteam
5. **Wochen 19–22:** Evaluation & Iteration
6. **Wochen 23–24:** Ausarbeitung & Abschlusspräsentation

### 8. Wissenschaftlicher Beitrag

Verbindet prädiktive Analytik und präskriptive Optimierung im realen Fertigungskontext und liefert eine Fallstudie zu KI-gestütztem Load Balancing in der Süßwarenindustrie.

---

**Warum ich?**
Als Praktikant im Bereich KI habe ich direkten Zugang zu Datenverantwortlichen, kann implizites Prozesswissen schnell erfassen, mit KI-Modellen gut umgehen und Prototypen im Tagesgeschäft validieren – für maximale wissenschaftliche und praktische Wirkung.

![image.png](attachment:1dcfbdd6-eb23-4c53-8548-f469ee4c4ecd:image.png)

# Detailierte Methodik fuer Forecasting und Optimierung

## A. Planübersicht

1. **Prognose (Forecasting)**
    - **Primäre Methode:** Gradient Boosting (LightGBM / XGBoost)
    - **Fallback:** N BEATS oder Alternative Deep‑Learning‑Modelle (TFT, LSTM)
    - **Workflow:**
        1. Feature‑Engineering (Lag‑Merkmale, Rollende Statistiken, Kalenderdaten)
        2. Modelltraining & Backtesting (Walk‑Forward, MAPE)
        3. Evaluation → {Performance OK?} → ja: weiter → nein: Alternative Modell
2. **Optimierung (Scheduling)**
    - **Methode:** Reinforcement Learning
        - **Online RL:** Training in digitalem Zwilling (SimPy / AnyLogic)
            
            ![CleanShot 2025-07-27 at 19.18.28@2x.png](attachment:9a6512da-e57a-45c8-89db-4d0ec7d030f1:CleanShot_2025-07-27_at_19.18.282x.png)
            
        - **Offline RL:** Training auf historischem Log‑Datensatz
            
            ![CleanShot 2025-07-27 at 19.18.03@2x.png](attachment:90fb5ba4-f5e8-422c-b515-2621e06d38a6:CleanShot_2025-07-27_at_19.18.032x.png)
            
    - **Umgebung:** OpenAI Gym‑API mit simulierter Produktionslinie
    - **Reward:** Minimierung von Überstunden, Leerlauf und Peak‑Kosten

| Phase | Methode | Tools & Bemerkungen |
| --- | --- | --- |
| Forecasting | Gradient Boosting | LightGBM,XGBoost, Optuna |
|  | Fallback N BEATS | PyTorch, Backcasting‑Blöcke |
| Scheduling | Reinforcement Learning | Stable Baselines3 / RLlib, Gym, Digital Twin (SimPy/AnyLogic) |

![Zen 2025-07-27 19.19.22.png](attachment:6b4db55c-5745-4d1d-9e90-817da5c3c278:Zen_2025-07-27_19.19.22.png)

## B. Detaillierte Komponenten

1. **Datenaufbereitung & Feature Engineering**
    - MES‑Logs, Auftragsbuchdaten, Personalprofile, Kalenderinfos
    - Erzeuge Lag‑Features (T-1, T-7), rollende Mittelwerte/Std, Feiertagsindikatoren
    - Split in Trainings‑ und Testzeiträume, Walk‑Forward‑CV
2. **Forecasting**
    - **Gradient Boosting**
        - Ensemble von Entscheidungsbäumen, korrigiert sukzessive Fehler
        - Optuna‑gestütztes Hyperparameter‑Tuning (Tree‑Tiefe, Lernrate)
    - **N BEATS / TFT**
        - Erlernt komplexe Zeitreihenmuster automatisch
        - Multi‑Horizon‑Forecast, Unsicherheitsabschätzung
3. **Optimierungs‑Umgebung**
    - **Digital Twin**
        - Diskrete‑Event‑Simulation der Linien in SimPy oder AnyLogic
        - Kalibrierung gegen historische Auslastungs‑ und Durchlaufzeiten
    - **Gym API**
        - Standardisierte Schnittstelle: step(state, action) → reward, next_state
4. **Reinforcement Learning**
    - **Online Training**
        - Agent probiert Policies in Simulation, schneller als Echtzeit
    - **Offline Training**
        - Nutzt vorhandene Logdaten, kein zusätzlicher Simulator nötig
    - **Algorithmen**
        - Value‑basiert: DQN für diskrete Aktionsräume
        - Policy‑Gradient: PPO / A2C für kontinuierliche Allokationen
5. **Evaluation & Deployment**
    - **Metriken:** MAPE, RMSE (Forecast); Überstundenreduktion, Leerlaufvarianz (Optimization)
    - **Simulation vs. Realität:** A/B‑Test auf historischen Wochen, Pilot im Werk
    - **Rollout:** REST‑Service für Forecast, Python‑Package für Scheduling, Dashboard (Dash/Streamlit)

> Diese Struktur stellt sicher, dass wir zunächst mit einem bewährten, effizienten Verfahren (Gradient Boosting) starten und bei Bedarf auf komplexe Netzwerke umschwenken. Für die Optimierung nutzen wir RL sowohl auf Basis des Digital Twins als auch offline auf vorhandenen Daten, um maximale Flexibilität und Sicherheit zu gewährleisten.
> 

# C. Reward‑Design und Feedback‑Loop

### 1. Reward‑Komponenten

| Ereignis | Reward‑Gewicht | Beispiel (Intensität) | Total Reward |
| --- | --- | --- | --- |
| Unbenutzte Arbeiter | – 5 Punkte / Stunde | 3 Stunden | – 15 |
| Leerlauf einer Linie | – 20 Punkte / Stunde | 5 Stunden | – 100 |
| Unverarbeitete Ressourcen (pro Einheit) | – 2.5 Punkte | 10 Einheiten | – 25 |
| **Gesamt‑Reward** |  |  | **– 140** |

### 2. Beispiel‑Durchlauf eines Trainingsschritts

1. **Input (State)**
    - Verfügbare Maschinenstunden pro Tag
    - Personalpläne
    - Störparameter (z. B. Feiertage)
2. **Action**
    
    ```json
    {
      "Massiv3": 0.5,
      "Hohl3":   0.3,
      "Team1":   0.7,
      ...
    }
    
    ```
    
3. **Output**
    - Simulierte Produktion über die Woche (Stunden pro Linie, Restbestände)
4. **Feedback / Reward**
    - Scan aller negativen/positiven Ereignisse
    - Summiere Einzel‑Rewards (Gewicht × Intensität)
    - Beispiel:
        
        ```
        Leerlauf Massiv3 5 h × (– 20 P/h)   = – 100
        Unbenutzte Arbeiter 3 h × (– 5 P/h)  = – 15
        → Finaler Reward = – 115
        
        ```
        
5. **Loss & Policy‑Update**
    - Setze finalen Reward in den Loss (z. B. TD‑Loss bei DQN, Policy‑Gradient‑Loss bei PPO)
    - Führe Backpropagation durch und aktualisiere Policy‑Netzwerk

### 3. Post‑Training / RLHF

- Sobald das System im Echtbetrieb läuft, sammeln wir **Mitarbeiter‑Feedback** zu vorgeschlagenen Plänen
- Dieses Feedback wird als zusätzliche Reward‑Komponente eingesetzt
- **Reinforcement Learning with Human Feedback (RLHF)** verfeinert die Policy basierend auf qualitativen Nutzerbewertungen

---

> Hinweis: Mit dieser Reward‑Struktur kann der Agent gezielt Leerlauf und Ressourcenschwund minimieren und lernt gleichzeitig, praktikable Schichtpläne für das Werk zu erstellen.
> 

---