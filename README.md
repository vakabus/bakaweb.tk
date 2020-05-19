Projekt není spravován a použité závislosti obsahují bezpečnostní díry! Používejte s opatrností!

---

# bakaweb.tk webapp

## Lokalni testovaci prostredi

vyzaduje Python3.7 a `pipenv`

```bash
git clone ...
cd naklonovana_slozka

# Instalace prostredi
pipenv install

# Spusteni lokalniho serveru
pipenv shell # timto se vstoupi do prostredi potrebneho pro beh serveru
python manage.py runserver  # v settings.py je potreba zmenit DEBUG na True, jinak to neprobehne
```

## Produkční nasazení

* vyžaduje server s Dockerem
* procedura buildu vicemene odpovida tomu, co je ve skriptu `redeploy.sh`
* server si nehostuje sam staticke soubory, ty ale udrzuje ve slozce `/data/static` v kontejneru. Je potreba tuto slozku nabindovat nekam ven a namirit na ni webserver
* na samotnem serveru bakaweb.tk se jako webserver pouziva Caddy
