import telebot
import pygame
import time
import socket
from threading import Thread

TOKEN = input("Your token: ")
max_message_speed = 0.2
save_freq = 30
banlist = ['bdiaq']

white = (255, 174, 66)
black = (0, 0, 0)

width = 96
height = 64
field = {}

bot = telebot.TeleBot(TOKEN, parse_mode=None)

save_n_load = False


class Server(Thread):
    def __init__(self):
        Thread.__init__(self)

    def run(self):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.bind((socket.gethostbyname(socket.gethostname()), 25500))
        self.s.setblocking(False)

        clients = []

        while True:
            try:



def saveMap():
    f = open('save.txt', 'w')
    f.write(str(field))
    f.close()
    print("Saved field to file")


def loadMap():
    global field
    f = open('save.txt', 'r')
    field = eval(f.read())
    f.close()


class Renderer:
    def __init__(self):
        self.pixelsPerUnit = 13

        pygame.init()
        self.font = pygame.font.SysFont('Arial', self.pixelsPerUnit-1)
        self.sc = pygame.display.set_mode((1+self.pixelsPerUnit*(width),
                                           1+self.pixelsPerUnit*(height)))
        pygame.display.set_caption("Холст")

        img = pygame.image.load("icon.png").convert_alpha()
        pygame.display.set_icon(img)

        self.quit = False

    def render(self):
        if not self.quit:
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    self.quit = True
                    saveMap()
                    pygame.display.quit()
                    bot.stop_bot()
                    return

            self.sc.fill((0,0,0))

            for x in range(width):
                for y in range(height):
                    try:
                        if x == 0:
                            t = self.font.render(str(y-1), True, (255, 255, 255))
                            r = t.get_rect(topleft=(0, y*self.pixelsPerUnit))
                            self.sc.blit(t, r)
                        elif y == 0:
                            t = self.font.render(str(x-1), True, (255, 255, 255))
                            r = t.get_rect(midtop=(x*self.pixelsPerUnit+self.pixelsPerUnit/2, 0))
                            self.sc.blit(t, r)
                        else:
                            pygame.draw.rect(self.sc, field[x-1, y-1],
                                             (x*self.pixelsPerUnit,
                                              y*self.pixelsPerUnit,
                                              self.pixelsPerUnit, self.pixelsPerUnit))
                    except Exception as e:
                        print("Exception in Renderer.render() -", e)

            # Drawing vertical lines
            for x in range(0, width * 2, 8):
                pygame.draw.line(self.sc, (128, 128, 128),
                                 [(x + 1) * self.pixelsPerUnit, 0],
                                 [(x + 1) * self.pixelsPerUnit, height * self.pixelsPerUnit])

            # Drawing horizontal lines
            for y in range(0, height * 2, 8):
                pygame.draw.line(self.sc, (128, 128, 128),
                                 [0, (y+1) * self.pixelsPerUnit],
                                 [width*self.pixelsPerUnit, (y+1) * self.pixelsPerUnit])

            pygame.display.update()

            time.sleep(1/60)


renderingThread = Renderer()


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    string = """
Холст отображается на стриме - https://www.twitch.tv/zelduv
Размер поля - """ + str(width) + 'x' + str(height) + """ пикселей
-------
Доступные комманды
/set x y - Закрасить белым пиксель на координатах x y
/clr x y - Закрасить черным пиксель на координатах x y
/setcolor x y r g b (пример - /setcolor 5 5 255 0 0) - Закрасить пиксель определённым цветом
/help - отобразить этот текст
    """
    bot.reply_to(message, string)


def fieldAsText() -> str:
    s = ''
    for y in range(height):
        for x in range(width):
            if field[x, y] == black:
                s += '⬛'
            elif field[x, y] == white:
                s += '⬜'
            else:
                s += 'u'
        s += '\n'
    return s


def clamp(val, mn, mx):
    if val < mn: return mn
    elif val > mx: return mx
    else: return val


last_user_messages = {}


@bot.message_handler(commands=['set', 'clr', 'clrfill', 'setfill', 'setcolor'])
def echo_all(message: telebot.types.Message):
    global field

    msg = message.text.split(' ')
    try:
        user = message.from_user.username

        if user not in last_user_messages:
            last_user_messages[user] = 0

        if time.time()-last_user_messages[user] > max_message_speed and\
           user not in banlist:
            x, y = int(msg[1]), int(msg[2])
            if 0 <= x < width and 0 <= y < height:
                if msg[0] == '/clr':
                    field[x, y] = black
                elif msg[0] == '/set':
                    field[x, y] = white
                elif msg[0] == '/clrfill' or msg[0] == '/setfill':
                    if user == 'zvmine':
                        clr = black
                        if msg[0] == '/setfill':
                            clr = white

                        for x1 in range(x, int(msg[3])):
                            for y1 in range(y, int(msg[4])):
                                field[x1, y1] = clr
                elif msg[0] == '/setcolor':
                    r,g,b = clamp(int(msg[3]), 0, 255), clamp(int(msg[4]), 0, 255), clamp(int(msg[5]), 0, 255)
                    field[x, y] = (r, g, b)

                print("Message", message.text, "by", message.from_user.first_name, '@'+message.from_user.username)

            last_user_messages[user] = time.time()

    except Exception as e:
        print("Exception /set /clr -", e)


def start():
    global field

    print("Filling field")
    for x in range(192):
        for y in range(108):
            field[x, y] = black

    try:
        loadMap()
    except Exception as e:
        print("Failed to load field from file:", e)

    th = Thread(target=bot.polling)
    th.start()

    lastSave = time.time()
    while True:
        renderingThread.render()

        if time.time() - lastSave >= save_freq:
            try:
                saveMap()

                lastSave = time.time()
            except Exception as e:
                print("Failed to save field to the file:", e)


if __name__ == '__main__':
    start()
