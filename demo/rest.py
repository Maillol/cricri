import cherrypy
import json
import random
import sys
from time import sleep
import uuid


def jsonify_error(status, message, traceback, version):
    return json.dumps({'status': status, 'message': message})


@cherrypy.expose
class Hotel(object):

    hotels = {}

    @cherrypy.tools.json_out()
    def GET(self, hotel_id=None):
        if hotel_id is None:
            return list(type(self).hotels.values())

        try:
            return type(self).hotels[hotel_id]
        except KeyError:
            raise cherrypy.NotFound()

    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def POST(self):
        hotel = cherrypy.request.json
        hotel['id'] = uuid.uuid4().hex
        type(self).hotels[hotel['id']] = hotel
        cherrypy.response.status = '201' 
        return hotel

    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def PUT(self, hotel_id):
        hotel = cherrypy.request.json
        hotel['id'] = hotel_id
        type(self).hotels[hotel_id] = hotel
        return hotel

    def DELETE(self, hotel_id):
        cherrypy.response.status = 204
        type(self).hotels.pop(hotel_id, None)


if __name__ == '__main__':
    port = int(sys.argv[1])

    conf = {
        'global': {
            'server.socket_port': port
        },
        '/': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'error_page.default': jsonify_error,
            'tools.response_headers.on': True,
            'tools.response_headers.headers': [('Content-Type', 'application/json')],
        }
    }
    cherrypy.quickstart(Hotel(), '/hotels', conf)

