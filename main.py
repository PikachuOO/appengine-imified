#!/usr/bin/env python

import os
import logging
from datetime import datetime, timedelta

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.api import memcache

from models import Message
import settings

class Index(webapp.RequestHandler):
    """
    This is just the demo application and isn't needed if you
    are creating your own applications
    """
    def get(self):
        "Displays the home page, which lists the latest messages"
        # lets have some basic cachine just in case
        output = memcache.get("index")
        if output is None:
            # we're only showing messages from within the last day
            # this is for demonstration purposes only and stops 
            # the demo getting swamped with messages
            yesterday = datetime.today() - timedelta(1)
            
            # get all messages posted in the last day and order them
            # by the date posted
            messages = Message.all()
            messages.order('-date')
            messages.filter('date >', yesterday)
            # prepare the context for the template
            context = {
                'messages': messages,
                'debug': settings.DEBUG,
            }
            # calculate the template path
            path = os.path.join(os.path.dirname(__file__), 'templates',
                'index.html')
            # render the template with the provided context
            output = template.render(path, context)
            memcache.add("index", output, settings.CACHE_TIME)
        self.response.out.write(output)
                
class IMified(webapp.RequestHandler):
    "This is the endpoint for the message from IMified"
    def post(self):
        "We recieve post data from IMified"
        userkey = self.request.get('userkey')
        network = self.request.get('network')
        msg = self.request.get('msg')
        step = self.request.get('step')
        try:
            # we try and create the message
            message = Message(
                userkey = userkey,
                network = network,
                msg = msg,
                step = int(step)
            )   
            message.put()
            # we just added a message so we need to clear our cache
            memcache.delete("index")
            # simple logging
            logging.info("Saved new message")
            # the response is send as an IM message to the sender
            self.response.out.write('Message saved')
        except:
            # we'll log the error if it occurs
            # and report we couldn't save the message to the sender
            logging.error("Error occured creating new message")
            self.response.out.write('An error ocured, message not saved')
                        
# wire up the views
application = webapp.WSGIApplication([
    ('/', Index),
    ('/endpoint', IMified),
], debug=True)

def main():
    "Run the application"
    run_wsgi_app(application)

if __name__ == '__main__':
    main()