import requests
import json
import re
import warnings

from .filterhandler import filter_handler
from .habanero_utils import switch_classes,check_json,is_json,parse_json_err,make_ua,filter_dict,rename_query_filters
from .exceptions import Error,RequestError
from .request_class import Request

def request(mailto, url, path, ids = None, query = None, filter = None,
        offset = None, limit = None, sample = None, sort = None,
        order = None, facet = None, select = None, works = None,
        cursor = None, cursor_max = None, agency = False, 
        progress_bar = False, should_warn = False, **kwargs):

  url = url + path

  if cursor_max is not None:
    if not isinstance(cursor_max, int):
      raise ValueError("cursor_max must be of class int")

  filt = filter_handler(filter)
  if isinstance(select, list):
    select = ','.join(select)

  payload = {'query':query, 'filter':filt, 'offset':offset,
             'rows':limit, 'sample':sample, 'sort':sort,
             'order':order, 'facet':facet, 'select':select,
             'cursor':cursor}
  payload = dict((k, v) for k, v in payload.items() if v)
  # add query filters
  payload.update(filter_dict(kwargs))
  # rename query filters
  payload = rename_query_filters(payload)

  if ids is None:
    url = url.strip("/")
    try:
      r = requests.get(url, params = payload, headers = make_ua(mailto))
      r.raise_for_status()
    except requests.exceptions.HTTPError:
      if is_json(r):
        raise RequestError(r.status_code, parse_json_err(r))
      else:
        r.raise_for_status()
    except requests.exceptions.RequestException as e:
      raise e
    check_json(r)
    coll = r.json()
  else:
    if isinstance(ids, str):
      ids = ids.split()
    if isinstance(ids, int):
      ids = [ids]
    should_warn = len(ids) > 1
    coll = []
    for i in range(len(ids)):
      if works:
        res = Request(mailto, url, str(ids[i]) + "/works",
          query, filter, offset, limit, sample, sort,
          order, facet, select, cursor, cursor_max, None, 
          progress_bar, **kwargs).do_request(should_warn = should_warn)
        coll.append(res)
      else:
        if agency:
          endpt = url + str(ids[i]) + "/agency"
        else:
          endpt = url + str(ids[i])

        endpt = endpt.strip("/")

        mssg = None
        try:
          r = requests.get(endpt, params = payload, headers = make_ua(mailto))
          if r.status_code > 201 and should_warn:
            mssg = '%s on %s: %s' % (r.status_code, ids[i], r.reason)
            warnings.warn(mssg)
        except requests.exceptions.HTTPError:
          if is_json(r):
            raise RequestError(r.status_code, parse_json_err(r))
          else:
            r.raise_for_status()
        except requests.exceptions.RequestException as e:
          raise e

        if mssg is not None:
          coll.append(None)
        else:
          check_json(r)
          js = r.json()
          #tt_out = switch_classes(js, path, works)
          coll.append(js)

    if len(coll) == 1:
      coll = coll[0]

  return coll
