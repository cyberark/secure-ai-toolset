#!/bin/bash
# filepath: /Users/niv.rabin/code/cyberark/agent-guard/docker_proxy.sh
LOGFILE="/tmp/agent_guard_docker.log"
echo "=== Starting Docker MCP proxy at $(date) ===" > $LOGFILE

docker run --rm -i \
  agent-guard mcp-proxy \
  -cf /app/config_example.json \
  --debug 2>> $LOGFILE

echo "=== Docker exited with code $? at $(date) ===" >> $LOGFILE