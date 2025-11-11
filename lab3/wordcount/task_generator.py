import json
import constPipe
import os
import sys

# Ordner, in dem sich das Skript befindet
subfolder = os.path.relpath(os.path.dirname(os.path.abspath(__file__)), os.getcwd())

# Python-Interpreter, der aktuell benutzt wird (z. B. aus venv)
python_interpreter = sys.executable

tasks = []

# Splitter
tasks.append({
    "label": "Splitter",
    "type": "shell",
    "command": f"{python_interpreter} splitter.py",
    "options": {
        "cwd": f"${{workspaceFolder}}/{subfolder}"
    },
    "problemMatcher": []
})

# Mapper
for i in range(1, constPipe.NUM_MAPPERS + 1):
    tasks.append({
        "label": f"Mapper {i}",
        "type": "shell",
        "command": f"{python_interpreter} mapper.py {i}",
        "options": {
            "cwd": f"${{workspaceFolder}}/{subfolder}"
        },
        "problemMatcher": []
    })

# Reducer
for i in range(1, constPipe.NUM_REDUCERS + 1):
    tasks.append({
        "label": f"Reducer {i}",
        "type": "shell",
        "command": f"{python_interpreter} reducer.py {i}",
        "options": {
            "cwd": f"${{workspaceFolder}}/{subfolder}"
        },
        "problemMatcher": []
    })

# Meta-Task: Run WordCount
tasks.append({
    "label": "Run WordCount",
    "dependsOn": [t["label"] for t in tasks],
    "dependsOrder": "parallel"
})

# .vscode-Verzeichnis sicherstellen
os.makedirs(".vscode", exist_ok=True)
tasks_file = os.path.join(".vscode", "tasks.json")

# Alte tasks.json löschen
if os.path.exists(tasks_file):
    os.remove(tasks_file)
    print("🗑 Alte .vscode/tasks.json gelöscht.")

# Neue tasks.json schreiben
with open(tasks_file, "w") as f:
    json.dump({"version": "2.0.0", "tasks": tasks}, f, indent=2)

print(f"✅ Neue .vscode/tasks.json generiert! Python-Interpreter: {python_interpreter}")
