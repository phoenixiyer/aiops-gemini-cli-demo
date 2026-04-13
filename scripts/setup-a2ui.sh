#!/usr/bin/env bash

# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

set -e

echo "=========================================================="
echo "  Setting up A2UI Dashboard Shell Client"
echo "=========================================================="

REPO_DIR="a2ui-dashboard-client"

# 1. Clone the A2UI repository (if it doesn't exist)
if [ ! -d "$REPO_DIR" ]; then
  echo "📦 Cloning A2UI repository..."
  git clone https://github.com/google/A2UI.git "$REPO_DIR"
else
  echo "📦 A2UI repository already cloned."
fi

# 2. Build the dependencies as per A2UI docs
echo "⚙️ Building Markdown renderer..."
cd "$REPO_DIR/renderers/markdown/markdown-it"
npm install
npm run build
cd - > /dev/null

echo "⚙️ Building Web Core library..."
cd "$REPO_DIR/web_core"
npm install
npm run build
cd - > /dev/null

echo "⚙️ Building Lit renderer..."
cd "$REPO_DIR/renderers/lit"
npm install
npm run build
cd - > /dev/null

# 3. Setup the shell client
echo "⚙️ Setting up Lit Shell Client..."
cd "$REPO_DIR/samples/client/lit/shell"
npm install

echo "=========================================================="
echo "✅ A2UI Dashboard Setup Complete"
echo ""
echo "To run the dashboard:"
echo "1. Start the Apollo ADK Agent in one terminal:"
echo "   cd a2ui-agent && UV_INDEX_URL=https://pypi.org/simple/ uv run ."
echo ""
echo "2. Start the UI Shell Client in a second terminal:"
echo "   cd $REPO_DIR/samples/client/lit/shell && npm run dev"
echo ""
echo "3. Open your browser to http://localhost:5173"
echo "=========================================================="
