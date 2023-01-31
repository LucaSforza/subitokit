#!/usr/bin/env python3.10.9

import requests
from bs4 import BeautifulSoup, Tag
import json
import requests
import re
from inspect import currentframe,getargvalues
from copy import copy

class product:

    def __init__(self,title:str,price,location:str,link:str) -> None:
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
        prod = dict()
        prod[self.link] = {'title': self.title, 'price': self.price, 'location': self.location}
        return prod

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
    
    def __add__(self,other):
        new_prods = copy(self.prods)
        if isinstance(other,product):
            new_prods.append(other)
        elif isinstance(other,list):
            if all([type(prod)==product for prod in other]):
                new_prods.extend(other)
            else:
                raise TypeError(f"unsupported operand type(s) for +: 'subito_query' and '{type(other)}' ,with 'subito_query' you can add only 'product' or 'list[product]'")
        else:
            raise TypeError(f"unsupported operand type(s) for +: 'subito_query' and '{type(other)}' ,with 'subito_query' you can add only 'product' or 'list[product]'")
        return subito_query(self.name,self.url,self.min_price,self.max_price,prods=new_prods)
    
    def __sub__(self,other):
        new_prods = copy(self.prods)
        if isinstance(other,product):
            new_prods.remove(other)
        elif isinstance(other,list):
            if all([type(prod)==product for prod in other]):
                for prod in other:
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
            self.prods.append(new_prod)
        elif isinstance(new_prod,list):
            if all([type(prod)==product for prod in new_prod]):
                self.prods.extend(new_prod)
            else:
                raise TypeError("In the list there are obj that are not: 'product'")
        else:
            raise TypeError("only supported operand for add to query: 'product'")
    
    def to_dict(self) -> dict:
        query = dict()
        for prod in self.prods:
            if not query.get(self.name):
                query[self.name] = {self.url:{self.min_price: {self.max_price: {prod.link: {'title': prod.title, 'price': prod.price, 'location': prod.location}}}}}
            else:
                query[self.name][self.url][self.min_price][self.max_price][prod.link] ={'title': prod.title, 'price': prod.price, 'location': prod.location}
        return query

    def to_json(self,pathname=None,indent=0):
        """
            Return a json string if not specificate 'pathname'
            Save in to a json file if specificate 'pathname'"""

        if pathname:
            with open(pathname,'w') as f:
                json.dump(self.to_dict(),f,indent=indent)
        return json.dumps(self.to_dict(),indent=indent)
    
    def refresh(self) -> list[product]:

        try:
            new_quary = run_query(self.url, self.name, self.min_price, self.max_price)
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
        self.prods.remove(to_delete)

    def sort(self,key=lambda x:x.price,reverse=False) -> None:
        self.prods.sort(key=key,reverse=reverse)


def load_product_from_dict(link,prod:dict)->product:
    items = list(prod.items())
    return product(items[0][1],items[1][1],items[2][1],link)

def load_query(pathname:str) -> subito_query:
    with open(pathname,'r') as f:
        query_dict:dict = json.load(f)
    for search in query_dict.items():
        name = search[0]
        for query_url in search[1]:
            url = query_url
            for u in search[1].items():
                for minP in u[1].items():
                    min_price = minP[0]
                    for maxP in minP[1].items():
                        max_price = maxP[0]
                        query = subito_query(name,url,min_price,max_price)
                        for result in maxP[1].items():
                            query += load_product_from_dict(result[0],result[1])

    return query

def run_query(url:str, name:str, minPrice:str, maxPrice:str) -> subito_query:

    frame = currentframe()
    args, _, _, values = getargvalues(frame)

    if any([type(values[par])!=str for par in args]):
        raise ValueError("All the parameters must be a string")
    
    query = subito_query(name,url,minPrice,maxPrice)
    page = requests.get(url)
    soup = BeautifulSoup(page.text, 'html.parser')
        
    product_list_items = soup.find_all('div', class_=re.compile(r'item-key-data'))

    for p in product_list_items:
        title = p.find('h2').string
                
        try:
            price=p.find('p',class_=re.compile(r'price')).contents[0]
            # check if the span tag exists
            price_soup = BeautifulSoup(price, 'html.parser')
            if type(price_soup) == Tag:
                continue
            #at the moment (20.5.2021) the price is under the 'p' tag with 'span' inside if shipping available

        except:
            price = "Unknown price__"
        link = p.parent.parent.parent.parent.get('href') 
        try:
            location = p.find('span',re.compile(r'town')).string + p.find('span',re.compile(r'city')).string
        except:
            location = "Unknown location"
        if minPrice == "null" or price == "Unknown price__" or price[:-2]>=minPrice:
            if maxPrice == "null" or price == "Unknown price__" or price[:-2]<=maxPrice:
                query += product(title,price[:-2],location,link)
    return query
