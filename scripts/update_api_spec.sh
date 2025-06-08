#!/bin/bash

# Script to update the NexBlue API specification
# Usage: ./scripts/update_api_spec.sh

# Set variables
API_SPEC_URL="https://prod-management.nexblue.com/swagger/dist/openapi_gen.json"
OUTPUT_DIR="docs/api"
OUTPUT_FILE="nexblue_api_spec.json"
BACKUP_DIR="$OUTPUT_DIR/archive"
DATE_STAMP=$(date +"%Y%m%d")

# Create directories if they don't exist
mkdir -p "$OUTPUT_DIR"
mkdir -p "$BACKUP_DIR"

# Backup current spec if it exists
if [ -f "$OUTPUT_DIR/$OUTPUT_FILE" ]; then
    echo "Backing up current API specification..."
    cp "$OUTPUT_DIR/$OUTPUT_FILE" "$BACKUP_DIR/${DATE_STAMP}_${OUTPUT_FILE}"
fi

# Download new spec
echo "Downloading latest API specification from $API_SPEC_URL..."
curl -s "$API_SPEC_URL" -o "$OUTPUT_DIR/$OUTPUT_FILE"

# Check if download was successful
if [ $? -eq 0 ]; then
    echo "API specification successfully updated at $OUTPUT_DIR/$OUTPUT_FILE"

    # Create a dated copy in the archive
    cp "$OUTPUT_DIR/$OUTPUT_FILE" "$BACKUP_DIR/${DATE_STAMP}_${OUTPUT_FILE}"
    echo "A backup copy has been saved to $BACKUP_DIR/${DATE_STAMP}_${OUTPUT_FILE}"
else
    echo "Error downloading API specification"
    exit 1
fi

echo "Done!"
