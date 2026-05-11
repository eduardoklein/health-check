# Health Check

Robo simples para monitorar dois sites e avisar quando algum deles cair.

## Instalar

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install ".[dev,twilio]"
```

## Configurar sites

Crie um `config.toml` baseado em `config.example.toml`:

```toml
interval_seconds = 60
timeout_seconds = 10

[[sites]]
name = "Site Principal"
url = "https://example.com"
auth_token_env = "SITE_PRINCIPAL_HEALTH_TOKEN"
accepted_status_codes = [200, 301, 302]

[[sites]]
name = "API"
url = "https://example.com/health"
auth_token_env = "API_HEALTH_TOKEN"
accepted_status_codes = [200, 204]
```

Quando o site exigir token, defina a variável de ambiente correspondente antes
de rodar o monitor. O token é enviado como `Authorization: Bearer <token>`.
Use `accepted_status_codes` quando o alvo retorna um status específico mesmo
estando acessível.

## Rodar no terminal

Para testar sem WhatsApp:

```bash
health-check --config config.toml --notifier console
```

Para executar apenas uma verificação:

```bash
health-check --config config.toml --notifier console --once
```

## Enviar alerta por e-mail

Configure o `.env`:

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=alertas@suaempresa.com
SMTP_PASSWORD=senha-ou-app-password
ALERT_EMAIL_FROM=alertas@suaempresa.com
ALERT_EMAIL_TO=pessoa1@suaempresa.com,pessoa2@suaempresa.com
```

Depois rode:

```bash
health-check --config config.toml --notifier email
```

## Enviar alerta por Discord

Configure o `.env`:

```env
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
```

Depois rode:

```bash
health-check --config config.toml --notifier discord
```

## Enviar WhatsApp com Twilio

Configure as variáveis de ambiente:

```bash
export TWILIO_ACCOUNT_SID="..."
export TWILIO_AUTH_TOKEN="..."
export TWILIO_WHATSAPP_FROM="+14155238886"
export TWILIO_WHATSAPP_TO="+5581999999999"
```

Depois rode:

```bash
health-check --config config.toml --notifier twilio-whatsapp
```

O monitor envia alerta quando um site sai do ar e não repete o mesmo alerta
enquanto ele continua fora. Quando o site volta, envia uma mensagem de
recuperação.
