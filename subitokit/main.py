#!/usr/bin/env python3.10.9

#stdlib
import json
import re
from copy import copy
from inspect import currentframe, getargvalues

# third party
import requests
from bs4 import BeautifulSoup, Tag

#TODO: aggiungere test e vedere se funziona l'implementazione del prezzo in interi

class product:

    def __init__(self,title:str,price:int,location:str,link:str) -> None:
        self.title = title
        self.price = price
        self.location = location
        self.link = link
    
    def __str__(self) -> str:
        return f'title: {self.title}\nlink:  {self.link}\nprice: {self.price}\nlocation: {self.location}'

    def __repr__(self) -> str:
        return self.__str__()
    
    def __eq__(self, other) -> bool:
        if isinstance(other,product):
            if other.title != self.title:
                return False
            if other.price != self.price:
                return False
            if other.location != self.location:
                return False
            if other.link != self.link:
                return False
        else:
            return False
        return True

    def to_dict(self) -> dict:
        return {'title': self.title, 'price': self.price, 'location': self.location, 'link':self.link}

class subito_query:

    def __init__(self,name:str,url:str,min_price:int,max_price:int,prods=None) -> None:
        if not prods:
            self.prods:list[product] = []
        else:
            self.prods = prods
        self.name = name
        self.url = url
        self.min_price = min_price
        self.max_price = max_price

    def __iter__(self):
        return iter(self.prods)
    
    def __len__(self) -> int:
        return self.prods.__len__()

    def __eq__(self, other) -> bool:

        if isinstance(other,subito_query):

            if self.name != other.name:
                return False
            if self.url != other.url:
                return False
            if self.min_price != other.min_price:
                return False
            if self.max_price != other.max_price:
                return False

            for prod in self.prods:
                if not prod in other:
                    return False

        else:
            return False

        return True
    
    def __add__(self,other):
        new_prods = copy(self.prods)
        if isinstance(other,product):
            if not other in self.prods:
                new_prods.append(other)
        elif isinstance(other,list):
            if all([type(prod)==product for prod in other]):
                new_prods.extend(list(set(other) - set(self.prods)))
            else:
                raise TypeError(f"unsupported operand type(s) for +: 'subito_query' and '{type(other)}' ,with 'subito_query' you can add only 'product' or 'list[product]'")
        else:
            raise TypeError(f"unsupported operand type(s) for +: 'subito_query' and '{type(other)}' ,with 'subito_query' you can add only 'product' or 'list[product]'")
        return subito_query(self.name,self.url,self.min_price,self.max_price,prods=new_prods)
    
    def __sub__(self,other):
        new_prods = copy(self.prods)
        if isinstance(other,product):
            if other in self.prods:
                new_prods.remove(other)
        elif isinstance(other,list):
            if all([type(prod)==product for prod in other]):
                for prod in other:
                    if prod in self.prods:
                        new_prods.remove(prod)
            else:
                raise TypeError(f"unsupported operand type(s) for -: 'subito_query' and '{type(other)}' ,with 'subito_query' you can subtract only 'product' or 'list[product]'")
        else:
            raise TypeError(f"unsupported operand type(s) for -: 'subito_query' and '{type(other)}' ,with 'subito_query' you can subtract only 'product' or 'list[product]'")
        return subito_query(self.name,self.url,self.min_price,self.max_price,prods=new_prods)
    
    def __str__(self) -> str:
        s = f"\nsearch: {self.name}\nquery url: {self.url}\n"
        for prod in self.prods:
            s+=f"\n\n {prod.title} : {prod.price} --> {prod.location}\n {prod.link}"
        return s
  
    def __repr__(self) -> str:
        return self.__str__()
    
    def add(self,new_prod) -> None:
        if isinstance(new_prod,product):
            if not new_prod in self.prods:
                self.prods.append(new_prod)
        elif isinstance(new_prod,list):
            if all([type(prod)==product for prod in new_prod]):
                self.prods.extend(list(set(new_prod) - set(self.prods)))
            else:
                raise TypeError("In the list there are obj that are not: 'product'")
        else:
            raise TypeError("only supported operand for add to query: 'product'")
    
    def to_dict(self) -> dict:

        query              = dict()

        query['name']      = self.name
        query['url']       = self.url
        query['min_price'] = self.min_price
        query['max_price'] = self.max_price

        query['products']  = list(map(lambda x:x.to_dict(),self.prods))

        return query

    def to_json(self,pathname=None,indent=0):

        if pathname:
            with open(pathname,'w') as f:
                json.dump(self.to_dict(),f,indent=indent)
        return json.dumps(self.to_dict(),indent=indent)
    
    def refresh(self) -> list[product]:

        try:
            new_quary = run_query(self.name, self.min_price, self.max_price,url=self.url)
        except requests.exceptions.ConnectionError:
            print("***Connection error when executing .refresh()***")
            return []
        except requests.exceptions.Timeout:
            print("***Server timeout error when executing .refresh()***")
            return []
        except requests.exceptions.HTTPError:
            print("***HTTP error when executing .refresh()***")
            return []

        app = copy(self.prods)
        new_prods = []

        for p in app:
            if not p in new_quary:
                self.delete(p)

        for new_p in new_quary:
            if not new_p in self.prods:
                self.add(new_p)
                new_prods.append(new_p)
        return new_prods

    def delete(self,to_delete:product) -> None:

        if to_delete in self.prods:
            self.prods.remove(to_delete)

    def sort(self,key=lambda x:x.price,reverse=False) -> None:
        self.prods.sort(key=key,reverse=reverse)


def load_product(prod_dict:dict) -> product:

    return product(
        prod_dict.get('title','Null'),
        prod_dict.get('price','Unknown price'),
        prod_dict.get('location','Unknown location'),
        prod_dict.get('link','Null')
    )

def load_query(query_dict:dict) -> subito_query:

    query = subito_query(
        query_dict.get('name','Null'),
        query_dict.get('url','Null'),
        query_dict.get('min_price','Null'),
        query_dict.get('max_price','Null')
    )

    for prod_dict in query_dict.get('products',[]):
        query += load_product(prod_dict)

    return query

def run_query(name:str, minPrice='null', maxPrice='null',url='') -> subito_query:

    args, _, _, values = getargvalues(currentframe())

    if any([type(values[par])!=str for par in args]):
        raise ValueError("All the parameters must be a string")

    if not minPrice == 'null':
        minPrice = int(minPrice)
    
    if not maxPrice == 'null':
        maxPrice = int(maxPrice)

    if url == '':
        url = 'https://www.subito.it/annunci-italia/vendita/usato/?q='+name
    
    query = subito_query(name,url,minPrice,maxPrice)
    page = requests.get(url)
    soup = BeautifulSoup(page.text, 'html.parser')
        
    product_list_items = soup.find_all('div', class_=re.compile(r'item-key-data'))

    for p in product_list_items:
        title = p.find('h2').string
                
        try:

            price =p.find('p',class_=re.compile(r'price')).contents[0]
            
            # check if the span tag exists
            price_soup = BeautifulSoup(price, 'html.parser')
            if type(price_soup) == Tag:
                continue
            price = int(price.replace('.','')[:-2])
            #at the moment (20.5.2021) the price is under the 'p' tag with 'span' inside if shipping available

        except:
            price = "Unknown price"
        link = p.parent.parent.parent.parent.get('href') 
        try:
            location = p.find('span',re.compile(r'town')).string + p.find('span',re.compile(r'city')).string
        except:
            location = "Unknown location"
        if minPrice == "null" or price == "Unknown price" or price>=minPrice:
            if maxPrice == "null" or price == "Unknown price" or price<=maxPrice:
                query += product(title,price,location,link)
    return query
