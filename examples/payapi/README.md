# Payment service core imitation

### Services

| service | description |
| --- | ----------- |
| actual_rate | service of getting actual rates from external API (periodic polling with aiohttp) |
| ps_common | main service API based on DRF and Django admin ui |
| rate_source_mock | mock of external rate service to getting actual data (random values +- %5) |
| deployment | dockerfiles (used in docker-compose.yml) |

### Launching docker-compose

All the same. After building:

`docker-compose up --build -d`

Make sure that you have launched migration for new base:

`docker-compose exec sys_api python manage.py migrate`

Use django admin tools to create users for testing:

`docker-compose exec sys_api python manage.py createsuperuser`

Details of API in (debug mode is turned on):

`http://localhost:8000/api/`

Check availability currently rates in shell:

~~~
$ docker-compose exec sys_api python manage.py shell
Python 3.7.6
[GCC 8.3.0] on linux
Type "help", "copyright", "credits" or "license" for more information.
(InteractiveConsole)
>>> from common.payment_api.api import get_actual_exchange_rates
>>> import logging
>>> logger = logging.getLogger("stdout")
>>> data = get_actual_exchange_rates(logger)
2020-02-02T12:30:26.910     INFO stdout api.py:119 From 'http://actual_rate_api:8000/actual_rates.json' rates for CAD,HKD,ISK,PHP,DKK,HUF,CZK,GBP,RON,SEK,IDR,INR,BRL,RUB,HRK,JPY,THB,CHF,EUR,MYR,BGN,TRY,CNY,NOK,NZD,ZAR,USD,MXN,SGD,AUD,ILS,KRW,PLN
~~~

### Tests

There are tests only for main internal API methods with simple cases (on Django unittest).
