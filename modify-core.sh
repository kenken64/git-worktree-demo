#!/bin/bash
# modify-core.sh - Script to dynamically add "Save to DB" button to prompt compressor result page
# This script modifies the result.html template on-the-fly to add database save functionality

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESULT_TEMPLATE="$SCRIPT_DIR/templates/result.html"
BACKUP_FILE="$RESULT_TEMPLATE.backup"
SAVE_ENDPOINT="http://localhost:5001/save-prompt"

echo "🚀 modify-core.sh: Adding Save to DB functionality to prompt compressor..."

# Check if result.html exists
if [ ! -f "$RESULT_TEMPLATE" ]; then
    echo "❌ Error: result.html template not found at $RESULT_TEMPLATE"
    exit 1
fi

# Create backup if it doesn't exist
if [ ! -f "$BACKUP_FILE" ]; then
    echo "📁 Creating backup of original result.html..."
    cp "$RESULT_TEMPLATE" "$BACKUP_FILE"
fi

# Check if Save to DB button already exists
if grep -q "saveToDbBtn" "$RESULT_TEMPLATE"; then
    echo "✅ Save to DB button already exists in result.html"
    exit 0
fi

echo "🔧 Modifying result.html to add Save to DB functionality..."

# Create temporary file with save button and JavaScript
cat > /tmp/save_button_addition.html << 'SAVE_ADDITION_EOF'

      <!-- Save to DB Section -->
      <div class="save-section" style="margin-top: 20px; text-align: center;">
        <button id="saveToDbBtn" class="save-button" onclick="saveToDatabase()">Save Compressed Text to Database</button>
        <div id="saveStatus" class="save-status" style="display: none; margin-top: 10px;">
          <div class="save-message"></div>
        </div>
      </div>

    <style>
      .save-button {
        background-color: #4CAF50;
        color: white;
        padding: 12px 24px;
        border: none;
        border-radius: 6px;
        cursor: pointer;
        font-size: 16px;
        font-weight: 600;
        transition: background-color 0.3s;
      }
      .save-button:hover {
        background-color: #45a049;
      }
      .save-button:disabled {
        background-color: #cccccc;
        cursor: not-allowed;
      }
      .save-status {
        padding: 10px;
        border-radius: 4px;
        font-weight: 500;
      }
      .save-status.success {
        background-color: #d4edda;
        color: #155724;
        border: 1px solid #c3e6cb;
      }
      .save-status.error {
        background-color: #f8d7da;
        color: #721c24;
        border: 1px solid #f5c6cb;
      }
    </style>

    <script>
      async function saveToDatabase() {
        const saveBtn = document.getElementById('saveToDbBtn');
        const saveStatus = document.getElementById('saveStatus');
        const saveMessage = saveStatus.querySelector('.save-message');

        // Get the compressed text from the textarea
        const compressedTextElement = document.querySelector('textarea[readonly]');
        if (!compressedTextElement || compressedTextElement.value.includes('{{ original_text }}')) {
          // Try to find the second textarea (compressed text)
          const textareas = document.querySelectorAll('textarea[readonly]');
          if (textareas.length < 2) {
            showSaveStatus('Error: Could not find compressed text to save', 'error');
            return;
          }
          compressedTextElement = textareas[1]; // Second textarea should be compressed text
        }

        const compressedText = compressedTextElement.value;

        if (!compressedText || compressedText.trim() === '') {
          showSaveStatus('Error: No compressed text found to save', 'error');
          return;
        }

        // Disable button and show loading
        saveBtn.disabled = true;
        saveBtn.textContent = 'Saving...';

        try {
SAVE_ADDITION_EOF

# Add the save endpoint URL dynamically
echo "          const response = await fetch('$SAVE_ENDPOINT', {" >> /tmp/save_button_addition.html

cat >> /tmp/save_button_addition.html << 'SAVE_ADDITION_EOF'
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              prompt: compressedText
            })
          });

          const result = await response.json();

          if (response.ok) {
            showSaveStatus(`✅ Saved successfully! ID: ${result.id}, Compression ratio: ${result.compression_ratio}`, 'success');
          } else {
            showSaveStatus(`❌ Error: ${result.error}`, 'error');
          }
        } catch (error) {
          showSaveStatus(`❌ Network error: ${error.message}. Make sure the save app is running on port 5001.`, 'error');
        } finally {
          // Re-enable button
          saveBtn.disabled = false;
          saveBtn.textContent = 'Save Compressed Text to Database';
        }
      }

      function showSaveStatus(message, type) {
        const saveStatus = document.getElementById('saveStatus');
        const saveMessage = saveStatus.querySelector('.save-message');

        saveMessage.textContent = message;
        saveStatus.className = `save-status ${type}`;
        saveStatus.style.display = 'block';

        // Auto-hide success messages after 5 seconds
        if (type === 'success') {
          setTimeout(() => {
            saveStatus.style.display = 'none';
          }, 5000);
        }
      }
    </script>
SAVE_ADDITION_EOF

# Insert the save button section before the closing </div> of the container
# Create a temp file with the modified content
{
  # Read everything before the closing container </div>
  sed '/^    <\/div>$/,$d' "$RESULT_TEMPLATE"
  # Add our save button content (indented properly within the container)
  sed 's/^/    /' /tmp/save_button_addition.html
  # Add the closing tags
  echo "    </div>"
  echo "  </body>"
  echo "</html>"
} > "${RESULT_TEMPLATE}.new"

# Replace the original file
mv "${RESULT_TEMPLATE}.new" "$RESULT_TEMPLATE"

# Clean up temporary files
rm -f /tmp/save_button_addition.html "$RESULT_TEMPLATE.tmp"

echo "✅ Successfully added Save to DB functionality to result.html"
echo "📍 The button will call the save endpoint at: $SAVE_ENDPOINT"
echo "💡 To restore original template, run: cp $BACKUP_FILE $RESULT_TEMPLATE"
echo ""
echo "🔄 Restart your prompt compressor app to see the changes!"
echo ""
echo "📋 Usage:"
echo "   1. Start the save app: cd .. && python save_app.py"
echo "   2. Start the compressor app: cd .. && python app.py"
echo "   3. Compress some text and use the 'Save to DB' button on the result page"