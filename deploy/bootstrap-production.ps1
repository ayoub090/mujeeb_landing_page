param([switch]$RenewOnly)

$ErrorActionPreference = 'Stop'
if (!(Test-Path '.env')) { throw 'Copy .env.example to .env and fill every required value first.' }

if ($RenewOnly) {
  docker compose -f docker-compose.prod.yml --profile renew run --rm certbot-renew
  docker compose -f docker-compose.prod.yml exec nginx nginx -s reload
  exit $LASTEXITCODE
}

# DNS for all three domains must already point to this VPS. Bootstrap obtains
# the certificates before Nginx binds the public HTTPS ports.
docker compose -f docker-compose.prod.yml up -d postgres redis api worker dashboard
docker compose -f docker-compose.prod.yml --profile bootstrap run --rm --service-ports certbot-init
docker compose -f docker-compose.prod.yml up -d nginx
