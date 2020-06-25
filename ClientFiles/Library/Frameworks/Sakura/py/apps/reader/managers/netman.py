# coding: utf8
# netman.py
# 10/17/2012 jichi
#
# About requests:
# - Gzip are automatically decoded by requests according to:
# http://docs.python-requests.org/en/latest/user/quickstart/
# - requests uses urllib3, which is thread-safe
# http://docs.python-requests.org/en/latest/
#
# Some of the expensive requests that will parse large data are using session
# Some cheap requests are using Qt session

#from sakurakit.skprof import SkProfiler

import json, operator
import requests
from datetime import datetime
from functools import partial
from cStringIO import StringIO
#import xml.etree.cElementTree as etree
from lxml import etree
from PySide.QtCore import Signal, QObject, QCoreApplication
from PySide.QtNetwork import QNetworkAccessManager, QNetworkConfigurationManager
from sakurakit import skthreads, skstr
from sakurakit.skclass import Q_Q, memoized, memoizedproperty, memoizedmethod_filter
from sakurakit.skdebug import dprint, dwarn, derror
from sakurakit.sknetdef import GZIP_HEADERS
from qtrequests import qtrequests
from mytr import my
from sysinfo import timestamp2jst
import config, dataman, defs, features, growl, json

session = requests.Session() # global request session

JSON_API = config.API_AJAX

CACHE_API = config.API_CACHE

XML_API = config.API_REST
#XML_API = "http://localhost:5000/api/1"
#XML_API = "http://localhost:5000/api/1"

V3_API = "http://localhost:5000/api/"
V3_HEADER = {
  'Accept-Encoding': 'gzip'
}

# Return true when context-type is xml or is None
def _response_is_xml(r):
  try: return "/xml" in r.headers['Content-Type'].lower()
  except (KeyError, TypeError, AttributeError): return True

XML_POST_HEADERS = {
  'Accept-Encoding': 'gzip',
  'Content-Type': 'application/x-www-form-urlencoded',
}

JSON_HEADERS = {
  'Content-Type': 'application/json',
}

@Q_Q
class _NetworkManager(object):
  def __init__(self, q):
    self._online = None # cached online status from qncm
    self.version = 0    # long timestamp

    self.cachedGamesById = {} # {long id:dataman.Game}
    self.cachedGamesByMd5 = {} # {str id:dataman.Game}
    self.blockedLanguages = '' # str

    if features.WINE:
      self.qtSession = qtrequests.AsyncSession(session) # qtSession is very slow on wine
    else:
      self.qtSession = qtrequests.Session(QNetworkAccessManager(q))

    # Track online status when network is down
    #self._onlineTimer = QTimer(self.q)
    #self._onlineTimer.setInterval(5000) # update every 5 seconds
    #self._onlineTimer.timeout.connect(self._updateOnline)

    # Update online on startup
    self.online

  def _addBlockedLanguages(self, params):
    """
    @param  params  dict
    """
    if self.blockedLanguages:
      params['nolang'] = self.blockedLanguages.replace('zh', 'zhs,zht')

  ## Filters ##

  #@staticmethod
  #def filterCommentText(text):
  #  """
  #  @param  unicode or None
  #  @return  unicode
  #  """
  #  return text.replace('\\sub', '').lstrip()

  ## Online status ##

  @memoizedproperty
  def qncm(self):
    ret = QNetworkConfigurationManager(self.q)
    ret.onlineStateChanged.connect(self._setOnline)
    return ret

  @property
  def online(self):
    if self._online is None:
      self.updateOnline()
    return self._online

  def updateOnline(self):
    self._setOnline(self.qncm.isOnline())

  def _setOnline(self, online):
    if features.INTERNET_CONNECTION == defs.INTERNET_CONNECTION_ON:
      online = True
      dwarn("force enabling Internet CONNECTION")
      growl.notify(my.tr("Always enable Internet access as you wish"))
    elif features.INTERNET_CONNECTION == defs.INTERNET_CONNECTION_OFF:
      online = False
      dwarn("force disabling Internet access")
      growl.notify(my.tr("Always disable Internet access as you wish"))
    if self._online != online:
      self._online = online
      dprint("online = %s" % online)

      if online:
        growl.msg(my.tr("Connected to the Internet"))
      else:
        growl.notify(my.tr("Disconnected from the Internet"))
      self.q.onlineChanged.emit(online)
  ## App ##

  @property
  @memoizedmethod_filter(bool)
  def cachedVersion(self):
     #return skthreads.runsync(self.queryVersion, parent=self.q)
     return self.queryVersion()

  def queryVersion(self):
    params = {'ver': self.version}
    try:
      r = self.qtSession.get(XML_API + '/app/version', params=params, headers=GZIP_HEADERS)
      if r.ok: #and _response_is_xml(r):
        root = etree.fromstring(r.content)
        #app = root.find('./apps/app[@id="%i"]' % config.VERSION_ID)
        app = root.find('./apps/app[@name="vnr"]')
        timestamp = int(app.find('./timestamp').text)
        dprint("timestamp = %i" % timestamp)
        return timestamp

    #except socket.error, e:
    #  dwarn("socket error", e.args)
    #except requests.ConnectionError, e:
    #  dwarn("connection error", e.args)
    #except requests.HTTPError, e:
    #  dwarn("http error", e.args)
    except etree.ParseError, e:
      dwarn("xml parse error", e.args)
    except KeyError, e:
      dwarn("invalid response header", e.args)
    except (TypeError, ValueError, AttributeError), e:
      dwarn("xml malformat", e.args)
    except Exception, e:
      derror(e)

    dwarn("failed URL follows")
    try: dwarn(r.url)
    except: pass
    return 0

  def getUpdateMessage(self, lang):
    """
    @param  lang  str
    @return  unicode or None
    """
    params = {'ver': self.version}
    if lang not in ('en', 'zhs', 'zht'):
      lang = 'en'
    try:
      r = session.get(XML_API + '/app/msg', params=params, headers=GZIP_HEADERS)
      if r.ok and _response_is_xml(r):
        root = etree.fromstring(r.content)
        #app = root.find('./apps/app[@id="%i"]' % config.VERSION_ID)
        for msg in root.iterfind('./messages/message[@app="vnr"][@language="%s"]' % lang):
          timestamp = int(msg.find('./timestamp').text)
          if timestamp > self.version:
            text = msg.find('./text').text
            return text

    #except socket.error, e:
    #  dwarn("socket error", e.args)
    except requests.ConnectionError, e:
      dwarn("connection error", e.args)
    except requests.HTTPError, e:
      dwarn("http error", e.args)
    except etree.ParseError, e:
      dwarn("xml parse error", e.args)
    except KeyError, e:
      dwarn("invalid response header", e.args)
    except (TypeError, ValueError, AttributeError), e:
      dwarn("xml malformat", e.args)
    except Exception, e:
      derror(e)

    dwarn("failed URL follows")
    try: dwarn(r.url)
    except: pass

  ## AJAX #

  def ajax(self, path, data, params=None, returndict=False):
    """
    @param  path  unicode
    @param  data  kw or str
    @param* returndict  bool
    @return  bool or kw
    """
    #data['ver'] = self.version
    try:
      if not isinstance(data, basestring):
        data = json.dumps(data)
      #r = session.post(JSON_API + path,
      r = self.qtSession.post(JSON_API + path,
          data=data,
          params=params,
          headers=JSON_HEADERS) #, headers=GZIP_HEADERS)
      if r.ok:
        res = json.loads(r.content)
        if returndict:
          return res
        return res['status'] == 0
    except Exception, e:
      derror(e)

    dwarn("failed data follow")
    try: dwarn(path, params or data)
    except: pass
    return False

  def upload(self, path, data, params):
    """
    @param  path  unicode
    @param  data  kw or str
    @param  params  kw
    @return  long or None
    """
    r = self.ajax(path, data, params, returndict=True)
    return r and r.get('id')

  ## User #

  # def queryUser(self, userName, password):
  #   assert userName and password, "missing user name or password "
  #   params = {'ver':self.version, 'login':userName, 'password':password, 'app':'reader'}
  #   try:
  #     r = self.qtSession.get(XML_API + 'go=auth', params=params, headers=GZIP_HEADERS)
  #     if r.ok and _response_is_xml(r.content):
  #       root = etree.fromstring(r.content)
  #       user = root.find('./users/user')
  #       ret = dataman.User()
  #       ret.id = int(user.get('id'))
  #       for e in user:
  #         tag = e.tag
  #         if tag in ('name', 'language', 'gender', 'color', 'avatar', 'homepage', 'access'):
  #           setattr(ret, tag, e.text or '')
  #         elif tag == 'levels':
  #           for it in e:
  #             if it.tag in ('term', 'comment'):
  #               setattr(ret, it.tag + 'Level', int(it.text))

  #       ret.password = password

  #       dprint("user name = %s" % ret.name)
  #       return ret

  #   #except socket.error, e:
  #   #  dwarn("socket error", e.args)
  #   #except requests.ConnectionError, e:
  #   #  dwarn("connection error", e.args)
  #   #except requests.HTTPError, e:
  #   #  dwarn("http error", e.args)
  #   except etree.ParseError, e:
  #     dwarn("xml parse error", e.args)
  #   except KeyError, e:
  #     dwarn("invalid response header", e.args)
  #   except (TypeError, ValueError, AttributeError), e:
  #     dwarn("xml malformat", e.args)
  #   except Exception, e:
  #     derror(e)

  #   dwarn("failed URL follows")
  #   try: dwarn(r.url, params)
  #   except: pass

  def queryUser(self, userName, password):
    """
    API Version: 3
    Return: dataman.User
    """
    params = {
      'username': userName,
      'password': password
    }
    try:
      r = session.post(V3_API + 'user/login', json=params)
      if not r.ok:
        r.raise_for_status()
      info = r.json()
      u = dataman.User()
      u.id = info.get('id', 0) # int
      u.name = info.get('username', '') # str
      u.language = info.get('language', '') # str
      u.gender = info.get('gender', '') # str
      u.homepage = info.get('homePage', '') # str
      u.avatar = info.get('avatar', '') # str
      u.color = info.get('color', '') # str
      u.termLevel = info.get('termLevel', 0) # int
      u.commentLevel = info.get('commentLevel', 0) # int
      u.access = info.get('access', '') # str
      u.password = password # str
      dprint("user name = %s" % u.name)
      return u
    except requests.ConnectionError as e:
      derror(e.message)
    except requests.HTTPError as e:
      derror(e.message)
    except Exception as e:
      derror(e.message)

    return None

  # def updateUser(self, userName, password, language=None, gender=None, avatar=None, color=None, homepage=None):
  #   """Return if succeeded"""
  #   assert userName and password, "missing user name or password "
  #   params = {'ver':self.version, 'login':userName, 'password':password}
  #   if language:
  #     params['lang'] = language
  #   if gender:
  #     params['gender'] = gender
  #   if avatar:
  #     params['avatar'] = avatar
  #   if homepage:
  #     params['homepage'] = homepage
  #   if color is not None:
  #     if color:
  #       params['color'] = color
  #     else:
  #       params['delcolor'] = True
  #
  #   try:
  #     r = self.qtSession.post(XML_API + 'go=user_update', data=params, headers=XML_POST_HEADERS)
  #     if r.ok and _response_is_xml(r.content):
  #       root = etree.fromstring(r.content)
  #       user = root.find('./users/user')
  #       userId = int(user.get('id'))
  #
  #       dprint("user id = %i" % userId)
  #       return userId != 0
  #
  #   #except socket.error, e:
  #   #  dwarn("socket error", e.args)
  #   #except requests.ConnectionError, e:
  #   #  dwarn("connection error", e.args)
  #   #except requests.HTTPError, e:
  #   #  dwarn("http error", e.args)
  #   except etree.ParseError, e:
  #     dwarn("xml parse error", e.args)
  #   except KeyError, e:
  #     dwarn("invalid response header", e.args)
  #   except (TypeError, ValueError, AttributeError), e:
  #     dwarn("xml malformat", e.args)
  #   except Exception, e:
  #     derror(e)
  #
  #   dwarn("failed URL follows")
  #   try: dwarn(r.url, params)
  #   except: pass
  #   return False

  def updateUser(self, userName, password, language=None, gender=None, avatar=None, color=None, homepage=None):
    """
    API Version: 3
    Return: bool
    """
    params = {
      'username': userName,
      'password': password
    }
    if language:
      params['language'] = language
    if gender:
      params['gender'] = gender
    if avatar:
      params['avatar'] = avatar
    if color:
      params['color'] = color
    if homepage:
      params['homePage'] = homepage
    try:
      r = session.post(V3_API + 'user/update', json=params)
      if not r.ok:
        r.raise_for_status()
      dprint('user profile updated')
      return True
    except requests.ConnectionError as e:
      derror(e.message)
    except requests.HTTPError as e:
      derror(e.message)
    except Exception as e:
      derror(e.message)

    return False

  ## Game ##

  #def getGameFiles(self):
  #  """
  #  @return [str md5] or None
  #  """
  #  params = {'ver': self.version}
  #  try:
  #    r = session.get(XML_API + '/game/md5', params=params, headers=GZIP_HEADERS)
  #    if r.ok:
  #      c = r.content
  #      if c:
  #        ret = c.split('\n')
  #        if len(ret) > 100:
  #          dprint("count = %i" % len(ret))
  #          return ret

  #  except socket.error, e:
  #    dwarn("socket error", e.args)
  #  except requests.ConnectionError, e:
  #    dwarn("connection error", e.args)
  #  except requests.HTTPError, e:
  #    dwarn("http error", e.args)

  #  dwarn("failed URL follows")
  #  try: dwarn(r.url)
  #  except: pass

  # def getGameItems(self):
  #   """
  #   @return {long itemId:dataman.GameItem} or None
  #   """
  #   params = {'ver': self.version}
  #   try:
  #     #url = XML_API + '/item/list'
  #     url = CACHE_API + 'go=gameitems'
  #     r = session.get(url, params=params, headers=GZIP_HEADERS)
  #     if r.ok and _response_is_xml(r):
  #       root = etree.fromstring(r.content)
  #       TYPES = dataman.Reference.TYPES
  #       ret = {}
  #       items = root.find('./items')
  #       if items is not None:
  #         for item in items:
  #           e = dataman.GameItem(id=int(item.get('id')))
  #           for el in item:
  #             tag = el.tag
  #             text = el.text
  #             if tag in ('title', 'romajiTitle', 'brand', 'series', 'image', 'banner', 'wiki', 'tags', 'artists', 'sdartists', 'writers', 'musicians'):
  #               setattr(e, tag, text)
  #             elif tag in ('otome', 'ecchi', 'okazu'):
  #               setattr(e, tag, text == 'true')
  #             elif tag in ('timestamp', 'fileSize', 'topicCount', 'annotCount', 'playUserCount', 'subtitleCount'):
  #               setattr(e, tag, int(text))
  #             elif tag == 'date':
  #               e.date = datetime.strptime(text, '%Y%m%d')
  #             elif tag == 'scape':
  #               for it in el:
  #                 if it.tag in ('count', 'median'):
  #                   setattr(e, 'scape' + it.tag.capitalize(), int(it.text))
  #             elif tag == 'scores':
  #               for it in el:
  #                 if it.tag == 'score':
  #                   t = it.get('type')
  #                   if t in defs.GAME_SCORE_TYPES:
  #                     setattr(e, t + 'ScoreCount', int(it.get('count')))
  #                     setattr(e, t + 'ScoreSum', int(it.get('sum')))
  #           ret[e.id] = e
  #       dprint("game item count = %i" % len(ret))
  #       return ret

  #   #except socket.error, e:
  #   #  dwarn("socket error", e.args)
  #   except requests.ConnectionError, e:
  #     dwarn("connection error", e.args)
  #   except requests.HTTPError, e:
  #     dwarn("http error", e.args)
  #   except etree.ParseError, e:
  #     dwarn("xml parse error", e.args)
  #   except KeyError, e:
  #     dwarn("invalid response header", e.args)
  #   except (TypeError, ValueError, AttributeError), e:
  #     dwarn("xml malformat", e.args)
  #   except Exception, e:
  #     derror(e)

  #   dwarn("failed URL follows")
  #   try: dwarn(r.url, params)
  #   except: 
  #     dwarn("pass")
  #     pass

  def getGameItems(self):
    """
    API Version: 3
    Return: Dict<ItemId,dataman.GameItem>
    """
    try:
      r = session.post(V3_API + 'game/items')
      if not r.ok:
        r.raise_for_status()
      items = r.json()
      ret = {}
      for item in items:
        it = dataman.GameItem()
        it.id = item.get('id', 0) # int
        it.title = item.get('title', '') # str
        it.romajiTitle = item.get('romajiTitle', '') # str
        it.brand = item.get('brand', '') # str
        it.series = item.get('series', '') # str
        it.image = item.get('imageUrl', '') # str
        it.banner = item.get('bannerUrl', '') # str
        it.wiki = item.get('wiki', '') # str
        it.fileSize = item.get('fileSize', 0) # int
        it.timestamp = item.get('timestamp', 0) # int
        it.date = datetime.strptime(item.get('date', ''), '%Y%m%d') # DateTime
        it.otome = item.get('otome', False) # bool
        it.ecchi = item.get('ecchi', False) # bool
        it.okazu = item.get('okazu', False) # bool
        it.scapeMedian = item.get('scapeMedian', 0) # int
        it.scapeCount = item.get('scapeCount', 0) # int
        it.topicCount = item.get('topicCount', 0) # int
        it.annotCount = item.get('annotCount', 0) # int
        it.subtitleCount = item.get('subtitleCount', 0) # int
        it.playUserCount = item.get('playUserCount', 0) # int
        it.tags = item.get('tags', '') # str
        it.artists = item.get('artists', '') # str
        it.sdartists = item.get('sdartists', '') # str
        it.writers = item.get('writers', '') # str
        it.musicians = item.get('musicians', '') # str
        it.overallScoreSum = item.get('overallScoreSum', 0) # int
        it.overallScoreCount = item.get('overallScoreCount', 0) # int
        it.ecchiScoreSum = item.get('ecchiScoreSum', 0) # int
        it.ecchiScoreCount = item.get('ecchiScoreCount', 0) # int
        ret[it.id] = it
      dprint("game item count = %i" % len(ret))
      return ret
    except requests.ConnectionError as e:
      derror(e.message)
    except requests.HTTPError as e:
      derror(e.message)
    except Exception as e:
      derror(e.message)

    return None

  #def getReferenceDigests(self):
  #  """
  #  @return {long itemId:[dataman.ReferenceDigest]} or None
  #  """
  #  params = {'ver': self.version}
  #  try:
  #    r = session.get(XML_API + '/ref/list', params=params, headers=GZIP_HEADERS)
  #    if r.ok and _response_is_xml(r):
  #      root = etree.fromstring(r.content)
  #      TYPES = dataman.Reference.TYPES
  #      ret = {}
  #      refs = root.find('./references')
  #      if refs is not None:
  #        TYPES = dataman.Reference.TYPES
  #        for ref in refs:
  #          r = dataman.ReferenceDigest(
  #              id = int(ref.get('id')),
  #              type = ref.get('type'))
  #          for el in ref:
  #            tag = el.tag
  #            text = el.text
  #            if tag in ('itemId', 'gameId', 'timestamp'):
  #              setattr(r, tag, int(text))
  #            elif tag in ('key', 'title', 'brand', 'image'):
  #              setattr(r, tag, text or '')
  #            elif tag == 'date':
  #              r.date = timestamp2jst(int(text))
  #          if r.type in TYPES:
  #            try: ret[r.itemId].append(r)
  #            except KeyError: ret[r.itemId] = [r]
  #      dprint("game item count = %i" % len(ret))
  #      return ret

  #  except socket.error, e:
  #    dwarn("socket error", e.args)
  #  except requests.ConnectionError, e:
  #    dwarn("connection error", e.args)
  #  except requests.HTTPError, e:
  #    dwarn("http error", e.args)
  #  except etree.ParseError, e:
  #    dwarn("xml parse error", e.args)
  #  except KeyError, e:
  #    dwarn("invalid response header", e.args)
  #  except (TypeError, ValueError, AttributeError), e:
  #    dwarn("xml malformat", e.args)
  #  except Exception, e:
  #    derror(e)

  #  dwarn("failed URL follows")
  #  try: dwarn(r.url, params)
  #  except: pass

  # def getGameFiles(self):
  #   """
  #   @return {long id:dataman.GameFile} or None
  #   """
  #   params = {'ver': self.version}
  #   try:
  #     r = session.get(XML_API + 'go=gamefiles', params=params, headers=GZIP_HEADERS)
  #     if r.ok and _response_is_xml(r):
  #       root = etree.fromstring(r.content)
  #       ret = {}
  #       games = root.find('./games')
  #       if games is not None:
  #         for game in games:
  #           g = dataman.GameFile(id=int(game.get('id')))
  #           for el in game:
  #             tag = el.tag
  #             if tag in ('itemId', 'visitCount', 'commentCount'):
  #               setattr(g, tag, int(el.text))
  #             elif tag == 'md5':
  #               g.md5 = el.text
  #             elif tag == 'names':
  #               e = el.find('./name[@type="file"]')
  #               if e is not None:
  #                 g.name = e.text
  #           ret[g.id] = g
  #       dprint("game count = %i" % len(ret))
  #       return ret

  #   #except socket.error, e:
  #   #  dwarn("socket error", e.args)
  #   except requests.ConnectionError, e:
  #     dwarn("connection error", e.args)
  #   except requests.HTTPError, e:
  #     dwarn("http error", e.args)
  #   except etree.ParseError, e:
  #     dwarn("xml parse error", e.args)
  #   except KeyError, e:
  #     dwarn("invalid response header", e.args)
  #   except (TypeError, ValueError, AttributeError), e:
  #     dwarn("xml malformat", e.args)
  #   except Exception, e:
  #     derror(e)

  #   dwarn("failed URL follows")
  #   try: dwarn(r.url, params)
  #   except: pass

  def getGameFiles(self):
    """
    API Version: 3
    Return: Dict<GameId,dataman.GameFile>
    """
    try:
      r = session.post(V3_API + 'game/files')
      if not r.ok:
        r.raise_for_status()
      games = r.json()
      ret = {}
      for game in games:
        g = dataman.GameFile()
        g.id = game.get('id', 0) # int
        g.md5 = game.get('md5', '') # str
        g.name = game.get('fileName', '') # str
        g.itemId = game.get('itemId', 0) # int
        g.visitCount = game.get('visits', 0) # int
        g.commentCount = game.get('comments', 0) # int
        ret[g.id] = g
      dprint("game count = %i" % len(ret))
      return ret
    except requests.ConnectionError as e:
      derror(e.message)
    except requests.HTTPError as e:
      derror(e.message)
    except Exception as e:
      derror(e.message)

    return None

  # def getUsers(self):
  #   """
  #   @return {long id:dataman.UserDigest} or None
  #   """
  #   params = {'ver': self.version}
  #   try:
  #     #url = XML_API + '/user/list'
  #     url = CACHE_API + 'go=users'
  #     r = session.get(url, params=params, headers=GZIP_HEADERS)
  #     if r.ok and _response_is_xml(r):
  #       context = etree.iterparse(StringIO(r.content), events=('start', 'end'))

  #       ret = {}
  #       path = 0
  #       for event, elem in context:
  #         if event == 'start':
  #           path += 1
  #           if path == 3: # grimoire/users/user
  #             u = dataman.UserDigest(id=int(elem.get('id')))
  #         else:
  #           path -= 1
  #           if path == 3: # grimoire/users/user
  #             tag = elem.tag
  #             if tag in ('name', 'language', 'gender', 'avatar', 'color', 'homepage'):
  #               setattr(u, tag, elem.text or '')
  #             elif tag == 'levels':
  #               for it in elem:
  #                 if it.tag in ('term', 'comment'):
  #                   setattr(u, it.tag + 'Level', int(it.text))
  #           elif path == 2:
  #             ret[u.id] = u

  #       #dprint("user count = %i" % len(ret))
  #       dprint("succeed")
  #       return ret

  #   #except socket.error, e:
  #   #  dwarn("socket error", e.args)
  #   except requests.ConnectionError, e:
  #     dwarn("connection error", e.args)
  #   except requests.HTTPError, e:
  #     dwarn("http error", e.args)
  #   except etree.ParseError, e:
  #     dwarn("xml parse error", e.args)
  #   except KeyError, e:
  #     dwarn("invalid response header", e.args)
  #   except (TypeError, ValueError, AttributeError), e:
  #     dwarn("xml malformat", e.args)
  #   except Exception, e:
  #     derror(e)

  #   dwarn("failed URL follows")
  #   try: dwarn(r.url, params)
  #   except: pass

  def getUsers(self):
    """
    API Version: 3
    Return: Dict<UserId,dataman.UserDigest>
    """
    try:
      r = session.post(V3_API + 'user/all')
      if not r.ok:
        r.raise_for_status()
      users = r.json()
      ret = {}
      for user in users:
        u = dataman.UserDigest()
        u.id = user.get('id', 0) # int
        u.name = user.get('username', '') # str
        u.language = user.get('language', '') #str
        u.gender = user.get('gender', '') # str
        u.homepage = user.get('homePage', '') # str
        u.avatar = user.get('avatar', '') # str
        u.color = user.get('color', '') # str
        u.termLevel = user.get('termLevel', 0) # int
        u.commentLevel = user.get('commentLevel', 0) # int
        u.access = user.get('access', '') # str
        ret[u.id] = u
      dprint("user count = %i" % len(ret))
      return ret
    except requests.ConnectionError as e:
      derror(e.message)
    except requests.HTTPError as e:
      derror(e.message)
    except Exception as e:
      derror(e.message)

    return None

  # def queryGame(self, id=None, md5=None):
  #   assert id or md5, "missing id and digest"
  #   params = {'ver': self.version}
  #   if id:
  #     params['id'] = id
  #   else:
  #     params['md5'] = md5

  #   try:
  #     r = session.get(XML_API + 'go=game_query', params=params, headers=GZIP_HEADERS)
  #     if r.ok and _response_is_xml(r):
  #       root = etree.fromstring(r.content)
  #       game = root.find('./games/game')

  #       ret = dataman.Game()
  #       ret.id = int(game.get('id'))

  #       for e in game:
  #         tag = e.tag
  #         if tag in ('md5', 'encoding', 'language'):
  #           setattr(ret, tag, e.text or '')
  #         elif tag in ('itemId', 'commentCount'):
  #           setattr(ret, tag, int(e.text))
  #         elif tag in ('removesRepeat', 'ignoresRepeat', 'keepsSpace', 'threadKept'):
  #           setattr(ret, tag, e.text == 'true')
  #         elif tag == 'hook':
  #           if e.get('deleted') == 'true':
  #             ret.deletedHook = e.text
  #           else:
  #             ret.hook = e.text
  #             #if e.get('kept') == 'true':
  #             #  ret.hookKept = True
  #         elif tag == 'threads':
  #           thread = e.find('./thread[@type="scene"]')
  #           if thread is not None and thread.get('deleted') != 'true':
  #             ret.threadName = thread.find('./name').text
  #             ret.threadSignature = long(thread.find('./signature').text)
  #           thread = e.find('./thread[@type="name"]')
  #           if thread is not None and thread.get('deleted') != 'true':
  #             ret.nameThreadName = thread.find('./name').text
  #             ret.nameThreadSignature = long(thread.find('./signature').text)
  #         elif tag == 'names':
  #           ret.names = {
  #             t:[it.text for it in e.iterfind('./name[@type="%s"]' % t)]
  #             for t in ret.NAME_TYPES
  #           }

  #       if not ret.language: ret.language = 'ja'

  #       dprint("game id = %i" % ret.id)
  #       return ret

  #   #except socket.error, e:
  #   #  dwarn("socket error", e.args)
  #   except requests.ConnectionError, e:
  #     dwarn("connection error", e.args)
  #   except requests.HTTPError, e:
  #     dwarn("http error", e.args)
  #   except etree.ParseError, e:
  #     dwarn("xml parse error", e.args)
  #   except KeyError, e:
  #     dwarn("invalid response header", e.args)
  #   except (TypeError, ValueError, AttributeError), e:
  #     dwarn("xml malformat", e.args)
  #   except Exception, e:
  #     derror(e)

  #   dwarn("failed URL follows")
  #   try: dwarn(r.url, params)
  #   except: pass

  def queryGame(self, id=None, md5=None):
    """
    API Version: 3
    Return: dataman.Game
    """
    params = {
      'id': id,
      'md5': md5
    }
    try:
      r = session.post(V3_API + 'game/detail', json=params)
      if not r.ok:
        r.raise_for_status()
      dt = r.json()
      g = dataman.Game()
      g.id = dt.get('id', 0) # int
      g.md5 = dt.get('md5', '') # str
      g.itemId = dt.get('gameItemId', 0) # int
      g.commentCount = dt.get('comments', 0) # int
      if 'textSetting' in dt:
        setting = dt.get('textSetting')
        g.encoding = setting.get('encoding', '') # str
        g.language = setting.get('language', 'ja') # str
        g.removesRepeat = setting.get('removeRepeat', False) # bool
        g.ignoresRepeat = setting.get('ignoreRepeat', False) # bool
        g.keepsSpace = setting.get('keepSpaces', False) # bool
        g.threadKept = setting.get('keepAllText', False) # bool
        g.hook = setting.get('hookCode', '') # str
        if 'hooks' in setting:
          hooks = setting.get('hooks')
          for hook in hooks:
            if hook['type'] == 'scene':
              g.threadName = hook['name'] # str
              g.threadSignature = long(hook['sig']) # int
            elif hook['type'] == 'name':
              g.nameThreadName = hook['name'] # str
              g.nameThreadSignature = long(hook['sig']) # int
      if 'names' in dt:
        names = dt.get('names')
        for name in names:
          g.names[name['type']] = name['value'].split('||') # [str]
      dprint("game id = %i" % g.id)
      return g
    except requests.ConnectionError as e:
      derror(e.message)
    except requests.HTTPError as e:
      derror(e.message)
    except Exception as e:
      derror(e.message)

    return None

  # def updateGame(self, game, userName, password, deleteHook=False):
  #   """Return if succeeded"""
  #   assert userName and password, "missing user name or password"
  #   assert game and (game.id or game.md5), "missing id and digest"
  #
  #   params = {'ver':self.version, 'login':userName, 'password':password}
  #
  #   #if game.md5 and len(game.md5) != defs.MD5_HEX_LENGTH:
  #   #  assert False, "invalid md5 digest"
  #
  #   if game.id:               params['id']          = game.id
  #   if game.md5:              params['md5']         = game.md5
  #   if game.encoding:         params['encoding']    = game.encoding
  #   if game.language:         params['lang']        = game.language
  #   if game.hook:             params['hook']        = game.hook
  #   if game.threadName:       params['threadname']  = game.threadName
  #   if game.threadSignature:  params['threadsig']   = game.threadSignature
  #   if game.nameThreadName:      params['namethreadname'] = game.nameThreadName
  #   if game.nameThreadSignature: params['namethreadsig']  = game.nameThreadSignature
  #   if deleteHook:            params['delhook'] = True
  #   #if game.hookKept is not None: params['keephook'] = game.hookKept
  #   if game.threadKept is not None: params['keepthread'] = game.threadKept
  #   if game.keepsSpace is not None:  params['keepspace'] = game.keepsSpace
  #   if game.removesRepeat is not None:  params['removerepeat'] = game.removesRepeat
  #   if game.ignoresRepeat is not None:  params['ignorerepeat'] = game.ignoresRepeat
  #   if game.nameThreadDisabled is not None: params['delnamethread'] = game.nameThreadDisabled
  #
  #   for t in game.names:
  #     if game.names[t]:       params['%sname' % t]      = game.names[t]
  #
  #   try:
  #     r = session.post(XML_API + 'go=game_update', data=params, headers=XML_POST_HEADERS)
  #     dwarn(r.url, params)
  #     if r.ok and _response_is_xml(r):
  #       root = etree.fromstring(r.content)
  #       e_game = root.find('./games/game')
  #       game.id = int(e_game.get('id'))
  #       game.md5 = e_game.find('./md5').text
  #       try: game.itemId = long(e_game.find('./itemId').text)
  #       except: pass
  #
  #       dprint("game id = %i" % game.id)
  #       return game.id != 0
  #
  #   #except socket.error, e:
  #   #  dwarn("socket error", e.args)
  #   except requests.ConnectionError, e:
  #     dwarn("connection error", e.args)
  #   except requests.HTTPError, e:
  #     dwarn("http error", e.args)
  #   except etree.ParseError, e:
  #     dwarn("xml parse error", e.args)
  #   except KeyError, e:
  #     dwarn("invalid response header", e.args)
  #   except (TypeError, ValueError, AttributeError), e:
  #     dwarn("xml malformat", e.args)
  #   except Exception, e:
  #     derror(e)
  #
  #   dwarn("failed URL follows")
  #   try: dwarn(r.url, params)
  #   except: pass
  #   return False

  def updateGame(self, game, userName, password, deleteHook=False):
    """
    API Version: 3
    Return: bool
    """
    params = {
      'username': userName,
      'password': password,
      'id': game.id,
      'md5': game.md5,
      'names': [],
      'textSetting': {
        'encoding': game.encoding,
        'language': game.language,
        'keepAllText': game.threadKept,
        'keepSpaces': game.keepsSpace,
        'removeRepeat': game.removesRepeat,
        'ignoreRepeat': game.ignoresRepeat,
        'hooks': [
          {
            'type': 'scene',
            'name': game.threadName,
            'sig': str(game.threadSignature),
            'delete': deleteHook
          },
          {
            'type': 'name',
            'name': game.nameThreadName,
            'sig': str(game.nameThreadSignature),
            'delete': game.nameThreadDisabled
          }
        ]
      },
      'hookCode': game.hook
    }
    for (t, v) in game.names.items():
      if (v is not None) and (len(v) > 0):
        params['names'].append({
          'type': t,
          'value': '||'.join(v)
        })
    try:
      r = session.post(V3_API + 'game/update', json=params)
      if not r.ok:
        r.raise_for_status()
      data = r.json()
      game.id = data.get('id', game.id)
      dprint('game(%i) data updated' % game.id)
      return True
    except requests.ConnectionError as e:
      derror(e.message)
    except requests.HTTPError as e:
      derror(e.message)
    except Exception as e:
      derror(e.message)

    return False

  ## References ##

  # def queryReferences(self, gameId=None, md5=None, init=True):
  #   """
  #   @param  init  bool whether init comment object
  #   @param  hash  bool
  #   @return  [Reference] or None
  #   """
  #   assert gameId or md5, "missing id and digest"
  #   params = {'ver':self.version}
  #   if gameId:
  #     params['gameid'] = gameId
  #   else:
  #     params['md5'] = md5
  #
  #   try:
  #     r = session.get(XML_API + 'go=reference', params=params, headers=GZIP_HEADERS)
  #     if r.ok and _response_is_xml(r):
  #       #root = etree.fromstring(r.content)
  #       GUEST_ID = dataman.GUEST.id
  #
  #       context = etree.iterparse(StringIO(r.content), events=('start', 'end'))
  #
  #       ret = []
  #       path = 0
  #       TYPES = dataman.Reference.TYPES
  #       for event, elem in context:
  #         if event == 'start':
  #           path += 1
  #           if path == 3: # grimoire/references/reference
  #             kw = {
  #               #'comment': "",
  #               #'updateComment': "",
  #               #'updateTimestamp':  0,
  #               #'updateUserId': 0,
  #               #'disabled': False,
  #               'id': int(elem.get('id')),
  #               'type': elem.get('type'),
  #             }
  #         else:
  #           path -= 1
  #           if path == 3: # grimoire/references/reference
  #             tag = elem.tag
  #             text = elem.text
  #             if tag in ('key', 'title', 'brand', 'url', 'comment', 'updateComment'): #'image'
  #               kw[tag] = text or ''
  #             elif tag in ('itemId', 'gameId', 'userId', 'userHash', 'timestamp', 'updateUserId', 'updateTimestamp'):
  #               kw[tag] = int(text)
  #             elif tag == 'disabled':
  #               kw[tag] = text == 'true'
  #             elif tag == 'date':
  #               kw[tag] = timestamp2jst(int(text))
  #             #else:
  #             #  kw[tag] = text or ''
  #
  #           elif path == 2 and kw['type'] in TYPES: # grimoire/references
  #             #if not kw.get('userHash'):
  #             #  kw['userHash'] = kw['userId']
  #             ret.append(dataman.Reference(init=init, **kw))
  #
  #       if init:
  #         mainThread = QCoreApplication.instance().thread()
  #         for it in ret:
  #           it.moveToThread(mainThread)
  #       dprint("reference count = %i" % len(ret))
  #       return ret
  #
  #   #except socket.error, e:
  #   #  dwarn("socket error", e.args)
  #   except requests.ConnectionError, e:
  #     dwarn("connection error", e.args)
  #   except requests.HTTPError, e:
  #     dwarn("http error", e.args)
  #   except etree.ParseError, e:
  #     dwarn("xml parse error", e.args)
  #   except KeyError, e:
  #     dwarn("invalid response header", e.args)
  #   except (TypeError, ValueError, AttributeError), e:
  #     dwarn("xml malformat", e.args)
  #   except Exception, e:
  #     derror(e)
  #
  #   dwarn("failed URL follows")
  #   try: dwarn(r.url, params)
  #   except: pass

  def queryReferences(self, gameId=None, md5=None, init=True):
    """
    API Version: 3
    Return: dataman.Reference[]
    """
    params = {
      'gameId': gameId,
      'md5': md5
    }
    try:
      r = session.post(V3_API + 'game/references', json=params)
      if not r.ok:
        r.raise_for_status()
      refs = r.json()
      ret = []
      for ref in refs:
        kw = {}
        kw['id'] = ref.get('id', 0) # int
        kw['itemId'] = ref.get('gameItemId', 0) # int
        kw['gameId'] = ref.get('gameId', 0)  # int
        # kw['gameMd5'] = ref.get('gameMd5', 0)  # str
        kw['userId'] = ref.get('creatorId', 0)  # int
        # kw['userHash'] = long(ref.get('userHash', '0'))  # int
        kw['type'] = ref.get('type', '')  # str
        kw['key'] = ref.get('key', '')  # str
        kw['timestamp'] = ref.get('creationTime', 0)  # int
        kw['title'] = ref.get('title', '')  # str
        kw['brand'] = ref.get('brand', '')  # str
        kw['url'] = ref.get('url', '')  # str
        kw['date'] = ref.get('date', 0)  # int
        kw['comment'] = ref.get('creationComment', '')  # str
        kw['updateComment'] = ref.get('revisionComment', '')  # str
        kw['updateUserId'] = ref.get('editorId', 0)  # int
        kw['updateTimestamp'] = ref.get('revisionTime', 0)  # int
        kw['disabled'] = ref.get('disabled', 0)  # bool
        if kw['type'] in dataman.Reference.TYPES:
          ret.append(dataman.Reference(init=init, **kw))
      if init:
        mainThread = QCoreApplication.instance().thread()
        for it in ret:
          it.moveToThread(mainThread)
      dprint("reference count = %i" % len(ret))
      return ret
    except requests.ConnectionError as e:
      derror(e.message)
    except requests.HTTPError as e:
      derror(e.message)
    except Exception as e:
      derror(e.message)

    return None

  def submitReference(self, ref, userName, password, md5=None, async=False):
    """Update reference if succeeded
    @return  (gameId, itemId) or None
    """
    rd = ref.d
    #assert userName and password, "missing user name or password"
    #assert ref and (ref.gameId or md5), "missing game id and digest"

    params = {
      'ver': self.version,
      'login': userName,
      'password': password,
      'type': rd.type,
      'key': rd.key,
      'url': rd.url,
      'title': rd.title
          if len(rd.title) <= defs.MAX_TEXT_LENGTH
          else rd.title[:defs.MAX_TEXT_LENGTH],
    }
    if rd.brand:
      params['brand'] = rd.brand
    if rd.date:
      params['date'] = rd.date
    if ref.image:
      params['image'] = ref.image # _References don't have image
    #if rd.itemId:
    #  params['itemId'] = rd.itemId
    if rd.gameId:
      params['gameid'] = rd.gameId
    else:
      params['md5'] = md5 or rd.gameMd5

    if rd.comment:
      params['comment'] = (rd.comment
          if len(rd.comment) <= defs.MAX_TEXT_LENGTH
          else rd.comment[:defs.MAX_TEXT_LENGTH])

    if rd.updateComment:
      params['updatecomment'] = (rd.updateComment
          if len(rd.updateComment) <= defs.MAX_TEXT_LENGTH
          else rd.updateComment[:defs.MAX_TEXT_LENGTH])

    if rd.deleted:
      # Should never happen. I mean, deleted subs should have been skipped in dataman
      params['del'] = True
    if rd.disabled:
      params['disable'] = True

    try:
      if not async:
        r = session.post(XML_API + 'go=add_reference', data=params, headers=XML_POST_HEADERS)
      else:
        r = skthreads.runsync(partial(
            session.post,
            XML_API + 'go=add_reference', data=params, headers=XML_POST_HEADERS))

      if r.ok and _response_is_xml(r):
        root = etree.fromstring(r.content)
        el = root.find('./references/reference')

        # Be careful about async here
        # Might raise after ref QObject is deleted
        try:
          ref.id = int(el.get('id'))
          ref.itemId = int(el.find('itemId').text)
        except Exception, e:
          dwarn(e)
          rd.id = int(el.get('id'))
          rd.itemId = int(el.find('itemId').text)

        gameId = itemId = 0
        el = root.find('./games/game')
        if el:
          gameId = int(el.get('id'))
          itemId = int(el.find('itemId').text)

        dprint("ref id = %i" % rd.id)
        return gameId, itemId

    #except socket.error, e:
    #  dwarn("socket error", e.args)
    except requests.ConnectionError, e:
      dwarn("connection error", e.args)
    except requests.HTTPError, e:
      dwarn("http error", e.args)
    except etree.ParseError, e:
      dwarn("xml parse error", e.args)
    except KeyError, e:
      dwarn("invalid response header", e.args)
    except (TypeError, ValueError, AttributeError), e:
      dwarn("xml malformat", e.args)
    except Exception, e:
      derror(e)

    dwarn("failed URL follows")
    try: dwarn(r.url, params)
    except: pass

  def updateReference(self, ref, userName, password, async=False):
    """
    @return  (int gameId, int itemId) or None
    """
    #assert userName and password, "missing user name or password"
    #assert ref and ref.id, "missing reference id"
    rd = ref.d
    params = {}
    pty = ref.dirtyProperties()
    if not pty:
      dwarn("warning: reference to update is not dirty")
      return rd.itemId

    if 'deleted' in pty:        params['del'] = rd.deleted
    #if not rd.deleted:
    if 'disabled' in pty:     params['disable'] = rd.disabled

    for k in 'comment', 'updateComment':
      if k in pty:
        v = getattr(rd, k)
        if v:
          params[k.lower()] = (v
              if len(v) <= defs.MAX_TEXT_LENGTH
              else v[:defs.MAX_TEXT_LENGTH])
        else:
          params['del' + k.lower()] = True

    if not params:
      dwarn("warning: nothing change")
      return rd.itemId

    params['login'] = userName
    params['password'] = password
    params['id'] = rd.id
    params['ver'] = self.version

    try:
      if not async:
        r = session.post(XML_API + 'go=update_reference', data=params, headers=XML_POST_HEADERS)
      else:
        r = skthreads.runsync(partial(
            session.post,
            XML_API + 'go=update_reference', data=params, headers=XML_POST_HEADERS))

      if r.ok and _response_is_xml(r):
        root = etree.fromstring(r.content)
        el = root.find('./references/reference')
        refId = int(el.get('id'))
        if refId:
          gameId = itemId = 0
          el = root.find('./games/game')
          if el:
            gameId = int(el.get('id'))
            itemId = int(el.find('itemId').text)
          dprint("ref id = %i" % refId)
          return gameId, itemId

    #except socket.error, e:
    #  dwarn("socket error", e.args)
    except requests.ConnectionError, e:
      dwarn("connection error", e.args)
    except requests.HTTPError, e:
      dwarn("http error", e.args)
    except etree.ParseError, e:
      dwarn("xml parse error", e.args)
    except KeyError, e:
      dwarn("invalid response header", e.args)
    except (TypeError, ValueError, AttributeError), e:
      dwarn("xml malformat", e.args)
    except Exception, e:
      derror(e)

    dwarn("failed URL follows")
    try: dwarn(r.url, params)
    except: pass

  # Subtitles

  def querySubtitles(self, itemId, gameLang, langs, difftime):
    """
    @param  itemId  long
    @param* gameLang  str
    @param* langs  [str]
    @param* difftime  long
    @return  [dataman.Subtitle] or None
    """
    params = {
      'ver': self.version,
      'gameid': itemId,
    }
    if gameLang:
      params['textlang'] = gameLang
    if langs:
      params['sublang'] = ','.join(langs)
    if difftime:
      params['mintime'] = difftime

    try:
      r = session.get(XML_API + '/sub/query', params=params, headers=GZIP_HEADERS)
      if r.ok and _response_is_xml(r):
        #root = etree.fromstring(r.content)

        ret = []
        context = etree.iterparse(StringIO(r.content), events=('start', 'end'))
        path = 0
        for event, elem in context:
          if event == 'start':
            path += 1
            if path == 3: # grimoire/texts/text
              kw = {
                'textId': int(elem.get('id')),
              }
              v = elem.get('time')
              if v:
                kw['textTime'] = int(v)
            elif path == 4: # grimoire/texts/text/subs
              kw['subLang'] = elem.get('lang') or ''
            elif path == 5: # grimoire/texts/text/subs/sub
              v = elem.get('time')
              if v:
                kw['subTime'] = int(v)
              v = elem.get('userId')
              if v:
                kw['userId'] = int(v)
          else:
            path -= 1
            if path == 3: # grimoire/texts/text
              tag = elem.tag
              text = elem.text
              if tag == 'content':
                kw['text'] = text
              elif tag == 'name':
                kw['textName'] = text
            if path == 5: # grimoire/texts/text/subs/sub
              tag = elem.tag
              text = elem.text
              if tag == 'content':
                kw['sub'] = text
              elif tag == 'name':
                kw['subName'] = text
            elif path == 2: # grimoire/texts
              s = dataman.Subtitle(**kw)
              ret.append(s)

        dprint("subtitle count = %i" % len(ret))
        return ret

    except requests.ConnectionError, e:
      dwarn("connection error", e.args)
    except requests.HTTPError, e:
      dwarn("http error", e.args)
    except etree.ParseError, e:
      dwarn("xml parse error", e.args)
    except KeyError, e:
      dwarn("invalid response header", e.args)
    except (TypeError, ValueError, AttributeError), e:
      dwarn("xml malformat", e.args)
    except Exception, e:
      derror(e)

    dwarn("failed URL follows")
    try: dwarn(r.url, params)
    except: pass

  ## Comment ##

  # def queryComments(self, gameId=None, md5=None, init=True, hash=True):
  #   """
  #   @param  init  bool whether init comment object
  #   @param  hash  bool
  #   @return  {long:Comment} or [Comment] or None
  #   """
  #   assert gameId or md5, "missing id and digest"
  #   params = {'ver':self.version}
  #   if gameId:
  #     params['gameid'] = gameId
  #   else:
  #     params['md5'] = md5
  #
  #   self._addBlockedLanguages(params)
  #   dwarn("Params", params)
  #   try:
  #     r = session.get(XML_API + 'go=allcomments', params=params, headers=GZIP_HEADERS)
  #     if r.ok and _response_is_xml(r):
  #       #root = etree.fromstring(r.content)
  #
  #       mainThread = QCoreApplication.instance().thread()
  #
  #       ret = {} if hash else []
  #
  #       context = etree.iterparse(StringIO(r.content), events=('start', 'end'))
  #       path = 0
  #       TYPES = dataman.Comment.TYPES
  #       for event, elem in context:
  #         if event == 'start':
  #           path += 1
  #           if path == 3: # grimoire/comments/comment
  #             kw = {
  #               'id': int(elem.get('id')),
  #               'type': elem.get('type'),
  #             }
  #         else:
  #           path -= 1
  #           if path == 3: # grimoire/comments/comment
  #             tag = elem.tag
  #             text = elem.text
  #             if tag in ('gameId', 'itemId', 'userId', 'userHash', 'timestamp', 'updateUserId', 'updateTimestamp', 'likeCount', 'dislikeCount'):
  #               kw[tag] = int(text)
  #             elif tag in ('disabled', 'locked'):
  #               kw[tag] = text == 'true'
  #             else:
  #               kw[tag] = text or ''
  #
  #             if tag == 'context':
  #               kw['hash'] = long(elem.get('hash'))
  #               kw['contextSize'] = int(elem.get('size'))
  #
  #           elif path == 2 and kw['type'] in TYPES: # grimoire/comments
  #             c = dataman.Comment(init=init, **kw)
  #             if init:
  #               c.moveToThread(mainThread)
  #
  #             if not hash:
  #               ret.append(c)
  #             else:
  #               h = kw['hash']
  #               if h in ret:
  #                 ret[h].append(c)
  #               else:
  #                 ret[h] = [c]
  #
  #       dprint("comment count = %i" % len(ret))
  #       return ret
  #
  #       #comments = root.find('./comments')
  #       #if comments is not None:
  #       #  for comment in comments.iterfind('./comment'):
  #       #    c_type = comment.get('type')
  #       #    if not c_type in dataman.Comment.TYPES:
  #       #      continue
  #       #    c_id = long(comment.get('id'))
  #       #    c_gameId = long(comment.find('./gameId').text)
  #       #    c_userName = comment.find('./userName').text
  #       #    c_language = comment.find('./language').text
  #       #    c_timestamp = long(comment.find('./timestamp').text)
  #
  #       #    e = comment.find('./updateTimestamp')
  #       #    c_updateTimestamp = long(e.text) if e is not None else 0
  #
  #       #    e = comment.find('./updateUserName')
  #       #    c_updateUserName = e.text if e is not None else ''
  #
  #       #    e = comment.find('./disabled')
  #       #    c_disabled = e is not None and e.text == 'true'
  #
  #       #    e = comment.find('./locked')
  #       #    c_locked = e is not None and e.text == 'true'
  #
  #       #    #e = comment.find('./popup')
  #       #    #c_popup = e is not None and e.text == 'true'
  #
  #       #    c_text = comment.find('./text').text
  #       #    #if '\\' in c_text:
  #       #    #  c_text = _NetworkManager.filterCommentText(c_text)
  #
  #       #    ctx = comment.find('./context')
  #       #    c_context = ctx.text
  #       #    c_hash = long(ctx.get('hash'))
  #       #    c_contextSize = int(ctx.get('size'))
  #
  #       #    e = comment.find('./comment')
  #       #    c_comment = e.text if e is not None else ""
  #       #    e = comment.find('./updateComment')
  #       #    c_updateComment = e.text if e is not None else ""
  #
  #       #    if c_hash:
  #       #      #if c_context:
  #       #      #  contexts[c_hash] = c_context
  #       #      if c_text:
  #       #        c = dataman.Comment(init=init,
  #       #          id=c_id, type=c_type, gameId=c_gameId, userName=c_userName,
  #       #          language=c_language, timestamp=c_timestamp, disabled=c_disabled, locked=c_locked,
  #       #          updateTimestamp=c_updateTimestamp, updateUserName=c_updateUserName,
  #       #          text=c_text, context=c_context, hash=c_hash, contextSize=c_contextSize,
  #       #          comment=c_comment, updateComment=c_updateComment)
  #
  #       #        if not hash:
  #       #          ret.append(c)
  #       #        else:
  #       #          if c_hash in ret:
  #       #            ret[c_hash].append(c)
  #       #          else:
  #       #            ret[c_hash] = [c]
  #
  #   #except socket.error, e:
  #   #  dwarn("socket error", e.args)
  #   except requests.ConnectionError, e:
  #     dwarn("connection error", e.args)
  #   except requests.HTTPError, e:
  #     dwarn("http error", e.args)
  #   except etree.ParseError, e:
  #     dwarn("xml parse error", e.args)
  #   except KeyError, e:
  #     dwarn("invalid response header", e.args)
  #   except (TypeError, ValueError, AttributeError), e:
  #     dwarn("xml malformat", e.args)
  #   except Exception, e:
  #     derror(e)
  #
  #   dwarn("failed URL follows")
  #   try: dwarn(r.url, params)
  #   except: pass

  def queryComments(self, gameId=None, md5=None, init=True, hash=True):
    """
    API Version: 3
    Return: Dict<Id,dataman.Comment> or [dataman.Comment]
    """
    params = {
      'gameId': gameId,
      'md5': md5
    }
    self._addBlockedLanguages(params)
    try:
      r = session.post(V3_API + 'comment/query', json=params)
      if not r.ok:
        r.raise_for_status()
      comments = r.json()
      ret = {} if hash else []
      mainThread = QCoreApplication.instance().thread()
      for c in comments:
        kw = {}
        kw['id'] = c.get('id', 0) # int
        kw['gameId'] = c.get('gameId', 0) # int
        kw['userId'] = c.get('creatorId', 0) # int
        kw['type'] = c.get('type', '') # str
        kw['language'] = c.get('language', '') # str
        kw['timestamp'] = c.get('creationTime', 0) # int
        kw['text'] = c.get('text', '') # str
        if 'context' in c:
          ctx = c.get('context')
          kw['hash'] = long(ctx.get('hash', 0)) # int
          kw['contextSize'] = ctx.get('size', 0) # int
          kw['context'] = ctx.get('content', '') # str
        kw['comment'] = c.get('creationComment', '') # str
        kw['updateComment'] = c.get('revisionComment', '') # str
        kw['disabled'] = c.get('disabled', False) # bool
        kw['locked'] = c.get('locked', False) # bool
        kw['updateUserId'] = c.get('editorId', 0) # int
        kw['updateTimestamp'] = c.get('revisionTime', 0) # int
        kw['likeCount'] = c.get('liked', 0) # int
        kw['dislikeCount'] = c.get('disliked', 0) # int
        if kw['type'] in dataman.Comment.TYPES:
          c = dataman.Comment(init=init, **kw)
          if init:
            c.moveToThread(mainThread)
          if not hash:
            ret.append(c)
          else:
            h = kw['hash']
            if h in ret:
              ret[h].append(c)
            else:
              ret[h] = [c]
      dprint("comment count = %i" % len(ret))
      return ret
    except requests.ConnectionError as e:
      derror(e.message)
    except requests.HTTPError as e:
      derror(e.message)
    except Exception as e:
      derror(e.message)

    return None

  # def submitComment(self, comment, userName, password, md5=None, async=False):
  #   """Return comment and update comment if succeeded"""
  #   #assert userName and password, "missing user name or password"
  #   #assert comment and (comment.gameId or md5), "missing game id and digest"
  #   cd = comment.d
  #
  #   params = {
  #     'ver': self.version,
  #     'login': userName,
  #     'password': password,
  #     'lang': cd.language,
  #     'type': cd.type,
  #     'ctxhash': cd.hash,
  #     'ctxsize': cd.contextSize,
  #     'text': cd.text
  #         if len(cd.text) <= defs.MAX_TEXT_LENGTH
  #         else cd.text[:defs.MAX_TEXT_LENGTH],
  #   }
  #   if cd.gameId:
  #     params['gameid'] = cd.gameId
  #   else:
  #     params['md5'] = md5 or cd.gameMd5
  #
  #   if cd.comment:
  #     params['comment'] = (cd.comment
  #         if len(cd.comment) <= defs.MAX_TEXT_LENGTH
  #         else cd.comment[:defs.MAX_TEXT_LENGTH])
  #
  #   if cd.updateComment:
  #     params['updatecomment'] = (cd.updateComment
  #         if len(cd.updateComment) <= defs.MAX_TEXT_LENGTH
  #         else cd.updateComment[:defs.MAX_TEXT_LENGTH])
  #
  #   if cd.context:
  #     params['ctx'] = (cd.context
  #         if len(cd.context) <= defs.MAX_TEXT_LENGTH
  #         else cd.context[:defs.MAX_TEXT_LENGTH])
  #   if cd.deleted:
  #     # Should never happen. I mean, deleted subs should have been skipped in dataman
  #     params['del'] = True
  #   if cd.disabled:
  #     params['disable'] = True
  #   if cd.locked:
  #     params['lock'] = True
  #   #if cd.popup:
  #   #  params['popup'] = True
  #
  #   try:
  #     if not async:
  #       r = session.post(XML_API + 'go=submit_comment', data=params, headers=XML_POST_HEADERS)
  #     else:
  #       r = skthreads.runsync(partial(
  #           session.post,
  #           XML_API + 'go=submit_comment', data=params, headers=XML_POST_HEADERS))
  #
  #     if r.ok and _response_is_xml(r):
  #       root = etree.fromstring(r.content)
  #       el = root.find('./comments/comment')
  #
  #       # Be careful about async here
  #       # Might crash after QObject is deleted
  #       cid = int(el.get('id'))
  #       try: comment.id = cid
  #       except Exception, e:
  #         dwarn(e)
  #         cd.id = cid
  #
  #       dprint("comment id = %i" % cd.id)
  #       return cd.id
  #
  #   #except socket.error, e:
  #   #  dwarn("socket error", e.args)
  #   except requests.ConnectionError, e:
  #     dwarn("connection error", e.args)
  #   except requests.HTTPError, e:
  #     dwarn("http error", e.args)
  #   except etree.ParseError, e:
  #     dwarn("xml parse error", e.args)
  #   except KeyError, e:
  #     dwarn("invalid response header", e.args)
  #   except (TypeError, ValueError, AttributeError), e:
  #     dwarn("xml malformat", e.args)
  #   except Exception, e:
  #     derror(e)
  #
  #   dwarn("failed URL follows")
  #   try: dwarn(r.url, params)
  #   except: pass
  #   return 0

  def limitStrLen(self, istr, maxlen):
    if len(istr) <= maxlen:
      return istr
    return istr[:maxlen]

  def submitComment(self, comment, userName, password, md5=None, async=False):
    """
    API Version: 3
    Return: Id
    """
    cd = comment.d
    params = {
      'username': userName,
      'password': password,
      'gameId': cd.gameId,
      'gameMd5': md5 or cd.gameMd5,
      'type': cd.type,
      'language': cd.language,
      'context': {
        'hash': str(cd.hash),
        'size': cd.contextSize,
        'content': self.limitStrLen(cd.context, 1024)
      },
      'text': self.limitStrLen(cd.text, 1024),
      'creationComment': self.limitStrLen(cd.comment, 300),
      'revisionComment': self.limitStrLen(cd.updateComment, 300),
      'disabled': cd.disabled,
      'locked': cd.locked,
      'deleted': cd.deleted
    }
    try:
      url = V3_API + 'comment/submit'
      if not async:
        r = session.post(url=url, json=params)
      else:
        r = skthreads.runsync(partial(session.post, url=url, json=params))
      if not r.ok:
        r.raise_for_status()
      data = r.json()
      # Be careful about async here
      # Might crash after QObject is deleted
      cid = data.get('id', 0)
      try:
        comment.id = cid
      except Exception as e:
        cd.id = cid
        dwarn(e.message)
      dprint("comment id = %i" % cid)
      return cid
    except requests.ConnectionError as e:
      derror(e.message)
    except requests.HTTPError as e:
      derror(e.message)
    except Exception as e:
      derror(e.message)

    return 0

  # def updateComment(self, comment, userName, password, async=False):
  #   """Return if succeeded"""
  #   #assert userName and password, "missing user name or password"
  #   #assert comment and comment.id, "missing comment id"
  #   cd = comment.d
  #
  #   params = {}
  #   pty = comment.dirtyProperties()
  #   if not pty:
  #     dwarn("warning: comment to update is not dirty")
  #     return True
  #
  #   if 'deleted' in pty:        params['del'] = cd.deleted
  #   #if not cd.deleted:
  #   for k,v in (
  #       ('type', 'type'),
  #       ('language', 'lang'),
  #       ('hash', 'ctxhash'),
  #       ('contextSize', 'ctxsize'),
  #       ('disabled', 'disable'),
  #       ('locked', 'lock'),
  #     ):
  #     if k in pty:
  #       params[v] = getattr(cd, k)
  #
  #   if 'text' in pty:
  #     params['text'] = (cd.text
  #         if len(cd.text) <= defs.MAX_TEXT_LENGTH
  #         else cd.text[:defs.MAX_TEXT_LENGTH])
  #   if 'context' in pty and cd.context:
  #     params['ctx'] = (cd.context
  #         if len(cd.context) <= defs.MAX_TEXT_LENGTH
  #         else cd.context[:defs.MAX_TEXT_LENGTH])
  #
  #   for k in 'comment', 'updateComment':
  #     if k in pty:
  #       v = getattr(comment, k)
  #       if v:
  #         params[k.lower()] = (v
  #             if len(v) <= defs.MAX_TEXT_LENGTH
  #             else v[:defs.MAX_TEXT_LENGTH])
  #       else:
  #         params['del' + k.lower()] = True
  #
  #   if not params:
  #     dwarn("warning: nothing change")
  #     return True
  #
  #   params['login'] = userName
  #   params['password'] = password
  #   params['id'] = cd.id
  #   params['ver'] = self.version
  #
  #   try:
  #     if not async:
  #       r = session.post(XML_API + 'go=update_comments', data=params, headers=XML_POST_HEADERS)
  #     else:
  #       r = skthreads.runsync(partial(
  #           session.post,
  #           XML_API + 'go=update_comments', data=params, headers=XML_POST_HEADERS))
  #
  #     if r.ok and _response_is_xml(r):
  #       root = etree.fromstring(r.content)
  #       el = root.find('./comments/comment')
  #       commentId = int(el.get('id'))
  #       ok = commentId != 0
  #       #if ok:
  #       #  comment.clearDirtyProperties()
  #       dprint("comment id = %i" % commentId)
  #       return ok
  #
  #   #except socket.error, e:
  #   #  dwarn("socket error", e.args)
  #   except requests.ConnectionError, e:
  #     dwarn("connection error", e.args)
  #   except requests.HTTPError, e:
  #     dwarn("http error", e.args)
  #   except etree.ParseError, e:
  #     dwarn("xml parse error", e.args)
  #   except KeyError, e:
  #     dwarn("invalid response header", e.args)
  #   except (TypeError, ValueError, AttributeError), e:
  #     dwarn("xml malformat", e.args)
  #   except Exception, e:
  #     derror(e)
  #
  #   dwarn("failed URL follows")
  #   try: dwarn(r.url, params)
  #   except: pass
  #   return False

  def updateComment(self, comment, userName, password, async=False):
    """
    API Version: 3
    Return: bool
    """
    cd = comment.d
    params = {
      'username': userName,
      'password': password,
      'id': cd.id
    }
    pty = comment.dirtyProperties()
    if not pty:
      dwarn("warning: comment to update is not dirty")
      return True
    if 'deleted' in pty:
      params['deleted'] = cd.deleted
    if 'type' in pty:
      params['type'] = cd.type
    if 'language' in pty:
      params['language'] = cd.language
    params['context'] = {
      'hash': str(cd.hash) if 'hash' in pty else None,
      'size': cd.contextSize if 'contextSize' in pty else None,
      'content': self.limitStrLen(cd.context, 1024) if 'context' in pty else None
    }
    if 'text' in pty:
      params['text'] = self.limitStrLen(cd.text, 1024)
    if 'comment' in pty:
      params['creationComment'] = self.limitStrLen(cd.comment, 300)
    if 'updateComment' in pty:
      params['revisionComment'] = self.limitStrLen(cd.updateComment, 300)
    if 'disabled' in pty:
      params['disabled'] = cd.disabled
    if 'locked' in pty:
      params['locked'] = cd.locked
    if not params:
      dwarn("warning: nothing change")
      return True
    try:
      url = V3_API + 'comment/update'
      if not async:
        r = session.post(url=url, json=params)
      else:
        r = skthreads.runsync(partial(session.post, url=url, json=params))
      if not r.ok:
        derror(r.content)
        r.raise_for_status()
      data = r.json()
      cid = data.get('id', 0)
      dprint("comment id = %i" % cid)
      return True
    except requests.ConnectionError as e:
      derror(e.message)
    except requests.HTTPError as e:
      derror(e.message)
    except Exception as e:
      derror(e.message)

    return False

  ## Terminology ##

  def mergeTerms(self, userId, terms, init, **kwargs):
    """Return [] if no changes, None if error, or list of terms if succeed
    @param  userId  long
    @param  terms  [dataman.Term]
    @param* init  bool
    @param* kwargs  passed to getTerms
    @return  [dataman.Term] or [] or None
    """
    result = self.getTerms(sort=False, init=init, **kwargs)
    if not result:
      return
    l, timestamp = result
    if l == []: # not modified
      return result
    if l:
      dprint("number of modified terms: %s" % len(l))
      if init:
        mainThread = QCoreApplication.instance().thread()
        for it in terms:
          if not it.isInitialized():
            it.init()
            it.moveToThread(mainThread)

      index = {} # {long id:dataman.Term}
      for it in l:
        index[it.d.id] = it

      TYPES = dataman.Term.TYPES
      def _good_term_data(td): # dataman._Term -> bool
        return not td.deleted and td.type in TYPES and (userId == td.userId or not td.private)

      ret = []
      for it in terms:
        t = index.get(it.d.id)
        if not t:
          ret.append(it)
        else:
          del index[it.d.id]
          if _good_term_data(t.d):
            ret.append(t)
      if index:
        for t in index.itervalues():
          if _good_term_data(t.d):
            ret.append(t)
      ret.sort(key=operator.attrgetter('modifiedTimestamp'))
      return ret, timestamp

  # def getTerms(self, userName, password, sort=True, init=True, difftime=0):
  #   """
  #   @param  userName  str
  #   @param  password  str
  #   @param* init  bool  whether init term object
  #   @param* sort  bool  whether sort the result list
  #   @param* difftime  long  timestamp
  #   @return  None or (terms, timestamp)
  #   """
  #   params = {
  #     'ver': self.version,
  #     'login': userName,
  #     'password': password,
  #   }
  #   self._addBlockedLanguages(params)
  #   try:
  #     #if difftime:
  #       #params['mintime'] = difftime
  #       #url = XML_API + '/term/diff'
  #       #url = XML_API + '/term/list'
  #     #else:
  #     url = CACHE_API + 'go=terms'
  #     r = session.get(url, params=params, headers=GZIP_HEADERS)
  #     if r.ok and _response_is_xml(r):
  #       context = etree.iterparse(StringIO(r.content), events=('start', 'end'))
  #       dwarn(r.url, params)
  #       ret = []
  #       path = 0
  #       timestamp = 0
  #       TYPES = dataman.Term.TYPES
  #       for event, elem in context:
  #         if event == 'start':
  #           path += 1
  #           if path == 1: # grimoire
  #             timestamp = elem.get('timestamp')
  #           elif path == 3: # grimoire/terms/term
  #             kw = {
  #               'id': int(elem.get('id')),
  #               'type': elem.get('type'),
  #               'host': elem.get('host') or '',
  #               'context': elem.get('context') or '',
  #               'deleted': elem.get('deleted') == 'true',
  #             }
  #         else:
  #           path -= 1
  #           if path == 3: # grimoire/terms/term
  #             tag = elem.tag
  #             text = elem.text
  #             if tag in ('gameId', 'userId', 'userHash', 'timestamp', 'updateUserId', 'updateTimestamp'):
  #               kw[tag] = int(text)
  #             elif tag in ('special', 'private', 'hentai', 'regex', 'phrase', 'icase', 'disabled'):
  #               kw[tag] = text == 'true'
  #             else:
  #               kw[tag] = text or ''
  #
  #           elif path == 2 and (difftime or kw['type'] in TYPES):
  #             #if not kw.get('userHash'):
  #             #  kw['userHash'] = kw['userId']
  #             ret.append(dataman.Term(init=init, **kw))
  #       if ret:
  #         if sort:
  #           ret.sort(key=operator.attrgetter('modifiedTimestamp'))
  #         if init:
  #           mainThread = QCoreApplication.instance().thread()
  #           #with SkProfiler(): # 12/8/2014: 0.213 seconds
  #           for it in ret:
  #             it.moveToThread(mainThread)
  #       dprint("term count = %i" % len(ret))
  #       return ret, timestamp
  #
  #   #except socket.error, e:
  #   #  dwarn("socket error", e.args)
  #   except requests.ConnectionError, e:
  #     dwarn("connection error", e.args)
  #   except requests.HTTPError, e:
  #     dwarn("http error", e.args)
  #   except etree.ParseError, e:
  #     dwarn("xml parse error", e.args)
  #   except KeyError, e:
  #     dwarn("invalid response header", e.args)
  #   except (TypeError, ValueError, AttributeError), e:
  #     dwarn("xml malformat", e.args)
  #   except Exception, e:
  #     derror(e)
  #
  #   dwarn("failed URL follows")
  #   try: dwarn(r.url)
  #   except: pass

  def getTerms(self, userName, password, sort=True, init=True, difftime=0):
    """
    API Version: 3
    Return:
    """
    params = {
      'username': userName,
      'password': password
    }
    self._addBlockedLanguages(params)
    try:
      r = session.post(V3_API + 'term/query', json=params)
      if not r.ok:
        r.raise_for_status()
      data = r.json()
      ret = []
      for term in data.get('terms', []):
        kw = {}
        kw['id'] = term.get('id', 0) # int
        kw['gameId'] = term.get('gameId', 0) # int
        # kw['gameMd5'] = term.get('gameMd5', '') # str
        kw['userId'] = term.get('creatorId', 0)  # int
        # kw['userHash'] = term.get('userHash', 0)  # int
        kw['type'] = term.get('type', '')  # str
        kw['host'] = term.get('translators', '')  # str
        kw['context'] = term.get('contextType', '')  # str
        kw['language'] = term.get('toLanguage', '')  # str
        kw['sourceLanguage'] = term.get('fromLanguage', '')  # str
        kw['timestamp'] = term.get('creationTime', 0)  # int
        kw['text'] = term.get('text', '')  # str
        kw['pattern'] = term.get('pattern', '')  # str
        kw['ruby'] = term.get('ruby', '')  # str
        kw['priority'] = term.get('priority', 0.0)  # float
        kw['role'] = term.get('role', '')  # str
        kw['comment'] = term.get('creationComment', '')  # str
        kw['updateComment'] = term.get('revisionComment', '')  # str
        kw['updateUserId'] = term.get('editorId', 0)  # int
        kw['updateTimestamp'] = term.get('revisionTime', 0)  # int
        kw['regex'] = term.get('isRegex', False)  # bool
        kw['phrase'] = term.get('isPhrase', False)  # bool
        kw['disabled'] = term.get('disabled', False)  # bool
        kw['deleted'] = term.get('deleted', False)  # bool
        kw['special'] = term.get('isSpecial', False)  # bool
        kw['private'] = term.get('isPrivate', False)  # bool
        kw['hentai'] = term.get('isHentai', False)  # bool
        kw['icase'] = term.get('ignoreCase', False)  # bool
        if (kw['type'] in dataman.Term.TYPES) or difftime:
          ret.append(dataman.Term(init=init, **kw))
      timestamp = data.get('timestamp', 0)
      if ret:
        if sort:
          ret.sort(key=operator.attrgetter('updateTimestamp'))
        if init:
          mainThread = QCoreApplication.instance().thread()
          for it in ret:
            it.moveToThread(mainThread)
      dprint("term count = %i" % len(ret))
      return ret, timestamp
    except requests.ConnectionError as e:
      derror(e.message)
    except requests.HTTPError as e:
      derror(e.message)
    except Exception as e:
      derror(e.message)

    return None, 0

  # def submitTerm(self, term, userName, password, async=False):
  #   """Return term and update term if succeeded"""
  #   #assert userName and password, "missing user name or password"
  #   #assert term, "term"
  #   td = term.d
  #
  #   params = {
  #     'ver': self.version,
  #     'login': userName,
  #     'password': password,
  #     'lang': td.language,
  #     'sourcelang': td.sourceLanguage,
  #     'type': td.type,
  #   }
  #   for k in 'host', 'context':
  #     v = getattr(td, k)
  #     if v:
  #       params[k.lower()] = v
  #
  #   if td.gameId:
  #     params['gameid'] = td.gameId
  #   elif td.gameMd5:
  #     params['md5'] = td.gameMd5
  #
  #   if td.priority:
  #     params['priority'] = td.priority
  #
  #   if td.role:
  #     params['role'] = (td.role
  #         if len(td.role) <= defs.MAX_TEXT_LENGTH
  #         else td.role[:defs.MAX_TEXT_LENGTH])
  #
  #   if td.pattern:
  #     params['pattern'] = (td.pattern
  #         if len(td.pattern) <= defs.MAX_TEXT_LENGTH
  #         else td.pattern[:defs.MAX_TEXT_LENGTH])
  #
  #   if td.text:
  #     params['text'] = (td.text
  #         if len(td.text) <= defs.MAX_TEXT_LENGTH
  #         else td.text[:defs.MAX_TEXT_LENGTH])
  #
  #   if td.ruby:
  #     params['ruby'] = (td.ruby
  #         if len(td.ruby) <= defs.MAX_TEXT_LENGTH
  #         else td.ruby[:defs.MAX_TEXT_LENGTH])
  #
  #   if td.comment:
  #     params['comment'] = (td.comment
  #         if len(td.comment) <= defs.MAX_TEXT_LENGTH
  #         else td.comment[:defs.MAX_TEXT_LENGTH])
  #
  #   if td.updateComment:
  #     params['updatecomment'] = (td.updateComment
  #         if len(td.updateComment) <= defs.MAX_TEXT_LENGTH
  #         else td.updateComment[:defs.MAX_TEXT_LENGTH])
  #
  #   for pty in 'special', 'private', 'hentai', 'regex', 'phrase', 'icase':
  #     if getattr(td, pty):
  #       params[pty] = True
  #
  #   if td.deleted:
  #     # Should never happen. I mean, deleted subs should have been skipped in dataman
  #     params['del'] = True
  #   if td.disabled:
  #     params['disable'] = True
  #
  #   try:
  #     if not async:
  #       r = session.post(XML_API + 'go=add_terms', data=params, headers=XML_POST_HEADERS)
  #     else:
  #       r = skthreads.runsync(partial(
  #           session.post,
  #           XML_API + 'go=add_terms', data=params, headers=XML_POST_HEADERS))
  #
  #     if r.ok and _response_is_xml(r):
  #       root = etree.fromstring(r.content)
  #       el = root.find('./terms/term')
  #
  #       # Be careful about async here
  #       # Might raise after ref QObject is deleted
  #       tid = int(el.get('id'))
  #       try: term.id = tid
  #       except Exception, e:
  #         dwarn(e)
  #         td.id = tid
  #
  #       dprint("term id = %i" % td.id)
  #       return td.id
  #
  #   #except socket.error, e:
  #   #  dwarn("socket error", e.args)
  #   except requests.ConnectionError, e:
  #     dwarn("connection error", e.args)
  #   except requests.HTTPError, e:
  #     dwarn("http error", e.args)
  #   except etree.ParseError, e:
  #     dwarn("xml parse error", e.args)
  #   except KeyError, e:
  #     dwarn("invalid response header", e.args)
  #   except (TypeError, ValueError, AttributeError), e:
  #     dwarn("xml malformat", e.args)
  #   except Exception, e:
  #     derror(e)
  #
  #   dwarn("failed URL follows")
  #   try: dwarn(r.url, params)
  #   except: pass
  #   return 0

  def submitTerm(self, term, userName, password, async=False):
    """
    API Version: 3
    Return Id
    """
    td = term.d
    MAX_LEN = defs.MAX_TEXT_LENGTH
    params = {
      'username': userName,
      'password': password,
      'type': td.type,
      'toLanguage': td.language,
      'fromLanguage': td.sourceLanguage,
      'gameId': td.gameId,
      'gameMd5': td.gameMd5,
      'translators': td.host,
      'contextType': td.context,
      'priority': int(td.priority),
      'role': self.limitStrLen(td.role, 500),
      'pattern': self.limitStrLen(td.pattern, 500),
      'text': self.limitStrLen(td.text, 500),
      'ruby': self.limitStrLen(td.ruby, 500),
      'creationComment': self.limitStrLen(td.comment, 300),
      'revisionComment': self.limitStrLen(td.updateComment, 300),
      'isSpecial': td.special,
      'isPrivate': td.private,
      'isHentai': td.hentai,
      'isRegex': td.regex,
      'isPhrase': td.phrase,
      'ignoreCase': td.icase,
      'disabled': td.disabled,
      'deleted': td.deleted
    }
    try:
      url = V3_API + 'term/submit'
      if not async:
        r = session.post(url=url, json=params)
      else:
        r = skthreads.runsync(partial(session.post, url=url, json=params))
      if not r.ok:
        r.raise_for_status()
      data = r.json()
      # Be careful about async here
      # Might raise after ref QObject is deleted
      tid = data.get('id', 0)
      try:
        term.id = tid
      except Exception as e:
        td.id = tid
        dwarn(e.message)
      dprint("term id = %i" % tid)
      return tid
    except requests.ConnectionError as e:
      derror(e.message)
    except requests.HTTPError as e:
      derror(e.message)
    except Exception as e:
      derror(e.message)

    return 0

  # def updateTerm(self, term, userName, password, async=False):
  #   """Return if succeeded"""
  #   #assert userName and password, "missing user name or password"
  #   #assert term and term.id, "missing term id"
  #   td = term.d
  #
  #   params = {}
  #   pty = term.dirtyProperties()
  #   if not pty:
  #     dwarn("warning: term to update is not dirty")
  #     return True
  #
  #   if 'deleted' in pty:            params['del'] = td.deleted
  #   #if not td.deleted:
  #   if 'language' in pty:         params['lang'] = td.language
  #   if 'sourceLanguage' in pty:   params['sourcelang'] = td.sourceLanguage
  #   if 'disabled' in pty:         params['disable'] = td.disabled
  #
  #   for k in 'gameId', 'type', 'host', 'context', 'special', 'private', 'hentai', 'icase', 'regex', 'phrase':
  #     if k in pty:
  #       params[k.lower()] = getattr(term, k)
  #
  #   k = 'priority'
  #   if k in pty:
  #     v = getattr(td, k)
  #     if v:
  #       params[k] = v
  #     else:
  #       params['del' + k.lower()] = True
  #
  #   # Note: actually, there is no 'delpattern'
  #   for k in 'pattern', 'text', 'ruby', 'role', 'comment', 'updateComment':
  #     if k in pty:
  #       v = getattr(td, k)
  #       if v:
  #         params[k.lower()] = (v
  #             if len(v) <= defs.MAX_TEXT_LENGTH
  #             else v[:defs.MAX_TEXT_LENGTH])
  #       else:
  #         params['del' + k.lower()] = True
  #
  #   if not params:
  #     dwarn("warning: nothing change")
  #     return True
  #
  #   params['login'] = userName
  #   params['password'] = password
  #   params['id'] = td.id
  #   params['ver'] = self.version
  #
  #   try:
  #     if not async:
  #       r = session.post(XML_API + 'go=update_terms', data=params, headers=XML_POST_HEADERS)
  #     else:
  #       r = skthreads.runsync(partial(
  #           session.post,
  #           XML_API + 'go=update_terms', data=params, headers=XML_POST_HEADERS))
  #     dwarn(r.url, params)
  #     if r.ok and _response_is_xml(r):
  #       root = etree.fromstring(r.content)
  #       el = root.find('./terms/term')
  #       termId = int(el.get('id'))
  #       ok = termId != 0
  #       #if ok:
  #       #  term.clearDirtyProperties()
  #       dprint("term id = %i" % termId)
  #       return ok
  #
  #   #except socket.error, e:
  #   #  dwarn("socket error", e.args)
  #   except requests.ConnectionError, e:
  #     dwarn("connection error", e.args)
  #   except requests.HTTPError, e:
  #     dwarn("http error", e.args)
  #   except etree.ParseError, e:
  #     dwarn("xml parse error", e.args)
  #   except KeyError, e:
  #     dwarn("invalid response header", e.args)
  #   except (TypeError, ValueError, AttributeError), e:
  #     dwarn("xml malformat", e.args)
  #   except Exception, e:
  #     derror(e)
  #
  #   dwarn("failed URL follows")
  #   try: dwarn(r.url, params)
  #   except: pass
  #   return False

  def updateTerm(self, term, userName, password, async=False):
    """
    API Version: 3
    Return: bool
    """
    td = term.d
    pty = term.dirtyProperties()
    if not pty:
      dwarn("warning: term to update is not dirty")
      return True
    params = {
      'username': userName,
      'password': password,
      'id': td.id,
      'deleted': td.deleted if 'deleted' in pty else None,
      'toLanguage': td.language if 'language' in pty else None,
      'fromLanguage': td.sourceLanguage if 'sourceLanguage' in pty else None,
      'disabled': td.disabled if 'disabled' in pty else None,
      'gameId': td.gameId if 'gameId' in pty else None,
      'type': td.type if 'type' in pty else None,
      'translators': td.host if 'host' in pty else None,
      'contextType': td.context if 'context' in pty else None,
      'isSpecial': td.special if 'special' in pty else None,
      'isPrivate': td.private if 'private' in pty else None,
      'isHentai': td.hentai if 'hentai' in pty else None,
      'ignoreCase': td.icase if 'icase' in pty else None,
      'isRegex': td.regex if 'regex' in pty else None,
      'isPhrase': td.phrase if 'phrase' in pty else None,
      'priority': int(td.priority) if 'priority' in pty else None,
      'pattern': td.pattern if 'pattern' in pty else None,
      'text': td.text if 'text' in pty else None,
      'ruby': td.ruby if 'ruby' in pty else None,
      'role': td.role if 'role' in pty else None,
      'creationComment': td.comment if 'comment' in pty else None,
      'revisionComment': td.updateComment if 'updateComment' in pty else None
    }
    try:
      url = V3_API + 'term/update'
      if not async:
        r = session.post(url=url, json=params)
      else:
        r = skthreads.runsync(partial(session.post, url=url, json=params))
      if not r.ok:
        r.raise_for_status()
      data = r.json()
      tid = data.get('id', 0)
      dprint("term id = %i" % tid)
      return True
    except requests.ConnectionError as e:
      derror(e.message)
    except requests.HTTPError as e:
      derror(e.message)
    except Exception as e:
      derror(e.message)

    return False

  def jisho_api(self, text):
    params = {'keyword': text}

    r = session.get('http://jisho.org/api/v1/search/words', params=params, headers=GZIP_HEADERS)
    if r.ok:
      items = json.loads(r.content)
      return items['data']

  def byars_api(self, text):
    params = {'w': text, 'm':0}

    r = session.get('http://e-lib.ua/dic/results', params=params, headers=GZIP_HEADERS)
    if r.ok:
      content = r.content
      return content


  #@staticmethod
  #def _parseTranslationScripts(h, begin, end):
  #  """
  #  @param  h  str  html
  #  @param  begin  str
  #  @param  end  str
  #  @return  unicode
  #  """
  #  ENCODING = 'utf8'
  #  start = h.find(begin)
  #  if start > 0:
  #    start += len(begin)
  #    stop = h.find(end, start)
  #    if stop > 0:
  #      h = h[start:stop]
  #      h = h.decode(ENCODING, errors='ignore')
  #      h = skstr.unescapehtml(h)
  #      dprint("line number = %s" % len(h))
  #      return h

  #def getTranslationScripts(self):
  #  """
  #  @return  {str key:unicode contents}
  #  """
  #  markers = (
  #    ('ja', ("TAH SCRIPT JA-JA BEGIN", "TAH SCRIPT JA-JA END")),
  #    ('en', ("TAH SCRIPT JA-EN BEGIN", "TAH SCRIPT JA-EN END")),
  #  )
  #  try:
  #    r = session.get(config.TAHSCRIPT_URL, headers=GZIP_HEADERS)
  #    if r.ok:
  #      h = r.content
  #      if h:
  #        return {k:self._parseTranslationScripts(h, *args) for k,args in markers}

  #  #except socket.error, e:
  #  #  dwarn("socket error", e.args)
  #  except requests.ConnectionError, e:
  #    dwarn("connection error", e.args)
  #  except requests.HTTPError, e:
  #    dwarn("http error", e.args)
  #  except Exception, e:
  #    derror(e)

  #  dwarn("failed URL follows")
  #  try: dwarn(r.url)
  #  except: pass

class NetworkManager(QObject):
  """All methods are stateless and thread-safe"""

  def __init__(self, parent=None):
    super(NetworkManager, self).__init__(parent)
    self.__d = _NetworkManager(self)

  ## Properties ##

  onlineChanged = Signal(bool)
  def isOnline(self): return self.__d.online
  def updateOnline(self): self.__d.updateOnline()

  def jisho_api(self, text): return self.__d.jisho_api(text)

  def byars_api(self, text): return self.__d.byars_api(text)

  def blockedLanguages(self, v): return self.__d.blockedLanguages
  def setBlockedLanguages(self, v): self.__d.blockedLanguages = v

  ## Update ##

  def setVersion(self, timestamp):
    """
    @param  timestamp  long
    """
    self.__d.version = timestamp

  def queryVersion(self):
    """Return the version timestamp. Result is cached.
    @return  int or 0

    Thread-safe.
    """
    return self.__d.cachedVersion if self.isOnline() else 0

  def getUpdateMessage(self, lang):
    """
    @param  lang  str
    @return  unicode or None

    Thread-safe.
    """
    if self.isOnline() and lang:
      return skthreads.runsync(partial(
          self.__d.getUpdateMessage, lang))

  ## User ##

  def queryUser(self, userName, password):
    """
    @return  dataman.User or None

    Thread-safe.
    """
    if self.isOnline() and userName and password:
      return self.__d.queryUser(userName, password)
      #return skthreads.runsync(partial(
      #    self.__d.queryUser, userName, password))

  def updateUser(self, userName, password, language=None, gender=None, avatar=None, color=None, homepage=None):
    """
    @return  bool  if succeed

    Thread-safe.
    """
    if self.isOnline() and userName and password:
      return self.__d.updateUser(userName, password,
          language=language, gender=gender, avatar=avatar, color=color, homepage=homepage)
      #return skthreads.runsync(partial(
      #    self.__d.updateUser, userName, password,
      #    language=language, gender=gender, avatar=avatar, color=color, homepage=homepage))
    return False

  def getUsers(self):
    """
    @return {long id:dataman.UserDigest} or None
    """
    if self.isOnline():
      return skthreads.runsync(self.__d.getUsers)

  ## Games ##

  def getGameFiles(self):
    """
    @return {long id:dataman.GameFile} or None
    """
    if self.isOnline():
      return skthreads.runsync(self.__d.getGameFiles)

  def queryGame(self, id=0, md5=None, cached=True, timeout=config.APP_GAME_QUERY_TIMEOUT):
    """Either id or digest should be specified
    @param* cached  bool
    @param* timeout  int  wait for at most seconds and stop
    @return  dataman.Game or None

    Thread-safe.
    """
    d = self.__d
    if not id and not md5:
      return
    if cached or not self.isOnline():
      if id:
        try: return d.cachedGamesById[id]
        except KeyError: pass
      if md5:
        try: return d.cachedGamesByMd5[md5]
        except KeyError: pass

    if self.isOnline():
      ret = skthreads.runsync(partial(
          d.queryGame, id, md5),
          timeout=timeout)
      if ret:
        if ret.id:
          d.cachedGamesById[ret.id] = ret
        if ret.md5:
          d.cachedGamesById[ret.md5] = ret
      return ret

  def updateGame(self, game, userName, password, deleteHook=False, timeout=config.APP_GAME_UPDATE_TIMEOUT):
    """Either id or digest should be specified.
    @param[inout]  game  dataman.Game  Update gameid If succeed,.
    @param  deleteHook  bool
    @param* timeout  int  wait for at most seconds and stop
    @return  bool  if succeed

    Thread-safe.
    """
    if self.isOnline() and (game.id or game.md5) and userName and password:
      return skthreads.runsync(partial(
          self.__d.updateGame, game, userName, password, deleteHook=deleteHook),
          timeout=timeout)
    return False

  ## Items ##

  def getGameItems(self):
    """
    @return {long itemId:dataman.GameItem} or None
    """
    if self.isOnline():
      return skthreads.runsync(self.__d.getGameItems)

  ## References ##

  #def getReferenceDigests(self):
  #  """
  #  @return {long itemId:[dataman.ReferenceDigest]} or None
  #  """
  #  if self.isOnline():
  #    return skthreads.runsync(self.__d.getReferenceDigests)

  def queryReferences(self, gameId=0, md5=None, init=True):
    """Either gameid or digest should be specified
    @param  gameId  long or 0
    @param  md5  str or None
    @param* init  bool
    @return  [dataman.Reference] or None
    """
    if self.isOnline() and (gameId or md5):
      return skthreads.runsync(partial(
          self.__d.queryReferences, gameId, md5, init=init))

  def submitReference(self, ref, userName, password, md5=None, async=False):
    """Either id or digest should be specified.
    @param[inout]  ref  dataman.References  Update ref id If succeed,.
    @return  (int gameId, int itemId) or None

    Thread-safe.
    """
    if self.isOnline() and (ref.d.gameId or md5) and userName and password:
      return self.__d.submitReference(ref, userName, password, md5, async=async)

  def updateReference(self, ref, userName, password, async=False):
    """Reference id must be specified
    @param[in]  ref  dataman.Reference  Do NOT modify the ref
    @return  (int gameId, int itemId) or None

    Thread-safe.
    """
    if self.isOnline() and ref.d.id and userName and password:
      return self.__d.updateReference(ref, userName, password, async=async)

  ## Comments ##

  def queryComments(self, gameId=0, md5=None, hash=True, init=False):
    """Either gameid or digest should be specified
    @param  gameId  long or 0
    @param  md5  str or None
    @param* hash  bool
    @return  ({long:[dataman.Comment] if hash else [dataman.Comment]) or None
    """
    if self.isOnline() and (gameId or md5):
      return skthreads.runsync(partial(
          self.__d.queryComments, gameId, md5, init=init, hash=hash))
      #if ret:
      #  if hash:
      #    for l in ret.itervalues():
      #      #map(dataman.Comment.init, l) # for loop is faster
      #      for it in l: it.init()
      #  else:
      #    #map(dataman.Comment.init, ret) # for loop is faster
      #    for it in ret: it.init()
      #return ret

  def submitComment(self, comment, userName, password, md5=None, async=False):
    """Either id or digest should be specified.
    @param[inout]  comment  dataman.Comment  Update comment id If succeed,.
    @return  long or 0   comment id if succeed

    Thread-safe.
    """
    #return (skthreads.runsync(partial(
    #    self.__d.submitComment, comment, userName, password, md5))
    #    if self.isOnline() and (comment.gameId or md5) and userName and password
    #    else 0)
    if self.isOnline() and (comment.d.gameId or md5) and userName and password:
      return self.__d.submitComment(comment, userName, password, md5, async=async)
    return 0

  def updateComment(self, comment, userName, password, async=False):
    """Comment id must be specified
    @param[in]  comment  dataman.Comment  Do NOT modify the comment
    @return  bool  If succeed

    Thread-safe.
    """
    #return (skthreads.runsync(partial(
    #    self.__d.updateComment, comment, userName, password))
    #    if self.isOnline() and comment.id and userName and password
    #    else False)
    if self.isOnline() and comment.d.id and userName and password:
      return self.__d.updateComment(comment, userName, password, async=async)
    return False

  def querySubtitles(self, itemId, langs=(), gameLang='ja', time=0, async=True):
    """
    @param  itemId  long
    @param* langs  [str]
    @param* gameLang  str
    @param* time  long
    @return  [dataman.Subtitle] or None
    """
    if self.isOnline() and itemId:
      if async:
        return skthreads.runsync(partial(
          self.__d.querySubtitles, itemId, langs=langs, gameLang=gameLang, difftime=time))
      else:
        return self.__d.querySubtitles(itemId, langs=langs, gameLang=gameLang, difftime=time)

  ## Wiki ##

  #def getTranslationScripts(self):
  #  """
  #  @return  {str key:unicode contents} or None
  #  """
  #  if self.isOnline():
  #    return skthreads.runsync(self.__d.getTranslationScripts)

  ## Terms ##

  def getTerms(self, userName='', password='', init=False, parent=None):
    """
    @param* userName  str
    @param* password  str
    @param* init  bool  whether initialize QObject
    @param* parent  QObject  to init
    @return ([dataman.Term] or [] or None, long timestamp) or None
    """
    if self.isOnline():
      return skthreads.runsync(partial(
          self.__d.getTerms, userName, password, init=init))

  def mergeTerms(self, terms, time, userName='', password='', init=False, parent=None):
    """
    @param  terms  [dataman.Term]  current term
    @param  time  long  timestamp
    @param* userName  str
    @param* password  str
    @param* init  bool  whether initialize QObject
    @param* parent  QObject  to init
    @return  [dataman.Term] or [] or None
    """
    if self.isOnline():
      userId = dataman.manager().user().id # bad pattern
      return skthreads.runsync(partial(
          self.__d.mergeTerms, userId, terms,
          userName=userName, password=password, init=init, difftime=time))

  def submitTerm(self, term, userName, password, async=False):
    """Either id or digest should be specified.
    @param[inout]  term  dataman.Term  Update term id If succeed,.
    @return  long or 0   term id if succeed

    Thread-safe.
    """
    if self.isOnline() and userName and password:
      return self.__d.submitTerm(term, userName, password, async=async)
    return 0

  def updateTerm(self, term, userName, password, async=False):
    """Term id must be specified
    @param[in]  term  dataman.Term  Do NOT modify the term
    @return  bool  If succeed

    Thread-safe.
    """
    if self.isOnline() and term.d.id and userName and password:
      return self.__d.updateTerm(term, userName, password, async=async)
    return False

  ## Forum ##

  def submitPost(self, data):
    """
    @param  data  kw or str
    @return  bool
    Thread-safe.
    """
    return self.isOnline() and self.__d.ajax('post/create', data)

  def updatePost(self, data):
    """
    @param  data  kw or str
    @return  bool
    Thread-safe.
    """
    return self.isOnline() and self.__d.ajax('post/update', data)

  def submitTopic(self, data):
    """
    @param  data  kw or str
    @return  bool
    Thread-safe.
    """
    return self.isOnline() and self.__d.ajax('topic/create', data)

  def updateTopic(self, data):
    """
    @param  data  kw or str
    @return  bool
    Thread-safe.
    """
    return self.isOnline() and self.__d.ajax('topic/update', data)

  def updateTicket(self, data):
    """
    @param  data  kw or str
    @return  bool
    Thread-safe.
    """
    return self.isOnline() and self.__d.ajax('ticket/update', data)

  def submitImage(self, data, params):
    """
    @param  data  str  image data
    @param  params  kw
    @return  long or None
    Thread-safe.
    """
    if self.isOnline():
      return self.__d.upload('upload/image', data, params)

  #def submitAudio(self, data, params):
  #  """
  #  @param  data  image data
  #  @param  params  kw
  #  @return  bool
  #  Thread-safe.
  #  """
  #  if self.isOnline():
  #    self.__d.upload('upload/audio', data, params)

  # Shorthands

  def likeComment(self, commentId, value, userName, password):
    """
    @param  commentId  long
    @param  value  {True, None, False, -1, 0, 1}
    @param  userName  unicode
    @param  password  unicode
    """
    if not isinstance(value, (int, long)):
      if value is None:
        value = 0
      elif value == True:
        value = 1
      elif value == False:
        value = -1
    return self.updateTicket(json.dumps({
      'login': userName,
      'password': password,
      'targetType': 'annot',
      'targetId': commentId,
      'type': 'like',
      'value': value,
    }))


@memoized
def manager(): return NetworkManager()

# EOF
