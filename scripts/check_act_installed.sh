#!/bin/bash
#!/bin/bash
command -v act-cli >/dev/null 2>&1 || command -v act >/dev/null 2>&1 || {
  echo "Error: act or act-cli is required to modify workflow files"
  exit 1
}
