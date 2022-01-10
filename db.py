import json
import requests

from query import *

DATABASE = "https://replitdb.pythonanywhere.com/"

class Database():
  def __init__(self, name, tab):
    self.name = name
    self.tab = tab
    url = DATABASE + name + "/" + tab + "/{}"
    self.url = url.format
    self.state = requests.post(self.url("state")).json()
  
  def sync(self):
    self.sync_state()
    
  def sync_state(self):
    requests.post(self.url("state"), json=self.state)

class ConnectedDatabase(Database):
  """
  Sends queries to the online database. Slower, but less memory used.
  """
  def query_with_id(self, *queries):
    url = self.url("query")
    queries = [to_query(query) for query in queries]
    res = requests.post(url, json=queries)
    try:
      return res.json()
    except:
      raise RuntimeError(res.text)
  
  def query(self, *queries):
    return [entry[1] for entry in self.query_with_id(*queries)]
  
  def insert(self, entries):
    url = self.url("insert")
    req = requests.post(url, json=entries)
    return req.json()
  
  def replace(self, entries, *queries):
    url = self.url("replace")
    queries = [to_query(query) for query in queries]
    requests.post(url, json=[queries, entries])
  
  def delete(self, *queries):
    url = self.url("delete")
    queries = [to_query(query) for query in queries]
    requests.post(url, json=queries)
  
  def clear(self):
    url = self.url("clear")
    requests.post(url)
  
  def curr_id(self):
    url = self.url("id")
    return requests.post(url).json()

class DBResult():
  def __init__(self, data):
    self.data = data
    
  def eval(self):
    return self.data
  
  def has(self, entry):
    return True # expects entries from its own data

class QueryResult():
  def __init__(self, base, query):
    self.base = base
    self.query = query
  
  def eval(self):
    query = self.query
    for entry, pk in self.base.eval():
      if val(query, entry, pk):
        yield entry
  
  def has(self, entry):
    pk, entry_ = entry
    return val(self.query, entry_, pk) and self.base.has(entry)

class PkResult():
  def __init__(self, base, pks, dct):
    self.base = base
    self.pks = pks
    self.pk_set = set(pks)
    self.dct = dct
  
  def eval(self):
    dct = self.dct
    for pk in self.pks:
      entry = dct[pk]
      if self.base.has(entry):
        yield entry
    
  def has(self, entry):
    pk, _ = entry
    return pk in self.pk_set and self.base.has(entry)

class LoadedDatabase(Database):
  """
  Downloads entire database into RAM, then runs queries. Faster, but needs
  more memory.
  """
  def __init__(self, name):
    super().__init__(name)
    url = self.url("query")
    res = requests.post(url, json=[])
    self.data = res.json()
    self.pk_dct = {}
    for pk, entry in self.data:
      self.pk_dct[pk] = entry
    
    self.curr_pk = max(pk for pk, _ in self.data) + 1
  
  def sync(self):
    super().sync()
    url = self.url("clear")
    requests.post(url)
    url = self.url("insert")
    requests.post(url, json=self.data)
  
  def query_with_id(self, *queries):
    res = DBResult(self.data)
    
    for query in queries:
      if isinstance(query, Pks):
        res = PkResult(res, query["pks"], self.data)
      else:
        res = QueryResult(res, query)
    
    return list(res.eval())
  
  def query(self, *queries):
    return [entry[1] for entry in self.query_with_id(*queries)]
  
  def insert(self, entries):
    for entry in entries:
      self.data.append([self.curr_pk, entry])
      self.pk_dct[self.curr_pk] = entry
      self.curr_pk += 1
  
  def replace(self, entries, *queries):
    entries = iter(entries)
    for ind, entry in enumerate(self.data):
      if many_val(entry, queries, entry[0]):
        try:
          self.data[ind][1] = next(entries)
        except StopIteration:
          return
  
  def delete(self, *queries):
    result = [
        entry for entry in self.data if not many_val(entry, queries, entry[0])
    ]

    self.data = result