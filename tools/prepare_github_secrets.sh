#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Prepare GitHub Actions secrets for the macOS standalone release build.

Usage:
  tools/prepare_github_secrets.sh \
    --p12-path CERT.p12 \
    --p12-password PASSWORD \
    --p8-path AuthKey_KEYID.p8 \
    --issuer-id ISSUER_UUID \
    [options]

Positional form:
  tools/prepare_github_secrets.sh CERT.p12 P12_PASSWORD AuthKey_KEYID.p8 ISSUER_UUID [options]

Options:
  --p12-path PATH              Path to the signing certificate export in .p12 format.
  --p12-password PASS          Password used when exporting the .p12 file.
  --p8-path PATH               Path to the App Store Connect .p8 private key file.
  --issuer-id UUID             App Store Connect issuer UUID.
  --key-id KEYID               Override the inferred App Store Connect key id.
  --keychain-password PASS     Value to emit as MACOS_KEYCHAIN_PASSWORD.
                               Default: the .p12 password.
  --identity-filter TEXT       Prefer a signing identity containing this text.
                               Default: Developer ID Application.
  --allow-nonstandard-name     Allow .p8 filenames that do not match AuthKey_<KEYID>.p8.
  -h, --help                   Show this help.

Notes:
  - MACOS_CERT_P12_BASE64 is emitted as a single-line base64 value.
  - MACOS_CODESIGN_IDENTITY is discovered by importing the .p12 into a temporary keychain.
  - MACOS_NOTARY_KEY_ID is usually inferred from filenames like AuthKey_ABC123XYZ.p8.
  - MACOS_NOTARY_ISSUER_ID cannot be extracted from the .p8 file and must be provided.
  - The script runs on macOS because it uses the system security tool to resolve the signing identity.

After a successful check, the script prints export commands for:
  MACOS_CERT_P12_BASE64
  MACOS_CERT_P12_PASSWORD
  MACOS_CODESIGN_IDENTITY
  MACOS_KEYCHAIN_PASSWORD
  MACOS_NOTARY_KEY_ID
  MACOS_NOTARY_ISSUER_ID
  MACOS_NOTARY_API_KEY
EOF
}

p12_path=""
p12_password=""
p8_path=""
issuer_id=""
key_id=""
keychain_password=""
identity_filter="Developer ID Application"
allow_nonstandard_name="false"

cleanup() {
  if [[ -n "${temp_keychain_path:-}" && -f "${temp_keychain_path}" ]]; then
    security delete-keychain "${temp_keychain_path}" >/dev/null 2>&1 || rm -f "${temp_keychain_path}"
  fi
}

trap cleanup EXIT

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
    --p8-path)
      p8_path="${2:-}"
      shift 2
      ;;
    --issuer-id)
      issuer_id="${2:-}"
      shift 2
      ;;
    --key-id)
      key_id="${2:-}"
      shift 2
      ;;
    --keychain-password)
      keychain_password="${2:-}"
      shift 2
      ;;
    --identity-filter)
      identity_filter="${2:-}"
      shift 2
      ;;
    --allow-nonstandard-name)
      allow_nonstandard_name="true"
      shift
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
      elif [[ -z "$p8_path" ]]; then
        p8_path="$1"
      elif [[ -z "$issuer_id" ]]; then
        issuer_id="$1"
      else
        echo "Unexpected argument: $1" >&2
        usage >&2
        exit 2
      fi
      shift
      ;;
  esac
done

if [[ -z "$p12_path" || -z "$p12_password" || -z "$p8_path" || -z "$issuer_id" ]]; then
  echo "Missing required inputs." >&2
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

if [[ ! -f "$p8_path" ]]; then
  echo "Missing .p8 file: $p8_path" >&2
  exit 1
fi

if [[ -z "$keychain_password" ]]; then
  keychain_password="$p12_password"
fi

if [[ ! "$issuer_id" =~ ^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$ ]]; then
  echo "Issuer id does not look like a UUID: $issuer_id" >&2
  exit 1
fi

if ! grep -q -- "BEGIN PRIVATE KEY" "$p8_path"; then
  echo "The file does not look like a valid App Store Connect .p8 private key: $p8_path" >&2
  exit 1
fi

if [[ "$(basename "$p8_path")" =~ ^AuthKey_([A-Z0-9]+)\.p8$ ]]; then
  inferred_key_id="${BASH_REMATCH[1]}"
else
  inferred_key_id=""
fi

if [[ -z "$key_id" ]]; then
  key_id="$inferred_key_id"
fi

if [[ -z "$key_id" ]]; then
  echo "Could not infer the key id from filename: $(basename "$p8_path")" >&2
  echo "Use --key-id KEYID or rename the file to AuthKey_<KEYID>.p8" >&2
  exit 1
fi

if [[ "$allow_nonstandard_name" != "true" && -z "$inferred_key_id" ]]; then
  echo "Expected a standard App Store Connect key filename: AuthKey_<KEYID>.p8" >&2
  echo "Pass --allow-nonstandard-name with --key-id if you need to use a different filename." >&2
  exit 1
fi

temp_keychain_path="$(mktemp -u "$TMPDIR/mcsas3gui-signing.XXXXXX.keychain-db")"
security create-keychain -p "$keychain_password" "$temp_keychain_path"
security set-keychain-settings -lut 21600 "$temp_keychain_path"
security unlock-keychain -p "$keychain_password" "$temp_keychain_path"
security import "$p12_path" \
  -k "$temp_keychain_path" \
  -P "$p12_password" \
  -A \
  -t cert \
  -f pkcs12 >/dev/null
security set-key-partition-list \
  -S apple-tool:,apple:,codesign: \
  -s \
  -k "$keychain_password" \
  "$temp_keychain_path" >/dev/null

identity_lines="$(security find-identity -v -p codesigning "$temp_keychain_path")"
codesign_identity="$({
  printf '%s\n' "$identity_lines" |
    awk -v filter="$identity_filter" '
      index($0, filter) && match($0, /"[^"]+"/) {
        print substr($0, RSTART + 1, RLENGTH - 2)
        exit
      }
    '
} || true)"

if [[ -z "$codesign_identity" ]]; then
  codesign_identity="$({
    printf '%s\n' "$identity_lines" |
      awk 'match($0, /"[^"]+"/) {
        print substr($0, RSTART + 1, RLENGTH - 2)
        exit
      }'
  } || true)"
fi

if [[ -z "$codesign_identity" ]]; then
  echo "No codesigning identity found in the .p12 file: $p12_path" >&2
  printf '%s\n' "$identity_lines" >&2
  exit 1
fi

cert_p12_base64="$(base64 < "$p12_path" | tr -d '\n')"
if [[ -z "$cert_p12_base64" ]]; then
  echo "Failed to base64-encode the .p12 file: $p12_path" >&2
  exit 1
fi

notary_api_key="$(cat "$p8_path")"
if [[ -z "$notary_api_key" ]]; then
  echo "The .p8 file is empty: $p8_path" >&2
  exit 1
fi

echo "Prepared GitHub Actions secrets for the macOS standalone release build"
echo "Signing certificate: $p12_path"
echo "Selected codesign identity: $codesign_identity"
echo "Notary key: $p8_path"
echo "Selected notary key id: $key_id"
echo "Issuer id: $issuer_id"
echo
echo "Run these in your shell or copy them into GitHub Actions secrets:"
printf 'export MACOS_CERT_P12_BASE64=%q\n' "$cert_p12_base64"
printf 'export MACOS_CERT_P12_PASSWORD=%q\n' "$p12_password"
printf 'export MACOS_CODESIGN_IDENTITY=%q\n' "$codesign_identity"
printf 'export MACOS_KEYCHAIN_PASSWORD=%q\n' "$keychain_password"
printf 'export MACOS_NOTARY_KEY_ID=%q\n' "$key_id"
printf 'export MACOS_NOTARY_ISSUER_ID=%q\n' "$issuer_id"
printf 'export MACOS_NOTARY_API_KEY=%q\n' "$notary_api_key"