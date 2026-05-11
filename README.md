# Health Check

Robo simples para monitorar dois sites e avisar quando algum deles cair.

## Instalar

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,twilio]"
```

## Configurar sites

Crie um `config.toml` baseado em `config.example.toml`:

```toml
interval_seconds = 60
timeout_seconds = 10

[[sites]]
name = "Site Principal"
url = "https://example.com"

[[sites]]
name = "API"
url = "https://example.com/health"
```

## Rodar no terminal

Para testar sem WhatsApp:

```bash
health-check --config config.toml --notifier console
```

Para executar apenas uma verificação:

```bash
health-check --config config.toml --notifier console --once
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
