#!/bin/bash
# Setup script for LocalTopSH
# Creates required directory structure and placeholder files

set -e

echo "🔧 Setting up LocalTopSH..."

# Create directories
mkdir -p secrets workspace

# Required secrets (must be filled!)
if [ ! -f secrets/telegram_token.txt ]; then
  echo "YOUR_TELEGRAM_BOT_TOKEN" > secrets/telegram_token.txt
  echo "⚠️  Created secrets/telegram_token.txt - EDIT WITH YOUR BOT TOKEN!"
fi

if [ ! -f secrets/api_key.txt ]; then
  echo "YOUR_API_KEY" > secrets/api_key.txt
  echo "⚠️  Created secrets/api_key.txt - EDIT WITH YOUR API KEY!"
fi

if [ ! -f secrets/base_url.txt ]; then
  echo "https://api.openai.com/v1" > secrets/base_url.txt
  echo "📝 Created secrets/base_url.txt with default OpenAI URL"
fi

# Optional secrets (empty = feature disabled)
if [ ! -f secrets/zai_api_key.txt ]; then
  touch secrets/zai_api_key.txt
  echo "📝 Created empty secrets/zai_api_key.txt (Z.AI search optional)"
fi

if [ ! -f secrets/gdrive_client_id.txt ]; then
  touch secrets/gdrive_client_id.txt
  echo "📝 Created empty secrets/gdrive_client_id.txt (Google Drive optional)"
fi

if [ ! -f secrets/gdrive_client_secret.txt ]; then
  touch secrets/gdrive_client_secret.txt
  echo "📝 Created empty secrets/gdrive_client_secret.txt (Google Drive optional)"
fi

# Userbot secrets (optional - only needed for userbot mode)
if [ ! -f secrets/telegram_api_id.txt ]; then
  touch secrets/telegram_api_id.txt
  echo "📝 Created empty secrets/telegram_api_id.txt (Userbot optional)"
fi

if [ ! -f secrets/telegram_api_hash.txt ]; then
  touch secrets/telegram_api_hash.txt
  echo "📝 Created empty secrets/telegram_api_hash.txt (Userbot optional)"
fi

if [ ! -f secrets/telegram_phone.txt ]; then
  touch secrets/telegram_phone.txt
  echo "📝 Created empty secrets/telegram_phone.txt (Userbot optional)"
fi

# Set permissions
chmod 600 secrets/*.txt

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit secrets/telegram_token.txt with your bot token"
echo "2. Edit secrets/api_key.txt with your LLM API key"
echo "3. (Optional) Add Google Drive credentials for Drive integration"
echo "4. Run: docker compose up -d"
