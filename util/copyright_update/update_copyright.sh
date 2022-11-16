#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

find ${SCRIPT_DIR}/../../ -type f \( -name "*.py" -o -name "*.vue" -o -name "*.ts" \) | grep -vE '(venv3|node_modules|migrations)' | xargs addlicense -v -f ${SCRIPT_DIR}/copyright_template
