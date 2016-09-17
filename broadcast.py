#-*-encoding:utf-8-*-
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.httpserver
from datetime import datetime
from random import random
import os
from datetime import timedelta

from tornado.concurrent import Future
from tornado import gen
from tornado.options import define, options, parse_command_line


define("port", default=8888, help="run on the given port", type=int)
define("debug", default=False, help="run in debug mode")


class ListnerBox:
    '''
      хранилище слушателей
      позволяет сохранить список слушателей, удалять, добавлять 
      и очищать при необходимости его
    '''
    def __init__(self, *args, **kwargs):
        super(ListnerBox, self).__init__(*args, **kwargs)
        self.listners = set()

    def get_listners(self):
        return self.listners

    def add_listner(self, listner):
        self.listners.add(listner)

    def delete_listner(self, listner):
        self.listners.remove(listner)

    def clear_listners(self):
        self.listners.clear()

    def create_listner(self, future):
        return future


class BroadcastCycle:
    '''
       сервер хранит список подключенных клиентов и в один момент рассылает 
       сообщение со случайным набором символов и временем
    '''  
    def __init__(self, *args, **kwargs):
        super(BroadcastCycle, self).__init__(*args, **kwargs)
        self.timeout = timedelta(seconds = 20)
        self.message = ""
        self.current_wait = None
        self.ioloop = None
        self.broadcastListnerBox = ListnerBox()
        self.is_runned = False
        self.is_timeout_enabled = False

    def __new_timeout(self):
        if not self.is_timeout_enabled:
            self.is_timeout_enabled = True
            currrent_wait = self.ioloop.add_timeout(self.timeout, self.tic)

    def __generate_message(self):
        self.message = str(random())

    def __get_message_text(self):
        return self.message

    #основной цикл программы
    def run(self, ioloop):
        if not self.is_runned:
            self.ioloop = ioloop
            self.__new_timeout()

    #срабатывает через тайм-аут и инициализирует рассылку
    def tic(self):
        self.is_timeout_enabled = False
        self.__generate_message()

        #осуществляем рассылку
        listners = self.broadcastListnerBox.get_listners()
        for listner in listners:
            listner.set_result(self.__get_message_text())

        #очищаем список слушателей
        self.broadcastListnerBox.clear_listners()
        self.__new_timeout()

    def get_message(self):
        #добавляем информацию о слушателе в список слушателей
        listner_future = Future()
        self.listner = self.broadcastListnerBox.\
                        create_listner(listner_future)
        self.broadcastListnerBox.add_listner(self.listner)
        return listner_future

    def do_not_listen(self, listner):
        self.broadcastListnerBox.delete_listner(listner)

MainBroadcastCycle = BroadcastCycle()

class HomeHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("main.html")


class ListnerHandler(tornado.web.RequestHandler):
    def __init__(self, *args, **kwargs):
        super(ListnerHandler, self).__init__(*args, **kwargs)
        self.broadcastCycle = MainBroadcastCycle

    @gen.coroutine
    def post(self):
        #приостанавливаем выполнение до тех пока 
        #не появится необходимость в рассылке
        self.message_future = self.broadcastCycle.get_message()
        message = yield self.message_future

        #отсылаем сообщение
        self.write({"time": datetime.now().isoformat(), "message": message})

    def on_connection_close(self):
        self.broadcastCycle.do_not_listen(self.message_future)


def run():
    tornado.options.parse_command_line()
    application = tornado.web.Application(
        [
            (r"/", HomeHandler),
            (r"/listen", ListnerHandler),
        ],
        cookie_secret="trhb4ewgah$#$@TWGE@#^%@TEFWDGGREG",
        template_path=os.path.join(os.path.dirname(__file__), "templates"),
        static_path=os.path.join(os.path.dirname(__file__), "static"),
        xsrf_cookies=False,
        debug=options.debug,
    )
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(options.port)
    ioloop = tornado.ioloop.IOLoop.current()
    MainBroadcastCycle.run(ioloop)
    ioloop.start()
    

if __name__ == "__main__":
    run()