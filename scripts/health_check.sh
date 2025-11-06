#!/bin/bash
# MCP Multi-Context Memory System - Health Check Script
# Copyright (c) 2024 VoiceLessQ
# Version: 2.0.0

set -e

echo "======================================================"
echo "   MCP Multi-Context Memory - Health Check"
echo "   Version: 2.0.0"
echo "   Date: $(date)"
echo "======================================================"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}✗ docker-compose not found${NC}"
    exit 1
fi

echo -e "\n${YELLOW}1. Checking Docker Containers...${NC}"
if docker-compose ps | grep -q "Up"; then
    echo -e "${GREEN}✓ Containers are running${NC}"
    docker-compose ps
else
    echo -e "${RED}✗ Containers are not running${NC}"
    echo "Run: docker-compose up -d"
    exit 1
fi

echo -e "\n${YELLOW}2. Checking API Server Health...${NC}"
if curl -sf http://localhost:8002/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ API Server is healthy${NC}"
    curl -s http://localhost:8002/health | python -m json.tool || echo "Response received"
else
    echo -e "${RED}✗ API Server is not responding${NC}"
    echo "Check logs: docker-compose logs api-server"
fi

echo -e "\n${YELLOW}3. Checking Redis Connection...${NC}"
if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
    REDIS_RESPONSE=$(docker-compose exec -T redis redis-cli ping)
    if [ "$REDIS_RESPONSE" = "PONG" ]; then
        echo -e "${GREEN}✓ Redis is responding: $REDIS_RESPONSE${NC}"
    else
        echo -e "${RED}✗ Redis unexpected response: $REDIS_RESPONSE${NC}"
    fi
else
    echo -e "${RED}✗ Redis is not responding${NC}"
    echo "Check logs: docker-compose logs redis"
fi

echo -e "\n${YELLOW}4. Checking Database Connection...${NC}"
DB_CHECK=$(docker exec mcp-multi-context-memory-memory-server-1 \
  python -c "import sqlite3; conn = sqlite3.connect('/app/data/sqlite/memory.db'); cursor = conn.cursor(); cursor.execute('SELECT COUNT(*) FROM memories'); count = cursor.fetchone()[0]; cursor.execute('SELECT COUNT(*) FROM contexts'); ctx_count = cursor.fetchone()[0]; print(f'{count},{ctx_count}'); conn.close()" 2>/dev/null)

if [ $? -eq 0 ]; then
    IFS=',' read -r MEMORY_COUNT CONTEXT_COUNT <<< "$DB_CHECK"
    echo -e "${GREEN}✓ Database is accessible${NC}"
    echo "  - Memories: $MEMORY_COUNT"
    echo "  - Contexts: $CONTEXT_COUNT"
else
    echo -e "${RED}✗ Database connection failed${NC}"
    echo "Check logs: docker logs mcp-multi-context-memory-memory-server-1"
fi

echo -e "\n${YELLOW}5. Checking MCP Server Initialization...${NC}"
if docker logs mcp-multi-context-memory-memory-server-1 2>&1 | grep -q "Handler chain built with 4 handlers"; then
    echo -e "${GREEN}✓ MCP Server initialized correctly${NC}"

    # Extract supported tools count
    TOOLS_LINE=$(docker logs mcp-multi-context-memory-memory-server-1 2>&1 | grep "Supported tools:" | tail -1)
    if [ -n "$TOOLS_LINE" ]; then
        # Count the number of tools
        TOOLS_COUNT=$(echo "$TOOLS_LINE" | grep -o "," | wc -l)
        TOOLS_COUNT=$((TOOLS_COUNT + 1))
        echo "  - Tools available: $TOOLS_COUNT"
    fi
else
    echo -e "${RED}✗ MCP Server initialization issue${NC}"
    echo "Check logs: docker logs mcp-multi-context-memory-memory-server-1"
fi

echo -e "\n${YELLOW}6. Checking Environment Configuration...${NC}"
ENV_CHECK=$(docker exec mcp-multi-context-memory-memory-server-1 \
  python -c "import os; print(os.getenv('DATABASE_URL', 'NOT_SET'))" 2>/dev/null)

if [ "$ENV_CHECK" != "NOT_SET" ]; then
    echo -e "${GREEN}✓ Environment variables configured${NC}"
    echo "  - DATABASE_URL: $ENV_CHECK"
else
    echo -e "${YELLOW}⚠ Environment variables not fully configured${NC}"
fi

echo -e "\n${YELLOW}7. Checking Disk Space...${NC}"
DISK_USAGE=$(df -h . | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -lt 90 ]; then
    echo -e "${GREEN}✓ Disk space OK (${DISK_USAGE}% used)${NC}"
else
    echo -e "${RED}✗ Low disk space (${DISK_USAGE}% used)${NC}"
fi

echo -e "\n======================================================"
echo -e "${GREEN}Health Check Complete!${NC}"
echo "======================================================"

# Summary
echo -e "\n${YELLOW}Quick Troubleshooting:${NC}"
echo "  - View all logs: docker-compose logs"
echo "  - Restart services: docker-compose restart"
echo "  - Full rebuild: docker-compose down && docker-compose up -d --build"
echo "  - Full guide: See TROUBLESHOOTING.md"

exit 0
