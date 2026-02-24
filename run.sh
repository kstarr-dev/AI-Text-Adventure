#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${SCRIPT_DIR}/.venv"

setup_venv() {
    if [ ! -d "${VENV_DIR}" ]; then
        echo "Creating virtual environment..."
        python3 -m venv "${VENV_DIR}"
    fi
}

install_dependencies() {
    echo "Installing dependencies..."
    "${VENV_DIR}/bin/pip" install --quiet anthropic python-dotenv
}

run_adventure() {
    echo "Launching adventure..."
    "${VENV_DIR}/bin/python" "${SCRIPT_DIR}/create_adventure.py"
}

main() {
    setup_venv
    install_dependencies
    run_adventure
}

main
