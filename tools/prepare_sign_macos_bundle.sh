#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Prepare a macOS keychain for signing the standalone app bundle.

Usage:
  tools/prepare_sign_macos_bundle.sh --p12-path CERT.p12 --p12-password PASSWORD [options]
  tools/prepare_sign_macos_bundle.sh CERT.p12 PASSWORD [options]

Options:
  --keychain PATH             Keychain to create/use.
                              Default: ~/Library/Keychains/mcsas3-signing.keychain-db
  --keychain-password PASS    Password for the keychain.
                              Default: the .p12 password
  --replace-keychain          Delete an existing keychain at --keychain before creating it.
                              Default: enabled for the default mcsas3-signing keychain only
  --identity-filter TEXT      Prefer a signing identity containing this text.
                              Default: Developer ID Application
  -h, --help                  Show this help.

After a successful import, the script prints export commands for:
  MACOS_CODESIGN_IDENTITY
  MACOS_SIGNING_KEYCHAIN
EOF
}

p12_path=""
p12_password=""
default_keychain_path="${HOME}/Library/Keychains/mcsas3-signing.keychain-db"
keychain_path="$default_keychain_path"
keychain_password=""
replace_keychain="auto"
identity_filter="Developer ID Application"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --p12-path)
      p12_path="${2:-}"
      shift 2
      ;;
    --p12-password)
      p12_password="${2:-}"
      shift 2
      ;;
    --keychain)
      keychain_path="${2:-}"
      shift 2
      ;;
    --keychain-password)
      keychain_password="${2:-}"
      shift 2
      ;;
    --replace-keychain)
      replace_keychain="true"
      shift
      ;;
    --identity-filter)
      identity_filter="${2:-}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    --*)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
    *)
      if [[ -z "$p12_path" ]]; then
        p12_path="$1"
      elif [[ -z "$p12_password" ]]; then
        p12_password="$1"
      else
        echo "Unexpected argument: $1" >&2
        usage >&2
        exit 2
      fi
      shift
      ;;
  esac
done

if [[ -z "$p12_path" || -z "$p12_password" ]]; then
  echo "Missing required .p12 path or .p12 password." >&2
  usage >&2
  exit 2
fi

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "This script must run on macOS." >&2
  exit 1
fi

if [[ ! -f "$p12_path" ]]; then
  echo "Missing .p12 file: $p12_path" >&2
  exit 1
fi

if [[ -z "$keychain_password" ]]; then
  keychain_password="$p12_password"
fi

mkdir -p "$(dirname "$keychain_path")"

if [[ "$replace_keychain" == "auto" && "$keychain_path" == "$default_keychain_path" ]]; then
  replace_keychain="true"
elif [[ "$replace_keychain" == "auto" ]]; then
  replace_keychain="false"
fi

if [[ "$replace_keychain" == "true" && -f "$keychain_path" ]]; then
  echo "Deleting existing signing keychain: $keychain_path"
  security delete-keychain "$keychain_path" 2>/dev/null || rm -f "$keychain_path"
fi

if [[ ! -f "$keychain_path" ]]; then
  security create-keychain -p "$keychain_password" "$keychain_path"
fi
security set-keychain-settings -lut 21600 "$keychain_path"
security unlock-keychain -p "$keychain_password" "$keychain_path"

existing_keychains=()
existing_keychain_count=0
while IFS= read -r existing_keychain; do
  existing_keychain="${existing_keychain#"${existing_keychain%%[![:space:]]*}"}"
  existing_keychain="${existing_keychain%"${existing_keychain##*[![:space:]]}"}"
  existing_keychain="${existing_keychain%\"}"
  existing_keychain="${existing_keychain#\"}"
  if [[ -n "$existing_keychain" && -f "$existing_keychain" ]]; then
    existing_keychains+=("$existing_keychain")
    existing_keychain_count=$((existing_keychain_count + 1))
  fi
done < <(security list-keychains -d user)

keychain_in_search_list="false"
if [[ "$existing_keychain_count" -gt 0 ]]; then
  for existing_keychain in "${existing_keychains[@]}"; do
    if [[ "$existing_keychain" == "$keychain_path" ]]; then
      keychain_in_search_list="true"
      break
    fi
  done
fi

if [[ "$keychain_in_search_list" != "true" ]]; then
  if [[ "$existing_keychain_count" -gt 0 ]]; then
    security list-keychains -d user -s "$keychain_path" "${existing_keychains[@]}"
  else
    security list-keychains -d user -s "$keychain_path"
  fi
fi

security import "$p12_path" \
  -k "$keychain_path" \
  -P "$p12_password" \
  -A \
  -t cert \
  -f pkcs12
security set-key-partition-list \
  -S apple-tool:,apple:,codesign: \
  -s \
  -k "$keychain_password" \
  "$keychain_path"

identity_lines="$(security find-identity -v -p codesigning "$keychain_path")"
identity="$(
  printf '%s\n' "$identity_lines" |
    awk -v filter="$identity_filter" '
      index($0, filter) && match($0, /"[^"]+"/) {
        print substr($0, RSTART + 1, RLENGTH - 2)
        exit
      }
    '
)"

if [[ -z "$identity" ]]; then
  identity="$(
    printf '%s\n' "$identity_lines" |
      awk 'match($0, /"[^"]+"/) {
        print substr($0, RSTART + 1, RLENGTH - 2)
        exit
      }'
  )"
fi

if [[ -z "$identity" ]]; then
  echo "No codesigning identity found in keychain: $keychain_path" >&2
  printf '%s\n' "$identity_lines" >&2
  exit 1
fi

echo "Imported signing certificate into: $keychain_path"
echo "Selected signing identity: $identity"
echo
echo "Run these in your shell before tox -e standalone:"
printf 'export MACOS_CODESIGN_IDENTITY=%q\n' "$identity"
printf 'export MACOS_SIGNING_KEYCHAIN=%q\n' "$keychain_path"
