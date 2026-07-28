#!/bin/bash


set -o pipefail


JOB_NAME="${1:-unknown_job}"


CONFIG_FILE="${CRONBOARD_CONFIG_FILE:-$HOME/.config/cronboard/config.toml}"
NOTIFICATIONS_FILE="${CRONBOARD_NOTIFICATIONS_FILE:-$HOME/.config/cronboard/notifications.toml}"
LOG_DIR="${CRONBOARD_LOG_DIR:-$HOME/.config/cronboard/logs/${JOB_NAME}}"
mkdir -p "$LOG_DIR"


TELEGRAM_TOKEN_ENCRYPTED=$(grep 'telegram_token' "$CONFIG_FILE" | sed 's/^telegram_token *= *//; s/^"//; s/"$//')
TELEGRAM_CHAT_ID=$(grep 'telegram_chat_id' "$CONFIG_FILE" | sed 's/^telegram_chat_id *= *//; s/^"//; s/"$//')
TELEGRAM_TOKEN=$(printf '%s' "$TELEGRAM_TOKEN_ENCRYPTED" | openssl enc -d -aes-256-cbc -salt -pbkdf2 -pass file:"$HOME/.config/cronboard/secret.key" -base64 -A 2>/dev/null)

# Check environment variable for per-job notification control
# Format: CRONBOARD_NOTIFICATIONS_<JOBNAME>=true/false
NOTIFICATIONS_ENABLED=false
ENV_NOTIFICATION_VAR="CRONBOARD_NOTIFICATIONS_${JOB_NAME}"
if [ -n "${!ENV_NOTIFICATION_VAR}" ]; then
    if [ "${!ENV_NOTIFICATION_VAR}" = "true" ]; then
        NOTIFICATIONS_ENABLED=true
    fi
else
    # Fall back to notifications.toml if no environment variable is set
    if [ -f "$NOTIFICATIONS_FILE" ]; then
        if awk "/^\[(${JOB_NAME}|.*\.${JOB_NAME})\]/{found=1;next}/^\[/{found=0}found && /^notifications *= *true/{print;exit}" "$NOTIFICATIONS_FILE" | grep -q .; then
            NOTIFICATIONS_ENABLED=true
        fi
    fi
fi

# Check environment variable for per-job logging control
# Format: CRONBOARD_LOGGING_<JOBNAME>=true/false
LOGGING_ENABLED=false
ENV_LOGGING_VAR="CRONBOARD_LOGGING_${JOB_NAME}"
if [ -n "${!ENV_LOGGING_VAR}" ]; then
    if [ "${!ENV_LOGGING_VAR}" = "true" ]; then
        LOGGING_ENABLED=true
    fi
else
    # Fall back to notifications.toml if no environment variable is set
    if [ -f "$NOTIFICATIONS_FILE" ]; then
        if awk "/^\[(${JOB_NAME}|.*\.${JOB_NAME})\]/{found=1;next}/^\[/{found=0}found && /^logging *= *true/{print;exit}" "$NOTIFICATIONS_FILE" | grep -q .; then
            LOGGING_ENABLED=true
        fi
    fi
fi


TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
shift


LOG_FILE="$LOG_DIR/${JOB_NAME}_${TIMESTAMP}.log"
ERR_FILE="$LOG_DIR/${JOB_NAME}_${TIMESTAMP}.err"


# Ensure PATH works in cron
export PATH="/usr/local/bin:/usr/bin:/bin:$PATH"


# Text shown in the log header (decoded user command, not the base64 wire form)
COMMAND_SUMMARY=""
if [ "$#" -ge 1 ] && [ "${1#cronboard1:}" != "$1" ]; then
  _enc=${1#cronboard1:}
  if COMMAND_SUMMARY=$(printf '%s' "$_enc" | base64 -d 2>/dev/null); then
    :
  elif COMMAND_SUMMARY=$(printf '%s' "$_enc" | base64 -D 2>/dev/null); then
    :
  elif COMMAND_SUMMARY=$(printf '%s' "$_enc" | base64 --decode 2>/dev/null); then
    :
  else
    COMMAND_SUMMARY="(invalid base64 command payload)"
  fi
else
  COMMAND_SUMMARY="$*"
fi


# Header (only if logging is enabled)
if $LOGGING_ENABLED; then
{
  echo "========================================"
  echo "Cronboard Job Execution"
  echo "Job: $JOB_NAME"
  echo "Time: $TIMESTAMP"
  printf '%s\n' "Command: ${COMMAND_SUMMARY}"
  echo "========================================"
  echo ""
} > "$LOG_FILE"
fi


# Run command (capture stdout + stderr separately for stable ordering).
if [ "$#" -ge 1 ] && [ "${1#cronboard1:}" != "$1" ]; then
  encoded=${1#cronboard1:}
  shift
  if ! _tmp=$(mktemp); then
    echo "cronboard: mktemp failed" >>"$LOG_FILE"
    EXIT_CODE=1
  elif printf '%s' "$encoded" | base64 -d >"$_tmp" 2>/dev/null \
    || printf '%s' "$encoded" | base64 -D >"$_tmp" 2>/dev/null \
    || printf '%s' "$encoded" | base64 --decode >"$_tmp" 2>/dev/null; then
    bash "$_tmp" >"$LOG_FILE.out" 2>"$ERR_FILE"
    EXIT_CODE=$?
    rm -f "$_tmp"
  else
    rm -f "$_tmp"
    echo "cronboard: invalid base64 command payload" >>"$LOG_FILE"
    EXIT_CODE=1
  fi
else
  "$@" >"$LOG_FILE.out" 2>"$ERR_FILE"
  EXIT_CODE=$?
fi


# Append stdout first (only if logging is enabled)
if $LOGGING_ENABLED; then
  if [ -s "$LOG_FILE.out" ]; then
    cat "$LOG_FILE.out" >> "$LOG_FILE"
  fi


  # Append cleaned stderr after stdout (stable order)
  if [ -s "$ERR_FILE" ]; then
    echo "" >> "$LOG_FILE"
    sed 's/^.*: line [0-9]\+: //' "$ERR_FILE" >> "$LOG_FILE"
  fi


  # Footer
  {
    echo ""
    echo "========================================"
    echo "Exit Code: $EXIT_CODE"
    echo "Status: $([ $EXIT_CODE -eq 0 ] && echo SUCCESS || echo FAILED)"
    echo "========================================"
  } >> "$LOG_FILE"
fi


# Capture error message
ERROR_MSG=""
if [ $EXIT_CODE -ne 0 ] && [ -s "$ERR_FILE" ]; then
  ERROR_MSG=$(head -1 "$ERR_FILE" | sed 's/^.*: line [0-9]\+: //')
fi


# Cleanup temp files
rm -f "$LOG_FILE.out" "$ERR_FILE"


# Send notification
if [ $EXIT_CODE -ne 0 ] && $NOTIFICATIONS_ENABLED; then
  if [ -z "$TELEGRAM_TOKEN" ]; then
    echo "ERROR: Telegram token is empty - decryption likely failed" >> "$LOG_FILE"
  else
    curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_TOKEN}/sendMessage" \
      --data-urlencode "chat_id=${TELEGRAM_CHAT_ID}" \
      --data-urlencode "text=${JOB_NAME} failed (exit ${EXIT_CODE}): ${ERROR_MSG:-unknown error}" \
      2>> "$LOG_DIR/curl_errors.log"
  fi
fi


exit $EXIT_CODE