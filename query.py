from operator import(not_, eq, ne,
                     lt, gt, le, ge, add, sub,
                     mul, truediv as div, contains)

class QueryFail(Exception):
    pass

def op_wrap(op):
    def wrapper(*args):
        try:
            return op(*args)
        except (TypeError, ZeroDivisionError) as e:
            raise QueryFail(str(e))
    return wrapper

OPS = {
    "nt": op_wrap(not_),
    "eq": op_wrap(eq),
    "ne": op_wrap(ne),
    "lt": op_wrap(lt),
    "gt": op_wrap(gt),
    "le": op_wrap(le),
    "ge": op_wrap(ge),
    "pl": op_wrap(add),
    "su": op_wrap(sub),
    "ml": op_wrap(mul),
    "dv": op_wrap(div),
    "in": op_wrap(contains),
    "ln": op_wrap(len),
    "it": op_wrap(lambda c, ind: c[ind]),
}

class Query():
  def cond(self, true, false):
    return If(self, true, false)
  
  def in_(self, other):
    return Op("in", other, self)
  
  def len(self):
    return Op("ln", self)
  
  def __or__(self, other):
    return Or(self, other)
  
  def __and__(self, other):
    return And(self, other)
  
  def __eq__(self, other):
    return Op("eq", self, other)
  
  def __ne__(self, other):
    return Op("ne", self, other)
  
  def __lt__(self, other):
    return Op("lt", self, other)
  
  def __le__(self, other):
    return Op("le", self, other)
  
  def __gt__(self, other):
    return Op("gt", self, other)
  
  def __ge__(self, other):
    return Op("ge", self, other)
  
  def __add__(self, other):
    return Op("pl", self, other)
  
  def __sub__(self, other):
    return Op("su", self, other)
  
  def __mul__(self, other):
    return Op("ml", self, other)
  
  def __truediv__(self, other):
    return Op("dv", self, other)
  
  def __getitem__(self, ind):
    return Op("it", self, ind)
  
class Entry(Query):
  def to_query(self):
    return {"type": "entry"}
  
  def val(self, entry):
    return entry

class Pk(Query):
  def to_query(self):
    return {"type": "pk"}
  
  def val(self, entry, pk):
    return pk

class Pks(Query):
  def __init__(self, pks):
    self.pks = pks
  
  def to_query(self):
    return {
      "type": "pks",
      "pks": self.pks
    }

class Op(Query):
  def __init__(self, op, *args):
    self.op = op
    self.args = list(args)
  
  def to_query(self):
    return {
      "type": self.op,
      "args": [to_query(arg) for arg in self.args],
    }
  
  def val(self, entry, pk):
    args = (val(arg, entry, pk) for arg in self.args)
    return OPS[self.op](*args)

class Not(Op):
  def __init__(self, arg):
    super().__init__("nt", arg)

class Or(Query):
  def __init__(self, left, right):
    self.left = left
    self.right = right
  
  def to_query(self):
    return {
      "type": "or",
      "left": to_query(self.left),
      "right": to_query(self.right),
    }
  
  def val(self, entry, pk):
    return val(self.left, entry, pk) or val(self.right, entry, pk)

class And(Query):
  def __init__(self, left, right):
    self.left = left
    self.right = right
  
  def to_query(self):
    return {
      "type": "and",
      "left": to_query(self.left),
      "right": to_query(self.right),
    }
  
  def val(self, entry, pk):
    return val(self.left, entry, pk) and val(self.right, entry, pk)

class If(Query):
  def __init__(self, cond, true, false):
    self.cond = cond
    self.true = true
    self.false = false
  
  def to_query(self):
    return {
      "type": "if",
      "cond": to_query(self.cond),
      "true": to_query(self.true),
      "false": to_query(self.false),
    }
  
  def val(self, entry, pk):
    if val(self.cond, entry, pk):
      return val(self.true, entry, pk)
    else:
      return val(self.false, entry, pk)

class Attr(Query):
  def __init__(self, *which):
    self.which = which
  
  def to_query(self):
    return {
      "type": "attr",
      "which": self.which,
    }
  
  def val(self, entry, pk):
    res = entry
    for attr in self.which:
      res = res[attr]
    return res

class Const(Query):
  def __init__(self, val):
    self.value = val
  
  def to_query(self):
    return {
      "type": "const",
      "val": self.value,
    }
  
  def val(self, entry, pk):
    return self.value

def to_query(query):
  if isinstance(query, Query):
    return query.to_query()
  else:
    return Const(query).to_query()

def val(query, entry, pk):
  if isinstance(query, Query):
    return query.val(entry, pk)
  else:
    return query

def many_val(entry, queries, pk):
  return all(val(query, entry, pk) for query in queries)