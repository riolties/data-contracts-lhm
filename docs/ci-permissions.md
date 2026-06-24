# CI-Berechtigungen — Auto-PR aus der Pipeline

Der Workflow `intake-to-contract.yml` öffnet nach der Governance-Freigabe automatisch einen Pull Request mit dem generierten Contract. Damit die **Gate-Workflows** (`validate-contracts`, `pipeline-and-quality`) auf diesem PR **automatisch laufen**, darf der PR **nicht** mit dem `GITHUB_TOKEN` erstellt werden.

## Warum
GitHub unterdrückt absichtlich, dass mit `GITHUB_TOKEN` erzeugte Events weitere Workflow-Runs auslösen (Schleifenschutz). Ein so erstellter PR würde also geöffnet, aber **keine Checks** starten — der Demo-Kern „Intake → Auto-PR → Gates → Merge" wäre kaputt. Lösung: PR-Erstellung mit einer **anderen Identität** durchführen.

## Aktuelle Lösung (Hackathon): Fine-grained PAT
Der Workflow nutzt `token: ${{ secrets.CI_PAT || secrets.GITHUB_TOKEN }}` — also den PAT, falls gesetzt, sonst Fallback auf den Standard-Token.

**Einmaliges Setup:**
1. **PAT erstellen:** GitHub → Settings → Developer settings → **Fine-grained tokens** → *Generate new token*
   - **Repository access:** *Only select repositories* → `riolties/data-contracts-lhm`
   - **Permissions:** `Contents` → **Read and write**, `Pull requests` → **Read and write**
   - Ablaufdatum nach Bedarf (z. B. 30 Tage).
2. **Als Secret hinterlegen:** Repo → Settings → Secrets and variables → Actions → *New repository secret*
   - Name: **`CI_PAT`** · Wert: der Token aus Schritt 1.
3. Fertig — der nächste Auto-PR triggert die Gates.

> Bereits aktiviert (Repo → Settings → Actions → General → Workflow permissions): *Read and write permissions* + *Allow GitHub Actions to create and approve pull requests*.

⚠️ Ein persönlicher PAT ist an eine Person gebunden und läuft ab — für den Hackathon ok, für den Dauerbetrieb durch das Zielbild unten ersetzen.

## Zielbild (Produktion): GitHub App
Best Practice ist ein **GitHub-App-Installations-Token** statt eines PAT:
- kurzlebig (1 h, pro Run frisch), fein scopebar, **nicht** personengebunden, sauber auditierbar.
- Mechanik: `actions/create-github-app-token@v1` erzeugt das Token → als `token:` an `create-pull-request` geben.

## Portierung nach LHM-GitLab
Gleiches Muster: Der `CI_JOB_TOKEN` kann (standardmäßig) keine Pipelines auf dem erzeugten MR auslösen. Entsprechung zur GitHub App ist dort ein **Project/Group Access Token** (Bot-Identität) oder ein **Pipeline-Trigger-Token**. Die Architektur „Automations-Identität ≠ Job-Token" überträgt sich 1:1.
