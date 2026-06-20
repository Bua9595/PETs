Install the Hatch Real Pet skill into Codex:

mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
cp -R "${PWD}/assets/hatch-skill/hatch-real-pet" "${CODEX_HOME:-$HOME/.codex}/skills/"

Then restart Codex or start a new session. The skill should appear as `$hatch-real-pet`.

Note: this folder contains skill code only; demo data and generated pet artifacts are not copied here.
