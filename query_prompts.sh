#!/bin/bash

set -e

# Configuration
DATABASE="prompts.db"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DB_PATH="$SCRIPT_DIR/$DATABASE"

# Check if database exists
if [ ! -f "$DB_PATH" ]; then
    echo "❌ Database not found at: $DB_PATH"
    echo "💡 Run the save app first to create the database"
    exit 1
fi

echo "🗃️  Querying compressed_prompts table from: $DATABASE"
echo "=" | head -c 80 | tr -d '\n' && echo

# Function to execute SQL query
query_db() {
    local sql="$1"
    local description="$2"

    echo "📊 $description"
    echo "-" | head -c 60 | tr -d '\n' && echo

    sqlite3 "$DB_PATH" "$sql" 2>/dev/null || {
        echo "❌ Failed to execute query"
        return 1
    }
    echo
}

# Parse command line arguments
case "${1:-summary}" in
    "all"|"list")
        query_db "SELECT id, substr(prompt_hash, 1, 8) as hash_short, original_size, compressed_size,
                        printf('%.1f%%', (1.0 - CAST(compressed_size AS FLOAT)/original_size) * 100) as compression_ratio,
                        datetime(created_at, 'localtime') as created
                 FROM compressed_prompts
                 ORDER BY created_at DESC;" \
                "All saved compressed prompts"
        ;;

    "summary"|"stats")
        query_db "SELECT
                    COUNT(*) as total_prompts,
                    AVG(original_size) as avg_original_size,
                    AVG(compressed_size) as avg_compressed_size,
                    printf('%.1f%%', AVG((1.0 - CAST(compressed_size AS FLOAT)/original_size) * 100)) as avg_compression_ratio,
                    MIN(datetime(created_at, 'localtime')) as first_prompt,
                    MAX(datetime(created_at, 'localtime')) as latest_prompt
                 FROM compressed_prompts;" \
                "Database summary statistics"
        ;;

    "recent")
        query_db "SELECT id, substr(prompt_hash, 1, 12) as hash_short, original_size, compressed_size,
                        printf('%.1f%%', (1.0 - CAST(compressed_size AS FLOAT)/original_size) * 100) as compression_ratio,
                        datetime(created_at, 'localtime') as created
                 FROM compressed_prompts
                 ORDER BY created_at DESC
                 LIMIT 5;" \
                "5 most recent compressed prompts"
        ;;

    "best")
        query_db "SELECT id, substr(prompt_hash, 1, 12) as hash_short, original_size, compressed_size,
                        printf('%.1f%%', (1.0 - CAST(compressed_size AS FLOAT)/original_size) * 100) as compression_ratio,
                        datetime(created_at, 'localtime') as created
                 FROM compressed_prompts
                 ORDER BY (1.0 - CAST(compressed_size AS FLOAT)/original_size) DESC
                 LIMIT 5;" \
                "Top 5 best compression ratios"
        ;;

    "schema")
        query_db ".schema compressed_prompts" \
                "Table schema"
        ;;

    "count")
        query_db "SELECT COUNT(*) as total_saved_prompts FROM compressed_prompts;" \
                "Total number of saved prompts"
        ;;

    "help"|"-h"|"--help")
        echo "📋 Usage: $0 [COMMAND]"
        echo ""
        echo "Available commands:"
        echo "  summary, stats  - Show database statistics (default)"
        echo "  all, list      - List all compressed prompts"
        echo "  recent         - Show 5 most recent prompts"
        echo "  best           - Show top 5 compression ratios"
        echo "  count          - Show total count"
        echo "  schema         - Show table structure"
        echo "  help           - Show this help message"
        echo ""
        echo "Examples:"
        echo "  $0                # Show summary statistics"
        echo "  $0 all           # List all prompts"
        echo "  $0 recent        # Show recent prompts"
        echo "  $0 best          # Show best compression ratios"
        ;;

    *)
        echo "❌ Unknown command: $1"
        echo "💡 Use '$0 help' to see available commands"
        exit 1
        ;;
esac

echo "✅ Query completed successfully"