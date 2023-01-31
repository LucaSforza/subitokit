# Module version of subito-it-searcher

BeautifulSoup scraper running queries on a popular italian ad website.
This module is compatible with Python 3.x versions.

Subitokit module allows you to create queries within the popular italian site subito.it,
filter the results and easily manipulate them with pythone code.

## Example
```py
from subitokit import *

url = 'https://www.subito.it/annunci-italia/vendita/usato/?q=ryzen+5+5600x'
name = 'Ryzen 5 5600x'
min_price = '100'
max_price = '130'

query = run_query(url,name,min_price,max_price)
query.sort() #if key not specified it sort by price

print(query)
#.refresh() is used to reload the query, update it and return extra products (if there are)
for prod in query.refresh():
    print(prod)

```
## How to build it

To build it ,just write in the terminal :
```
pip3 install .
```
After that you can use this package in all projects where you might need it.
