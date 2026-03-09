# Simple QRCode generator

> This is a mod from [DietPawel/pwscapp: Simple QR code generator](https://github.com/DietPawel/pwscapp)

I added some visual cleanup, ARM-friendly runtime support, and a simple deployment path for a Raspberry Pi/home server setup.

## Code Quality

SonarQube project: `Raskitoma-QRCode`

> The previous README exposed a badge URL containing a token parameter. That token reference was removed.

## Screenshot

![Screenshot](qrcoderun.png)

## Running locally

```bash
git clone https://github.com/raskitoma/qrcode.git
cd qrcode
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd app
uwsgi --ini uwsgi.ini
```

By default it runs on `0.0.0.0:3000`.

## Run in Docker

Edit `docker-compose.yml` as needed (ports, env vars, etc.), then:

```bash
docker compose build
docker compose up -d
```

Browse to `http://<qrcode-host>:<port>`. In the current compose file, the exposed port is `8060`.

## Validation rules

The `/qr` endpoint now rejects:
- missing `text`
- empty/blank `text`
- text longer than `2048` characters

## Tests

```bash
python3 -m unittest discover -s tests -v
```
