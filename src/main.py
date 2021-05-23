import sys
import urllib
from urllib.parse import urlparse, parse_qs
import xbmcgui
import xbmcplugin
from resources.lib import redbullv3

base_url = sys.argv[0]
addon_handle = int(sys.argv[1])
args = parse_qs(sys.argv[2][1:])

baseUrl = "https://api.redbull.tv/v3/"


token = args.get('token', None)

redbull = redbullv3.RedBull(baseUrl, token)

def build_url(query):
    return base_url + '?' + urllib.parse.urlencode(query)

xbmcplugin.setContent(addon_handle, 'movies')

mode = args.get('mode', None)

if mode is None:
    url = build_url({
        'mode': 'product',
        'id': 'discover',
        'token': redbull.Token
        })  

    li = xbmcgui.ListItem()
    li.setLabel('Discover')

    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=li, isFolder=True)

    url = build_url({
        'mode': 'product',
        'id': 'channels',
        'token': redbull.Token
        })  

    li = xbmcgui.ListItem()
    li.setLabel('Channels')

    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=li, isFolder=True)

    url = build_url({
        'mode': 'product',
        'id': 'calendar',
        'token': redbull.Token
        })  

    li = xbmcgui.ListItem()
    li.setLabel('Calendar')

    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=li, isFolder=True)


elif mode[0] == 'collection':
    id = args.get('id')
    offset = args.get('offset', None)
    limit = args.get('limit', None)

    if offset is None:
        offset = 0
    else:
        offset = offset[0]

    if limit is None:
        limit = 20
    else:
        limit = limit[0]

    redbull.GetCollection(id[0], offset, limit)

elif mode[0] == 'product':
    id = args.get('id')
    redbull.GetProduct(id[0])

xbmcplugin.endOfDirectory(addon_handle)
