#!/usr/bin/python2

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: http://blog.h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import SocketServer
import logging
import os
import json
import time
BUFSIZE = 1024


# this class is used for the threaded unix stream server and 
# extends the constructor to pass the global configured data to all threads
class ThreadedUnixStreamServer(SocketServer.ThreadingMixIn,
    SocketServer.UnixStreamServer):
    
    def __init__(self, globalData, serverAddress, RequestHandlerClass):

        # get reference to global data object
        self.globalData = globalData

        SocketServer.TCPServer.__init__(self, serverAddress, 
            RequestHandlerClass)


# this class is used for incoming local client connections (i.e., web page)
class LocalServerSession(SocketServer.BaseRequestHandler):

    def __init__(self, request, clientAddress, server):

        # file nme of this file (used for logging)
        self.fileName = os.path.basename(__file__)

        # get reference to global data object
        self.globalData = server.globalData
        self.serverComm = self.globalData.serverComm

        SocketServer.BaseRequestHandler.__init__(self, request, 
            clientAddress, server)

    def handle(self):

        logging.info("[%s]: Client connected." % self.fileName)

        # get received data
        data = self.request.recv(BUFSIZE).strip()

        # convert data to json
        try:
            incomingMessage = json.loads(data)

            # at the moment only option messages are allowed
            if incomingMessage["message"] != "option":

                # send error message back
                try:
                    utcTimestamp = int(time.time())
                    message = {"serverTime": utcTimestamp,
                        "message": incomingMessage["message"],
                        "error": "only option message valid"}
                    self.request.send(json.dumps(message))
                except Exception as e:
                    pass

                return

        except Exception as e:
            logging.exception("[%s]: Received message " % self.fileName
                + "invalid.")

            # send error message back
            try:
                utcTimestamp = int(time.time())
                message = {"serverTime": utcTimestamp,
                    "message": incomingMessage["message"],
                    "error": "received json message invalid"}
                self.request.send(json.dumps(message))
            except Exception as e:
                pass

            return

        # extract option type and value from message
        try:
            optionType = str(incomingMessage["payload"]["optionType"])
            optionValue = float(incomingMessage["payload"]["value"])
            optionDelay = int(incomingMessage["payload"]["timeDelay"])
        except Exception as e:

            logging.exception("[%s]: Attributes of option " % self.fileName
                + "message invalid.")

            # send error message back
            try:
                utcTimestamp = int(time.time())
                message = {"serverTime": utcTimestamp,
                    "message": incomingMessage["message"],
                    "error": "received attributes invalid"}
                self.request.send(json.dumps(message))
            except Exception as e:
                pass

            return

        # at the moment only "alertSystemActive" is an allowed option type
        if optionType != "alertSystemActive":

            # send error message back
            try:
                utcTimestamp = int(time.time())
                message = {"serverTime": utcTimestamp,
                    "message": incomingMessage["message"],
                    "error": "only option type 'alertSystemActive' allowed"}
                self.request.send(json.dumps(message))
            except Exception as e:
                pass

            return

        # send option message to server
        if self.serverComm.sendOption(optionType, optionValue,
            optionDelay):

            # send response to client
            try:
                utcTimestamp = int(time.time())
                message = {"serverTime": utcTimestamp,
                    "message": incomingMessage["message"],
                    "payload": 
                        {"type": "response",
                        "result": "ok"}
                    }
                self.request.send(json.dumps(message))
            except Exception as e:
                logging.exception("[%s]: Sending response " % self.fileName
                    + "message failed.")

            return

        else:

            logging.error("[%s]: Sending message to server failed." 
            % self.fileName)

            # send error message back
            try:
                utcTimestamp = int(time.time())
                message = {"serverTime": utcTimestamp,
                    "message": incomingMessage["message"],
                    "error": "sending message to server failed"}
                self.request.send(json.dumps(message))
            except Exception as e:
                pass

            return

        logging.info("[%s]: Client disconnected." 
            % self.fileName)