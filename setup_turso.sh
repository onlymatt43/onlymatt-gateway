#!/bin/bash
# Setup script for OnlyMatt Gateway Turso Database

echo 'Setting up Turso database...'
echo 'Please ensure you have the Turso CLI installed and authenticated.'
echo 'Run: turso db create onlymatt-gateway'
echo 'Then run the schema: turso db shell onlymatt-gateway < schema.sql'
echo ''
echo 'After setup, update your .env file with the TURSO_URL and TURSO_AUTH_TOKEN.'
